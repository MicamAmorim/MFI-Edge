from __future__ import annotations

"""Stage 16f: fixed rolling-guidance conditioning of the Scharr localizer.

The compact Choquet context, its fold fitting, and Scharr+NMS localization are
unchanged.  The sole candidate change is a fixed scale-aware rolling-guidance
filter between the incumbent median conditioning and Scharr+NMS.
"""

from collections import defaultdict
from pathlib import Path
import argparse
import json
import math
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage as ndi
from skimage.io import imread

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12b_fuzzy_signature import membership_stack, prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage14c_positive_bank_pruning import (
    COMPACT_FEATURES,
    FLOOR,
    GAMMA,
    STRENGTH,
    _filter_bank,
)
from src.bipolar_fuzzy import context_gate, distorted_choquet
from src.classical_detectors import detector_score
from src.features import gray_float
from src.postprocess import gradient_orientation, non_maximum_suppression


EXPERIMENT_ID = "stage16f_rolling_guidance_localizer"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
VARIANTS = ("compact_mfi", "rolling_guidance_localizer")
PREVIEW_POSITIONS = (0, 7, 14)

# Fixed to the standard OpenCV RGF interface defaults: sigma_space=3,
# sigma_color=25 on an 8-bit scale (approximately 0.1 here), and four
# iterations.  Unlike a historically reported OpenCV initialization defect,
# this equation-level implementation uses the primary paper's constant initial
# guide.  The 3-sigma truncation is a fixed numerical support convention.
SIGMA_SPACE = 3.0
SIGMA_RANGE = 0.1
ITERATIONS = 4
TRUNCATE = 3.0


def rolling_guidance_gray(image: np.ndarray) -> np.ndarray:
    """Equation-level grayscale rolling guidance with fixed finite support.

    A constant initial guide makes the first iteration exactly a Gaussian
    weighted average.  Later iterations use the preceding output as the range
    guide while always averaging the same source image, matching the combined
    formulation in Zhang et al. (ECCV 2014).
    """
    source = np.asarray(gray_float(image), dtype=np.float64)
    if source.ndim != 2 or not np.all(np.isfinite(source)):
        raise ValueError("rolling guidance requires a finite grayscale image")
    source = np.clip(source, 0.0, 1.0)
    height, width = source.shape
    radius = int(math.ceil(TRUNCATE * SIGMA_SPACE))
    padded_source = np.pad(source, radius, mode="reflect")
    guide = np.zeros_like(source)
    offsets = [
        (dy, dx, math.exp(-(dy * dy + dx * dx) / (2.0 * SIGMA_SPACE**2)))
        for dy in range(-radius, radius + 1)
        for dx in range(-radius, radius + 1)
    ]
    range_denominator = 2.0 * SIGMA_RANGE**2
    for _ in range(ITERATIONS):
        padded_guide = np.pad(guide, radius, mode="reflect")
        numerator = np.zeros_like(source)
        denominator = np.zeros_like(source)
        for dy, dx, spatial_weight in offsets:
            ys = radius + dy
            xs = radius + dx
            neighbor_guide = padded_guide[ys : ys + height, xs : xs + width]
            neighbor_source = padded_source[ys : ys + height, xs : xs + width]
            weight = spatial_weight * np.exp(
                -np.square(guide - neighbor_guide) / range_denominator
            )
            numerator += weight * neighbor_source
            denominator += weight
        guide = numerator / np.maximum(denominator, np.finfo(np.float64).tiny)
    return np.clip(guide, 0.0, 1.0).astype(np.float32)


def _ordered_compact(bank: list[dict]) -> list[dict]:
    selected = _filter_bank(bank, COMPACT_FEATURES)
    by_feature = {str(row["feature"]): row for row in selected}
    missing = [name for name in COMPACT_FEATURES if name not in by_feature]
    if missing:
        raise RuntimeError(f"compact bank missing features: {missing}")
    return [by_feature[name] for name in COMPACT_FEATURES]


def _add_candidate_localizers(items: list[dict]) -> None:
    for index, item in enumerate(items, start=1):
        print(
            f"STAGE16F_RGF {index:03d}/{len(items):03d} {item['id']}",
            flush=True,
        )
        filtered = rolling_guidance_gray(item["pre_img"])
        orientation = gradient_orientation(filtered, 1.0)
        localizer = non_maximum_suppression(
            detector_score(filtered, "scharr", 1.0), orientation
        ).astype(np.float32)
        item["rgf_filtered"] = filtered
        item["rgf_scharr"] = localizer
        item["rgf_diagnostic"] = {
            "filtered_mean": float(np.mean(filtered)),
            "filtered_std": float(np.std(filtered)),
            "mean_abs_removed_detail": float(
                np.mean(np.abs(np.asarray(gray_float(item["pre_img"])) - filtered))
            ),
            "incumbent_localizer_mass": float(np.sum(item["scharr"])),
            "candidate_localizer_mass": float(np.sum(localizer)),
            "candidate_nonzero_fraction": float(np.mean(localizer > 0)),
        }


def _contexts(items: list[dict], names: list[str], compact: list[dict]):
    contexts = []
    for item in items:
        memberships, weights = membership_stack(item, names, compact, "edge")
        contexts.append(distorted_choquet(memberships, weights, GAMMA))
    return contexts


def _score_maps(items: list[dict], contexts: list[np.ndarray]):
    incumbents, candidates = [], []
    for item, context in zip(items, contexts):
        incumbents.append(
            context_gate(item["scharr"], context, STRENGTH, FLOOR).astype(np.float32)
        )
        candidates.append(
            context_gate(item["rgf_scharr"], context, STRENGTH, FLOOR).astype(
                np.float32
            )
        )
    return incumbents, candidates


def _save_soft_png(score: np.ndarray, path: Path) -> None:
    x = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(x)):
        raise RuntimeError(f"non-finite candidate score for {path.stem}")
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(
        np.rint(np.clip(x, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L"
    ).save(path)


def _fit_full_context(args: argparse.Namespace):
    raw = resize_items(
        load_uded(ensure_uded(Path(args.uded_root))), args.max_side_development
    )
    selection, names = prepare(raw[0::2])
    positive, _negative = learn_banks(
        selection,
        names,
        args.seed,
        args.max_positive,
        args.max_negative,
        args.max_abs_corr,
    )
    return names, _ordered_compact(positive)


def _write_official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [
            {
                "name": VARIANTS[1],
                "export": {
                    "script": "run_stage16f_rolling_guidance_localizer.py",
                    "args": [
                        "--export-bsds",
                        "--image-dir",
                        "{image_dir}",
                        "--output-dir",
                        "{output_dir}",
                        "--split",
                        "{split}",
                    ],
                    "timeout_minutes": 240,
                },
            }
        ],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def export_bsds(args: argparse.Namespace) -> int:
    names, compact = _fit_full_context(args)
    image_paths = sorted(Path(args.image_dir).glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {args.image_dir}")
    output_dir = Path(args.output_dir)
    diagnostics = []
    for index, path in enumerate(image_paths, start=1):
        print(
            f"STAGE16F_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {path.stem}",
            flush=True,
        )
        prepared, candidate_names = prepare([{"id": path.stem, "img": imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        _add_candidate_localizers(prepared)
        candidate = _score_maps(prepared, _contexts(prepared, names, compact))[1][0]
        _save_soft_png(candidate, output_dir / f"{path.stem}.png")
        diagnostics.append({"image_id": path.stem, **prepared[0]["rgf_diagnostic"]})
    pd.DataFrame(diagnostics).to_csv(
        output_dir / "conditioning_diagnostics.csv", index=False
    )
    metadata = {
        "method": VARIANTS[1],
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "development_source": "UDED selection only",
        "output": "8-bit soft PNG without per-image normalization",
        "mechanism": {
            "implementation_fidelity": (
                "equation-level repository reimplementation of grayscale rolling "
                "guidance; not an exact author-code reproduction"
            ),
            "sigma_space": SIGMA_SPACE,
            "sigma_range": SIGMA_RANGE,
            "iterations": ITERATIONS,
            "spatial_truncation_sigma": TRUNCATE,
            "source": "incumbent median-conditioned grayscale image",
            "downstream": "unchanged Scharr+NMS and compact Choquet context gate",
        },
        "n_maps": len(image_paths),
    }
    (output_dir / "export_manifest.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return 0


def run_experiment(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    selection, names = prepare(raw[0::2])
    if len(selection) != 15:
        raise RuntimeError(f"expected 15 UDED selection images, found {len(selection)}")
    _add_candidate_localizers(selection)

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts: dict[str, list] = defaultdict(list)
    fold_f1: dict[str, list[float]] = defaultdict(list)
    thresholds: dict[str, list[float]] = defaultdict(list)
    fold_rows, image_rows, diagnostic_rows = [], [], []
    first_repeat_predictions: dict[str, dict[int, np.ndarray]] = {
        name: {} for name in VARIANTS
    }

    for split_no, (repeat, fold, tr_idx, va_idx) in enumerate(splits, start=1):
        train = [selection[index] for index in tr_idx]
        valid = [selection[index] for index in va_idx]
        positive, _negative = learn_banks(
            train,
            names,
            args.seed + 10000 * repeat + fold,
            args.max_positive,
            args.max_negative,
            args.max_abs_corr,
        )
        compact = _ordered_compact(positive)
        train_maps = _score_maps(train, _contexts(train, names, compact))
        valid_maps = _score_maps(valid, _contexts(valid, names, compact))
        print(
            f"STAGE16F_SPLIT {split_no:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1}",
            flush=True,
        )
        for variant_index, variant in enumerate(VARIANTS):
            train_scores = train_maps[variant_index]
            valid_scores = valid_maps[variant_index]
            threshold = float(
                selection_metric(train_scores, train, args.thresholds)["threshold"]
            )
            metric, event_counts, per_image = fixed_eval(
                valid_scores, valid, threshold
            )
            counts[variant].extend(event_counts)
            fold_f1[variant].append(float(metric["F1"]))
            thresholds[variant].append(threshold)
            fold_rows.append(
                {
                    "repeat": repeat + 1,
                    "fold": fold + 1,
                    "variant": variant,
                    "train_threshold": threshold,
                    **metric,
                }
            )
            image_rows.extend(
                {
                    "repeat": repeat + 1,
                    "fold": fold + 1,
                    "variant": variant,
                    **row,
                }
                for row in per_image
            )
            if repeat == 0:
                for global_index, score in zip(va_idx, valid_scores):
                    first_repeat_predictions[variant][int(global_index)] = (
                        score >= threshold
                    )
        for global_index in va_idx:
            diagnostic_rows.append(
                {
                    "repeat": repeat + 1,
                    "fold": fold + 1,
                    "image_index": int(global_index),
                    "image_id": selection[int(global_index)]["id"],
                    **selection[int(global_index)]["rgf_diagnostic"],
                }
            )

    aggregate = {name: aggregate_counts(counts[name]) for name in VARIANTS}
    candidate_folds = np.asarray(fold_f1[VARIANTS[1]], dtype=np.float64)
    incumbent_folds = np.asarray(fold_f1[VARIANTS[0]], dtype=np.float64)
    deltas = {
        "aggregate_F1": float(
            aggregate[VARIANTS[1]]["F1"] - aggregate[VARIANTS[0]]["F1"]
        ),
        "aggregate_precision": float(
            aggregate[VARIANTS[1]]["precision"]
            - aggregate[VARIANTS[0]]["precision"]
        ),
        "aggregate_recall": float(
            aggregate[VARIANTS[1]]["recall"] - aggregate[VARIANTS[0]]["recall"]
        ),
        "mean_fold_F1": float(np.mean(candidate_folds - incumbent_folds)),
        "fold_wins": int(np.sum(candidate_folds > incumbent_folds)),
    }
    uded_gate = bool(
        deltas["aggregate_F1"] >= 0.002
        and deltas["aggregate_precision"] >= 0.002
        and deltas["aggregate_recall"] >= -0.01
        and deltas["mean_fold_F1"] >= 0.0
        and deltas["fold_wins"] >= 9
    )

    ranking = []
    for variant in VARIANTS:
        values = np.asarray(fold_f1[variant], dtype=np.float64)
        ranking.append(
            {
                "variant": variant,
                "cv_precision": aggregate[variant]["precision"],
                "cv_recall": aggregate[variant]["recall"],
                "cv_F1": aggregate[variant]["F1"],
                "mean_fold_F1": float(np.mean(values)),
                "std_fold_F1": float(np.std(values)),
                "threshold_mean": float(np.mean(thresholds[variant])),
                "threshold_std": float(np.std(thresholds[variant])),
            }
        )
    pd.DataFrame(ranking).sort_values("cv_F1", ascending=False).to_csv(
        out / "variant_ranking.csv", index=False
    )
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)
    pd.DataFrame(diagnostic_rows).to_csv(
        out / "conditioning_diagnostics.csv", index=False
    )

    if any(len(first_repeat_predictions[name]) != len(selection) for name in VARIANTS):
        raise RuntimeError("first-repeat out-of-fold preview predictions are incomplete")
    rows = []
    for position in PREVIEW_POSITIONS:
        item = selection[position]
        rows.append(
            [
                item["img"],
                item["gt"],
                first_repeat_predictions[VARIANTS[0]][position],
                item["rgf_filtered"],
                first_repeat_predictions[VARIANTS[1]][position],
            ]
        )
    preview_path = write_panel_grid(out / "best_method_preview.png", rows)
    manifest_path = _write_official_manifest(out)
    summary = {
        "stage": "16f-rolling-guidance-localizer",
        "role": "generation_2_scale_aware_conditioning_falsification",
        "architecture_changed": False,
        "protected_split_used": False,
        "datasets": {
            "UDED_selection": {
                "n_images": len(selection),
                "role": "development repeated leakage-free CV",
                "repeats": args.repeats,
                "folds": args.folds,
            },
            "BSDS500_validation": {
                "role": "development official attachment",
                "status": "pending controller attachment",
            },
        },
        "mechanism": {
            "description": (
                "fixed grayscale rolling-guidance small-structure removal before "
                "the unchanged Scharr+NMS localizer; compact Choquet context unchanged"
            ),
            "implementation_fidelity": (
                "equation-level repository reimplementation of Zhang et al. (ECCV "
                "2014), not an exact author-code reproduction"
            ),
            "parameters": {
                "sigma_space": SIGMA_SPACE,
                "sigma_range": SIGMA_RANGE,
                "iterations": ITERATIONS,
                "spatial_truncation_sigma": TRUNCATE,
                "input": "incumbent median-conditioned grayscale",
            },
            "parameter_selection": (
                "primary-paper equations with standard OpenCV interface defaults and "
                "fixed numerical truncation; no search"
            ),
        },
        "promotion_rule": (
            "Conjunctive: UDED aggregate F1 delta at least +0.002, aggregate "
            "precision delta at least +0.002, aggregate recall no worse than -0.01, "
            "mean paired fold-F1 delta nonnegative, and at least 9/15 fold wins. "
            "The official attachment must complete; BSDS500-validation ODS delta "
            "must be at least +0.002 and OIS/AP deltas must both be nonnegative. "
            "All conditions are required."
        ),
        "uded_gate": {"met": uded_gate, "deltas": deltas},
        "metrics": aggregate,
        "promotion_pending_official_bsds_val": True,
        "official_evaluation": {
            "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
            "required_before_promotion": True,
            "stage15a_caveat": (
                "the unmodified Windows matcher remains stochastic and reference-"
                "uncertified; the fixed-seed diagnostic matcher is forbidden"
            ),
        },
        "visual_preview": {
            "file": preview_path.name,
            "selection": "fixed UDED-selection positions 1, 8, and 15",
            "columns": [
                "input",
                "ground_truth",
                "compact_MFI_out_of_fold_prediction",
                "rolling_guidance_conditioned_grayscale",
                "candidate_out_of_fold_prediction",
            ],
            "use": "documentary only; not an optimization signal",
        },
        "files": [
            "summary.json",
            "variant_ranking.csv",
            "fold_results.csv",
            "per_image_metrics.csv",
            "conditioning_diagnostics.csv",
            "best_method_preview.png",
            "official_eval_manifest.json",
        ],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("STAGE16F_ROLLING_GUIDANCE_LOCALIZER_COMPLETE", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uded-root", default=str(DEFAULT_UDED))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--max-side", type=int, default=256)
    parser.add_argument("--thresholds", type=int, default=41)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-positive", type=int, default=10)
    parser.add_argument("--max-negative", type=int, default=8)
    parser.add_argument("--max-abs-corr", type=float, default=0.88)
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--export-bsds", action="store_true")
    parser.add_argument("--image-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--split", default="val")
    parser.add_argument("--max-side-development", type=int, default=256)
    args = parser.parse_args()
    if args.export_bsds:
        if not args.image_dir or not args.output_dir:
            parser.error("--export-bsds requires --image-dir and --output-dir")
        return export_bsds(args)
    return run_experiment(args)


if __name__ == "__main__":
    raise SystemExit(main())
