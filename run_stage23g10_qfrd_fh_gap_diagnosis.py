from __future__ import annotations

"""Stage 23G10: frozen-map QFrD versus FH-region gap diagnosis."""

from pathlib import Path
import csv
import json
import sys

import numpy as np
import pandas as pd
from PIL import Image
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED
from benchmark_uded_stage7 import selection_metric
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage23c_cached_uded_descriptor_baselines import _identity, _implementation_hash, _load_overlap_clean_selection, _sha256
from run_stage23f_literature_validation_frontier import DEFAULT_IMAGE_DIR, _descriptor_identity, _read_image
from run_stage23g1_sed_halfdisc_gap_diagnosis import _metrics
from src.bsds import _extract_boundaries
from src.stage23_cache import load_cached, validate_manifest_record

EXPERIMENT_ID = "stage23g10_qfrd_fh_gap_diagnosis"
OUT = ROOT / "results/local_dev" / EXPERIMENT_ID
CACHE_ROOT = ROOT / "cache/local_dev/stage23"
CUE = "fh_region_boundary"
UDED_TARGET_DIR = ROOT / "results/local_dev/stage23g9_qfrd_overlap_clean_materialization/predictions"
UDED_HASHES = ROOT / "results/local_dev/stage23g9_qfrd_overlap_clean_materialization/map_hashes.json"
BSDS_TARGET_DIR = ROOT / "results/local_dev/stage15i_qfrd_exact_reproduction/predictions"
BSDS_HASHES = BSDS_TARGET_DIR / "map_hashes.json"
BSDS_GT_DIR = ROOT / "evaluation/bsds_official/vendor/BSDS500/BSDS500/data/groundTruth/val"
BSDS_OFFICIAL = ROOT / "results/official_eval/stage15i_qfrd_exact_reproduction/summary.json"
STAGE23C_FOLDS = ROOT / "results/local_dev/stage23c_cached_uded_descriptor_baselines/individual_descriptor_fold_metrics.csv"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _target(path: Path, expected: str) -> np.ndarray:
    if not path.is_file() or _sha256(path) != expected:
        raise RuntimeError(f"frozen QFrD map hash mismatch: {path}")
    value = np.asarray(Image.open(path).convert("L"), np.float32) / 255.0
    if not np.all(np.isfinite(value)):
        raise RuntimeError(f"non-finite QFrD map: {path}")
    return value


def _cue_thresholds() -> tuple[dict[tuple[int, int], float], float]:
    table = pd.read_csv(STAGE23C_FOLDS)
    table = table[table.descriptor_id == CUE]
    folds = {(int(r.repeat), int(r.fold)): float(r.train_threshold) for r in table.itertuples()}
    if len(folds) != 15:
        raise RuntimeError("frozen Stage-23C FH threshold-fold mismatch")
    # FH evidence is binary; the all-development threshold is therefore the
    # preregistered median of the already frozen outer-training thresholds.
    return folds, float(np.median(list(folds.values())))


def _qfrd_metrics(target: np.ndarray, cue: np.ndarray, gt: np.ndarray,
                  target_threshold: float, cue_threshold: float) -> dict[str, float]:
    row = _metrics(target, cue, gt, target_threshold, cue_threshold)
    renames = {
        "sed_threshold": "qfrd_threshold",
        "sed_gt_coverage": "qfrd_gt_coverage",
        "cue_rescue_of_sed_misses": "cue_rescue_of_qfrd_misses",
        "sed_fp_fraction": "qfrd_fp_fraction",
        "p_cue_correct_given_sed_wrong": "p_cue_correct_given_qfrd_wrong",
    }
    return {renames.get(key, key): value for key, value in row.items()}


def _domain_summary(frame: pd.DataFrame) -> dict[str, float]:
    return {
        "n_rows": int(len(frame)),
        "n_unique_images": int(frame.image_id.nunique()),
        "mean_spearman": float(frame.spearman.mean()),
        "mean_cue_unique_gt_fraction": float(frame.cue_unique_gt_fraction.mean()),
        "mean_cue_rescue_of_qfrd_misses": float(frame.cue_rescue_of_qfrd_misses.mean()),
        "mean_cue_unique_fp_fraction": float(frame.cue_unique_fp_fraction.mean()),
        "mean_p_cue_correct_given_qfrd_wrong": float(frame.p_cue_correct_given_qfrd_wrong.mean()),
        "unique_gt_image_fraction": float(frame.groupby("image_id").cue_has_unique_gt.max().mean()),
    }


def _load_uded():
    items, manifest = _load_overlap_clean_selection(DEFAULT_UDED)
    if any(r.get("excluded") and r.get("bytes_read") for r in manifest["records"]):
        raise RuntimeError("protected-lineage bytes read")
    expected, code_hash = _json(UDED_HASHES), _implementation_hash()
    targets, cues, provenance = [], [], []
    for item in items:
        image_id = item["id"]
        target = _target(UDED_TARGET_DIR / f"{image_id}.png", expected[image_id])
        identity = _identity(item, CUE, code_hash)
        cue = load_cached(identity, CACHE_ROOT)
        if cue is None:
            raise RuntimeError(f"forbidden Stage-23C cache miss: {image_id}")
        record = validate_manifest_record(identity, CACHE_ROOT)
        cue = np.asarray(cue, np.float32)
        if target.shape != item["gt"].shape or cue.shape != item["gt"].shape:
            raise RuntimeError(f"UDED shape mismatch: {image_id}")
        targets.append(target); cues.append(cue)
        provenance.append({"domain": "UDED_selection_overlap_clean", "image_id": image_id,
                           "qfrd_png_sha256": expected[image_id], "cue_cache_key": identity.cache_key(),
                           "cue_artifact_sha256": record["artifact_sha256"], "cache_hit": True})
    return items, targets, cues, provenance


def _load_bsds():
    paths, expected, code_hash = sorted(DEFAULT_IMAGE_DIR.glob("*.jpg")), _json(BSDS_HASHES), _implementation_hash()
    if len(paths) != 100:
        raise RuntimeError(f"expected 100 BSDS-val images, found {len(paths)}")
    items, targets, cues, provenance = [], [], [], []
    for path in paths:
        image_id, image = path.stem, _read_image(path)
        gt = np.any(np.stack(_extract_boundaries(loadmat(BSDS_GT_DIR / f"{image_id}.mat"))).astype(bool), axis=0)
        target = _target(BSDS_TARGET_DIR / f"{image_id}.png", expected[image_id])
        identity = _descriptor_identity(image_id, _sha256(path), CUE, code_hash)
        cue = load_cached(identity, CACHE_ROOT)
        if cue is None:
            raise RuntimeError(f"forbidden Stage-23F cache miss: {image_id}")
        record = validate_manifest_record(identity, CACHE_ROOT); cue = np.asarray(cue, np.float32)
        if target.shape != gt.shape or cue.shape != gt.shape:
            raise RuntimeError(f"BSDS shape mismatch: {image_id}")
        items.append({"id": image_id, "img": image, "gt": gt}); targets.append(target); cues.append(cue)
        provenance.append({"domain": "BSDS500_validation", "image_id": image_id,
                           "qfrd_png_sha256": expected[image_id], "cue_cache_key": identity.cache_key(),
                           "cue_artifact_sha256": record["artifact_sha256"], "cache_hit": True})
    return items, targets, cues, provenance


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cue_thresholds, bsds_cue_threshold = _cue_thresholds()
    ui, ut, uc, up = _load_uded(); bi, bt, bc, bp = _load_bsds()
    rows, target_thresholds = [], {}
    for repeat, fold, train, valid in _make_repeated_folds(len(ui), 3, 5, 20261031):
        key = (repeat + 1, fold + 1)
        target_thresholds[key] = float(selection_metric([ut[int(i)] for i in train], [ui[int(i)] for i in train], 41)["threshold"])
        for index in valid:
            i = int(index)
            rows.append({"domain": "UDED_selection_overlap_clean", "repeat": key[0], "fold": key[1], "image_id": ui[i]["id"],
                         **_qfrd_metrics(ut[i], uc[i], ui[i]["gt"], target_thresholds[key], cue_thresholds[key])})
    official = _json(BSDS_OFFICIAL)
    bsds_target_threshold = float(official["methods"]["stage15i_exact_author_qfrd"]["ODS_threshold"])
    for item, target, cue in zip(bi, bt, bc):
        rows.append({"domain": "BSDS500_validation", "repeat": 0, "fold": 0, "image_id": item["id"],
                     **_qfrd_metrics(target, cue, item["gt"], bsds_target_threshold, bsds_cue_threshold)})
    frame = pd.DataFrame(rows)
    if len(frame) != 170 or not np.all(np.isfinite(frame.select_dtypes(include=[np.number]).to_numpy(float))):
        raise RuntimeError("Stage-23G10 diagnostic cardinality/finite contract failed")
    domains = ("UDED_selection_overlap_clean", "BSDS500_validation")
    summaries = {name: _domain_summary(frame[frame.domain == name]) for name in domains}
    checks = {name: {"unique_gt_at_least_0p02": s["mean_cue_unique_gt_fraction"] >= 0.02,
                     "conditional_correctness_at_least_0p50": s["mean_p_cue_correct_given_qfrd_wrong"] >= 0.50,
                     "unique_gt_on_at_least_0p60_images": s["unique_gt_image_fraction"] >= 0.60,
                     "mean_spearman_at_most_0p80": s["mean_spearman"] <= 0.80} for name, s in summaries.items()}
    gap_supported = all(all(v.values()) for v in checks.values())
    frame.to_csv(OUT / "per_image_gap_metrics.csv", index=False)
    pd.DataFrame(up + bp).to_csv(OUT / "frozen_input_provenance.csv", index=False)
    with (OUT / "threshold_provenance.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["domain", "method", "threshold", "source"]); writer.writeheader()
        for key in sorted(target_thresholds):
            writer.writerow({"domain": f"UDED_repeat{key[0]}_fold{key[1]}", "method": "QFrD", "threshold": target_thresholds[key], "source": "Stage23G10 outer-training diagnostic fit"})
            writer.writerow({"domain": f"UDED_repeat{key[0]}_fold{key[1]}", "method": CUE, "threshold": cue_thresholds[key], "source": "Stage23C outer-training fold"})
        writer.writerow({"domain": "BSDS500_validation", "method": "QFrD", "threshold": bsds_target_threshold, "source": "Stage15I existing official ODS"})
        writer.writerow({"domain": "BSDS500_validation", "method": CUE, "threshold": bsds_cue_threshold, "source": "median of frozen Stage23C outer-training thresholds"})
    preview_rows = [[items[i]["img"], items[i]["gt"], targets[i], cues[i]]
                    for items, targets, cues, positions in ((ui, ut, uc, (0, 6, 13)), (bi, bt, bc, (0, 49, 99))) for i in positions]
    preview_path = write_panel_grid(OUT / "best_method_preview.png", preview_rows, panel_height=112, panel_width=112, gap=2)
    manifest = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": [],
                "analysis_only_note": "Frozen QFrD/FH gap diagnosis; no candidate map. Official attachment is incumbent-only."}
    (OUT / "official_eval_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary = {"status": "completed", "experiment_id": EXPERIMENT_ID, "role": "frozen_strong_detector_gap_diagnosis",
               "target": "exact pinned-author QFrD", "missing_evidence_hypothesis": CUE, "detector_runs": 0,
               "descriptor_computations": 0, "cache_hits": 114, "protected_lineage_bytes_read": False,
               "summaries": summaries, "preregistered_checks": checks, "gap_supported": gap_supported,
               "decision_semantics": "A pass authorizes only a separate prospective intervention decision; no fusion is preselected. Failure closes QFrD/FH without substitution.",
               "incumbent_changed": False, "visual_preview": {"path": preview_path.relative_to(ROOT).as_posix(),
               "selection": "UDED 1/7/14 then BSDS-val 1/50/100", "panel_order": ["input", "GT union", "exact QFrD", "cached FH region boundary"],
               "optimization_use": "documentary only"}, "official_attachment": "incumbent-only; no candidate exists"}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE23G10_QFRD_FH_GAP_DIAGNOSIS_COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
