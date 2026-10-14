from __future__ import annotations

"""Stage 16r: fixed Sugeno aggregation of the compact positive context."""

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
from skimage.io import imread

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12b_fuzzy_signature import membership_stack, prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage14c_positive_bank_pruning import FLOOR, GAMMA, STRENGTH
from run_stage16f_rolling_guidance_localizer import _ordered_compact
from src.bipolar_fuzzy import context_gate, distorted_choquet
from src.sugeno_context import distorted_capacity_sugeno


EXPERIMENT_ID = "stage16r_sugeno_context"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
VARIANTS = ("compact_mfi", "sugeno_compact_mfi")
PREVIEW_POSITIONS = (0, 7, 14)


def _raw_compact(bank: list[dict]) -> list[dict]:
    rows = []
    for row in bank:
        copied = dict(row)
        copied["weight"] = max(float(row["texture_auc"]) - 0.5, 0.0) * (
            1.0 + float(row["mutual_information"])
        )
        rows.append(copied)
    return rows


def _context_pairs(items: list[dict], names: list[str], compact: list[dict]):
    controls, candidates = [], []
    spec = _raw_compact(compact)
    for item in items:
        memberships, weights = membership_stack(item, names, spec, "edge")
        controls.append(distorted_choquet(memberships, weights, GAMMA))
        candidates.append(distorted_capacity_sugeno(memberships, weights, GAMMA))
    return controls, candidates


def _score_pairs(items: list[dict], names: list[str], compact: list[dict]):
    control_contexts, candidate_contexts = _context_pairs(items, names, compact)
    controls = [
        context_gate(item["scharr"], context, STRENGTH, FLOOR).astype(np.float32)
        for item, context in zip(items, control_contexts)
    ]
    candidates = [
        context_gate(item["scharr"], context, STRENGTH, FLOOR).astype(np.float32)
        for item, context in zip(items, candidate_contexts)
    ]
    return controls, candidates, control_contexts, candidate_contexts


def _aggregation_contract_checks() -> dict:
    weights = np.asarray([0.10, 0.15, 0.20, 0.25, 0.30], dtype=np.float64)
    probe = np.asarray(
        [[0.05, 0.25, 0.40, 0.70, 0.95], [0.80, 0.10, 0.55, 0.35, 0.65]],
        dtype=np.float64,
    )
    raised = np.clip(probe + 0.03, 0.0, 1.0)
    first = distorted_capacity_sugeno(probe, weights, GAMMA)
    second = distorted_capacity_sugeno(probe, weights, GAMMA)
    raised_out = distorted_capacity_sugeno(raised, weights, GAMMA)
    constants = np.asarray([0.0, 0.2, 0.5, 0.8, 1.0], dtype=np.float64)
    idempotent = [
        float(distorted_capacity_sugeno(np.full((1, 5), value), weights, GAMMA)[0])
        for value in constants
    ]
    perm = np.asarray([3, 0, 4, 1, 2])
    permuted = distorted_capacity_sugeno(probe[:, perm], weights[perm], GAMMA)
    checks = {
        "finite_and_bounded": bool(np.all(np.isfinite(first)) and np.all((first >= 0.0) & (first <= 1.0))),
        "repeat_bitwise_equal": bool(np.array_equal(first, second)),
        "componentwise_monotone": bool(np.all(raised_out + 1.0e-7 >= first)),
        "idempotent": bool(np.allclose(idempotent, constants, atol=1.0e-7, rtol=0.0)),
        "joint_permutation_invariant": bool(np.allclose(first, permuted, atol=1.0e-7, rtol=0.0)),
        "capacity_normalized": bool(np.isclose(np.power(weights.sum(), GAMMA), 1.0)),
    }
    if not all(checks.values()):
        raise RuntimeError(f"Sugeno aggregation contract failure: {checks}")
    return checks


def _fit_full_candidate(args: argparse.Namespace):
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side_development)
    selection, names = prepare(raw[0::2])
    positive, _negative = learn_banks(
        selection, names, args.seed, args.max_positive, args.max_negative, args.max_abs_corr
    )
    return names, _ordered_compact(positive)


def _save_soft_png(score: np.ndarray, path: Path) -> None:
    x = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(x)):
        raise RuntimeError(f"non-finite candidate score for {path.stem}")
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.rint(np.clip(x, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L").save(path)


def _write_official_manifest(out: Path, seed: int) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": VARIANTS[1],
            "export": {
                "script": "run_stage16r_sugeno_context.py",
                "args": [
                    "--export-bsds", "--image-dir", "{image_dir}",
                    "--output-dir", "{output_dir}", "--split", "{split}",
                    "--seed", str(seed),
                ],
                "timeout_minutes": 240,
            },
        }],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def export_bsds(args: argparse.Namespace) -> int:
    checks = _aggregation_contract_checks()
    names, compact = _fit_full_candidate(args)
    image_paths = sorted(Path(args.image_dir).glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {args.image_dir}")
    output_dir = Path(args.output_dir)
    diagnostics = []
    for index, path in enumerate(image_paths, start=1):
        print(f"STAGE16R_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {path.stem}", flush=True)
        prepared, candidate_names = prepare([{"id": path.stem, "img": imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        incumbent, candidate, control_context, candidate_context = _score_pairs(prepared, names, compact)
        _save_soft_png(candidate[0], output_dir / f"{path.stem}.png")
        diagnostics.append({
            "image_id": path.stem,
            "mean_choquet_context": float(np.mean(control_context[0])),
            "mean_sugeno_context": float(np.mean(candidate_context[0])),
            "mean_abs_context_delta": float(np.mean(np.abs(candidate_context[0] - control_context[0]))),
            "mean_abs_score_delta": float(np.mean(np.abs(candidate[0] - incumbent[0]))),
        })
    pd.DataFrame(diagnostics).to_csv(output_dir / "sugeno_diagnostics.csv", index=False)
    metadata = {
        "method": VARIANTS[1],
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "development_source": "UDED selection only",
        "output": "direct 8-bit soft PNG without per-image output normalization",
        "sugeno_contract": {
            "formula": "max_i min(x_(i), (sum_{j in suffix_i} w_j)^0.55)",
            "capacity": "same normalized distorted-probability capacity as incumbent",
            "checks": checks,
            "localizer": "unchanged median-conditioned grayscale Scharr+NMS",
        },
        "n_maps": len(image_paths),
    }
    (output_dir / "export_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return 0


def run_experiment(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    contract_checks = _aggregation_contract_checks()
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    selection, names = prepare(raw[0::2])
    if len(selection) != 15:
        raise RuntimeError(f"expected 15 UDED selection images, found {len(selection)}")

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts: dict[str, list] = defaultdict(list)
    fold_f1: dict[str, list[float]] = defaultdict(list)
    thresholds: dict[str, list[float]] = defaultdict(list)
    fold_rows, image_rows, diagnostic_rows = [], [], []
    first_repeat_predictions: dict[str, dict[int, np.ndarray]] = {name: {} for name in VARIANTS}
    first_repeat_contexts: dict[int, np.ndarray] = {}

    for split_no, (repeat, fold, tr_idx, va_idx) in enumerate(splits, start=1):
        train = [selection[index] for index in tr_idx]
        valid = [selection[index] for index in va_idx]
        positive, _negative = learn_banks(
            train, names, args.seed + 10000 * repeat + fold,
            args.max_positive, args.max_negative, args.max_abs_corr,
        )
        compact = _ordered_compact(positive)
        train_control, train_candidate, train_choquet, train_sugeno = _score_pairs(train, names, compact)
        valid_control, valid_candidate, valid_choquet, valid_sugeno = _score_pairs(valid, names, compact)
        train_maps = (train_control, train_candidate)
        valid_maps = (valid_control, valid_candidate)
        print(f"STAGE16R_SPLIT {split_no:02d}/{len(splits)} repeat={repeat + 1} fold={fold + 1}", flush=True)
        for local_index, global_index in enumerate(va_idx):
            diagnostic_rows.append({
                "repeat": repeat + 1,
                "fold": fold + 1,
                "image_id": valid[local_index]["id"],
                "mean_choquet_context": float(np.mean(valid_choquet[local_index])),
                "mean_sugeno_context": float(np.mean(valid_sugeno[local_index])),
                "mean_abs_context_delta": float(np.mean(np.abs(valid_sugeno[local_index] - valid_choquet[local_index]))),
                "mean_abs_score_delta": float(np.mean(np.abs(valid_candidate[local_index] - valid_control[local_index]))),
            })
            if repeat == 0:
                first_repeat_contexts[int(global_index)] = valid_sugeno[local_index]
        for variant_index, variant in enumerate(VARIANTS):
            threshold = float(selection_metric(train_maps[variant_index], train, args.thresholds)["threshold"])
            metric, event_counts, per_image = fixed_eval(valid_maps[variant_index], valid, threshold)
            counts[variant].extend(event_counts)
            fold_f1[variant].append(float(metric["F1"]))
            thresholds[variant].append(threshold)
            fold_rows.append({"repeat": repeat + 1, "fold": fold + 1, "variant": variant, "train_threshold": threshold, **metric})
            image_rows.extend({"repeat": repeat + 1, "fold": fold + 1, "variant": variant, **row} for row in per_image)
            if repeat == 0:
                for global_index, score in zip(va_idx, valid_maps[variant_index]):
                    first_repeat_predictions[variant][int(global_index)] = score >= threshold

    aggregate = {name: aggregate_counts(counts[name]) for name in VARIANTS}
    incumbent_folds = np.asarray(fold_f1[VARIANTS[0]], dtype=np.float64)
    candidate_folds = np.asarray(fold_f1[VARIANTS[1]], dtype=np.float64)
    deltas = {
        "aggregate_F1": float(aggregate[VARIANTS[1]]["F1"] - aggregate[VARIANTS[0]]["F1"]),
        "aggregate_precision": float(aggregate[VARIANTS[1]]["precision"] - aggregate[VARIANTS[0]]["precision"]),
        "aggregate_recall": float(aggregate[VARIANTS[1]]["recall"] - aggregate[VARIANTS[0]]["recall"]),
        "mean_fold_F1": float(np.mean(candidate_folds - incumbent_folds)),
        "fold_wins": int(np.sum(candidate_folds > incumbent_folds)),
    }
    uded_gate = bool(
        deltas["aggregate_F1"] >= 0.002
        and deltas["aggregate_precision"] >= -0.002
        and deltas["aggregate_recall"] >= -0.003
        and deltas["mean_fold_F1"] >= 0.0
        and deltas["fold_wins"] >= 9
    )

    ranking = []
    for variant in VARIANTS:
        values = np.asarray(fold_f1[variant], dtype=np.float64)
        ranking.append({
            "variant": variant,
            "cv_precision": aggregate[variant]["precision"],
            "cv_recall": aggregate[variant]["recall"],
            "cv_F1": aggregate[variant]["F1"],
            "mean_fold_F1": float(np.mean(values)),
            "std_fold_F1": float(np.std(values)),
            "threshold_mean": float(np.mean(thresholds[variant])),
            "threshold_std": float(np.std(thresholds[variant])),
        })
    pd.DataFrame(ranking).sort_values("cv_F1", ascending=False).to_csv(out / "variant_ranking.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)
    pd.DataFrame(diagnostic_rows).to_csv(out / "sugeno_diagnostics.csv", index=False)

    if any(len(first_repeat_predictions[name]) != len(selection) for name in VARIANTS):
        raise RuntimeError("first-repeat out-of-fold preview predictions are incomplete")
    if len(first_repeat_contexts) != len(selection):
        raise RuntimeError("first-repeat Sugeno context maps are incomplete")
    rows = [[
        selection[position]["img"], selection[position]["gt"],
        first_repeat_predictions[VARIANTS[0]][position],
        first_repeat_predictions[VARIANTS[1]][position],
        first_repeat_contexts[position],
    ] for position in PREVIEW_POSITIONS]
    preview_path = write_panel_grid(out / "best_method_preview.png", rows)
    manifest_path = _write_official_manifest(out, args.seed)
    summary = {
        "stage": "16r-sugeno-context",
        "role": "generation_2_qualitative_aggregation_falsification",
        "architecture_changed": False,
        "protected_split_used": False,
        "datasets": {
            "UDED_selection": {"n_images": len(selection), "role": "development repeated leakage-free CV", "repeats": args.repeats, "folds": args.folds, "seed": args.seed},
            "BSDS500_validation": {"role": "development official attachment", "status": "pending controller attachment"},
        },
        "mechanism": {
            "description": "replace only the incumbent Choquet arithmetic accumulation by the discrete Sugeno max-min integral over the same five memberships and same distorted-probability capacity",
            "implementation_fidelity": "equation-level discrete Sugeno integral; repository application to retained MFI memberships, not a reproduction of a published complete detector",
            "parameters": {"formula": "max_i min(x_(i), (suffix_weight_i)^gamma)", "gamma": GAMMA, "capacity_weights": "unchanged outer-fold compact singleton weights"},
            "contract_checks": contract_checks,
            "unchanged": ["five retained features, memberships, and fold-fitted singleton weights", "distorted-probability capacity gamma 0.55", "gate strength 2.0 and floor 0.10", "median-conditioned grayscale Scharr+NMS localizer"],
        },
        "promotion_rule": (
            "Conjunctive: UDED aggregate F1 delta at least +0.002, precision delta at least -0.002, "
            "recall delta at least -0.003, mean paired fold-F1 nonnegative, and at least 9/15 fold wins. "
            "The official attachment must complete; BSDS500-validation ODS delta must be at least +0.002 "
            "and OIS/AP deltas must both be nonnegative. Aggregation-contract checks and preview are required."
        ),
        "uded_gate": {"met": uded_gate, "deltas": deltas},
        "metrics": aggregate,
        "promotion_pending_official_bsds_val": True,
        "official_evaluation": {
            "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
            "required_before_promotion": True,
            "stage15a_caveat": "the unmodified Windows matcher remains stochastic and reference-uncertified; the fixed-seed diagnostic matcher is forbidden",
        },
        "visual_preview": {
            "file": preview_path.name,
            "selection": "fixed UDED-selection positions 1, 8, and 15",
            "columns": ["input", "ground_truth", "compact_MFI_out_of_fold_prediction", "Sugeno_candidate_out_of_fold_prediction", "Sugeno_context"],
            "use": "documentary only; not an optimization signal",
        },
        "files": ["summary.json", "variant_ranking.csv", "fold_results.csv", "per_image_metrics.csv", "sugeno_diagnostics.csv", "best_method_preview.png", "official_eval_manifest.json"],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE16R_SUGENO_CONTEXT_COMPLETE", flush=True)
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
