from __future__ import annotations

"""Stage 23C: cache the frozen UDED evidence pool and baseline each map."""

from collections import defaultdict
from pathlib import Path
import argparse
import hashlib
import inspect
import json
import sys
import time

import numpy as np
import pandas as pd
from skimage.io import imread
from skimage.transform import resize

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12d_bipolar_cv import _make_repeated_folds
from src.stage23_cache import CacheIdentity, get_or_compute, load_cached, validate_manifest_record
from src.stage23_descriptors import DESCRIPTOR_IDS, compute_descriptor, descriptor_parameters, synthetic_contract


EXPERIMENT_ID = "stage23c_cached_uded_descriptor_baselines"
OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
CACHE_ROOT = ROOT / "cache" / "local_dev" / "stage23"
MAX_SIDE = 256
SEED = 20261029
PREVIEW_POSITIONS = (0, 6, 13)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _implementation_hash() -> str:
    digest = hashlib.sha256()
    for relative in (
        "src/stage23_descriptors.py", "src/features.py", "src/conditioning.py",
        "src/phase_congruency.py", "src/texture_gradient.py",
        "src/pmi_dependency_context.py", "src/semiglobal_changepoint.py",
        "src/fh_region_boundary.py",
    ):
        digest.update(relative.encode("utf-8"))
        digest.update((ROOT / relative).read_bytes())
    return digest.hexdigest()


def _load_overlap_clean_selection(root: Path) -> tuple[list[dict], dict[str, object]]:
    pairs = json.loads((root / "test_pair.lst").read_text(encoding="utf-8"))
    retained, records = [], []
    for zero_index in range(0, len(pairs), 2):
        image_rel, gt_rel = pairs[zero_index]
        image_id = Path(image_rel).stem
        excluded = "35028" in image_id
        row: dict[str, object] = {
            "selection_position": zero_index // 2 + 1, "uded_pair_position": zero_index + 1,
            "image_id": image_id, "image_path": str(image_rel).replace("\\", "/"),
            "gt_path": str(gt_rel).replace("\\", "/"), "excluded": excluded,
            "reason": "known protected BSDS-test filename lineage" if excluded else "none",
            "bytes_read": False,
        }
        if not excluded:
            image_path, gt_path = root / image_rel, root / gt_rel
            image, gt = imread(image_path), imread(gt_path)
            if gt.ndim == 3: gt = gt[..., 0]
            gt = gt > (0.5 * np.iinfo(gt.dtype).max) if np.issubdtype(gt.dtype, np.integer) else gt > 0.5
            h, w = gt.shape
            scale = min(1.0, MAX_SIDE / max(h, w))
            if scale < 1.0:
                nh, nw = max(8, int(round(h * scale))), max(8, int(round(w * scale)))
                image = resize(image, (nh, nw, image.shape[2]), order=1, mode="reflect", anti_aliasing=True, preserve_range=True)
                gt = resize(gt.astype(np.uint8), (nh, nw), order=0, mode="edge", anti_aliasing=False, preserve_range=True) > 0.5
            row.update({
                "bytes_read": True, "source_sha256": _sha256(image_path), "gt_sha256": _sha256(gt_path),
                "original_shape": [int(h), int(w)], "evaluation_shape": [int(gt.shape[0]), int(gt.shape[1])],
                "resize_scale": float(scale),
            })
            retained.append({"id": image_id, "img": image, "gt": np.asarray(gt, bool), "source_sha256": row["source_sha256"]})
        records.append(row)
    manifest = {
        "schema_version": 1, "selection_count_before": len(records), "selection_count_after": len(retained),
        "known_lineage_id": "35028", "lineage_filter_applied_before_bytes": True, "records": records,
    }
    if len(retained) != 14 or sum(bool(row["excluded"]) for row in records) != 1:
        raise RuntimeError("overlap-clean UDED contract drift")
    return retained, manifest


def _identity(item: dict, descriptor_id: str, code_hash: str) -> CacheIdentity:
    return CacheIdentity(
        dataset="UDED", split="selection_overlap_clean", image_id=str(item["id"]),
        artifact_type="descriptors", artifact_id=descriptor_id,
        preprocessing_id="downscale_maxside256_then_registered_descriptor_preprocessing_v1",
        parameters={"max_side": MAX_SIDE, **descriptor_parameters(descriptor_id)},
        implementation="src.stage23_descriptors.compute_descriptor",
        implementation_version="stage23c_frozen_pool_v1", code_version=code_hash,
        source_sha256=str(item["source_sha256"]), representation="raw_evidence", gt_used=False,
    )


def _extract(items: list[dict]) -> tuple[dict[str, list[np.ndarray]], list[dict[str, object]], int, int]:
    code_hash = _implementation_hash()
    maps = {name: [] for name in DESCRIPTOR_IDS}
    rows, hits, misses = [], 0, 0
    for image_no, item in enumerate(items, start=1):
        for descriptor_id in DESCRIPTOR_IDS:
            identity = _identity(item, descriptor_id, code_hash)
            started = time.perf_counter()
            value, cache_hit = get_or_compute(
                identity,
                lambda descriptor_id=descriptor_id, image=np.asarray(item["img"]): compute_descriptor(descriptor_id, image),
                CACHE_ROOT,
            )
            elapsed = time.perf_counter() - started
            validate_manifest_record(identity, CACHE_ROOT)
            value = np.asarray(value, dtype=np.float32)
            if value.shape != item["gt"].shape or not np.all(np.isfinite(value)):
                raise RuntimeError(f"invalid cached map {item['id']} {descriptor_id}")
            maps[descriptor_id].append(value)
            hits += int(cache_hit); misses += int(not cache_hit)
            rows.append({
                "image_id": item["id"], "image_position": image_no, "descriptor_id": descriptor_id,
                "cache_key": identity.cache_key(), "cache_hit": bool(cache_hit), "request_seconds": elapsed,
                "shape": "x".join(str(x) for x in value.shape), "dtype": str(value.dtype),
                "minimum": float(np.min(value)), "maximum": float(np.max(value)),
            })
    for item in items:
        for descriptor_id in DESCRIPTOR_IDS:
            identity = _identity(item, descriptor_id, code_hash)
            if load_cached(identity, CACHE_ROOT) is None:
                raise RuntimeError("exact cache reload unexpectedly missed")
            validate_manifest_record(identity, CACHE_ROOT)
    return maps, rows, hits, misses


def _evaluate(items: list[dict], maps: dict[str, list[np.ndarray]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    folds = _make_repeated_folds(len(items), 3, 5, SEED)
    all_counts: dict[str, list[tuple[int, int, int, int]]] = defaultdict(list)
    fold_rows, image_rows = [], []
    for descriptor_id in DESCRIPTOR_IDS:
        for repeat, fold, train_idx, valid_idx in folds:
            train_scores = [maps[descriptor_id][int(i)] for i in train_idx]
            valid_scores = [maps[descriptor_id][int(i)] for i in valid_idx]
            train_items = [items[int(i)] for i in train_idx]
            valid_items = [items[int(i)] for i in valid_idx]
            threshold = float(selection_metric(train_scores, train_items, 41)["threshold"])
            metric, counts, per_image = fixed_eval(valid_scores, valid_items, threshold)
            all_counts[descriptor_id].extend(counts)
            support = float(np.mean([np.mean(score >= threshold) for score in valid_scores]))
            fold_rows.append({"descriptor_id": descriptor_id, "repeat": repeat + 1, "fold": fold + 1, "train_threshold": threshold, "validation_support_density": support, **metric})
            image_rows.extend({"descriptor_id": descriptor_id, "repeat": repeat + 1, "fold": fold + 1, "train_threshold": threshold, **row} for row in per_image)
    fold_frame = pd.DataFrame(fold_rows)
    summary_rows = []
    for descriptor_id in DESCRIPTOR_IDS:
        aggregate = aggregate_counts(all_counts[descriptor_id])
        subset = fold_frame[fold_frame.descriptor_id == descriptor_id]
        flat = np.concatenate([value.ravel() for value in maps[descriptor_id]])
        summary_rows.append({
            "descriptor_id": descriptor_id, **aggregate,
            "mean_fold_F1": float(subset.F1.mean()), "std_fold_F1": float(subset.F1.std(ddof=0)),
            "mean_threshold": float(subset.train_threshold.mean()), "std_threshold": float(subset.train_threshold.std(ddof=0)),
            "mean_support_density": float(subset.validation_support_density.mean()),
            "score_min": float(np.min(flat)), "score_q05": float(np.quantile(flat, 0.05)), "score_median": float(np.median(flat)),
            "score_q95": float(np.quantile(flat, 0.95)), "score_max": float(np.max(flat)),
            "score_mean": float(np.mean(flat)), "score_std": float(np.std(flat)),
        })
    return pd.DataFrame(summary_rows), fold_frame, pd.DataFrame(image_rows)


def _write_preview(items: list[dict], maps: dict[str, list[np.ndarray]]) -> dict[str, object]:
    rows = [[items[p]["img"], items[p]["gt"], *[maps[name][p] for name in DESCRIPTOR_IDS]] for p in PREVIEW_POSITIONS]
    path = write_panel_grid(OUT / "best_method_preview.png", rows, panel_height=112, panel_width=112, gap=2)
    return {"path": path.relative_to(ROOT).as_posix(), "selection": "sorted overlap-clean UDED positions 1, 7, and 14", "panel_order": ["input", "ground_truth", *DESCRIPTOR_IDS], "optimization_use": "none"}


def _write_official_manifest() -> None:
    manifest = {
        "schema_version": 1, "split": "val", "include_incumbent": True, "methods": [],
        "analysis_only_note": "Stage 23C defines no BSDS candidate detector. The attachment is incumbent-only; split-specific BSDS evidence extraction is reserved for Stage 23F.",
    }
    (OUT / "official_eval_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> int:
    global OUT, CACHE_ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--uded-root", default=str(DEFAULT_UDED)); parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--cache-root", default=str(CACHE_ROOT)); parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        contract = synthetic_contract()
        if contract["count"] != 13 or not contract["all_finite"]: raise RuntimeError("descriptor smoke failed")
        if tuple(inspect.signature(compute_descriptor).parameters) != ("descriptor_id", "image"): raise RuntimeError("GT-isolated signature drift")
        print("STAGE23C_DESCRIPTOR_SMOKE_OK"); return 0
    OUT, CACHE_ROOT = Path(args.out), Path(args.cache_root)
    OUT.mkdir(parents=True, exist_ok=True)
    items, dataset_manifest = _load_overlap_clean_selection(Path(args.uded_root))
    (OUT / "overlap_clean_dataset_manifest.json").write_text(json.dumps(dataset_manifest, indent=2), encoding="utf-8")
    maps, cache_rows, hits, misses = _extract(items)
    ranking, folds, per_image = _evaluate(items, maps)
    pd.DataFrame(cache_rows).to_csv(OUT / "descriptor_cache_provenance.csv", index=False)
    ranking.to_csv(OUT / "individual_descriptor_baselines.csv", index=False)
    folds.to_csv(OUT / "individual_descriptor_fold_metrics.csv", index=False)
    per_image.to_csv(OUT / "individual_descriptor_per_image_metrics.csv", index=False)
    preview = _write_preview(items, maps); _write_official_manifest()
    summary = {
        "status": "completed", "experiment_id": EXPERIMENT_ID,
        "role": "cached_descriptor_extraction_and_nonselective_individual_baselines",
        "dataset": "UDED selection overlap-clean", "retained_images": len(items), "protected_lineage_bytes_read": False,
        "descriptor_count": len(DESCRIPTOR_IDS), "descriptor_ids": list(DESCRIPTOR_IDS),
        "cache_root": str(CACHE_ROOT.relative_to(ROOT)).replace("\\", "/"), "cache_requests": len(cache_rows),
        "cache_hits": hits, "cache_misses": misses, "exact_reload_manifest_validations": len(items) * len(DESCRIPTOR_IDS),
        "cache_repair_performed": False, "cv": {"repeats": 5, "folds": 3, "seed": SEED, "threshold_grid": 41},
        "evaluation": "repository tolerant proxy at 0.0075 image diagonal; not Berkeley official evaluation",
        "selection_or_promotion_allowed": False,
        "next_contract": "Stage 23D must consume all thirteen exact cached maps and may prune only under its prospective complementarity rule.",
        "visual_preview": preview, "official_attachment": "incumbent-only BSDS500-validation attachment",
        "files": ["summary.json", "overlap_clean_dataset_manifest.json", "descriptor_cache_provenance.csv", "individual_descriptor_baselines.csv", "individual_descriptor_fold_metrics.csv", "individual_descriptor_per_image_metrics.csv", "best_method_preview.png", "official_eval_manifest.json"],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE23C_CACHED_UDED_DESCRIPTOR_BASELINES_COMPLETED"); print(OUT / "summary.json"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
