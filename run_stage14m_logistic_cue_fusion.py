from __future__ import annotations

"""Stage 14m: leakage-free linear probability-of-boundary cue fusion.

Only UDED selection images are loaded. The candidate replaces the incumbent's
fixed multiplicative context gate with a class-balanced L2-regularized logistic
fusion of the same Scharr+NMS localizer and retained compact memberships. Model
coefficients and thresholds are fit inside every outer training fold.
"""

from collections import defaultdict
from pathlib import Path
import argparse
import json
import math

import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from scipy.optimize import minimize

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
from src.edge_signature import binary_auc


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14m_logistic_cue_fusion"
VARIANTS = ("compact_incumbent", "linear_logistic_fusion")
MODEL_FEATURES = (
    "scharr_nms",
    "compact_choquet_context",
    "scharr_x_context",
    *COMPACT_FEATURES,
)


def _cue_maps(items: list[dict], names: list[str], compact: list[dict]):
    controls, model_maps = [], []
    for item in items:
        memberships, weights = membership_stack(item, names, compact, "edge")
        context = distorted_choquet(memberships, weights, GAMMA)
        scharr = np.asarray(item["scharr"], np.float32)
        controls.append(context_gate(scharr, context, STRENGTH, FLOOR))
        model_maps.append(
            np.concatenate(
                [
                    scharr[..., None],
                    context[..., None],
                    (scharr * context)[..., None],
                    memberships,
                ],
                axis=-1,
            ).astype(np.float32)
        )
    return controls, model_maps


def _sample_training_rows(
    items: list[dict],
    feature_maps: list[np.ndarray],
    seed: int,
    max_samples_per_class: int,
):
    rows, targets = [], []
    sample_counts = []
    structure = ndi.generate_binary_structure(2, 1)
    for item_no, (item, maps) in enumerate(zip(items, feature_maps)):
        scharr = np.asarray(item["scharr"], float)
        support = np.isfinite(scharr) & (scharr > 0.0)
        gt = np.asarray(item["gt"], bool)
        tol = max(1, int(round(0.0075 * math.hypot(*gt.shape))))
        positive_region = ndi.binary_dilation(gt, structure=structure, iterations=tol)
        positive_ids = np.flatnonzero((support & positive_region).ravel())
        negative_ids = np.flatnonzero((support & ~positive_region).ravel())
        rng = np.random.default_rng(int(seed) + 1009 * item_no)

        if positive_ids.size > int(max_samples_per_class):
            positive_ids = rng.choice(
                positive_ids, size=int(max_samples_per_class), replace=False
            )

        if negative_ids.size > int(max_samples_per_class):
            hard_n = int(max_samples_per_class) // 2
            negative_scores = scharr.ravel()[negative_ids]
            order = np.argsort(negative_scores, kind="mergesort")[::-1]
            hard_ids = negative_ids[order[:hard_n]]
            remaining = negative_ids[order[hard_n:]]
            random_n = int(max_samples_per_class) - hard_ids.size
            if remaining.size > random_n:
                remaining = rng.choice(remaining, size=random_n, replace=False)
            negative_ids = np.concatenate([hard_ids, remaining])

        flat = np.asarray(maps, np.float32).reshape(-1, maps.shape[-1])
        if positive_ids.size:
            rows.append(flat[positive_ids])
            targets.append(np.ones(positive_ids.size, dtype=np.float64))
        if negative_ids.size:
            rows.append(flat[negative_ids])
            targets.append(np.zeros(negative_ids.size, dtype=np.float64))
        sample_counts.append(
            {
                "id": str(item["id"]),
                "positive_samples": int(positive_ids.size),
                "negative_samples": int(negative_ids.size),
                "tolerance_px": int(tol),
            }
        )
    if not rows:
        raise RuntimeError("No Stage-14m logistic calibration samples were extracted")
    return np.concatenate(rows, axis=0), np.concatenate(targets), sample_counts


def _fit_logistic(
    X: np.ndarray,
    y: np.ndarray,
    l2: float = 1.0,
):
    X = np.asarray(X, np.float64)
    y = np.asarray(y, np.float64)
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std < 1.0e-6] = 1.0
    Z = (X - mean) / std
    n_pos = max(float(y.sum()), 1.0)
    n_neg = max(float((1.0 - y).sum()), 1.0)
    sample_weight = np.where(y > 0.5, 0.5 / n_pos, 0.5 / n_neg)
    n_features = max(int(Z.shape[1]), 1)

    def objective(theta):
        weights, bias = theta[:-1], theta[-1]
        linear = np.clip(Z @ weights + bias, -30.0, 30.0)
        loss = np.sum(sample_weight * (np.logaddexp(0.0, linear) - y * linear))
        probability = 1.0 / (1.0 + np.exp(-linear))
        residual = sample_weight * (probability - y)
        gradient = np.concatenate(
            [
                Z.T @ residual + (float(l2) / n_features) * weights,
                np.asarray([residual.sum()]),
            ]
        )
        regularizer = 0.5 * float(l2) * float(np.dot(weights, weights)) / n_features
        return float(loss + regularizer), gradient

    initial = np.zeros(Z.shape[1] + 1, dtype=np.float64)
    optimum = minimize(
        objective,
        initial,
        method="L-BFGS-B",
        jac=True,
        options={"maxiter": 250, "ftol": 1.0e-9},
    )
    model = {
        "weights": np.asarray(optimum.x[:-1], np.float64),
        "bias": float(optimum.x[-1]),
        "mean": mean,
        "std": std,
        "success": bool(optimum.success),
        "message": str(optimum.message),
        "objective": float(optimum.fun),
        "l2": float(l2),
    }
    fitted = _predict_rows(X, model)
    model["training_auc"] = float(binary_auc(fitted, y > 0.5))
    return model


def _predict_rows(X: np.ndarray, model: dict) -> np.ndarray:
    Z = (np.asarray(X, np.float64) - model["mean"]) / model["std"]
    linear = np.clip(Z @ model["weights"] + float(model["bias"]), -30.0, 30.0)
    return (1.0 / (1.0 + np.exp(-linear))).astype(np.float32)


def _predict_maps(items: list[dict], feature_maps: list[np.ndarray], model: dict):
    scores = []
    for item, maps in zip(items, feature_maps):
        shape = maps.shape[:2]
        probability = _predict_rows(maps.reshape(-1, maps.shape[-1]), model).reshape(shape)
        support = np.asarray(item["scharr"], float) > 0.0
        scores.append(np.where(support, probability, 0.0).astype(np.float32))
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
    parser.add_argument("--max-samples-per-class", type=int, default=2500)
    parser.add_argument("--l2", type=float, default=1.0)
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
    fold_rows, image_rows, coefficient_rows, sample_rows = [], [], [], []
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
        X, y, split_sample_counts = _sample_training_rows(
            train,
            train_maps,
            args.seed + 20000 * repeat + fold,
            args.max_samples_per_class,
        )
        model = _fit_logistic(X, y, args.l2)
        train_candidate = _predict_maps(train, train_maps, model)
        valid_candidate = _predict_maps(valid, valid_maps, model)
        variant_scores = {
            "compact_incumbent": (train_control, valid_control),
            "linear_logistic_fusion": (train_candidate, valid_candidate),
        }
        split_predictions = {}
        print(
            f"STAGE14M_SPLIT {split_no:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1} "
            f"auc={model['training_auc']:.4f} success={model['success']}",
            flush=True,
        )

        raw_weights = model["weights"] / model["std"]
        raw_intercept = float(model["bias"] - np.dot(model["weights"], model["mean"] / model["std"]))
        for feature_no, feature in enumerate(MODEL_FEATURES):
            coefficient_rows.append(
                {
                    "repeat": repeat + 1,
                    "fold": fold + 1,
                    "feature": feature,
                    "standardized_coefficient": float(model["weights"][feature_no]),
                    "raw_coefficient": float(raw_weights[feature_no]),
                    "raw_intercept": raw_intercept,
                    "training_auc": float(model["training_auc"]),
                    "optimizer_success": bool(model["success"]),
                    "optimizer_message": str(model["message"]),
                }
            )
        sample_rows.extend(
            {
                "repeat": repeat + 1,
                "fold": fold + 1,
                **row,
            }
            for row in split_sample_counts
        )

        for variant in VARIANTS:
            train_scores, valid_scores = variant_scores[variant]
            fit = selection_metric(train_scores, train, args.thresholds)
            threshold = float(fit["threshold"])
            metric, event_counts, per_image = fixed_eval(valid_scores, valid, threshold)
            predictions = [np.asarray(score) >= threshold for score in valid_scores]
            split_predictions[variant] = predictions
            counts[variant].extend(event_counts)
            fold_metrics[variant].append(metric)
            thresholds[variant].append(threshold)
            fold_rows.append(
                {
                    "repeat": repeat + 1,
                    "fold": fold + 1,
                    "variant": variant,
                    "train_threshold": threshold,
                    "optimizer_success": bool(model["success"]),
                    "training_auc": float(model["training_auc"]),
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

        if preview is None:
            preview = {
                "item": valid[0],
                "control": split_predictions["compact_incumbent"][0],
                "candidate": split_predictions["linear_logistic_fusion"][0],
            }

    aggregate = {variant: aggregate_counts(counts[variant]) for variant in VARIANTS}
    control, candidate = VARIANTS
    f1_delta = float(aggregate[candidate]["F1"] - aggregate[control]["F1"])
    precision_delta = float(
        aggregate[candidate]["precision"] - aggregate[control]["precision"]
    )
    fold_delta = np.asarray(
        [
            candidate_metric["F1"] - control_metric["F1"]
            for control_metric, candidate_metric in zip(
                fold_metrics[control], fold_metrics[candidate]
            )
        ],
        dtype=float,
    )
    convergence_count = int(
        sum(bool(row["optimizer_success"]) for row in fold_rows if row["variant"] == candidate)
    )
    criterion = bool(
        f1_delta >= 0.001
        and precision_delta >= -0.002
        and float(np.mean(fold_delta)) > 0.0
        and int(np.sum(fold_delta > 0.0)) >= 9
        and convergence_count == len(splits)
    )
    retained_best = candidate if criterion else control

    ranking_rows = []
    for variant in VARIANTS:
        values = np.asarray([row["F1"] for row in fold_metrics[variant]], dtype=float)
        ranking_rows.append(
            {
                "variant": variant,
                "cv_precision": float(aggregate[variant]["precision"]),
                "cv_recall": float(aggregate[variant]["recall"]),
                "cv_F1": float(aggregate[variant]["F1"]),
                "mean_fold_F1": float(np.mean(values)),
                "std_fold_F1": float(np.std(values)),
                "threshold_mean": float(np.mean(thresholds[variant])),
                "threshold_std": float(np.std(thresholds[variant])),
            }
        )
    pd.DataFrame(ranking_rows).sort_values("cv_F1", ascending=False).to_csv(
        out / "variant_ranking.csv", index=False
    )
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)
    pd.DataFrame(coefficient_rows).to_csv(out / "model_coefficients.csv", index=False)
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
        "stage": "14m-linear-logistic-cue-fusion",
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
            "family": "class-balanced L2-regularized linear logistic probability-of-boundary fusion",
            "features": list(MODEL_FEATURES),
            "support": "Scharr+NMS-positive pixels only",
            "l2": float(args.l2),
            "max_samples_per_class_per_image": int(args.max_samples_per_class),
            "hard_negative_policy": "half highest-Scharr negatives and half deterministic random negatives",
            "fit_policy": "coefficients, standardization, and threshold fit inside each outer training fold",
        },
        "threshold_policy": "fit independently inside each training fold; freeze on paired validation fold",
        "promotion_rule": (
            "promote only if aggregate F1 delta >= +0.001, precision delta >= -0.002, "
            "mean fold F1 delta > 0, candidate wins at least 9/15 folds, and all "
            "15 fold models converge"
        ),
        "primary_result": {
            "aggregate_F1_delta": f1_delta,
            "aggregate_precision_delta": precision_delta,
            "mean_fold_F1_delta": float(np.mean(fold_delta)),
            "fold_F1_wins": int(np.sum(fold_delta > 0.0)),
            "converged_models": convergence_count,
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
                "linear_logistic_fusion",
                "retained_best",
            ],
        },
        "files": [
            "variant_ranking.csv",
            "fold_results.csv",
            "per_image_metrics.csv",
            "model_coefficients.csv",
            "training_samples.csv",
            "best_method_preview.png",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14M_LOGISTIC_CUE_FUSION_COMPLETE", flush=True)
    print(out / "summary.json", flush=True)
    print(preview_path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
