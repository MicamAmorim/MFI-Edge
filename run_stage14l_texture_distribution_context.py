from __future__ import annotations

"""Stage 14l: oriented texture-distribution context falsification.

Only UDED selection images are loaded.  The sole candidate change is one
fixed, non-neural half-disc LBP-distribution gradient appended to the retained
compact positive context bank.  Candidate calibration and thresholds are fit
inside every training fold.
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
from src.edge_signature import binary_auc, mutual_information_binary, population_masks
from src.texture_gradient import lbp_half_disc_texture_gradient


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14l_texture_distribution_context"
VARIANTS = ("compact_incumbent", "compact_plus_texture_distribution")
TEXTURE_DEFAULTS = {
    "radius_fraction": 0.02,
    "lbp_points": 8,
    "lbp_radius": 1.0,
    "orientations": 8,
    "minimum_radius": 3,
}


def _attach_texture_maps(items: list[dict]) -> dict:
    metadata = None
    radii = []
    for number, item in enumerate(items, 1):
        print(f"STAGE14L_TEXTURE {number:02d}/{len(items)} {item['id']}", flush=True)
        value, item_metadata = lbp_half_disc_texture_gradient(
            item["pre_img"], **TEXTURE_DEFAULTS
        )
        item["texture_distribution_gradient"] = value
        metadata = item_metadata
        radii.append(int(item_metadata["half_disc_radius"]))
    result = dict(metadata or {})
    result.pop("half_disc_radius", None)
    if radii:
        result["observed_half_disc_radius_min"] = min(radii)
        result["observed_half_disc_radius_max"] = max(radii)
    return result


def _fit_texture_spec(items: list[dict], seed: int, max_samples: int = 2500) -> dict:
    values, targets = [], []
    for item_no, item in enumerate(items):
        masks = population_masks(item)
        flat = np.asarray(item["texture_distribution_gradient"], float).ravel()
        for group_no, (group, target) in enumerate((("edge", True), ("texture", False))):
            ids = np.flatnonzero(np.asarray(masks[group], bool).ravel())
            if ids.size > int(max_samples):
                rng = np.random.default_rng(int(seed) + 1009 * item_no + 97 * group_no)
                ids = rng.choice(ids, size=int(max_samples), replace=False)
            if ids.size:
                values.append(flat[ids])
                targets.append(np.full(ids.size, target, dtype=bool))
    if not values:
        raise RuntimeError("No texture-gradient calibration samples were extracted")
    score = np.concatenate(values)
    target = np.concatenate(targets)
    auc = float(binary_auc(score, target))
    information = float(mutual_information_binary(score, target))
    edge_values = score[target]
    texture_values = score[~target]
    q25, q75 = np.quantile(score, [0.25, 0.75])
    raw_weight = max(auc - 0.5, 0.0) * (1.0 + information)
    eligible = bool(auc >= 0.56 and raw_weight > 0.0)
    return {
        "feature": "lbp_half_disc_texture_distribution_gradient",
        "edge_direction": 1.0,
        "midpoint": float(0.5 * (np.median(edge_values) + np.median(texture_values))),
        "scale": float(max(q75 - q25, 0.05)),
        "edge_median": float(np.median(edge_values)),
        "texture_median": float(np.median(texture_values)),
        "texture_auc": auc,
        "mutual_information": information,
        "raw_weight": float(raw_weight if eligible else 0.0),
        "eligible": eligible,
    }


def _with_raw_weights(bank: list[dict]) -> list[dict]:
    out = []
    for row in bank:
        copied = dict(row)
        copied["weight"] = max(float(row["texture_auc"]) - 0.5, 0.0) * (
            1.0 + float(row["mutual_information"])
        )
        out.append(copied)
    return out


def _texture_membership(item: dict, spec: dict) -> np.ndarray:
    value = np.asarray(item["texture_distribution_gradient"], float)
    z = (value - float(spec["midpoint"])) / max(float(spec["scale"]), 1.0e-9)
    return (1.0 / (1.0 + np.exp(-np.clip(z, -20.0, 20.0)))).astype(np.float32)


def _context_pairs(
    items: list[dict], names: list[str], compact: list[dict], texture_spec: dict
) -> tuple[list[np.ndarray], list[np.ndarray]]:
    control, candidate = [], []
    raw_compact = _with_raw_weights(compact)
    for item in items:
        memberships, weights = membership_stack(item, names, raw_compact, "edge")
        incumbent = distorted_choquet(memberships, weights, GAMMA)
        control.append(incumbent)
        if not texture_spec["eligible"]:
            candidate.append(incumbent.copy())
            continue
        texture = _texture_membership(item, texture_spec)[..., None]
        candidate_memberships = np.concatenate([memberships, texture], axis=-1)
        compact_raw = np.asarray([row["weight"] for row in raw_compact], dtype=float)
        candidate_weights = np.concatenate([
            compact_raw,
            np.asarray([texture_spec["raw_weight"]], dtype=float),
        ])
        candidate_weights /= max(float(candidate_weights.sum()), 1.0e-9)
        candidate.append(
            distorted_choquet(candidate_memberships, candidate_weights, GAMMA)
        )
    return control, candidate


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
    texture_metadata = _attach_texture_maps(selection)

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts = defaultdict(list)
    fold_metrics = defaultdict(list)
    thresholds = defaultdict(list)
    fold_rows, image_rows, calibration_rows = [], [], []
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
        texture_spec = _fit_texture_spec(train, args.seed + 20000 * repeat + fold)
        calibration_rows.append({
            "repeat": repeat + 1,
            "fold": fold + 1,
            **texture_spec,
        })
        train_control, train_candidate = _context_pairs(
            train, names, compact, texture_spec
        )
        valid_control, valid_candidate = _context_pairs(
            valid, names, compact, texture_spec
        )
        contexts = {
            "compact_incumbent": (train_control, valid_control),
            "compact_plus_texture_distribution": (train_candidate, valid_candidate),
        }
        split_predictions = {}
        print(
            f"STAGE14L_SPLIT {split_no:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1} "
            f"texture_auc={texture_spec['texture_auc']:.4f}",
            flush=True,
        )

        for variant in VARIANTS:
            train_context, valid_context = contexts[variant]
            train_scores = [
                context_gate(item["scharr"], context, STRENGTH, FLOOR)
                for item, context in zip(train, train_context)
            ]
            valid_scores = [
                context_gate(item["scharr"], context, STRENGTH, FLOOR)
                for item, context in zip(valid, valid_context)
            ]
            fit = selection_metric(train_scores, train, args.thresholds)
            threshold = float(fit["threshold"])
            metric, event_counts, per_image = fixed_eval(
                valid_scores, valid, threshold
            )
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
                "texture_eligible": bool(texture_spec["eligible"]),
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
                "candidate": split_predictions["compact_plus_texture_distribution"][0],
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
    eligible_folds = int(sum(bool(row["eligible"]) for row in calibration_rows))
    criterion = bool(
        f1_delta >= 0.001
        and precision_delta >= -0.002
        and float(np.mean(fold_delta)) > 0.0
        and int(np.sum(fold_delta > 0.0)) >= 9
        and eligible_folds >= 12
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
    pd.DataFrame(calibration_rows).to_csv(
        out / "texture_calibration.csv", index=False
    )

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
        "stage": "14l-texture-distribution-context",
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
            "feature": "maximum oriented chi-square contrast of uniform-LBP half-disc histograms",
            "parameters": {**TEXTURE_DEFAULTS, **texture_metadata},
            "calibration": "positive direction, membership, eligibility, and singleton weight fitted inside each training fold",
            "eligibility_rule": "training edge-v-texture AUC >= 0.56",
        },
        "threshold_policy": "fit independently inside each training fold; freeze on paired validation fold",
        "promotion_rule": (
            "promote only if aggregate F1 delta >= +0.001, precision delta >= -0.002, "
            "mean fold F1 delta > 0, candidate wins at least 9/15 folds, and the "
            "texture feature is training-eligible in at least 12/15 folds"
        ),
        "primary_result": {
            "aggregate_F1_delta": f1_delta,
            "aggregate_precision_delta": precision_delta,
            "mean_fold_F1_delta": float(np.mean(fold_delta)),
            "fold_F1_wins": int(np.sum(fold_delta > 0.0)),
            "texture_eligible_folds": eligible_folds,
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
                "compact_plus_texture_distribution",
                "retained_best",
            ],
        },
        "files": [
            "variant_ranking.csv",
            "fold_results.csv",
            "per_image_metrics.csv",
            "texture_calibration.csv",
            "best_method_preview.png",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14L_TEXTURE_DISTRIBUTION_COMPLETE", flush=True)
    print(out / "summary.json", flush=True)
    print(preview_path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
