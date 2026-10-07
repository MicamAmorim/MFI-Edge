from __future__ import annotations

"""Stage 14p: fixed MFI-coupled Ambrosio--Tortorelli phase field.

This runner changes only the localization mechanism.  The retained compact
Choquet context becomes a fixed spatial prior in a classical phase-field
energy; no target-data parameter search is performed.  Bank fitting and
operating-threshold fitting remain inside every UDED outer fold.
"""

from collections import defaultdict
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from PIL import Image
from scipy.ndimage import convolve
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
from src.postprocess import non_maximum_suppression


DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14p_ambrosio_tortorelli"
VARIANTS = ("compact_incumbent", "mfi_coupled_at_phase_field")

# One fixed, dimensionless discretization of the classical AT functional.
# Epsilon is expressed in pixels; all other coefficients act on [0,1] images.
AT_ALPHA = 1.0
AT_BETA = 0.10
AT_EPSILON = 1.5
AT_MFI_ETA = 0.005
AT_ITERATIONS = 16

_NEIGHBOR_KERNEL = np.asarray(
    [[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]],
    dtype=np.float32,
)


def _ordered_compact(bank: list[dict]) -> list[dict]:
    selected = _filter_bank(bank, COMPACT_FEATURES)
    by_feature = {str(row["feature"]): row for row in selected}
    missing = [name for name in COMPACT_FEATURES if name not in by_feature]
    if missing:
        raise RuntimeError(f"compact bank missing features: {missing}")
    return [by_feature[name] for name in COMPACT_FEATURES]


def _contexts(items: list[dict], names: list[str], compact: list[dict]):
    contexts = []
    weights = None
    for item in items:
        stack, weights = membership_stack(item, names, compact, "edge")
        contexts.append(distorted_choquet(stack, weights, GAMMA))
    if weights is None:
        raise RuntimeError("no compact memberships were constructed")
    return contexts


def _at_phase_field(image: np.ndarray, context: np.ndarray):
    """Alternating Jacobi minimization of a discrete MFI-coupled AT energy.

    ``v`` is one in smooth regions and approaches zero at the diffuse
    discontinuity set.  The nonnegative MFI term eta*context*v^2 encourages
    discontinuities only where the already-retained context supports them.
    """
    f = np.asarray(image, dtype=np.float32)
    if f.ndim == 3:
        f = np.mean(f[..., :3], axis=-1, dtype=np.float32)
    f = np.clip(f, 0.0, 1.0)
    c = np.clip(np.asarray(context, dtype=np.float32), 0.0, 1.0)
    u = f.copy()
    v = np.ones_like(f, dtype=np.float32)

    for _ in range(AT_ITERATIONS):
        v2 = np.square(v)
        weighted_neighbors = np.zeros_like(u)
        weight_sum = np.zeros_like(u)
        padded_u = np.pad(u, 1, mode="reflect")
        padded_v2 = np.pad(v2, 1, mode="reflect")
        neighbor_slices = (
            (slice(0, -2), slice(1, -1)),
            (slice(2, None), slice(1, -1)),
            (slice(1, -1), slice(0, -2)),
            (slice(1, -1), slice(2, None)),
        )
        for ys, xs in neighbor_slices:
            shifted_u = padded_u[ys, xs]
            shifted_v2 = padded_v2[ys, xs]
            edge_weight = 0.5 * (v2 + shifted_v2)
            weighted_neighbors += edge_weight * shifted_u
            weight_sum += edge_weight
        u = (f + 2.0 * AT_ALPHA * weighted_neighbors) / (
            1.0 + 2.0 * AT_ALPHA * weight_sum
        )

        gy, gx = np.gradient(u)
        grad_sq = np.square(gx) + np.square(gy)
        neighbor_v = convolve(v, _NEIGHBOR_KERNEL, mode="reflect")
        well = AT_BETA / (2.0 * AT_EPSILON)
        diffusion = 2.0 * AT_BETA * AT_EPSILON
        denominator = (
            well
            + 4.0 * diffusion
            + 2.0 * AT_ALPHA * grad_sq
            + 2.0 * AT_MFI_ETA * c
        )
        v = (well + diffusion * neighbor_v) / np.maximum(denominator, 1e-8)
        v = np.clip(v, 0.0, 1.0).astype(np.float32)

    phase = np.clip(1.0 - v, 0.0, 1.0).astype(np.float32)
    return u.astype(np.float32), phase


def _score_maps(items: list[dict], contexts: list[np.ndarray]):
    incumbent, candidate, reconstructions, phases = [], [], [], []
    for item, context in zip(items, contexts):
        incumbent.append(context_gate(item["scharr"], context, STRENGTH, FLOOR))
        reconstruction, phase = _at_phase_field(item["pre_img"], context)
        localized = non_maximum_suppression(phase, item["orientation"])
        candidate.append(np.clip(localized, 0.0, 1.0).astype(np.float32))
        reconstructions.append(reconstruction)
        phases.append(phase)
    return incumbent, candidate, reconstructions, phases


def _write_official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": "mfi_coupled_at_phase_field",
            "export": {
                "script": "run_stage14p_ambrosio_tortorelli.py",
                "args": [
                    "--export-bsds", "--image-dir", "{image_dir}",
                    "--output-dir", "{output_dir}", "--split", "{split}",
                ],
            },
        }],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _save_soft_png(score: np.ndarray, path: Path) -> None:
    x = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(x)):
        raise RuntimeError(f"non-finite candidate score for {path.stem}")
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.rint(np.clip(x, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L").save(path)


def _fit_full_context(args: argparse.Namespace):
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side_development)
    selection, names = prepare(raw[0::2])
    positive, _negative = learn_banks(
        selection, names, args.seed, args.max_positive, args.max_negative, args.max_abs_corr
    )
    compact = _ordered_compact(positive)
    return selection, names, compact


def export_bsds(args: argparse.Namespace) -> int:
    _selection, names, compact = _fit_full_context(args)
    image_paths = sorted(Path(args.image_dir).glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {args.image_dir}")
    output_dir = Path(args.output_dir)
    for index, path in enumerate(image_paths, start=1):
        print(f"STAGE14P_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {path.stem}", flush=True)
        prepared, candidate_names = prepare([{"id": path.stem, "img": imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        contexts = _contexts(prepared, names, compact)
        _inc, candidate, _recon, _phase = _score_maps(prepared, contexts)
        _save_soft_png(candidate[0], output_dir / f"{path.stem}.png")
    metadata = {
        "method": VARIANTS[1], "dataset": "BSDS500", "split": args.split,
        "bsds_ground_truth_read": False, "native_resolution": True,
        "output": "8-bit soft PNG, no per-image normalization",
        "development_source": "UDED selection only",
        "parameters": {
            "alpha": AT_ALPHA, "beta": AT_BETA, "epsilon_pixels": AT_EPSILON,
            "mfi_eta": AT_MFI_ETA, "iterations": AT_ITERATIONS,
        },
        "n_maps": len(image_paths),
    }
    (output_dir / "export_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
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
    fold_rows, image_rows, diagnostic_rows = [], [], []
    preview = None

    for split_index, (repeat, fold, tr_idx, va_idx) in enumerate(splits, start=1):
        train = [selection[i] for i in tr_idx]
        valid = [selection[i] for i in va_idx]
        positive, _negative = learn_banks(
            train, names, args.seed + 10000 * repeat + fold,
            args.max_positive, args.max_negative, args.max_abs_corr,
        )
        compact = _ordered_compact(positive)
        train_context = _contexts(train, names, compact)
        valid_context = _contexts(valid, names, compact)
        train_inc, train_cand, _train_u, train_phase = _score_maps(train, train_context)
        valid_inc, valid_cand, valid_u, valid_phase = _score_maps(valid, valid_context)
        print(
            f"STAGE14P_SPLIT {split_index:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1}", flush=True,
        )

        variants = {
            VARIANTS[0]: (train_inc, valid_inc),
            VARIANTS[1]: (train_cand, valid_cand),
        }
        split_predictions = {}
        for variant in VARIANTS:
            train_scores, valid_scores = variants[variant]
            fit = selection_metric(train_scores, train, args.thresholds)
            threshold = float(fit["threshold"])
            metric, event_counts, per_image = fixed_eval(valid_scores, valid, threshold)
            split_predictions[variant] = [np.asarray(x) >= threshold for x in valid_scores]
            counts[variant].extend(event_counts)
            fold_metrics[variant].append(metric)
            thresholds[variant].append(threshold)
            fold_rows.append({
                "repeat": repeat + 1, "fold": fold + 1, "variant": variant,
                "train_threshold": threshold, **metric,
            })
            image_rows.extend({
                "repeat": repeat + 1, "fold": fold + 1, "variant": variant, **row,
            } for row in per_image)

        diagnostic_rows.append({
            "repeat": repeat + 1, "fold": fold + 1,
            "train_mean_phase": float(np.mean([np.mean(x) for x in train_phase])),
            "valid_mean_phase": float(np.mean([np.mean(x) for x in valid_phase])),
            "valid_mean_reconstruction_abs_change": float(np.mean([
                np.mean(np.abs(u - np.asarray(item["pre_img"], dtype=np.float32)))
                for u, item in zip(valid_u, valid)
            ])),
        })
        if preview is None:
            preview = {
                "item": valid[0], "incumbent": split_predictions[VARIANTS[0]][0],
                "candidate": split_predictions[VARIANTS[1]][0],
                "reconstruction": valid_u[0], "phase": valid_phase[0],
            }

    aggregate = {name: aggregate_counts(counts[name]) for name in VARIANTS}
    inc_name, cand_name = VARIANTS
    fold_delta = np.asarray([
        cand["F1"] - inc["F1"]
        for inc, cand in zip(fold_metrics[inc_name], fold_metrics[cand_name])
    ], dtype=float)
    f1_delta = float(aggregate[cand_name]["F1"] - aggregate[inc_name]["F1"])
    precision_delta = float(aggregate[cand_name]["precision"] - aggregate[inc_name]["precision"])
    uded_gate = bool(
        f1_delta >= 0.0 and precision_delta >= 0.0
        and float(np.mean(fold_delta)) >= 0.0 and int(np.sum(fold_delta > 0.0)) >= 9
    )
    ranking = []
    for name in VARIANTS:
        values = np.asarray([row["F1"] for row in fold_metrics[name]], dtype=float)
        ranking.append({
            "variant": name, "cv_precision": float(aggregate[name]["precision"]),
            "cv_recall": float(aggregate[name]["recall"]), "cv_F1": float(aggregate[name]["F1"]),
            "mean_fold_F1": float(np.mean(values)), "std_fold_F1": float(np.std(values)),
            "threshold_mean": float(np.mean(thresholds[name])),
            "threshold_std": float(np.std(thresholds[name])),
        })
    pd.DataFrame(ranking).sort_values("cv_F1", ascending=False).to_csv(out / "variant_ranking.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)
    pd.DataFrame(diagnostic_rows).to_csv(out / "phase_field_diagnostics.csv", index=False)

    if preview is None:
        raise RuntimeError("No deterministic preview sample was captured")
    preview_path = write_panel_grid(out / "best_method_preview.png", [[
        preview["item"]["pre_img"], preview["item"]["gt"], preview["incumbent"],
        preview["candidate"], preview["phase"], preview["incumbent"],
    ]])
    manifest_path = _write_official_manifest(out)
    summary = {
        "stage": "14p-mfi-coupled-ambrosio-tortorelli",
        "dataset_role": "UDED selection repeated CV plus BSDS500 validation; development",
        "heldout_used": False, "external_test_feedback_used": False,
        "n_selection_images": len(selection), "repeats": args.repeats,
        "folds": args.folds, "n_validation_events": len(splits),
        "mechanism": {
            "energy": "discrete Ambrosio-Tortorelli with fixed nonnegative MFI context prior eta*context*v^2",
            "localization": "NMS of the diffuse discontinuity field 1-v using unchanged image-gradient orientation",
            "parameters": {
                "alpha": AT_ALPHA, "beta": AT_BETA, "epsilon_pixels": AT_EPSILON,
                "mfi_eta": AT_MFI_ETA, "alternating_iterations": AT_ITERATIONS,
            },
            "fit_policy": "compact memberships and thresholds fit inside each outer fold; phase-field parameters fixed globally",
        },
        "promotion_rule": (
            "All criteria are conjunctive: UDED aggregate F1 and precision deltas >= 0, "
            "mean fold-F1 delta >= 0, at least 9/15 fold wins, completed official BSDS500-val "
            "evaluation, ODS delta >= +0.002, and nonnegative OIS and AP deltas."
        ),
        "uded_gate": {
            "aggregate_F1_delta": f1_delta, "aggregate_precision_delta": precision_delta,
            "mean_fold_F1_delta": float(np.mean(fold_delta)),
            "fold_F1_wins": int(np.sum(fold_delta > 0.0)), "met": uded_gate,
        },
        "promotion_pending_official_bsds_val": True,
        "metrics": aggregate,
        "visual_preview": {
            "file": preview_path.name,
            "selection": "first validation image of the first deterministic repeated-CV split",
            "rows": ["fixed representative"],
            "columns": [
                "conditioned_input", "ground_truth", "compact_incumbent",
                "mfi_coupled_at_phase_field", "soft_phase_field", "current_retained_incumbent",
            ],
            "use": "documentary only; not an optimization signal",
        },
        "official_evaluation": {
            "manifest": manifest_path.name, "split": "BSDS500 validation",
            "protocol": "official MATLAB multi-annotator boundary evaluation",
            "required_before_promotion": True,
        },
        "files": [
            "variant_ranking.csv", "fold_results.csv", "per_image_metrics.csv",
            "phase_field_diagnostics.csv", "best_method_preview.png", "official_eval_manifest.json",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14P_AMBROSIO_TORTORELLI_COMPLETE", flush=True)
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
    parser.add_argument("--seed", type=int, default=20261007)
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
