from __future__ import annotations

"""Stage 14n: leakage-free shallow edge-forest localizer falsification.

Only UDED selection images are loaded.  The incumbent compact positive
Choquet gate is compared with a small randomized decision forest trained
inside each outer fold.  The forest predicts a dense boundary probability
from the same interpretable compact memberships plus raw/localized Scharr
cues; fixed grayscale gradient orientation supplies NMS localization.

This is a deliberately bounded test of nonlinear cue interactions and a
learned non-neural localizer.  It is not a reproduction of Structured Edges
or Oriented Edge Forests and does not predict structured patch masks.
"""

from collections import defaultdict
from pathlib import Path
import argparse
import json
import math

import numpy as np
import pandas as pd
from scipy import ndimage as ndi

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
from src.edge_signature import binary_auc
from src.postprocess import non_maximum_suppression


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14n_shallow_edge_forest"
VARIANTS = ("compact_incumbent", "shallow_edge_forest")
MODEL_FEATURES = (
    "raw_scharr",
    "scharr_nms",
    "compact_choquet_context",
    "raw_scharr_x_context",
    "scharr_nms_x_context",
    *COMPACT_FEATURES,
)


def _gini(target: np.ndarray) -> float:
    if target.size == 0:
        return 0.0
    p = float(np.mean(target))
    return 2.0 * p * (1.0 - p)


def _fit_tree(
    X: np.ndarray,
    y: np.ndarray,
    rng: np.random.Generator,
    max_depth: int,
    min_leaf: int,
    max_features: int,
    thresholds_per_feature: int,
) -> tuple[list[dict], np.ndarray]:
    """Fit one compact ExtraTrees-style binary tree using Gini gain."""

    nodes: list[dict] = []
    importances = np.zeros(X.shape[1], dtype=np.float64)

    def grow(ids: np.ndarray, depth: int) -> int:
        node_no = len(nodes)
        positive = float(np.sum(y[ids]))
        probability = float((positive + 1.0) / (ids.size + 2.0))
        nodes.append({
            "feature": -1,
            "threshold": 0.0,
            "left": -1,
            "right": -1,
            "probability": probability,
            "samples": int(ids.size),
            "depth": int(depth),
        })
        if (
            depth >= int(max_depth)
            or ids.size < 2 * int(min_leaf)
            or positive <= 0.0
            or positive >= float(ids.size)
        ):
            return node_no

        parent_impurity = _gini(y[ids])
        feature_count = min(int(max_features), X.shape[1])
        candidates = rng.choice(X.shape[1], size=feature_count, replace=False)
        best = None
        best_impurity = parent_impurity
        for feature in candidates:
            values = X[ids, int(feature)]
            lo, hi = np.quantile(values, [0.10, 0.90])
            if not np.isfinite(lo + hi) or hi <= lo + 1.0e-8:
                continue
            thresholds = rng.uniform(float(lo), float(hi), int(thresholds_per_feature))
            for threshold in thresholds:
                left_mask = values <= float(threshold)
                left_n = int(np.sum(left_mask))
                right_n = int(ids.size - left_n)
                if left_n < int(min_leaf) or right_n < int(min_leaf):
                    continue
                left_y = y[ids[left_mask]]
                right_y = y[ids[~left_mask]]
                impurity = (
                    left_n * _gini(left_y) + right_n * _gini(right_y)
                ) / float(ids.size)
                if impurity < best_impurity - 1.0e-12:
                    best_impurity = float(impurity)
                    best = (int(feature), float(threshold), left_mask)
        if best is None:
            return node_no

        feature, threshold, left_mask = best
        gain = max(parent_impurity - best_impurity, 0.0) * float(ids.size)
        importances[feature] += gain
        left = grow(ids[left_mask], depth + 1)
        right = grow(ids[~left_mask], depth + 1)
        nodes[node_no].update({
            "feature": feature,
            "threshold": threshold,
            "left": left,
            "right": right,
        })
        return node_no

    grow(np.arange(X.shape[0], dtype=np.int64), 0)
    return nodes, importances


def _fit_forest(
    X: np.ndarray,
    y: np.ndarray,
    seed: int,
    trees: int,
    max_depth: int,
    min_leaf: int,
    thresholds_per_feature: int,
) -> dict:
    X = np.asarray(X, np.float32)
    y = np.asarray(y, np.uint8)
    positive = np.flatnonzero(y > 0)
    negative = np.flatnonzero(y == 0)
    if not positive.size or not negative.size:
        raise RuntimeError("Stage-14n forest requires both boundary and background rows")
    per_class = min(positive.size, negative.size)
    max_features = max(1, int(math.ceil(math.sqrt(X.shape[1]))))
    fitted, importance = [], np.zeros(X.shape[1], dtype=np.float64)
    for tree_no in range(int(trees)):
        rng = np.random.default_rng(int(seed) + 104729 * tree_no)
        ids = np.concatenate([
            rng.choice(positive, size=per_class, replace=True),
            rng.choice(negative, size=per_class, replace=True),
        ])
        rng.shuffle(ids)
        nodes, tree_importance = _fit_tree(
            X[ids],
            y[ids],
            rng,
            max_depth,
            min_leaf,
            max_features,
            thresholds_per_feature,
        )
        fitted.append(nodes)
        importance += tree_importance
    total = float(np.sum(importance))
    if total > 0.0:
        importance /= total
    return {
        "trees": fitted,
        "feature_importance": importance,
        "max_features": max_features,
    }


def _predict_tree(X: np.ndarray, nodes: list[dict]) -> np.ndarray:
    prediction = np.zeros(X.shape[0], dtype=np.float32)
    pending = [(0, np.arange(X.shape[0], dtype=np.int64))]
    while pending:
        node_no, ids = pending.pop()
        if ids.size == 0:
            continue
        node = nodes[node_no]
        if int(node["feature"]) < 0:
            prediction[ids] = float(node["probability"])
            continue
        feature = int(node["feature"])
        left_mask = X[ids, feature] <= float(node["threshold"])
        pending.append((int(node["right"]), ids[~left_mask]))
        pending.append((int(node["left"]), ids[left_mask]))
    return prediction


def _predict_forest(X: np.ndarray, model: dict) -> np.ndarray:
    X = np.asarray(X, np.float32)
    probability = np.zeros(X.shape[0], dtype=np.float64)
    for nodes in model["trees"]:
        probability += _predict_tree(X, nodes)
    probability /= max(len(model["trees"]), 1)
    return probability.astype(np.float32)


def _cue_maps(items: list[dict], names: list[str], compact: list[dict]):
    controls, model_maps = [], []
    for item in items:
        memberships, weights = membership_stack(item, names, compact, "edge")
        context = distorted_choquet(memberships, weights, GAMMA)
        raw_scharr = detector_score(item["pre_img"], "scharr", 1.0).astype(np.float32)
        scharr_nms = np.asarray(item["scharr"], np.float32)
        controls.append(context_gate(scharr_nms, context, STRENGTH, FLOOR))
        model_maps.append(np.concatenate([
            raw_scharr[..., None],
            scharr_nms[..., None],
            context[..., None],
            (raw_scharr * context)[..., None],
            (scharr_nms * context)[..., None],
            memberships,
        ], axis=-1).astype(np.float32))
    return controls, model_maps


def _sample_training_rows(
    items: list[dict],
    feature_maps: list[np.ndarray],
    seed: int,
    max_samples_per_class: int,
):
    rows, targets, sample_counts = [], [], []
    structure = ndi.generate_binary_structure(2, 1)
    for item_no, (item, maps) in enumerate(zip(items, feature_maps)):
        gt = np.asarray(item["gt"], bool)
        tol = max(1, int(round(0.0075 * math.hypot(*gt.shape))))
        positive_region = ndi.binary_dilation(gt, structure=structure, iterations=tol)
        positive_ids = np.flatnonzero(positive_region.ravel())
        negative_ids = np.flatnonzero((~positive_region).ravel())
        rng = np.random.default_rng(int(seed) + 1009 * item_no)
        if positive_ids.size > int(max_samples_per_class):
            positive_ids = rng.choice(
                positive_ids, size=int(max_samples_per_class), replace=False
            )
        if negative_ids.size > int(max_samples_per_class):
            hard_n = int(max_samples_per_class) // 2
            raw_scores = maps[..., 0].ravel()[negative_ids]
            order = np.argsort(raw_scores, kind="mergesort")[::-1]
            hard_ids = negative_ids[order[:hard_n]]
            remaining = negative_ids[order[hard_n:]]
            random_n = int(max_samples_per_class) - hard_ids.size
            if remaining.size > random_n:
                remaining = rng.choice(remaining, size=random_n, replace=False)
            negative_ids = np.concatenate([hard_ids, remaining])
        flat = maps.reshape(-1, maps.shape[-1])
        rows.extend([flat[positive_ids], flat[negative_ids]])
        targets.extend([
            np.ones(positive_ids.size, dtype=np.uint8),
            np.zeros(negative_ids.size, dtype=np.uint8),
        ])
        sample_counts.append({
            "id": str(item["id"]),
            "positive_samples": int(positive_ids.size),
            "negative_samples": int(negative_ids.size),
            "tolerance_px": int(tol),
        })
    return np.concatenate(rows), np.concatenate(targets), sample_counts


def _predict_maps(items: list[dict], feature_maps: list[np.ndarray], model: dict):
    scores = []
    for item, maps in zip(items, feature_maps):
        shape = maps.shape[:2]
        probability = _predict_forest(maps.reshape(-1, maps.shape[-1]), model).reshape(shape)
        scores.append(non_maximum_suppression(probability, item["orientation"]).astype(np.float32))
    return scores


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
    parser.add_argument("--max-samples-per-class", type=int, default=1500)
    parser.add_argument("--trees", type=int, default=48)
    parser.add_argument("--max-depth", type=int, default=8)
    parser.add_argument("--min-leaf", type=int, default=40)
    parser.add_argument("--thresholds-per-feature", type=int, default=4)
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
    fold_rows, image_rows, diagnostic_rows, importance_rows, sample_rows = [], [], [], [], []
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
        compact_unordered = _filter_bank(positive, COMPACT_FEATURES)
        compact_by_feature = {str(row["feature"]): row for row in compact_unordered}
        compact = [compact_by_feature[feature] for feature in COMPACT_FEATURES]
        train_control, train_maps = _cue_maps(train, names, compact)
        valid_control, valid_maps = _cue_maps(valid, names, compact)
        X, y, split_samples = _sample_training_rows(
            train,
            train_maps,
            args.seed + 20000 * repeat + fold,
            args.max_samples_per_class,
        )
        model = _fit_forest(
            X,
            y,
            args.seed + 30000 * repeat + fold,
            args.trees,
            args.max_depth,
            args.min_leaf,
            args.thresholds_per_feature,
        )
        train_candidate = _predict_maps(train, train_maps, model)
        valid_candidate = _predict_maps(valid, valid_maps, model)
        training_auc = float(binary_auc(_predict_forest(X, model), y > 0))
        tree_nodes = np.asarray([len(tree) for tree in model["trees"]], dtype=float)
        tree_depths = np.asarray([
            max(int(node["depth"]) for node in tree) for tree in model["trees"]
        ], dtype=float)
        finite_predictions = bool(all(np.isfinite(score).all() for score in valid_candidate))
        diagnostic_rows.append({
            "repeat": repeat + 1,
            "fold": fold + 1,
            "training_auc": training_auc,
            "mean_tree_nodes": float(np.mean(tree_nodes)),
            "mean_tree_depth": float(np.mean(tree_depths)),
            "finite_predictions": finite_predictions,
        })
        for feature, importance in zip(MODEL_FEATURES, model["feature_importance"]):
            importance_rows.append({
                "repeat": repeat + 1,
                "fold": fold + 1,
                "feature": feature,
                "gini_importance": float(importance),
            })
        sample_rows.extend({
            "repeat": repeat + 1,
            "fold": fold + 1,
            **row,
        } for row in split_samples)
        print(
            f"STAGE14N_SPLIT {split_no:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1} auc={training_auc:.4f} "
            f"nodes={np.mean(tree_nodes):.1f}",
            flush=True,
        )

        variants = {
            "compact_incumbent": (train_control, valid_control),
            "shallow_edge_forest": (train_candidate, valid_candidate),
        }
        split_predictions = {}
        for variant in VARIANTS:
            train_scores, valid_scores = variants[variant]
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
                "training_auc": training_auc,
                "finite_predictions": finite_predictions,
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
                "control": split_predictions["compact_incumbent"][0],
                "candidate": split_predictions["shallow_edge_forest"][0],
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
    valid_model_count = int(sum(bool(row["finite_predictions"]) for row in diagnostic_rows))
    criterion = bool(
        f1_delta >= 0.001
        and precision_delta >= -0.002
        and float(np.mean(fold_delta)) > 0.0
        and int(np.sum(fold_delta > 0.0)) >= 9
        and valid_model_count == len(splits)
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
    pd.DataFrame(diagnostic_rows).to_csv(out / "forest_diagnostics.csv", index=False)
    pd.DataFrame(importance_rows).to_csv(out / "feature_importances.csv", index=False)
    pd.DataFrame(sample_rows).to_csv(out / "training_samples.csv", index=False)

    if preview is None:
        raise RuntimeError("No deterministic preview sample was captured")
    best_prediction = preview["candidate"] if criterion else preview["control"]
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
        "stage": "14n-shallow-edge-forest",
        "dataset_role": "UDED selection only; repeated leakage-free development CV",
        "heldout_used": False,
        "external_feedback_used": False,
        "n_selection_images": len(selection),
        "repeats": args.repeats,
        "folds": args.folds,
        "n_validation_events": len(splits),
        "incumbent": {
            "features": list(COMPACT_FEATURES),
            "aggregation": {"family": "positive distorted Choquet", "gamma": GAMMA},
            "localizer": "Scharr+NMS",
            "gate": {"strength": STRENGTH, "floor": FLOOR},
        },
        "candidate_change": {
            "family": "shallow randomized decision forest boundary localizer",
            "features": list(MODEL_FEATURES),
            "trees": int(args.trees),
            "max_depth": int(args.max_depth),
            "min_leaf": int(args.min_leaf),
            "thresholds_per_feature": int(args.thresholds_per_feature),
            "max_features_per_node": int(math.ceil(math.sqrt(len(MODEL_FEATURES)))),
            "max_samples_per_class_per_image": int(args.max_samples_per_class),
            "class_policy": "balanced bootstrap per tree; half hard and half deterministic-random negatives per image",
            "localization": "dense forest posterior followed by fixed grayscale-gradient NMS",
            "fit_policy": "membership calibration, forest, and threshold fit inside every outer training fold",
            "scope_note": "bounded OEF/Structured-Edges-inspired falsification; not a structured-mask reproduction",
        },
        "threshold_policy": "fit independently inside each training fold; freeze on paired validation fold",
        "promotion_rule": (
            "promote only if aggregate F1 delta >= +0.001, precision delta >= -0.002, "
            "mean fold F1 delta > 0, candidate wins at least 9/15 folds, and all "
            "15 fold models produce finite predictions"
        ),
        "primary_result": {
            "aggregate_F1_delta": f1_delta,
            "aggregate_precision_delta": precision_delta,
            "mean_fold_F1_delta": float(np.mean(fold_delta)),
            "fold_F1_wins": int(np.sum(fold_delta > 0.0)),
            "valid_models": valid_model_count,
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
                "compact_incumbent",
                "shallow_edge_forest",
                "retained_best",
            ],
        },
        "files": [
            "variant_ranking.csv",
            "fold_results.csv",
            "per_image_metrics.csv",
            "forest_diagnostics.csv",
            "feature_importances.csv",
            "training_samples.csv",
            "best_method_preview.png",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14N_SHALLOW_EDGE_FOREST_COMPLETE", flush=True)
    print(out / "summary.json", flush=True)
    print(preview_path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
