from __future__ import annotations

"""Stage 22E: one support-preserving per-image score calibration candidate."""

from collections import defaultdict
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from skimage.io import imread

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12b_fuzzy_signature import prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage16f_rolling_guidance_localizer import _ordered_compact
from run_stage20_frozen_queue_candidate import (
    SEED,
    _attach_descriptors,
    _fit_candidate,
    _load_overlap_clean_uded,
    _model_hash,
    _model_rows,
    _save_soft_png,
    _score_pairs,
)


EXPERIMENT_ID = "stage22e_positive_support_quantile_calibration"
DESCRIPTORS = ("gabor4_s13", "semiglobal_changepoint")
REFERENCE_LEVELS = 255
REFERENCE_QUANTILES = (np.arange(REFERENCE_LEVELS, dtype=np.float64) + 0.5) / REFERENCE_LEVELS
PREVIEW_POSITIONS = (0, 6, 13)


def _fit_reference(scores: list[np.ndarray]) -> np.ndarray:
    curves = []
    for score in scores:
        positive = np.asarray(score, dtype=np.float64)[np.asarray(score) > 0.0]
        if positive.size == 0:
            raise RuntimeError("cannot fit score reference from an empty positive support")
        curves.append(np.quantile(positive, REFERENCE_QUANTILES, method="linear"))
    reference = np.median(np.stack(curves), axis=0)
    reference = np.maximum.accumulate(np.clip(reference, 1.0 / 255.0, 1.0))
    if not np.all(np.isfinite(reference)) or np.any(np.diff(reference) < 0.0):
        raise RuntimeError("invalid score-reference curve")
    return reference.astype(np.float64)


def _standardize(score: np.ndarray, reference: np.ndarray) -> np.ndarray:
    source = np.asarray(score, dtype=np.float64)
    output = np.zeros_like(source, dtype=np.float64)
    mask = source > 0.0
    values = source[mask]
    if values.size == 0:
        return output.astype(np.float32)
    unique, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    lower = np.cumsum(counts) - counts
    midranks = (lower + 0.5 * counts) / values.size
    mapped_unique = np.interp(
        midranks, REFERENCE_QUANTILES, reference,
        left=float(reference[0]), right=float(reference[-1]),
    )
    if np.any(np.diff(mapped_unique) < 0.0):
        raise RuntimeError("score standardization introduced an ordering inversion")
    output[mask] = mapped_unique[inverse]
    result = np.clip(output, 0.0, 1.0).astype(np.float32)
    if not np.array_equal(result > 0.0, mask):
        raise RuntimeError("score standardization changed positive support")
    return result


def _reference_hash(reference: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(reference, dtype="<f8").tobytes()).hexdigest()


def _standardize_many(scores: list[np.ndarray], reference: np.ndarray) -> list[np.ndarray]:
    return [_standardize(score, reference) for score in scores]


def _official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": EXPERIMENT_ID,
            "export": {
                "script": "automation/stage22e_score_calibration_venv_launcher.py",
                "args": [
                    "--export-bsds", "--image-dir", "{image_dir}",
                    "--output-dir", "{output_dir}", "--split", "{split}",
                ],
                "timeout_minutes": 360,
            },
        }],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _fit_full(args: argparse.Namespace):
    raw = resize_items(
        _load_overlap_clean_uded(ensure_uded(Path(args.uded_root))),
        args.max_side_development,
    )
    items, names = prepare(raw)
    _attach_descriptors(items, DESCRIPTORS, "STAGE22E_FULL_FIT_DESCRIPTOR")
    positive, _ = learn_banks(
        items, names, args.seed, args.max_positive, args.max_negative, args.max_abs_corr
    )
    compact = _ordered_compact(positive)
    model = _fit_candidate(items, DESCRIPTORS, args.seed)
    base = _score_pairs(items, names, compact, model)[1]
    reference = _fit_reference(base)
    return items, names, compact, model, reference


def export_bsds(args: argparse.Namespace) -> int:
    training, names, compact, model, reference = _fit_full(args)
    image_paths = sorted(Path(args.image_dir).glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {args.image_dir}")
    output_dir = Path(args.output_dir)
    rows = []
    for number, path in enumerate(image_paths, start=1):
        print(f"STAGE22E_BSDS_EXPORT {number:03d}/{len(image_paths):03d} {path.stem}", flush=True)
        prepared, candidate_names = prepare([{"id": path.stem, "img": imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        _attach_descriptors(prepared, DESCRIPTORS, "STAGE22E_BSDS_DESCRIPTOR")
        control, base, _contexts, runtimes = _score_pairs(prepared, names, compact, model)
        started = time.perf_counter()
        candidate = _standardize(base[0], reference)
        calibration_seconds = time.perf_counter() - started
        if not np.array_equal(candidate > 0.0, control[0] > 0.0):
            raise RuntimeError(f"support mismatch for {path.stem}")
        _save_soft_png(candidate, output_dir / f"{path.stem}.png")
        rows.append({
            "image_id": path.stem,
            "descriptor_runtime_seconds": prepared[0]["stage20_descriptor_runtime_seconds"],
            "base_score_runtime_seconds": runtimes[0],
            "calibration_runtime_seconds": calibration_seconds,
            "support_equal": True,
        })
    pd.DataFrame(rows).to_csv(output_dir / "runtime.csv", index=False)
    metadata = {
        "method": EXPERIMENT_ID,
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "development_source": "14-image overlap-clean UDED selection only",
        "excluded_lineage": "03-35028 / protected BSDS500-test 35028",
        "base_detector": "frozen Stage-20C dominant-pair monotone 2-additive Choquet",
        "standardization": "positive-support empirical midrank to outer-training median quantile reference",
        "reference_levels": REFERENCE_LEVELS,
        "reference_sha256": _reference_hash(reference),
        "reference_values": reference.tolist(),
        "model_sha256": _model_hash(model),
        "capacity_fit_success": bool(model["capacity"]["fit_success"]),
        "training_images": len(training),
        "native_resolution_output": True,
        "output": "8-bit soft PNG after unlabeled per-image monotone standardization",
        "n_maps": len(image_paths),
    }
    (output_dir / "export_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return 0


def run_experiment(args: argparse.Namespace) -> int:
    prior = json.loads((ROOT / "results/local_dev/stage22d_local_competition_nms_rank_swap_diagnosis/summary.json").read_text(encoding="utf-8"))
    if not prior["calibration_dominance_from_stage22c"]["calibration_dominant"] or prior["competition_dominance"]["competition_dominant"]:
        raise RuntimeError("Stage-22 mechanical branch does not authorize calibration candidate")

    out = Path(args.out) if args.out else ROOT / "results/local_dev" / EXPERIMENT_ID
    out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(_load_overlap_clean_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    selection, names = prepare(raw)
    _attach_descriptors(selection, DESCRIPTORS, "STAGE22E_DESCRIPTOR")
    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)

    variants = ("compact_mfi", "stage22e_calibrated_stage20c")
    counts, fold_f1, thresholds = defaultdict(list), defaultdict(list), defaultdict(list)
    fold_rows, image_rows, parameter_rows, reference_rows, runtime_rows = [], [], [], [], []
    first_predictions = {name: {} for name in variants}
    first_scores: dict[int, np.ndarray] = {}
    fit_successes = support_violations = order_violations = repeatability_violations = 0

    for split_no, (repeat, fold, train_indices, valid_indices) in enumerate(splits, start=1):
        train = [selection[index] for index in train_indices]
        valid = [selection[index] for index in valid_indices]
        positive, _ = learn_banks(
            train, names, args.seed + 10000 * repeat + fold,
            args.max_positive, args.max_negative, args.max_abs_corr,
        )
        compact = _ordered_compact(positive)
        started = time.perf_counter()
        model = _fit_candidate(train, DESCRIPTORS, args.seed + 20000 * repeat + fold)
        train_base = _score_pairs(train, names, compact, model)
        valid_base = _score_pairs(valid, names, compact, model)
        reference = _fit_reference(train_base[1])
        train_candidate = _standardize_many(train_base[1], reference)
        valid_candidate = _standardize_many(valid_base[1], reference)
        fit_seconds = time.perf_counter() - started
        fit_successes += int(bool(model["capacity"]["fit_success"]))
        parameter_rows.extend(_model_rows(model, repeat + 1, fold + 1))
        for q, value in zip(REFERENCE_QUANTILES, reference):
            reference_rows.append({"repeat": repeat + 1, "fold": fold + 1, "quantile": q, "reference_score": value, "reference_sha256": _reference_hash(reference)})

        train_maps = (train_base[0], train_candidate)
        valid_maps = (valid_base[0], valid_candidate)
        for controls, candidates in (train_maps, valid_maps):
            for control, candidate in zip(controls, candidates):
                support_violations += int(not np.array_equal(control > 0.0, candidate > 0.0))
        for base_score, candidate in zip(valid_base[1], valid_candidate):
            unique = np.unique(np.asarray(base_score)[np.asarray(base_score) > 0.0])
            mapped = np.array([candidate[np.asarray(base_score) == value][0] for value in unique]) if unique.size else np.array([])
            order_violations += int(bool(mapped.size and np.any(np.diff(mapped) < 0.0)))
            repeatability_violations += int(not np.array_equal(candidate, _standardize(base_score, reference)))

        runtime_rows.append({
            "repeat": repeat + 1, "fold": fold + 1,
            "fit_score_reference_seconds": fit_seconds,
            "reference_sha256": _reference_hash(reference),
        })
        print(f"STAGE22E_SPLIT {split_no:02d}/{len(splits):02d} repeat={repeat + 1} fold={fold + 1}", flush=True)
        for variant_index, variant in enumerate(variants):
            threshold = float(selection_metric(train_maps[variant_index], train, args.thresholds)["threshold"])
            metric, event_counts, per_image = fixed_eval(valid_maps[variant_index], valid, threshold)
            counts[variant].extend(event_counts)
            fold_f1[variant].append(float(metric["F1"]))
            thresholds[variant].append(threshold)
            fold_rows.append({"repeat": repeat + 1, "fold": fold + 1, "variant": variant, "train_threshold": threshold, "capacity_fit_success": bool(model["capacity"]["fit_success"]), "reference_sha256": _reference_hash(reference), **metric})
            image_rows.extend({"repeat": repeat + 1, "fold": fold + 1, "variant": variant, **row} for row in per_image)
            if repeat == 0:
                for global_index, score in zip(valid_indices, valid_maps[variant_index]):
                    first_predictions[variant][int(global_index)] = score >= threshold
                    if variant_index == 1:
                        first_scores[int(global_index)] = score

    aggregate = {name: aggregate_counts(counts[name]) for name in variants}
    incumbent_folds = np.asarray(fold_f1[variants[0]])
    candidate_folds = np.asarray(fold_f1[variants[1]])
    deltas = {
        "aggregate_F1": float(aggregate[variants[1]]["F1"] - aggregate[variants[0]]["F1"]),
        "aggregate_precision": float(aggregate[variants[1]]["precision"] - aggregate[variants[0]]["precision"]),
        "aggregate_recall": float(aggregate[variants[1]]["recall"] - aggregate[variants[0]]["recall"]),
        "mean_fold_F1": float(np.mean(candidate_folds - incumbent_folds)),
        "fold_wins": int(np.sum(candidate_folds > incumbent_folds)),
        "capacity_fit_successes": fit_successes,
        "support_violations": support_violations,
        "ordering_violations": order_violations,
        "repeatability_violations": repeatability_violations,
    }
    uded_gate = bool(
        deltas["aggregate_F1"] >= 0.002 and deltas["aggregate_precision"] >= 0.0
        and deltas["aggregate_recall"] >= -0.003 and deltas["mean_fold_F1"] >= 0.0
        and deltas["fold_wins"] >= 9 and fit_successes == 15
        and support_violations == order_violations == repeatability_violations == 0
    )

    ranking = [{
        "variant": variant,
        "cv_precision": aggregate[variant]["precision"],
        "cv_recall": aggregate[variant]["recall"],
        "cv_F1": aggregate[variant]["F1"],
        "mean_fold_F1": float(np.mean(fold_f1[variant])),
        "std_fold_F1": float(np.std(fold_f1[variant])),
        "threshold_mean": float(np.mean(thresholds[variant])),
        "threshold_std": float(np.std(thresholds[variant])),
    } for variant in variants]
    pd.DataFrame(ranking).sort_values("cv_F1", ascending=False).to_csv(out / "variant_ranking.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)
    pd.DataFrame(parameter_rows).to_csv(out / "capacity_parameters.csv", index=False)
    pd.DataFrame(reference_rows).to_csv(out / "score_standardization_reference.csv", index=False)
    pd.DataFrame(runtime_rows).to_csv(out / "runtime.csv", index=False)

    rows = [[selection[pos]["img"], selection[pos]["gt"], first_predictions[variants[0]][pos], first_predictions[variants[1]][pos], first_scores[pos]] for pos in PREVIEW_POSITIONS]
    preview = write_panel_grid(out / "best_method_preview.png", rows)
    manifest = _official_manifest(out)
    summary = {
        "stage": EXPERIMENT_ID,
        "status": "completed",
        "scientific_experiment_index": "5/5",
        "branch": "C_calibration",
        "base_detector": "frozen Stage-20C dominant-pair 2-additive Choquet",
        "candidate_change": "positive-support empirical midrank mapped to outer-training median quantile reference",
        "reference_levels": REFERENCE_LEVELS,
        "validation_statistics_used_for_transform_selection": False,
        "known_overlap_excluded_without_blob_read": "03-35028 / BSDS500-test 35028",
        "metrics": aggregate,
        "uded_gate": {"met": uded_gate, "deltas": deltas},
        "promotion_rule": "Conjunctive UDED gate plus standard-Berkeley delta ODS >= +0.002, OIS >= 0, AP >= 0, and all implementation contracts.",
        "promotion_pending_official_bsds_val": True,
        "stage22_terminal_after_decision": True,
        "official_evaluation": {"manifest": str(manifest.relative_to(ROOT)).replace("\\", "/"), "required_before_promotion": True, "reference_reproduction_verified": False},
        "visual_preview": {"file": preview.name, "selection": "fixed overlap-clean UDED positions 1, 7, and 14", "columns": ["input", "ground_truth", "compact_MFI_OOF_prediction", "calibrated_Stage20C_OOF_prediction", "calibrated_continuous_score"], "use": "documentary only"},
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE22E_SCORE_CALIBRATION_COMPLETE", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uded-root", default=str(DEFAULT_UDED))
    parser.add_argument("--out")
    parser.add_argument("--max-side", type=int, default=256)
    parser.add_argument("--max-side-development", type=int, default=256)
    parser.add_argument("--thresholds", type=int, default=41)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-positive", type=int, default=10)
    parser.add_argument("--max-negative", type=int, default=8)
    parser.add_argument("--max-abs-corr", type=float, default=0.88)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--export-bsds", action="store_true")
    parser.add_argument("--image-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--split", default="val")
    args = parser.parse_args()
    if args.export_bsds:
        if not args.image_dir or not args.output_dir:
            parser.error("--export-bsds requires --image-dir and --output-dir")
        return export_bsds(args)
    return run_experiment(args)


if __name__ == "__main__":
    raise SystemExit(main())
