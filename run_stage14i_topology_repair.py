from __future__ import annotations

"""Stage 14i: leakage-free natural-image topology-repair falsification.

The retained compact positive controller and Scharr+NMS score are unchanged.
This experiment asks whether the fixed Stage-4 geodesic linker improves contour
continuity on UDED selection without a material loss in boundary F1/precision.
"""

from collections import defaultdict
from pathlib import Path
import argparse
import json
import math

import numpy as np
import pandas as pd

from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12b_fuzzy_signature import prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage14c_positive_bank_pruning import (
    COMPACT_FEATURES,
    FLOOR,
    GAMMA,
    STRENGTH,
    _contexts,
    _filter_bank,
)
from src.bipolar_fuzzy import context_gate
from src.evaluation import counts_to_prf, tolerant_counts
from src.linking import continuity_metrics, postprocess_binary
from automation.visual_report import write_panel_grid


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14i_topology_repair"
VARIANTS = ("no_link_control", "fixed_geodesic")
GEODESIC = {"max_gap": 8.0, "max_mean_cost": 0.60}


def _threshold_grid(scores: list[np.ndarray], n_thresholds: int) -> np.ndarray:
    values = np.concatenate([
        np.asarray(score, float)[np.isfinite(score)].ravel() for score in scores
    ])
    if not values.size:
        raise RuntimeError("No finite score values available for threshold fitting")
    return np.unique(np.quantile(values, np.linspace(0.01, 0.995, int(n_thresholds))))


def _predictions(
    scores: list[np.ndarray],
    contexts: list[np.ndarray],
    items: list[dict],
    threshold: float,
    variant: str,
) -> list[np.ndarray]:
    if variant == "no_link_control":
        return [np.asarray(score) >= float(threshold) for score in scores]
    if variant != "fixed_geodesic":
        raise ValueError(variant)
    return [
        postprocess_binary(
            score,
            float(threshold),
            method="geodesic",
            mfi_confidence=context,
            theta_normal=item["orientation"],
            **GEODESIC,
        )
        for score, context, item in zip(scores, contexts, items)
    ]


def _evaluate(predictions: list[np.ndarray], items: list[dict]):
    counts = []
    per_image = []
    for prediction, item in zip(predictions, items):
        gt = np.asarray(item["gt"], bool)
        tol = max(1, int(round(0.0075 * math.hypot(*gt.shape))))
        count = tuple(int(x) for x in tolerant_counts(prediction, gt, tol))
        precision, recall, f1 = counts_to_prf(*count)
        topology = continuity_metrics(prediction, gt, tol=tol)
        counts.append(count)
        per_image.append({
            "id": str(item["id"]),
            "tol_px": tol,
            "precision": float(precision),
            "recall": float(recall),
            "F1": float(f1),
            **topology,
        })
    return aggregate_counts(counts), counts, per_image


def _fit_threshold(
    scores: list[np.ndarray],
    contexts: list[np.ndarray],
    items: list[dict],
    variant: str,
    n_thresholds: int,
) -> float:
    best = None
    for threshold in _threshold_grid(scores, n_thresholds):
        predictions = _predictions(scores, contexts, items, float(threshold), variant)
        metric, _counts, _per_image = _evaluate(predictions, items)
        key = (float(metric["F1"]), float(metric["precision"]), float(threshold))
        if best is None or key > best[0]:
            best = (key, float(threshold))
    if best is None:
        raise RuntimeError(f"Threshold fitting failed for {variant}")
    return best[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uded-root", default=str(DEFAULT_UDED))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--max-side", type=int, default=256)
    parser.add_argument("--thresholds", type=int, default=21)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-positive", type=int, default=10)
    parser.add_argument("--max-negative", type=int, default=8)
    parser.add_argument("--max-abs-corr", type=float, default=.88)
    parser.add_argument("--seed", type=int, default=20261006)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    selection, names = prepare(raw[0::2])
    if len(selection) != 15:
        raise RuntimeError(f"Expected 15 UDED selection images, found {len(selection)}")

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts = defaultdict(list)
    fold_metrics = defaultdict(list)
    thresholds = defaultdict(list)
    topology_rows = defaultdict(list)
    fold_rows = []
    image_rows = []
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
        train_scores = [
            context_gate(item["scharr"], context, STRENGTH, FLOOR)
            for item, context in zip(train, train_context)
        ]
        valid_scores = [
            context_gate(item["scharr"], context, STRENGTH, FLOOR)
            for item, context in zip(valid, valid_context)
        ]
        print(
            f"STAGE14I_SPLIT {split_no:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1}",
            flush=True,
        )

        split_predictions = {}
        for variant in VARIANTS:
            threshold = _fit_threshold(
                train_scores, train_context, train, variant, args.thresholds
            )
            predictions = _predictions(
                valid_scores, valid_context, valid, threshold, variant
            )
            metric, event_counts, per_image = _evaluate(predictions, valid)
            split_predictions[variant] = predictions
            counts[variant].extend(event_counts)
            fold_metrics[variant].append(metric)
            thresholds[variant].append(threshold)
            topology_rows[variant].extend(per_image)
            fold_rows.append({
                "repeat": repeat + 1,
                "fold": fold + 1,
                "variant": variant,
                "train_threshold": threshold,
                **metric,
                "mean_largest_component_gt_coverage": float(np.mean([
                    row["largest_component_gt_coverage"] for row in per_image
                ])),
                "mean_edge_components_on_gt": float(np.mean([
                    row["edge_components_on_gt"] for row in per_image
                ])),
                "mean_endpoint_count": float(np.mean([
                    row["endpoint_count"] for row in per_image
                ])),
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
                "control": split_predictions["no_link_control"][0],
                "candidate": split_predictions["fixed_geodesic"][0],
            }

    aggregate = {variant: aggregate_counts(counts[variant]) for variant in VARIANTS}
    control, candidate = VARIANTS
    f1_delta = float(aggregate[candidate]["F1"] - aggregate[control]["F1"])
    precision_delta = float(
        aggregate[candidate]["precision"] - aggregate[control]["precision"]
    )
    fold_f1_delta = np.asarray([
        cand["F1"] - base["F1"]
        for base, cand in zip(fold_metrics[control], fold_metrics[candidate])
    ], dtype=float)
    control_coverage = np.asarray([
        row["largest_component_gt_coverage"] for row in topology_rows[control]
    ], dtype=float)
    candidate_coverage = np.asarray([
        row["largest_component_gt_coverage"] for row in topology_rows[candidate]
    ], dtype=float)
    coverage_delta = candidate_coverage - control_coverage
    fold_table = pd.DataFrame(fold_rows)
    control_fold_coverage = fold_table[fold_table.variant == control][
        "mean_largest_component_gt_coverage"
    ].to_numpy()
    candidate_fold_coverage = fold_table[fold_table.variant == candidate][
        "mean_largest_component_gt_coverage"
    ].to_numpy()
    coverage_fold_wins = int(np.sum(candidate_fold_coverage > control_fold_coverage))
    criterion = bool(
        f1_delta >= -0.001
        and precision_delta >= -0.005
        and float(np.mean(coverage_delta)) >= 0.03
        and coverage_fold_wins >= 9
    )
    retained_best = candidate if criterion else control

    ranking_rows = []
    for variant in VARIANTS:
        variant_topology = topology_rows[variant]
        ranking_rows.append({
            "variant": variant,
            "cv_precision": float(aggregate[variant]["precision"]),
            "cv_recall": float(aggregate[variant]["recall"]),
            "cv_F1": float(aggregate[variant]["F1"]),
            "mean_fold_F1": float(np.mean([m["F1"] for m in fold_metrics[variant]])),
            "mean_largest_component_gt_coverage": float(np.mean([
                row["largest_component_gt_coverage"] for row in variant_topology
            ])),
            "mean_edge_components_on_gt": float(np.mean([
                row["edge_components_on_gt"] for row in variant_topology
            ])),
            "mean_endpoint_count": float(np.mean([
                row["endpoint_count"] for row in variant_topology
            ])),
            "threshold_mean": float(np.mean(thresholds[variant])),
            "threshold_std": float(np.std(thresholds[variant])),
        })

    pd.DataFrame(ranking_rows).sort_values("cv_F1", ascending=False).to_csv(
        out / "variant_ranking.csv", index=False
    )
    fold_table.to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)

    if preview is None:
        raise RuntimeError("No deterministic preview sample was captured")
    best_prediction = (
        preview["candidate"] if retained_best == candidate else preview["control"]
    )
    preview_path = write_panel_grid(
        out / "best_method_preview.png",
        [[
            preview["item"]["pre_img"],
            preview["item"]["gt"],
            preview["control"],
            preview["candidate"],
            best_prediction,
        ]],
    )

    summary = {
        "stage": "14i-fixed-geodesic-topology-repair",
        "dataset_role": "UDED selection only; repeated leakage-free development CV",
        "heldout_used": False,
        "external_feedback_used": False,
        "n_selection_images": len(selection),
        "repeats": args.repeats,
        "folds": args.folds,
        "n_validation_events": len(splits),
        "fixed_architecture": {
            "features": list(COMPACT_FEATURES),
            "aggregation": {"family": "positive distorted Choquet", "gamma": GAMMA},
            "localizer": "Scharr+NMS",
            "gate": {"strength": STRENGTH, "floor": FLOOR},
        },
        "candidate_change": {
            "postprocessor": "MFI/context-guided geodesic endpoint linking",
            "parameters": GEODESIC,
            "source": "fixed Stage-4 synthetic-development winner; no Stage-14i sweep",
        },
        "threshold_policy": "fit independently inside each training fold; freeze on paired validation fold",
        "promotion_rule": (
            "retain geodesic repair only if aggregate CV F1 delta >= -0.001, "
            "precision delta >= -0.005, mean paired image coverage delta >= +0.03, "
            "and coverage improves in at least 9/15 folds"
        ),
        "primary_result": {
            "aggregate_F1_delta": f1_delta,
            "aggregate_precision_delta": precision_delta,
            "mean_fold_F1_delta": float(np.mean(fold_f1_delta)),
            "fold_F1_wins": int(np.sum(fold_f1_delta > 0)),
            "mean_paired_largest_component_coverage_delta": float(np.mean(coverage_delta)),
            "coverage_fold_wins": coverage_fold_wins,
            "criterion_met": criterion,
        },
        "retained_best_method": retained_best,
        "metrics": aggregate,
        "visual_preview": {
            "file": preview_path.name,
            "selection": "first validation image of the first deterministic repeated-CV split",
            "rows": ["fixed representative"],
            "columns": [
                "conditioned_input",
                "ground_truth",
                "no_link_incumbent",
                "fixed_geodesic_candidate",
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
    print("STAGE14I_TOPOLOGY_REPAIR_COMPLETE", flush=True)
    print(out / "summary.json", flush=True)
    print(preview_path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
