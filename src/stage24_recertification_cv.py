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

from run_stage24_residual_campaign import select_pair, train_normalized, pair_proxy
from src.stage23_descriptors import DESCRIPTOR_IDS
from src.stage24_integrity import one_to_one_boundary_counts, aggregate_counts
from src.stage24_residual import (
    apply_membership, fit_membership, fit_residual_gate, apply_suppressor,
)
from src.stage24_recertification_ops import (
    AGGREGATORS, THINNING, SUPPRESSORS, CALIBRATION_MODES,
    calibrate_memberships, score_distribution_diagnostics,
    deterministic_seed, fit_aggregator,
    apply_aggregator, thin_score, binary_map, choose_threshold, serialize_model,
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
            seed=deterministic_seed(SEED, "shared_aggregator", key[0], key[2], name),
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
                seed=deterministic_seed(SEED, "shared_gate", key[0], key[2], name),
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


def select_inner_recipe(group, items, maps, outer_train, candidates, seed, count=13):
    """Genuine inner CV for every promoted recipe, including suppression/thinning."""
    split_plan = list(_inner_splits(outer_train, seed, 3))
    out = []
    for name, mode in candidates:
        if mode not in TRANSFER_MODES:
            continue
        for suppression in SUPPRESSORS:
            folds = []
            failed = None
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
            out.append({"aggregator": name, "mode": mode,
                        "suppressor": suppression[0], "strength": suppression[1],
                        "mean_inner_F1": (float(np.mean(folds)) if len(folds) == len(split_plan) else None),
                        "error": failed})
    valid = [x for x in out if x["mean_inner_F1"] is not None]
    if not valid:
        raise RuntimeError("No valid inner model for " + str(group))
    # Explicit deterministic tie breaker, not outer held-out feedback.
    valid.sort(key=lambda x: (-x["mean_inner_F1"], x["aggregator"],
                              x["mode"], x["suppressor"], x["strength"]))
    return valid[0], out


def run_group(group, items, maps, train, valid, fold_id, out, cfg):
    """Fixed factorial landscape plus inner-CV chosen recipe and matched ablations."""
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
    landscape = []
    per_image = []
    for name in AGGREGATORS:
        for mode in THINNING:
            seed = deterministic_seed(cfg["seed"], fold_id, group, name, mode)
            try:
                row = fit_and_score(group, name, items, maps, train, valid, mode,
                                    seed=seed, count=cfg["threshold_count"])
            except (ValueError, RuntimeError, FloatingPointError) as exc:
                landscape.append({"group": "|".join(group), "arity": len(group),
                                  "aggregator": name, "thinning": mode,
                                  "status": "failed", "error": str(exc),
                                  "train_F1": None, "validation_F1": None})
                continue
            per_image.extend(row.pop("per_image"))
            row.pop("model")
            row["status"] = "completed"
            landscape.append(row)
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


def individual_descriptor_baselines(items, maps, train, valid, fold, count=21):
    from src.stage24_residual import MembershipModel
    results, per_image = [], []
    gts = [v["gt"] for v in items]
    for name in DESCRIPTOR_IDS:
        mem = fit_membership([maps[name]], gts, train)
        scores = [apply_membership([maps[name][i]], mem)[..., 0] for i in range(len(items))]
        for mode in TRANSFER_MODES:
            threshold, ctrain = choose_threshold(
                [scores[int(i)] for i in train], subset(items, train, "gt"),
                subset(items, train, "img"), mode, count=count,
            )
            c, detail = _heldout_rows(scores, items, valid, threshold, mode, {
                "fold": fold, "descriptor_id": name, "thinning": mode,
                "threshold": threshold,
            })
            per_image.extend(detail)
            results.append({"fold": fold, "descriptor_id": name, "thinning": mode,
                            "threshold": threshold, "train_F1": ctrain.f1,
                            "validation_F1": c.f1, "tp": c.tp, "fp": c.fp, "fn": c.fn})
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
