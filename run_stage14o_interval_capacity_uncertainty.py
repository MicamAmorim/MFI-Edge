from __future__ import annotations

"""Stage 14o: interval uncertainty and reliability-conditioned capacity.

The retained compact Choquet context is compared with one preregistered
uncertainty-aware variant.  Membership fitting, uncertainty normalization,
and the operating threshold are rebuilt inside each UDED outer-training fold.
The candidate uses cue disagreement to (1) form interval memberships,
(2) interpolate the retained capacity toward its additive counterpart, and
(3) attenuate context by the resulting Choquet-envelope width.

The same file also exports a full-selection-fitted frozen candidate to native-
resolution BSDS500 validation images without reading BSDS ground truth.
"""

from collections import defaultdict
from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd
from PIL import Image
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


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14o_interval_capacity_uncertainty"
VARIANTS = ("compact_incumbent", "interval_capacity_uncertainty")
UNCERTAINTY_QUANTILE = 0.95
INTERVAL_HALF_WIDTH_FACTOR = 0.5


def _ordered_compact(bank: list[dict]) -> list[dict]:
    selected = _filter_bank(bank, COMPACT_FEATURES)
    by_feature = {str(row["feature"]): row for row in selected}
    return [by_feature[name] for name in COMPACT_FEATURES]


def _memberships(items: list[dict], names: list[str], compact: list[dict]):
    stacks: list[np.ndarray] = []
    weights = None
    for item in items:
        stack, weights = membership_stack(item, names, compact, "edge")
        stacks.append(stack)
    if weights is None:
        raise RuntimeError("no compact memberships were constructed")
    return stacks, np.asarray(weights, dtype=float)


def _fit_uncertainty_scale(stacks: list[np.ndarray]) -> float:
    disagreement = np.concatenate([
        np.std(np.asarray(stack, dtype=np.float32), axis=-1).ravel()
        for stack in stacks
    ])
    scale = float(np.quantile(disagreement, UNCERTAINTY_QUANTILE))
    return max(scale, 1e-6)


def _candidate_context(
    stack: np.ndarray,
    weights: np.ndarray,
    uncertainty_scale: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(stack, dtype=np.float32)
    u = np.clip(np.std(x, axis=-1) / float(uncertainty_scale), 0.0, 1.0)
    half_width = INTERVAL_HALF_WIDTH_FACTOR * u[..., None]
    lower_memberships = np.clip(x - half_width, 0.0, 1.0)
    upper_memberships = np.clip(x + half_width, 0.0, 1.0)

    lower_choquet = distorted_choquet(lower_memberships, weights, GAMMA)
    upper_choquet = distorted_choquet(upper_memberships, weights, GAMMA)
    lower_additive = distorted_choquet(lower_memberships, weights, 1.0)
    upper_additive = distorted_choquet(upper_memberships, weights, 1.0)

    # The Choquet integral is linear in the capacity for fixed memberships, so
    # these maps exactly implement g_x=(1-u)g_C+u g_A without constructing a
    # free per-pixel capacity table.
    lower = (1.0 - u) * lower_choquet + u * lower_additive
    upper = (1.0 - u) * upper_choquet + u * upper_additive
    width = np.clip(upper - lower, 0.0, 1.0)
    midpoint = 0.5 * (lower + upper)
    return midpoint.astype(np.float32), u.astype(np.float32), width.astype(np.float32)


def _score_maps(
    items: list[dict],
    stacks: list[np.ndarray],
    weights: np.ndarray,
    uncertainty_scale: float,
):
    incumbent, candidate, uncertainty, interval_width = [], [], [], []
    for item, stack in zip(items, stacks):
        base_context = distorted_choquet(stack, weights, GAMMA)
        midpoint, u, width = _candidate_context(stack, weights, uncertainty_scale)
        incumbent.append(context_gate(item["scharr"], base_context, STRENGTH, FLOOR))
        # Keep the incumbent context power unchanged and apply ignorance once,
        # outside that power: G(midpoint)*(1-width).  Putting width inside
        # context_gate would silently square the reliability penalty here.
        reliability_gate = (
            float(FLOOR)
            + (1.0 - float(FLOOR))
            * np.power(np.clip(midpoint, 0.0, 1.0), float(STRENGTH))
            * (1.0 - width)
        )
        candidate.append(
            np.asarray(item["scharr"], np.float32)
            * reliability_gate.astype(np.float32)
        )
        uncertainty.append(u)
        interval_width.append(width)
    return incumbent, candidate, uncertainty, interval_width


def _write_official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [
            {
                "name": "interval_capacity_uncertainty",
                "export": {
                    "script": "run_stage14o_interval_capacity_uncertainty.py",
                    "args": [
                        "--export-bsds",
                        "--image-dir", "{image_dir}",
                        "--output-dir", "{output_dir}",
                        "--split", "{split}",
                    ],
                },
            }
        ],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _save_soft_png(score: np.ndarray, path: Path) -> None:
    x = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(x)):
        raise RuntimeError(f"non-finite candidate score for {path.stem}")
    q = np.rint(np.clip(x, 0.0, 1.0) * 255.0).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(q, mode="L").save(path)


def export_bsds(args: argparse.Namespace) -> int:
    image_dir = Path(args.image_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw = resize_items(
        load_uded(ensure_uded(Path(args.uded_root))),
        args.max_side_development,
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
    compact = _ordered_compact(positive)
    training_stacks, weights = _memberships(selection, names, compact)
    uncertainty_scale = _fit_uncertainty_scale(training_stacks)

    image_paths = sorted(image_dir.glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {image_dir}")

    for index, path in enumerate(image_paths, start=1):
        print(
            f"STAGE14O_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {path.stem}",
            flush=True,
        )
        prepared, candidate_names = prepare([{"id": path.stem, "img": imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        stacks, candidate_weights = _memberships(prepared, names, compact)
        _incumbent, candidate, _u, _width = _score_maps(
            prepared,
            stacks,
            candidate_weights,
            uncertainty_scale,
        )
        _save_soft_png(candidate[0], output_dir / f"{path.stem}.png")

    metadata = {
        "method": "interval_capacity_uncertainty",
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "output": "8-bit soft PNG, no per-image normalization",
        "development_source": "UDED selection only",
        "compact_features": list(COMPACT_FEATURES),
        "uncertainty": {
            "definition": "pixelwise std across five compact memberships",
            "training_normalization_quantile": UNCERTAINTY_QUANTILE,
            "training_scale": uncertainty_scale,
            "interval_half_width_factor": INTERVAL_HALF_WIDTH_FACTOR,
        },
        "capacity_field": "convex interpolation of gamma-0.55 and additive capacities",
        "gate": {"strength": STRENGTH, "floor": FLOOR},
        "seed": args.seed,
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
        raise RuntimeError(f"Expected 15 UDED selection images, found {len(selection)}")

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts = defaultdict(list)
    fold_metrics = defaultdict(list)
    thresholds = defaultdict(list)
    fold_rows: list[dict] = []
    image_rows: list[dict] = []
    diagnostic_rows: list[dict] = []
    preview = None

    for split_index, (repeat, fold, tr_idx, va_idx) in enumerate(splits, start=1):
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
        compact = _ordered_compact(positive)
        train_stacks, weights = _memberships(train, names, compact)
        valid_stacks, valid_weights = _memberships(valid, names, compact)
        if not np.allclose(weights, valid_weights):
            raise RuntimeError("compact singleton weights changed between train and validation")
        uncertainty_scale = _fit_uncertainty_scale(train_stacks)
        train_inc, train_cand, train_u, train_w = _score_maps(
            train, train_stacks, weights, uncertainty_scale
        )
        valid_inc, valid_cand, valid_u, valid_w = _score_maps(
            valid, valid_stacks, weights, uncertainty_scale
        )
        diagnostic_rows.append({
            "repeat": repeat + 1,
            "fold": fold + 1,
            "uncertainty_scale_q95": uncertainty_scale,
            "train_mean_uncertainty": float(np.mean([np.mean(x) for x in train_u])),
            "valid_mean_uncertainty": float(np.mean([np.mean(x) for x in valid_u])),
            "train_mean_interval_width": float(np.mean([np.mean(x) for x in train_w])),
            "valid_mean_interval_width": float(np.mean([np.mean(x) for x in valid_w])),
        })
        print(
            f"STAGE14O_SPLIT {split_index:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1} q95={uncertainty_scale:.6f}",
            flush=True,
        )

        variants = {
            "compact_incumbent": (train_inc, valid_inc),
            "interval_capacity_uncertainty": (train_cand, valid_cand),
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
                "uncertainty_scale_q95": uncertainty_scale,
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
                "incumbent": split_predictions["compact_incumbent"][0],
                "candidate": split_predictions["interval_capacity_uncertainty"][0],
                "uncertainty": valid_u[0],
            }

    aggregate = {variant: aggregate_counts(counts[variant]) for variant in VARIANTS}
    incumbent_name, candidate_name = VARIANTS
    f1_delta = float(aggregate[candidate_name]["F1"] - aggregate[incumbent_name]["F1"])
    precision_delta = float(
        aggregate[candidate_name]["precision"] - aggregate[incumbent_name]["precision"]
    )
    fold_delta = np.asarray([
        candidate["F1"] - incumbent["F1"]
        for incumbent, candidate in zip(
            fold_metrics[incumbent_name], fold_metrics[candidate_name]
        )
    ], dtype=float)
    uded_noncollapse = bool(
        f1_delta >= -0.0015
        and precision_delta >= -0.002
        and float(np.mean(fold_delta)) >= -0.0015
        and int(np.sum(fold_delta > 0.0)) >= 6
    )
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
    pd.DataFrame(diagnostic_rows).to_csv(out / "uncertainty_diagnostics.csv", index=False)

    if preview is None:
        raise RuntimeError("No deterministic preview sample was captured")
    preview_path = write_panel_grid(
        out / "best_method_preview.png",
        [[
            preview["item"]["pre_img"],
            preview["item"]["gt"],
            preview["incumbent"],
            preview["candidate"],
            preview["uncertainty"],
            preview["incumbent"],
        ]],
    )
    official_manifest_path = _write_official_manifest(out)

    summary = {
        "stage": "14o-interval-capacity-uncertainty",
        "dataset_role": "UDED selection repeated CV; development",
        "heldout_used": False,
        "external_test_feedback_used": False,
        "n_selection_images": len(selection),
        "repeats": args.repeats,
        "folds": args.folds,
        "n_validation_events": len(splits),
        "mechanism": {
            "uncertainty": "pixelwise membership standard deviation divided by outer-training q95",
            "intervals": "mu_i plus/minus 0.5*u, clipped to [0,1]",
            "capacity_field": "(1-u)*retained distorted capacity + u*additive capacity",
            "reliability": "midpoint^strength multiplied by one minus Choquet-envelope width inside the fixed-floor gate",
            "fixed_gamma": GAMMA,
            "fixed_gate_strength": STRENGTH,
            "fixed_gate_floor": FLOOR,
            "fit_policy": "bank, membership parameters, uncertainty q95, and threshold fit inside every outer training fold",
        },
        "promotion_rule": (
            "Benchmark-aligned promotion requires all UDED non-collapse conditions "
            "(aggregate F1 delta >= -0.0015, precision delta >= -0.002, mean fold "
            "F1 delta >= -0.0015, at least 6/15 fold wins) and completed official "
            "BSDS500-val deltas ODS >= +0.002, OIS >= 0, AP >= 0."
        ),
        "uded_gate": {
            "aggregate_F1_delta": f1_delta,
            "aggregate_precision_delta": precision_delta,
            "mean_fold_F1_delta": float(np.mean(fold_delta)),
            "fold_F1_wins": int(np.sum(fold_delta > 0.0)),
            "noncollapse_met": uded_noncollapse,
        },
        "promotion_pending_official_bsds_val": True,
        "retained_method_pending_official_bsds_val": incumbent_name,
        "metrics": aggregate,
        "visual_preview": {
            "file": preview_path.name,
            "selection": "first validation image of the first deterministic repeated-CV split",
            "rows": ["fixed representative"],
            "columns": [
                "conditioned_input",
                "ground_truth",
                "compact_incumbent",
                "interval_capacity_uncertainty",
                "uncertainty_field",
                "current_retained_incumbent_pending_official_evaluation",
            ],
            "use": "documentary only; not an optimization signal",
        },
        "official_evaluation": {
            "manifest": official_manifest_path.name,
            "split": "BSDS500 validation",
            "protocol": "official MATLAB multi-annotator boundary evaluation",
            "required_before_promotion": True,
        },
        "files": [
            "variant_ranking.csv",
            "fold_results.csv",
            "per_image_metrics.csv",
            "uncertainty_diagnostics.csv",
            "best_method_preview.png",
            "official_eval_manifest.json",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14O_INTERVAL_CAPACITY_UNCERTAINTY_COMPLETE", flush=True)
    print(out / "summary.json", flush=True)
    print(preview_path, flush=True)
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
    parser.add_argument("--seed", type=int, default=20261006)
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
