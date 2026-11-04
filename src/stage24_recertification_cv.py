from __future__ import annotations
"""Resumable Stage 24G/H/I inner/outer train-only recertification.

This module NEVER uses outer held-out labels to choose a descriptor group,
aggregator, suppressor, thinning variant or threshold.
"""
from collections import Counter
from itertools import combinations
import hashlib
import csv
import json
from pathlib import Path

import numpy as np
from skimage.transform import resize
from tqdm.auto import tqdm

from run_stage24_residual_campaign import select_pair, train_normalized, pair_proxy
from src.stage23_descriptors import DESCRIPTOR_IDS
from src.stage24_integrity import one_to_one_boundary_counts, aggregate_counts
from src.stage24_residual import (
    apply_membership, fit_membership, fit_residual_gate, apply_suppressor,
)
from src.stage24_recertification_ops import (
    SEED as AGGREGATOR_FIT_SEED,
    AGGREGATORS, THINNING, SUPPRESSORS, CALIBRATION_MODES,
    calibrate_memberships, score_distribution_diagnostics,
    deterministic_seed, fit_aggregator,
    apply_aggregator, thin_score, binary_map, choose_threshold, serialize_model,
    inference_recipe,
)

HISTORIC_PAIRS = (
    ("gabor4_scale_persistence", "structure_tensor_coherence"),
    ("gabor4_scale_persistence", "halfdisc_distribution_contrast"),
    ("halfdisc_distribution_contrast", "fh_region_boundary"),
    ("halfdisc_distribution_contrast", "pmi_dependency_deficit"),
)
HISTORIC_TRIPLES = (
    ("fh_region_boundary", "halfdisc_distribution_contrast", "structure_tensor_coherence"),
    ("gabor4_scale_persistence", "pmi_dependency_deficit", "structure_tensor_coherence"),
)
TRANSFER_MODES = ("raw", "nms_image")

# Cache is confined to the current group; it never includes validation GT.
_MEMBERSHIP_CACHE = {}
_AGGREGATOR_CACHE = {}
_GATE_CACHE = {}
_BASE_CACHE = {}


def clear_group_cache():
    _MEMBERSHIP_CACHE.clear()
    _AGGREGATOR_CACHE.clear()
    _GATE_CACHE.clear()
    _BASE_CACHE.clear()


def _training_key(group, items, train):
    return (tuple(group), id(items), tuple(sorted(int(i) for i in train)))


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str), encoding="utf-8")
    tmp.replace(path)


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def subset(items, idx, key):
    return [items[int(i)][key] for i in idx]


def group_maps(maps, group):
    return [maps[k] for k in group]


def memberships_on_split(group, maps, gts, train, calibration_mode="legacy_sigmoid"):
    # Each fitted membership sees only training GT; reuse across aggregator modes.
    key = (tuple(group), id(maps), tuple(sorted(int(i) for i in train)), calibration_mode)
    if key not in _MEMBERSHIP_CACHE:
        cue = group_maps(maps, group)
        mem = fit_membership(cue, gts, train)
        arrays = [calibrate_memberships(
            apply_membership([c[i] for c in cue], mem), mem, calibration_mode)
            for i in range(len(gts))]
        _MEMBERSHIP_CACHE[key] = (mem, arrays)
    return _MEMBERSHIP_CACHE[key]


def train_pair_screen(items, maps, train):
    gts = [i["gt"] for i in items]
    norm = train_normalized(maps, gts, train)
    rows = []
    for p in combinations(DESCRIPTOR_IDS, 2):
        s = pair_proxy(norm[p[0]], norm[p[1]], gts, train)
        rows.append({"a": p[0], "b": p[1], "score": float(s)})
    rows.sort(key=lambda x: (-x["score"], x["a"], x["b"]))
    return rows


def choose_groups(pair_rows, n_pairs=3, n_triples=2):
    pairs = [tuple(sorted((r["a"], r["b"]))) for r in pair_rows]
    selected = list(dict.fromkeys(pairs[:n_pairs] + [tuple(sorted(p)) for p in HISTORIC_PAIRS]))
    selected = selected[:n_pairs + len(HISTORIC_PAIRS)]
    pair_scores = {tuple(sorted((r["a"], r["b"]))): r["score"] for r in pair_rows}
    tr = []
    for group in combinations(DESCRIPTOR_IDS, 3):
        edges = [tuple(sorted(x)) for x in combinations(group, 2)]
        score = float(np.mean([pair_scores[p] for p in edges]))
        tr.append((score, group))
    tr.sort(key=lambda x: (-x[0], x[1]))
    triplets = [tuple(sorted(g)) for _, g in tr[:n_triples]]
    triplets += [tuple(sorted(g)) for g in HISTORIC_TRIPLES]
    triplets = list(dict.fromkeys(triplets))
    return selected, triplets


def _heldout_rows(scores, items, valid, threshold, mode, identifiers):
    counts = []
    detail = []
    for i in valid:
        idx = int(i)
        item = items[idx]
        arr = thin_score(scores[idx], mode, item["img"])
        c = one_to_one_boundary_counts(binary_map(arr, threshold, mode), item["gt"])
        counts.append(c)
        detail.append({**identifiers, "image_id": item["id"], "tp": c.tp,
                       "fp": c.fp, "fn": c.fn, "precision": c.precision,
                       "recall": c.recall, "F1": c.f1})
    total = aggregate_counts(counts)
    return total, detail


def fit_and_score(group, name, items, maps, train, valid, mode, count=21, seed=0,
                  suppression=("identity", 1.0), calibration_mode="legacy_sigmoid"):
    gts = [v["gt"] for v in items]
    mem, ms = memberships_on_split(group, maps, gts, train, calibration_mode)
    # Model parameters must NOT change between raw/NMS or suppressor ablations.
    key = (tuple(group), id(maps), tuple(sorted(int(i) for i in train)),
           name, calibration_mode)
    if key not in _AGGREGATOR_CACHE:
        _AGGREGATOR_CACHE[key] = fit_aggregator(
            name, ms, gts, train,
            seed=deterministic_seed(AGGREGATOR_FIT_SEED, "shared_aggregator", key[0], key[2], name),
        )
    agg = _AGGREGATOR_CACHE[key]
    if key not in _BASE_CACHE:
        _BASE_CACHE[key] = [apply_aggregator(m, agg) for m in ms]
    base = _BASE_CACHE[key]
    gate = None
    if suppression[0] == "learned_gate":
        if key not in _GATE_CACHE:
            _GATE_CACHE[key] = fit_residual_gate(
                base, ms, gts, train,
                seed=deterministic_seed(AGGREGATOR_FIT_SEED, "shared_gate", key[0], key[2], name),
            )
        gate = _GATE_CACHE[key]
    scores = [
        apply_suppressor(base[i], ms[i], kind=suppression[0],
                         parameter=suppression[1], gate_model=gate)
        for i in range(len(items))
    ]
    threshold, training = choose_threshold(
        [scores[int(i)] for i in train], subset(items, train, "gt"),
        subset(items, train, "img"), mode, count=count,
    )
    identifiers = {
        "group": "|".join(group), "arity": len(group), "aggregator": name,
        "thinning": mode, "suppressor": suppression[0],
        "strength": suppression[1],
        "threshold": threshold, "calibration_mode": calibration_mode,
    }
    heldout, per_image = _heldout_rows(scores, items, valid, threshold, mode, identifiers)
    model = serialize_model(group, mem, agg, suppression, mode, gate,
                            calibration_mode=calibration_mode)
    model["threshold"] = threshold
    return {
        **identifiers, "train_F1": training.f1,
        "validation_F1": heldout.f1, "validation_precision": heldout.precision,
        "validation_recall": heldout.recall, "tp": heldout.tp,
        "fp": heldout.fp, "fn": heldout.fn,
        "per_image": per_image, "model": model,
    }


def _inner_splits(train, seed, count=3):
    train = np.asarray(train, int).copy()
    rng = np.random.default_rng(seed)
    rng.shuffle(train)
    for heldout in np.array_split(train, count):
        tr = np.asarray([i for i in train if i not in set(heldout)], int)
        if len(tr) and len(heldout):
            yield tr, heldout


def select_inner_recipe(group, items, maps, outer_train, candidates, seed, count=13,
                        *, checkpoint_dir=None, signature=None, stop_requested=None):
    """Genuine inner CV for each train-only recipe; resumable at candidate boundary."""
    split_plan = list(_inner_splits(outer_train, seed, 3))
    folder = Path(checkpoint_dir) if checkpoint_dir is not None else None
    if folder is not None:
        folder.mkdir(parents=True, exist_ok=True)
        if not signature:
            raise ValueError("Signature required for inner-CV checkpoints")
    out = []
    n_tasks = sum(1 for _, mode in candidates if mode in TRANSFER_MODES) * len(SUPPRESSORS)
    with tqdm(total=n_tasks, desc="train-only inner CV", position=2, leave=False,
              unit="recipe", dynamic_ncols=True) as inner_bar:
        for name, mode in candidates:
            if mode not in TRANSFER_MODES:
                continue
            for suppression in SUPPRESSORS:
                if stop_requested is not None and stop_requested():
                    raise Stage24StopRequested("Stop between inner-CV recipes")
                key = (name, mode, suppression[0], float(suppression[1]))
                spec = {"schema": 1, "group": list(group), "candidate": list(key),
                        "signature": signature, "seed": int(seed), "count": int(count),
                        "outer_train": sorted(int(i) for i in outer_train)}
                filename = (name + "__" + mode + "__" + suppression[0] + "__" +
                            str(suppression[1]).replace(".", "_") + ".json")
                part_path = folder / filename if folder is not None else None
                if part_path is not None and part_path.exists():
                    stored = json.loads(part_path.read_text(encoding="utf-8"))
                    if stored.get("spec") != spec or not isinstance(stored.get("row"), dict):
                        raise RuntimeError("Inner-CV checkpoint mismatch: " + str(part_path))
                    row = stored["row"]
                    if (row.get("aggregator"), row.get("mode"),
                        row.get("suppressor"), row.get("strength")) != key:
                        raise RuntimeError("Malformed inner-CV checkpoint: " + str(part_path))
                    inner_bar.set_postfix_str(name + " cached", refresh=False)
                else:
                    folds = []
                    failed = None
                    inner_bar.set_postfix_str(name + " " + mode + " " + suppression[0],
                                            refresh=False)
                    for j, (tr, va) in enumerate(split_plan):
                        try:
                            res = fit_and_score(
                                group, name, items, maps, tr, va, mode, count=count,
                                seed=deterministic_seed(seed, name, mode, suppression, j),
                                suppression=suppression,
                            )
                            folds.append(res["validation_F1"])
                        except (ValueError, RuntimeError) as exc:
                            failed = str(exc)
                            break
                    row = {"aggregator": name, "mode": mode,
                           "suppressor": suppression[0], "strength": suppression[1],
                           "mean_inner_F1": (float(np.mean(folds)) if len(folds) == len(split_plan) else None),
                           "error": failed}
                    if part_path is not None:
                        write_json(part_path, {"spec": spec, "row": row})
                out.append(row)
                inner_bar.update(1)
    valid = [x for x in out if x["mean_inner_F1"] is not None]
    if not valid:
        raise RuntimeError("No valid inner model for " + str(group))
    # Explicit deterministic tie breaker, not outer held-out feedback.
    valid.sort(key=lambda x: (-x["mean_inner_F1"], x["aggregator"],
                              x["mode"], x["suppressor"], x["strength"]))
    return valid[0], out

def _checkpoint_piece(path, spec, builder):
    """Load an exact signed partial result, or write the completed unit atomically."""
    path = Path(path)
    if path.is_file():
        stored = json.loads(path.read_text(encoding="utf-8"))
        if stored.get("spec") != spec or not isinstance(stored.get("value"), dict):
            raise RuntimeError("Group partial checkpoint mismatch: " + str(path))
        return stored["value"]
    value = builder()
    write_json(path, {"spec": spec, "value": value})
    return value


def run_group(group, items, maps, train, valid, fold_id, out, cfg,
              *, stop_requested=None):
    """Fixed factorial landscape with signed, resumable train-only checkpoints."""
    path = out / "folds" / fold_id / ("__".join(group) + ".json")
    sources = [
        Path(__file__), Path(__file__).with_name("stage24_recertification_ops.py"),
        Path(__file__).with_name("stage24_integrity.py"),
        Path(__file__).with_name("stage24_residual.py"),
    ]
    source_hashes={str(p.name):hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sources}
    configuration = {"source_sha256": source_hashes,
                     "cfg": cfg, "aggregators": AGGREGATORS,
                     "thinning": THINNING, "suppressors": SUPPRESSORS,
                     "calibrations": CALIBRATION_MODES,
                     "protocol": "native_GT_one_to_one_v1"}
    signature = hashlib.sha256(json.dumps(
        configuration, sort_keys=True, default=str).encode()).hexdigest()
    if path.exists():
        stored = json.loads(path.read_text(encoding="utf-8"))
        if stored.get("config_sha256") != signature:
            raise RuntimeError("Checkpoint configuration mismatch: " + str(path))
        return stored
    clear_group_cache()
    parts_dir = out / "folds" / fold_id / "group_parts" / "__".join(group)
    parts_dir.mkdir(parents=True, exist_ok=True)

    def piece_spec(kind, **fields):
        return {"schema": 1, "signature": signature, "fold_id": fold_id,
                "group": list(group), "kind": kind, **fields}

    landscape = []
    per_image = []
    with tqdm(total=len(AGGREGATORS)*len(THINNING),
              desc=f"operators {fold_id} ({len(group)} cues)",
              position=2, leave=False, unit="config",
              dynamic_ncols=True, mininterval=0.75) as agg_bar:
        for name in AGGREGATORS:
            for mode in THINNING:
                if stop_requested is not None and stop_requested():
                    clear_group_cache()
                    raise Stage24StopRequested("Stop between operator configurations")
                seed = deterministic_seed(cfg["seed"], fold_id, group, name, mode)
                spec = piece_spec("landscape", aggregator=name, thinning=mode,
                                  seed=seed)

                def build_operator():
                    try:
                        row = fit_and_score(group, name, items, maps, train, valid,
                                            mode, seed=seed,
                                            count=cfg["threshold_count"])
                    except (ValueError, RuntimeError, FloatingPointError) as exc:
                        return {"row": {"group": "|".join(group), "arity": len(group),
                                        "aggregator": name, "thinning": mode,
                                        "status": "failed", "error": str(exc),
                                        "train_F1": None, "validation_F1": None},
                                "per_image": []}
                    detail = row.pop("per_image")
                    row.pop("model")
                    row["status"] = "completed"
                    return {"row": row, "per_image": detail}

                agg_bar.set_postfix_str(name + " " + mode, refresh=False)
                piece = _checkpoint_piece(
                    parts_dir / "landscape" / (name + "__" + mode + ".json"),
                    spec, build_operator,
                )
                if not isinstance(piece.get("row"), dict) or not isinstance(piece.get("per_image"), list):
                    raise RuntimeError("Malformed landscape partial checkpoint")
                landscape.append(piece["row"])
                per_image.extend(piece["per_image"])
                agg_bar.update(1)
    # Failures remain explicit in the landscape; outer held-out never selects models.
    ordered = sorted((r for r in landscape if r["train_F1"] is not None),
                     key=lambda r: (-r["train_F1"], r["aggregator"], r["thinning"]))
    if not ordered:
        raise RuntimeError("No valid aggregation for group " + str(group))
    finalists = [(r["aggregator"], r["thinning"]) for r in ordered[:cfg["inner_top"]]]
    # Include core mathematical controls even if train-only screening misses them.
    finalists += [(name, "raw") for name in
                  ("equal_mean", "choquet_positive_2add", "choquet_signed_2add",
                   "sugeno_additive", "owa_centered")]
    finalists = list(dict.fromkeys(finalists))
    selected, inner = select_inner_recipe(
        group, items, maps, train, finalists,
        deterministic_seed(cfg["seed"], "inner", fold_id, group),
        count=cfg["inner_threshold_count"],
        checkpoint_dir=parts_dir / "inner", signature=signature,
        stop_requested=stop_requested,
    )
    selected_result = fit_and_score(
        group, selected["aggregator"], items, maps, train, valid, selected["mode"],
        seed=deterministic_seed(cfg["seed"], "selected", fold_id, group),
        count=cfg["threshold_count"],
        suppression=(selected["suppressor"], selected["strength"]),
    )
    winner_image = selected_result.pop("per_image")
    selected_result.pop("model")
    ablations = []
    ablation_summaries = []
    for supp in SUPPRESSORS:
        ab = fit_and_score(
            group, selected["aggregator"], items, maps, train, valid, selected["mode"],
            seed=deterministic_seed(cfg["seed"], "ablation", fold_id, group),
            count=cfg["threshold_count"], suppression=supp,
        )
        ablations.extend(ab.pop("per_image"))
        ab.pop("model")
        ab["fold"] = fold_id
        ablation_summaries.append(ab)
    # Calibration-by-thinning/suppression ablation on matched outer held-out.
    # Does not alter candidate discovery or the frozen recipe.
    cal_rows, cal_images, histograms = [], [], []
    for calibration in CALIBRATION_MODES:
        for calibration_thinning in TRANSFER_MODES:
            for cal_suppression in dict.fromkeys(
                (("identity",1.0),
                 (selected["suppressor"],selected["strength"]))):
                try:
                    cr = fit_and_score(
                        group, selected["aggregator"], items, maps, train, valid,
                        calibration_thinning,
                        seed=deterministic_seed(cfg["seed"],"calibration",fold_id,group),
                        count=cfg["threshold_count"],
                        suppression=cal_suppression,
                        calibration_mode=calibration,
                    )
                    cr["fold"] = fold_id
                    cal_images.extend(cr.pop("per_image"))
                    cr.pop("model")
                    cal_rows.append(cr)
                except (ValueError,RuntimeError) as exc:
                    cal_rows.append({"group":"|".join(group), "fold":fold_id,
                                     "calibration_mode":calibration,
                                     "aggregator":selected["aggregator"],
                                     "thinning":calibration_thinning,
                                     "suppressor":cal_suppression[0],
                                     "strength":cal_suppression[1],
                                     "status":"failed","error":str(exc)})
        mem, ms = memberships_on_split(group, maps, [x["gt"] for x in items],
                                        train, calibration_mode=calibration)
        for ii in valid:
            idx=int(ii)
            for channel,desc in enumerate(group):
                histograms.append(score_distribution_diagnostics(
                    ms[idx][...,channel],items[idx]["id"],
                    "calibration="+calibration+"|cue="+desc))
    # Inspect the final continuous scores as well as individual memberships;
    # this is essential to diagnose Berkeley 99-grid AP compression.
    for agg_name,diag_supp in dict.fromkeys((
        (selected["aggregator"],("identity",1.0)),
        (selected["aggregator"],(selected["suppressor"],selected["strength"])),
        ("equal_mean",("identity",1.0)),
    )):
        if agg_name not in AGGREGATORS:continue
        try:
            probe=fit_and_score(
                group,agg_name,items,maps,train,valid,selected["mode"],
                count=cfg["threshold_count"],suppression=diag_supp)
            model=probe["model"]
            for ii in valid:
                idx=int(ii)
                score=inference_recipe(
                    [maps[d][idx] for d in group],model,items[idx]["img"])
                histograms.append(score_distribution_diagnostics(
                    score,items[idx]["id"],
                    "final_score|aggregator="+agg_name+
                    "|suppressor="+diag_supp[0]+
                    "|thinning="+selected["mode"]))
        except (ValueError,RuntimeError) as exc:
            histograms.append({"label":"final_score_probe_failed",
                               "aggregator":agg_name,
                               "error":str(exc)})
    result = {"fold_id": fold_id, "group": list(group),
              "config_sha256": signature,
              "landscape": landscape, "landscape_per_image": per_image,
              "selected": selected, "selected_outer": selected_result,
              "selected_per_image": winner_image, "inner": inner,
              "suppression_ablation": ablation_summaries,
              "suppression_ablation_per_image": ablations,
              "calibration_ablation": cal_rows,
              "calibration_ablation_per_image": cal_images,
              "membership_score_histograms": histograms}
    write_json(path, result)
    clear_group_cache()
    return result


class Stage24StopRequested(RuntimeError):
    """Cooperative stop at a completed scientific checkpoint boundary."""


def individual_descriptor_baselines(
    items, maps, train, valid, fold, count=21, *, checkpoint_dir=None,
    stop_requested=None, show_progress=False,
):
    """Resumable individual baselines: one atomic checkpoint per cue and mode.

    Existing source/configuration protection is enforced by the parent campaign.
    Each part additionally records its fold, split indices and search count.
    The final summary and per-image schema remain unchanged.
    """
    results, per_image = [], []
    gts = [v["gt"] for v in items]
    folder = Path(checkpoint_dir) if checkpoint_dir is not None else None
    if folder is not None:
        folder.mkdir(parents=True, exist_ok=True)
    n_modes = len(DESCRIPTOR_IDS) * len(TRANSFER_MODES)
    with tqdm(total=n_modes, desc=f"{fold} individual descriptors",
              position=1, leave=False, unit="mode",
              dynamic_ncols=True, disable=not show_progress) as cue_bar:
        for name in DESCRIPTOR_IDS:
            scores = None
            for mode in TRANSFER_MODES:
                if stop_requested is not None and stop_requested():
                    raise Stage24StopRequested("Stop before individual descriptor " + name)
                spec = {"schema": 1, "fold": fold, "descriptor_id": name,
                        "thinning": mode, "threshold_count": int(count),
                        "train_indices": sorted(int(i) for i in train),
                        "valid_indices": sorted(int(i) for i in valid)}
                part_path = folder / (name + "__" + mode + ".json") if folder else None
                if part_path is not None and part_path.exists():
                    part = json.loads(part_path.read_text(encoding="utf-8"))
                    if (part.get("spec") != spec or
                            not isinstance(part.get("summary"), dict) or
                            not isinstance(part.get("per_image"), list)):
                        raise RuntimeError("Individual checkpoint mismatch: " + str(part_path))
                    row, detail = part["summary"], part["per_image"]
                    if (row.get("descriptor_id") != name or row.get("thinning") != mode or
                            row.get("fold") != fold or
                            len(detail) != len(valid)):
                        raise RuntimeError("Malformed individual checkpoint: " + str(part_path))
                    cue_bar.set_postfix_str(name + " " + mode + " cached", refresh=False)
                else:
                    if scores is None:
                        mem = fit_membership([maps[name]], gts, train)
                        scores = [apply_membership([maps[name][i]], mem)[..., 0]
                                  for i in range(len(items))]
                    with tqdm(total=0, desc=name + " " + mode + " thresholds",
                              position=2, leave=False, unit="threshold",
                              dynamic_ncols=True, disable=not show_progress) as threshold_bar:
                        def on_threshold(done, total):
                            threshold_bar.total = total
                            threshold_bar.n = done
                            threshold_bar.refresh()
                        threshold, ctrain = choose_threshold(
                            [scores[int(i)] for i in train], subset(items, train, "gt"),
                            subset(items, train, "img"), mode, count=count,
                            progress=on_threshold if show_progress else None,
                        )
                    c, detail = _heldout_rows(scores, items, valid, threshold, mode, {
                        "fold": fold, "descriptor_id": name, "thinning": mode,
                        "threshold": threshold,
                    })
                    row = {"fold": fold, "descriptor_id": name, "thinning": mode,
                           "threshold": threshold, "train_F1": ctrain.f1,
                           "validation_F1": c.f1, "tp": c.tp, "fp": c.fp, "fn": c.fn}
                    if part_path is not None:
                        write_json(part_path, {"spec": spec, "summary": row,
                                               "per_image": detail})
                    cue_bar.set_postfix_str(name + " " + mode + " saved", refresh=False)
                results.append(row)
                per_image.extend(detail)
                cue_bar.update(1)
    return results, per_image


def geometry_audit(items, maps, train, pair_rows, fold):
    """Isolate GT GEOMETRY for the SAME Stage24 proxy; NOT Stage23D score."""
    from src.stage24_residual import fit_membership
    original_gts = [item["gt"] for item in items]
    inf_shapes = [i["inference_img"].shape[:2] for i in items]
    legacy_gts = [resize(g.astype(np.uint8), shape, order=0, preserve_range=True,
                         anti_aliasing=False) > .5
                  for g, shape in zip(original_gts, inf_shapes)]
    rows = []
    for r in pair_rows:
        p = (r["a"], r["b"])
        raw = [[resize(maps[d][j], inf_shapes[j], order=1,
                       preserve_range=True, anti_aliasing=True).astype(np.float32)
                for j in range(len(items))] for d in p]
        a = [apply_membership([v], fit_membership([raw[0]], legacy_gts, train))[..., 0]
             for v in raw[0]]
        b = [apply_membership([v], fit_membership([raw[1]], legacy_gts, train))[..., 0]
             for v in raw[1]]
        old_proxy = pair_proxy(a, b, legacy_gts, train)
        rows.append({"fold": fold, "a": p[0], "b": p[1],
                     "stage24_proxy_native": r["score"],
                     "stage24_proxy_legacy_geometry": float(old_proxy),
                     "delta_geometry_proxy": float(r["score"] - old_proxy),
                     "caution": "same Stage24 proxy; resampled cached float evidence; not a historical Stage23D reproduction"})
    return rows
