from __future__ import annotations

"""Stage 14k: fixed CIELAB vector-gradient localizer falsification.

Only UDED selection images are loaded.  The compact positive context bank is
fit inside every training fold.  The sole candidate change is replacing the
incumbent grayscale Scharr+NMS score with a fixed CIELAB Di Zenzo tensor made
from channel-wise Scharr derivatives.  Each variant receives an independently
fit training-fold threshold.
"""

from collections import defaultdict
from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12b_fuzzy_signature import prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage14c_positive_bank_pruning import (
    COMPACT_FEATURES,
    FLOOR,
    STRENGTH,
    _contexts,
    _filter_bank,
)
from src.bipolar_fuzzy import context_gate
from src.color_gradient import lab_di_zenzo_scharr_nms


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14k_color_tensor_localizer"
VARIANTS = ("compact_gray_scharr", "compact_lab_tensor")


def _attach_color_localizers(items: list[dict]) -> None:
    for number, item in enumerate(items, 1):
        print(f"STAGE14K_COLOR {number:02d}/{len(items)} {item['id']}", flush=True)
        score, orientation = lab_di_zenzo_scharr_nms(item["img"], median_size=3)
        item["lab_tensor"] = score
        item["lab_tensor_orientation"] = orientation


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
    parser.add_argument("--seed", type=int, default=20261006)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    selection, names = prepare(raw[0::2])
    if len(selection) != 15:
        raise RuntimeError(f"Expected 15 UDED selection images, found {len(selection)}")
    if any(np.asarray(item["img"]).ndim != 3 for item in selection):
        raise RuntimeError("Stage 14k requires RGB UDED selection images")
    _attach_color_localizers(selection)

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts = defaultdict(list)
    fold_metrics = defaultdict(list)
    thresholds = defaultdict(list)
    fold_rows, image_rows = [], []
    preview = None

    for split_no, (repeat, fold, tr_idx, va_idx) in enumerate(splits, 1):
        train = [selection[i] for i in tr_idx]
        valid = [selection[i] for i in va_idx]
        positive, _negative = learn_banks(
            train,
            names,
            args.seed + 10000 * repeat + fold,
            args.max_positive,
            args.max_negative,
            args.max_abs_corr,
        )
        compact = _filter_bank(positive, COMPACT_FEATURES)
        train_context = _contexts(train, names, compact)
        valid_context = _contexts(valid, names, compact)
        print(
            f"STAGE14K_SPLIT {split_no:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1}",
            flush=True,
        )

        split_predictions = {}
        for variant, localizer_key in (
            ("compact_gray_scharr", "scharr"),
            ("compact_lab_tensor", "lab_tensor"),
        ):
            train_scores = [
                context_gate(item[localizer_key], context, STRENGTH, FLOOR)
                for item, context in zip(train, train_context)
            ]
            valid_scores = [
                context_gate(item[localizer_key], context, STRENGTH, FLOOR)
                for item, context in zip(valid, valid_context)
            ]
            fit = selection_metric(train_scores, train, args.thresholds)
            threshold = float(fit["threshold"])
            metric, event_counts, per_image = fixed_eval(valid_scores, valid, threshold)
            predictions = [np.asarray(score) >= threshold for score in valid_scores]
            split_predictions[variant] = predictions
            counts[variant].extend(event_counts)
            fold_metrics[variant].append(metric)
            thresholds[variant].append(threshold)
            fold_rows.append({
                "repeat": repeat + 1,
                "fold": fold + 1,
                "variant": variant,
                "train_threshold": threshold,
                **metric,
            })
            image_rows.extend({
                "repeat": repeat + 1,
                "fold": fold + 1,
                "variant": variant,
                **row,
            } for row in per_image)

        if preview is None:
            preview = {
                "item": valid[0],
                "control": split_predictions["compact_gray_scharr"][0],
                "candidate": split_predictions["compact_lab_tensor"][0],
            }

    aggregate = {variant: aggregate_counts(counts[variant]) for variant in VARIANTS}
    control, candidate = VARIANTS
    f1_delta = float(aggregate[candidate]["F1"] - aggregate[control]["F1"])
    precision_delta = float(
        aggregate[candidate]["precision"] - aggregate[control]["precision"]
    )
    fold_delta = np.asarray([
        candidate_metric["F1"] - control_metric["F1"]
        for control_metric, candidate_metric in zip(
            fold_metrics[control], fold_metrics[candidate]
        )
    ], dtype=float)
    criterion = bool(
        f1_delta >= 0.001
        and precision_delta >= -0.002
        and float(np.mean(fold_delta)) > 0.0
        and int(np.sum(fold_delta > 0.0)) >= 9
    )
    retained_best = candidate if criterion else control

    ranking_rows = []
    for variant in VARIANTS:
        values = np.asarray([row["F1"] for row in fold_metrics[variant]], dtype=float)
        ranking_rows.append({
            "variant": variant,
            "cv_precision": float(aggregate[variant]["precision"]),
            "cv_recall": float(aggregate[variant]["recall"]),
            "cv_F1": float(aggregate[variant]["F1"]),
            "mean_fold_F1": float(np.mean(values)),
            "std_fold_F1": float(np.std(values)),
            "threshold_mean": float(np.mean(thresholds[variant])),
            "threshold_std": float(np.std(thresholds[variant])),
        })
    pd.DataFrame(ranking_rows).sort_values("cv_F1", ascending=False).to_csv(
        out / "variant_ranking.csv", index=False
    )
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)

    if preview is None:
        raise RuntimeError("No deterministic preview sample was captured")
    best_prediction = preview["candidate"] if criterion else preview["control"]
    preview_path = write_panel_grid(
        out / "best_method_preview.png",
        [[
            preview["item"]["img"],
            preview["item"]["gt"],
            preview["control"],
            preview["candidate"],
            best_prediction,
        ]],
    )

    summary = {
        "stage": "14k-color-tensor-localizer",
        "dataset_role": "UDED selection only; repeated leakage-free development CV",
        "heldout_used": False,
        "external_feedback_used": False,
        "n_selection_images": len(selection),
        "repeats": args.repeats,
        "folds": args.folds,
        "n_validation_events": len(splits),
        "fixed_context": {
            "features": list(COMPACT_FEATURES),
            "aggregation": "positive distorted Choquet, gamma 0.55",
            "gate": {"strength": STRENGTH, "floor": FLOOR},
        },
        "candidate_change": {
            "from": "median-conditioned grayscale Scharr+NMS",
            "to": "channel-median-conditioned CIELAB Di Zenzo tensor Scharr+NMS",
            "parameters": {
                "color_space": "CIELAB",
                "common_lab_scale": 0.01,
                "median_size": 3,
                "derivative": "fixed 3x3 Scharr per channel",
                "magnitude": "sqrt(maximum Di Zenzo tensor eigenvalue), robust 1st-99th percentile normalization",
            },
        },
        "threshold_policy": "fit independently inside each training fold; freeze on paired validation fold",
        "promotion_rule": (
            "promote only if aggregate F1 delta >= +0.001, precision delta >= -0.002, "
            "mean fold F1 delta > 0, and candidate wins at least 9/15 folds"
        ),
        "primary_result": {
            "aggregate_F1_delta": f1_delta,
            "aggregate_precision_delta": precision_delta,
            "mean_fold_F1_delta": float(np.mean(fold_delta)),
            "fold_F1_wins": int(np.sum(fold_delta > 0.0)),
            "criterion_met": criterion,
        },
        "retained_best_method": retained_best,
        "metrics": aggregate,
        "visual_preview": {
            "file": preview_path.name,
            "selection": "first validation image of the first deterministic repeated-CV split",
            "rows": ["fixed representative"],
            "columns": [
                "input_rgb",
                "ground_truth",
                "compact_gray_scharr",
                "compact_lab_tensor",
                "retained_best",
            ],
        },
        "files": [
            "variant_ranking.csv",
            "fold_results.csv",
            "per_image_metrics.csv",
            "best_method_preview.png",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14K_COLOR_TENSOR_COMPLETE", flush=True)
    print(out / "summary.json", flush=True)
    print(preview_path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
