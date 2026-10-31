from __future__ import annotations

"""Stage 23G4: frozen-map SCO versus Gabor-persistence gap diagnosis."""

from pathlib import Path
import argparse
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
from run_stage23c_cached_uded_descriptor_baselines import (
    _identity,
    _implementation_hash,
    _load_overlap_clean_selection,
    _sha256,
)
from run_stage23f_literature_validation_frontier import (
    DEFAULT_IMAGE_DIR,
    _descriptor_identity,
    _read_image,
)
from run_stage23g1_sed_halfdisc_gap_diagnosis import _domain_summary, _metrics
from src.bsds import _extract_boundaries
from src.stage23_cache import load_cached, validate_manifest_record


EXPERIMENT_ID = "stage23g4_sco_persistence_gap_diagnosis"
OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
CACHE_ROOT = ROOT / "cache" / "local_dev" / "stage23"
CUE = "gabor4_scale_persistence"
UDED_SCO_DIR = ROOT / "results/local_dev/stage23g3_sco_overlap_clean_materialization/predictions"
UDED_SCO_HASHES = ROOT / "results/local_dev/stage23g3_sco_overlap_clean_materialization/map_hashes.json"
BSDS_SCO_DIR = ROOT / "results/local_dev/stage15e_co_sco_exact_reproduction/predictions/sco"
BSDS_SCO_HASHES = ROOT / "results/local_dev/stage15e_co_sco_exact_reproduction/predictions/map_hashes.json"
BSDS_GT_DIR = ROOT / "evaluation/bsds_official/vendor/BSDS500/BSDS500/data/groundTruth/val"
STAGE23C_FOLDS = ROOT / "results/local_dev/stage23c_cached_uded_descriptor_baselines/individual_descriptor_fold_metrics.csv"
STAGE23F_MODELS = ROOT / "results/local_dev/stage23f_literature_validation_frontier/frontier_fit_parameters.json"
BSDS_SCO_OFFICIAL = ROOT / "results/official_eval/stage15e_co_sco_exact_reproduction/summary.json"
PREVIEW_UDED = (0, 6, 13)
PREVIEW_BSDS = (0, 49, 99)


def _json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_png(path: Path, expected: str) -> np.ndarray:
    if not path.is_file() or _sha256(path) != expected:
        raise RuntimeError(f"frozen SCO map hash mismatch: {path}")
    value = np.asarray(Image.open(path).convert("L"), np.float32) / 255.0
    if not np.all(np.isfinite(value)):
        raise RuntimeError(f"non-finite SCO map: {path}")
    return value


def _threshold_tables() -> tuple[dict[tuple[int, int], float], float]:
    cue = pd.read_csv(STAGE23C_FOLDS)
    cue = cue[cue.descriptor_id == CUE]
    cue_map = {(int(r.repeat), int(r.fold)): float(r.train_threshold) for r in cue.itertuples()}
    if len(cue_map) != 15:
        raise RuntimeError("frozen UDED persistence threshold-fold mismatch")
    models = _json(STAGE23F_MODELS)
    pair03 = next(x for x in models if x["set_id"] == "pair_03")
    index = pair03["descriptors"].index(CUE)
    cue_midpoint = float(pair03["membership_midpoint"][index])
    if abs(cue_midpoint - float(np.median(list(cue_map.values())))) > 0.08:
        raise RuntimeError("persistence diagnostic threshold provenance drift")
    return cue_map, cue_midpoint


def _load_uded(root: Path):
    items, manifest = _load_overlap_clean_selection(root)
    if any(r.get("excluded") and r.get("bytes_read") for r in manifest["records"]):
        raise RuntimeError("protected-lineage bytes read")
    code_hash = _implementation_hash()
    expected = _json(UDED_SCO_HASHES)
    scores = {"target": [], "cue": []}
    provenance = []
    for item in items:
        image_id = item["id"]
        target = _validate_png(UDED_SCO_DIR / f"{image_id}.png", expected[image_id])
        identity = _identity(item, CUE, code_hash)
        cue = load_cached(identity, CACHE_ROOT)
        if cue is None:
            raise RuntimeError(f"forbidden Stage-23C cache miss: {image_id}")
        record = validate_manifest_record(identity, CACHE_ROOT)
        cue = np.asarray(cue, np.float32)
        if target.shape != item["gt"].shape or cue.shape != item["gt"].shape:
            raise RuntimeError(f"UDED shape mismatch: {image_id}")
        scores["target"].append(target); scores["cue"].append(cue)
        provenance.append({"domain": "UDED_selection_overlap_clean", "image_id": image_id,
                           "sco_png_sha256": expected[image_id], "cue_cache_key": identity.cache_key(),
                           "cue_artifact_sha256": record["artifact_sha256"], "cache_hit": True})
    return items, scores, provenance


def _load_bsds(image_dir: Path):
    paths = sorted(image_dir.glob("*.jpg"))
    if len(paths) != 100:
        raise RuntimeError(f"expected 100 BSDS-val images, found {len(paths)}")
    code_hash = _implementation_hash()
    expected = _json(BSDS_SCO_HASHES)["sco"]
    items, scores, provenance = [], {"target": [], "cue": []}, []
    for path in paths:
        image_id = path.stem
        image = _read_image(path)
        gt = np.any(np.stack(_extract_boundaries(loadmat(BSDS_GT_DIR / f"{image_id}.mat"))).astype(bool), axis=0)
        target = _validate_png(BSDS_SCO_DIR / f"{image_id}.png", expected[image_id])
        identity = _descriptor_identity(image_id, _sha256(path), CUE, code_hash)
        cue = load_cached(identity, CACHE_ROOT)
        if cue is None:
            raise RuntimeError(f"forbidden Stage-23F cache miss: {image_id}")
        record = validate_manifest_record(identity, CACHE_ROOT)
        cue = np.asarray(cue, np.float32)
        if target.shape != gt.shape or cue.shape != gt.shape:
            raise RuntimeError(f"BSDS shape mismatch: {image_id}")
        items.append({"id": image_id, "img": image, "gt": gt})
        scores["target"].append(target); scores["cue"].append(cue)
        provenance.append({"domain": "BSDS500_validation", "image_id": image_id,
                           "sco_png_sha256": expected[image_id], "cue_cache_key": identity.cache_key(),
                           "cue_artifact_sha256": record["artifact_sha256"], "cache_hit": True})
    return items, scores, provenance


def _write_preview(uded_items, uded_scores, bsds_items, bsds_scores):
    rows = []
    for items, scores, positions in ((uded_items, uded_scores, PREVIEW_UDED), (bsds_items, bsds_scores, PREVIEW_BSDS)):
        for i in positions:
            rows.append([items[i]["img"], items[i]["gt"], scores["target"][i], scores["cue"][i]])
    path = write_panel_grid(OUT / "best_method_preview.png", rows, panel_height=112, panel_width=112, gap=2)
    return {"path": path.relative_to(ROOT).as_posix(),
            "selection": "UDED overlap-clean positions 1/7/14 followed by BSDS500-val positions 1/50/100",
            "panel_order": ["input", "GT union", "exact author SCO score", "cached Gabor scale persistence"],
            "optimization_use": "documentary only; no result-driven example selection"}


def main() -> int:
    global OUT, CACHE_ROOT, BSDS_GT_DIR
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--image-dir", default=str(DEFAULT_IMAGE_DIR))
    ap.add_argument("--gt-dir", default=str(BSDS_GT_DIR))
    ap.add_argument("--cache-root", default=str(CACHE_ROOT))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(); OUT = Path(args.out); CACHE_ROOT = Path(args.cache_root); BSDS_GT_DIR = Path(args.gt_dir)
    if args.smoke:
        cue_map, midpoint = _threshold_tables()
        assert len(cue_map) == 15 and 0 <= midpoint <= 1
        print("STAGE23G4_SCO_PERSISTENCE_GAP_DIAGNOSIS_SMOKE_OK"); return 0

    OUT.mkdir(parents=True, exist_ok=True)
    cue_thresholds, bsds_cue_threshold = _threshold_tables()
    uded_items, uded_scores, provenance_u = _load_uded(Path(args.uded_root))
    bsds_items, bsds_scores, provenance_b = _load_bsds(Path(args.image_dir))
    folds = _make_repeated_folds(len(uded_items), 3, 5, 20261031)
    rows, target_thresholds = [], {}
    for repeat, fold, train, valid in folds:
        key = (repeat + 1, fold + 1)
        target_thresholds[key] = float(selection_metric(
            [uded_scores["target"][int(i)] for i in train], [uded_items[int(i)] for i in train], 41,
        )["threshold"])
        for index in valid:
            i = int(index)
            rows.append({"domain": "UDED_selection_overlap_clean", "repeat": key[0], "fold": key[1],
                         "image_id": uded_items[i]["id"], **_metrics(uded_scores["target"][i], uded_scores["cue"][i],
                         uded_items[i]["gt"], target_thresholds[key], cue_thresholds[key])})
    official = _json(BSDS_SCO_OFFICIAL)
    bsds_target_threshold = float(official["methods"]["stage15e_exact_author_sco"]["ODS_threshold"])
    for item, target, cue in zip(bsds_items, bsds_scores["target"], bsds_scores["cue"]):
        rows.append({"domain": "BSDS500_validation", "repeat": 0, "fold": 0, "image_id": item["id"],
                     **_metrics(target, cue, item["gt"], bsds_target_threshold, bsds_cue_threshold)})
    frame = pd.DataFrame(rows)
    if len(frame) != 170 or not np.all(np.isfinite(frame.select_dtypes(include=[np.number]).to_numpy(float))):
        raise RuntimeError("Stage-23G4 diagnostic cardinality/finite contract failed")
    summaries = {name: _domain_summary(frame[frame.domain == name]) for name in ("UDED_selection_overlap_clean", "BSDS500_validation")}
    checks = {name: {
        "unique_gt_at_least_0p02": summary["mean_cue_unique_gt_fraction"] >= 0.02,
        "conditional_correctness_at_least_0p50": summary["mean_p_cue_correct_given_sed_wrong"] >= 0.50,
        "unique_gt_on_at_least_0p60_images": summary["unique_gt_image_fraction"] >= 0.60,
        "mean_spearman_at_most_0p80": summary["mean_spearman"] <= 0.80,
    } for name, summary in summaries.items()}
    gap_supported = all(all(values.values()) for values in checks.values())
    frame.to_csv(OUT / "per_image_gap_metrics.csv", index=False)
    pd.DataFrame(provenance_u + provenance_b).to_csv(OUT / "frozen_input_provenance.csv", index=False)
    with (OUT / "threshold_provenance.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["domain", "method", "threshold", "source"]); writer.writeheader()
        for key in sorted(target_thresholds):
            writer.writerow({"domain": f"UDED_repeat{key[0]}_fold{key[1]}", "method": "SCO", "threshold": target_thresholds[key], "source": "Stage23G4 overlap-clean outer-training diagnostic fit"})
            writer.writerow({"domain": f"UDED_repeat{key[0]}_fold{key[1]}", "method": CUE, "threshold": cue_thresholds[key], "source": "Stage23C outer-training fold"})
        writer.writerow({"domain": "BSDS500_validation", "method": "SCO", "threshold": bsds_target_threshold, "source": "Stage15e existing official ODS"})
        writer.writerow({"domain": "BSDS500_validation", "method": CUE, "threshold": bsds_cue_threshold, "source": "Stage23F full-overlap-clean-UDED membership midpoint"})
    preview = _write_preview(uded_items, uded_scores, bsds_items, bsds_scores)
    manifest = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": [],
                "analysis_only_note": "Stage 23G4 reuses exact SCO and cached persistence maps for gap diagnosis; no candidate map is created. Official attachment is incumbent-only."}
    (OUT / "official_eval_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary = {"status": "completed", "experiment_id": EXPERIMENT_ID,
               "role": "frozen_strong_detector_gap_diagnosis", "target": "exact author-code SCO",
               "missing_evidence_hypothesis": CUE, "detector_runs": 0, "descriptor_computations": 0,
               "cache_hits": 114, "protected_lineage_bytes_read": False, "summaries": summaries,
               "preregistered_checks": checks, "gap_supported": gap_supported,
               "decision_semantics": "Only gap_supported=true may authorize a separately preregistered equal-mean intervention after the frozen Stage23F persistence membership transform. Failure closes SCO/persistence without substitution.",
               "incumbent_changed": False, "visual_preview": preview,
               "official_attachment": "incumbent-only; no Stage-23G4 candidate exists"}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE23G4_SCO_PERSISTENCE_GAP_DIAGNOSIS_COMPLETED"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
