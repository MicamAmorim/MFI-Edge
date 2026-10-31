from __future__ import annotations

"""Stage 23G5: frozen exact-SCO plus persistence-membership equal mean."""

from pathlib import Path
import argparse
import hashlib
import json
import sys

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage23e_cached_descriptor_aggregator_landscape import _fit_membership, _membership, _target
from run_stage23f_literature_validation_frontier import DEFAULT_IMAGE_DIR
from run_stage23g4_sco_persistence_gap_diagnosis import (
    BSDS_GT_DIR, STAGE23F_MODELS, _json, _load_bsds, _load_uded,
)

EXPERIMENT_ID = "stage23g5_sco_persistence_equal_mean"
OUT = ROOT / "results/local_dev" / EXPERIMENT_ID
SEED = 20261031
PREVIEW_UDED = (0, 6, 13)
PREVIEW_BSDS = (0, 49, 99)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _frozen_membership() -> dict[str, np.ndarray]:
    row = next(x for x in _json(STAGE23F_MODELS) if x["set_id"] == "pair_03")
    i = row["descriptors"].index("gabor4_scale_persistence")
    spec = {"midpoint": np.asarray([row["membership_midpoint"][i]], float),
            "scale": np.asarray([row["membership_scale"][i]], float)}
    if not np.allclose(spec["midpoint"], [0.5513500943779945], atol=1e-12):
        raise RuntimeError("frozen persistence midpoint drift")
    if not np.allclose(spec["scale"], [0.2824956402182579], atol=1e-12):
        raise RuntimeError("frozen persistence scale drift")
    return spec


def _transform(raw: np.ndarray, spec: dict[str, np.ndarray]) -> np.ndarray:
    return np.asarray(_membership(np.asarray(raw, float)[..., None], spec)[..., 0], np.float32)


def _candidate(sco: np.ndarray, membership: np.ndarray) -> np.ndarray:
    return np.clip(0.5 * np.asarray(sco, np.float32) + 0.5 * np.asarray(membership, np.float32), 0, 1)


def _png(path: Path, score: np.ndarray) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    value = np.clip(np.rint(np.asarray(score, float) * 255.0), 0, 255).astype(np.uint8)
    tmp = path.with_suffix(path.suffix + ".tmp")
    Image.fromarray(value, mode="L").save(tmp, format="PNG")
    tmp.replace(path)
    return _sha256(path)


def main() -> int:
    global OUT, BSDS_GT_DIR
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--image-dir", default=str(DEFAULT_IMAGE_DIR))
    ap.add_argument("--gt-dir", default=str(BSDS_GT_DIR))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(); OUT = Path(args.out); BSDS_GT_DIR = Path(args.gt_dir)
    spec = _frozen_membership()
    if args.smoke:
        x = np.linspace(0, 1, 17, dtype=np.float32)
        m = _transform(x, spec); c = _candidate(x, m)
        assert np.all(np.isfinite(c)) and np.all((c >= 0) & (c <= 1))
        assert np.all(np.diff(m) >= 0) and np.allclose(c, 0.5 * x + 0.5 * m)
        print("STAGE23G5_SCO_PERSISTENCE_EQUAL_MEAN_SMOKE_OK"); return 0

    OUT.mkdir(parents=True, exist_ok=True)
    uded_items, uded_scores, provenance_u = _load_uded(Path(args.uded_root))
    bsds_items, bsds_scores, provenance_b = _load_bsds(Path(args.image_dir))
    if len(provenance_u) != 14 or len(provenance_b) != 100 or not all(bool(x["cache_hit"]) for x in provenance_u + provenance_b):
        raise RuntimeError("expected 114 exact persistence cache hits")
    folds = _make_repeated_folds(len(uded_items), 3, 5, SEED)
    fold_rows, image_rows, transform_rows = [], [], []
    counts = {"sco": [], "candidate": []}; first_membership = {}; first_candidate = {}
    for repeat, fold, train, valid in folds:
        raw = np.concatenate([uded_scores["cue"][int(i)].ravel() for i in train])[:, None]
        y = np.concatenate([_target(uded_items[int(i)]["gt"]).ravel() for i in train]).astype(float)
        fold_spec = _fit_membership(raw, y)
        train_m = [_transform(uded_scores["cue"][int(i)], fold_spec) for i in train]
        valid_m = [_transform(uded_scores["cue"][int(i)], fold_spec) for i in valid]
        train_base = [uded_scores["target"][int(i)] for i in train]
        valid_base = [uded_scores["target"][int(i)] for i in valid]
        train_cand = [_candidate(s, m) for s, m in zip(train_base, train_m)]
        valid_cand = [_candidate(s, m) for s, m in zip(valid_base, valid_m)]
        base_thr = float(selection_metric(train_base, [uded_items[int(i)] for i in train], 41)["threshold"])
        cand_thr = float(selection_metric(train_cand, [uded_items[int(i)] for i in train], 41)["threshold"])
        base_metric, base_counts, base_images = fixed_eval(valid_base, [uded_items[int(i)] for i in valid], base_thr)
        cand_metric, cand_counts, cand_images = fixed_eval(valid_cand, [uded_items[int(i)] for i in valid], cand_thr)
        counts["sco"].extend(base_counts); counts["candidate"].extend(cand_counts)
        fold_rows.append({"repeat": repeat + 1, "fold": fold + 1, "sco_threshold": base_thr,
                          "candidate_threshold": cand_thr, "membership_midpoint": float(fold_spec["midpoint"][0]),
                          "membership_scale": float(fold_spec["scale"][0]),
                          "sco_precision": base_metric["precision"], "sco_recall": base_metric["recall"], "sco_F1": base_metric["F1"],
                          "candidate_precision": cand_metric["precision"], "candidate_recall": cand_metric["recall"], "candidate_F1": cand_metric["F1"],
                          "delta_F1": cand_metric["F1"] - base_metric["F1"]})
        for idx, b, c in zip(valid, base_images, cand_images):
            image_rows.append({"repeat": repeat + 1, "fold": fold + 1, "image_id": uded_items[int(idx)]["id"],
                               "sco_F1": b["F1"], "candidate_F1": c["F1"], "delta_F1": c["F1"] - b["F1"]})
            if repeat == 0:
                first_membership[int(idx)] = valid_m[list(valid).index(idx)]
                first_candidate[int(idx)] = valid_cand[list(valid).index(idx)]
        transform_rows.append({"domain": "UDED_outer_fold", "repeat": repeat + 1, "fold": fold + 1,
                               "midpoint": float(fold_spec["midpoint"][0]), "scale": float(fold_spec["scale"][0]),
                               "source": "outer-training tolerant-union labels; Stage23E equations"})

    aggregate = {name: aggregate_counts(value) for name, value in counts.items()}
    delta = {k: aggregate["candidate"][k] - aggregate["sco"][k] for k in ("precision", "recall", "F1")}
    frame = pd.DataFrame(fold_rows); wins = int((frame.delta_F1 > 0).sum()); mean_fold_delta = float(frame.delta_F1.mean())
    uded_pass = bool(delta["F1"] >= 0.002 and delta["precision"] >= -0.003 and delta["recall"] >= -0.003 and mean_fold_delta > 0 and wins >= 9)

    bsds_m = [_transform(x, spec) for x in bsds_scores["cue"]]
    bsds_c = [_candidate(s, m) for s, m in zip(bsds_scores["target"], bsds_m)]
    hash_rows, map_provenance = [], []
    bsds_provenance = {x["image_id"]: x for x in provenance_b}
    for item, score in zip(bsds_items, bsds_c):
        path = OUT / "frozen_maps/stage23g5_sco_persistence_equal_mean" / f"{item['id']}.png"
        sidecar = path.with_suffix(".json")
        identity = {"image_id": item["id"], "formula": "0.5*SCO+0.5*sigmoid_persistence",
                    "sco_png_sha256": bsds_provenance[item["id"]]["sco_png_sha256"],
                    "cue_cache_key": bsds_provenance[item["id"]]["cue_cache_key"],
                    "cue_artifact_sha256": bsds_provenance[item["id"]]["cue_artifact_sha256"],
                    "membership_midpoint": float(spec["midpoint"][0]), "membership_scale": float(spec["scale"][0])}
        hit = False
        if path.is_file() and sidecar.is_file():
            prior = _json(sidecar)
            if prior.get("identity") != identity or prior.get("png_sha256") != _sha256(path):
                raise RuntimeError(f"frozen candidate provenance mismatch: {item['id']}")
            png_hash, hit = prior["png_sha256"], True
        else:
            png_hash = _png(path, score)
            payload = {"identity": identity, "png_sha256": png_hash}
            tmp = sidecar.with_suffix(sidecar.suffix + ".tmp")
            tmp.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8"); tmp.replace(sidecar)
        hash_rows.append({"method": "stage23g5_sco_persistence_equal_mean", "image_id": item["id"], "png_sha256": png_hash, "cache_hit": hit})
        map_provenance.append({**identity, "png_sha256": png_hash, "cache_hit": hit})
    transform_rows.append({"domain": "BSDS500_validation", "repeat": 0, "fold": 0,
                           "midpoint": float(spec["midpoint"][0]), "scale": float(spec["scale"][0]),
                           "source": "frozen Stage23F pair-03 all-14-overlap-clean-UDED fit"})

    previews = []
    for items, scores, memberships, candidates, positions in (
        (uded_items, uded_scores, first_membership, first_candidate, PREVIEW_UDED),
        (bsds_items, bsds_scores, {i: x for i, x in enumerate(bsds_m)}, {i: x for i, x in enumerate(bsds_c)}, PREVIEW_BSDS),
    ):
        for i in positions:
            previews.append([items[i]["img"], items[i]["gt"], scores["target"][i], memberships[i], candidates[i]])
    preview = write_panel_grid(OUT / "best_method_preview.png", previews, panel_height=112, panel_width=112, gap=2)
    pd.DataFrame(fold_rows).to_csv(OUT / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(OUT / "per_image_metrics.csv", index=False)
    pd.DataFrame(transform_rows).to_csv(OUT / "transform_provenance.csv", index=False)
    pd.DataFrame(hash_rows).to_csv(OUT / "frozen_map_hashes.csv", index=False)
    with (OUT / "map_provenance.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for row in map_provenance:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    pd.DataFrame(provenance_u + provenance_b).to_csv(OUT / "frozen_input_provenance.csv", index=False)
    export_args = ["--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"]
    official = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": [
        {"name": "exact_author_sco", "export": {"script": "automation/stage23g3_sco_frozen_bsds_export.py", "args": export_args}},
        {"name": "stage23g5_sco_persistence_equal_mean", "export": {"script": "automation/stage23g5_frozen_bsds_export.py", "args": export_args}}],
        "stage23_note": "Compare exact SCO baseline and the single preregistered equal-mean intervention; standard Berkeley only is promotional."}
    (OUT / "official_eval_manifest.json").write_text(json.dumps(official, indent=2), encoding="utf-8")
    summary = {"status": "completed", "experiment_id": EXPERIMENT_ID, "detector_runs": 0,
               "descriptor_computations": 0, "cache_hits": 114, "protected_lineage_bytes_read": False,
               "uded": {"sco": aggregate["sco"], "candidate": aggregate["candidate"], "delta": delta,
                        "mean_fold_F1_delta": mean_fold_delta, "fold_wins": wins, "n_folds": 15, "gate_pass": uded_pass},
               "bsds_candidate_maps": len(hash_rows), "candidate_map_cache_hits": int(sum(bool(x["cache_hit"]) for x in hash_rows)), "incumbent_changed": False,
               "decision_semantics": "Final classification requires official exact-SCO comparison: operational ODS/OIS and ranking AP are separate axes.",
               "visual_preview": {"path": preview.relative_to(ROOT).as_posix(), "selection": "UDED 1/7/14 then BSDS val 1/50/100",
                                  "panel_order": ["input", "GT union", "exact SCO", "persistence membership", "equal mean"], "optimization_use": "documentary only"}}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE23G5_SCO_PERSISTENCE_EQUAL_MEAN_COMPLETED"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
