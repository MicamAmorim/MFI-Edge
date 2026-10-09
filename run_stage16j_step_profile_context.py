from __future__ import annotations

"""Stage 16j: fixed step-profile model evidence in the compact MFI context.

The candidate adds one positive context membership measuring whether the
intensity profile along the incumbent Scharr normal is better explained by a
centered blurred step than by smooth linear shading.  Localization, compact
memberships, Choquet gamma, context gate, and threshold fitting are unchanged.
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
)
from run_stage16f_rolling_guidance_localizer import _ordered_compact
from src.bipolar_fuzzy import context_gate, distorted_choquet
from src.edge_signature import binary_auc, mutual_information_binary, population_masks
from src.features import gray_float


EXPERIMENT_ID = "stage16j_step_profile_context"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
VARIANTS = ("compact_mfi", "compact_plus_step_profile")
PREVIEW_POSITIONS = (0, 7, 14)
PROFILE_OFFSETS = np.arange(-3.0, 4.0, 1.0, dtype=np.float64)
STEP_WIDTHS = (0.75, 1.5, 3.0)
PROFILE_ORDER = 1
PROFILE_BOUNDARY_MODE = "reflect"
ELIGIBILITY_AUC = 0.56


def step_profile_preference(item: dict) -> np.ndarray:
    """Return fixed step-vs-linear least-squares preference in [0, 1]."""
    image = np.asarray(gray_float(item["pre_img"]), dtype=np.float64)
    theta = np.asarray(item["orientation"], dtype=np.float64)
    yy, xx = np.mgrid[: image.shape[0], : image.shape[1]]
    nx, ny = np.cos(theta), np.sin(theta)
    samples = np.stack([
        ndi.map_coordinates(
            image,
            [yy + offset * ny, xx + offset * nx],
            order=PROFILE_ORDER,
            mode=PROFILE_BOUNDARY_MODE,
        )
        for offset in PROFILE_OFFSETS
    ], axis=-1)
    centered = samples - np.mean(samples, axis=-1, keepdims=True)
    total = np.sum(np.square(centered), axis=-1)

    linear = PROFILE_OFFSETS / np.sqrt(np.sum(np.square(PROFILE_OFFSETS)))
    linear_amplitude = np.sum(centered * linear, axis=-1, keepdims=True)
    linear_sse = np.sum(
        np.square(centered - linear_amplitude * linear), axis=-1
    )

    step_sse = []
    for width in STEP_WIDTHS:
        template = np.tanh(PROFILE_OFFSETS / float(width))
        template -= np.mean(template)
        template /= np.sqrt(np.sum(np.square(template)))
        amplitude = np.sum(centered * template, axis=-1, keepdims=True)
        step_sse.append(np.sum(np.square(centered - amplitude * template), axis=-1))
    best_step_sse = np.min(np.stack(step_sse, axis=-1), axis=-1)
    preference = np.maximum(linear_sse - best_step_sse, 0.0) / np.maximum(
        total, np.finfo(np.float64).eps
    )
    return np.clip(preference, 0.0, 1.0).astype(np.float32)


def _attach_profile_maps(items: list[dict], prefix: str = "STAGE16J_PROFILE") -> None:
    for index, item in enumerate(items, start=1):
        print(f"{prefix} {index:03d}/{len(items):03d} {item['id']}", flush=True)
        profile = step_profile_preference(item)
        if not np.all(np.isfinite(profile)) or np.min(profile) < 0.0 or np.max(profile) > 1.0:
            raise RuntimeError(f"invalid step-profile cue for {item['id']}")
        item["step_profile_preference"] = profile


def _fit_profile_spec(items: list[dict], seed: int, max_samples: int = 2500) -> dict:
    values, targets = [], []
    for item_no, item in enumerate(items):
        masks = population_masks(item)
        flat = np.asarray(item["step_profile_preference"], dtype=np.float64).ravel()
        for group_no, (group, target) in enumerate((("edge", True), ("texture", False))):
            ids = np.flatnonzero(np.asarray(masks[group], dtype=bool).ravel())
            if ids.size > int(max_samples):
                rng = np.random.default_rng(int(seed) + 1009 * item_no + 97 * group_no)
                ids = rng.choice(ids, size=int(max_samples), replace=False)
            if ids.size:
                values.append(flat[ids])
                targets.append(np.full(ids.size, target, dtype=bool))
    if not values:
        raise RuntimeError("no step-profile calibration samples were extracted")
    score = np.concatenate(values)
    target = np.concatenate(targets)
    auc = float(binary_auc(score, target))
    information = float(mutual_information_binary(score, target))
    edge_values, texture_values = score[target], score[~target]
    q25, q75 = np.quantile(score, [0.25, 0.75])
    raw_weight = max(auc - 0.5, 0.0) * (1.0 + information)
    eligible = bool(auc >= ELIGIBILITY_AUC and raw_weight > 0.0)
    return {
        "feature": "step_profile_preference",
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


def _raw_compact(bank: list[dict]) -> list[dict]:
    rows = []
    for row in bank:
        copied = dict(row)
        copied["weight"] = max(float(row["texture_auc"]) - 0.5, 0.0) * (
            1.0 + float(row["mutual_information"])
        )
        rows.append(copied)
    return rows


def _profile_membership(item: dict, spec: dict) -> np.ndarray:
    value = np.asarray(item["step_profile_preference"], dtype=np.float64)
    z = (value - float(spec["midpoint"])) / max(float(spec["scale"]), 1.0e-9)
    return (1.0 / (1.0 + np.exp(-np.clip(z, -20.0, 20.0)))).astype(np.float32)


def _context_pairs(items: list[dict], names: list[str], compact: list[dict], spec: dict):
    controls, candidates = [], []
    raw_compact = _raw_compact(compact)
    compact_weights = np.asarray([row["weight"] for row in raw_compact], dtype=np.float64)
    for item in items:
        memberships, weights = membership_stack(item, names, raw_compact, "edge")
        control = distorted_choquet(memberships, weights, GAMMA)
        controls.append(control)
        if not spec["eligible"]:
            candidates.append(control.copy())
            continue
        candidate_memberships = np.concatenate(
            [memberships, _profile_membership(item, spec)[..., None]], axis=-1
        )
        candidate_weights = np.concatenate(
            [compact_weights, np.asarray([spec["raw_weight"]], dtype=np.float64)]
        )
        candidate_weights /= max(float(candidate_weights.sum()), 1.0e-9)
        candidates.append(distorted_choquet(candidate_memberships, candidate_weights, GAMMA))
    return controls, candidates


def _score_pairs(items: list[dict], names: list[str], compact: list[dict], spec: dict):
    control_contexts, candidate_contexts = _context_pairs(items, names, compact, spec)
    controls = [
        context_gate(item["scharr"], context, STRENGTH, FLOOR).astype(np.float32)
        for item, context in zip(items, control_contexts)
    ]
    candidates = [
        context_gate(item["scharr"], context, STRENGTH, FLOOR).astype(np.float32)
        for item, context in zip(items, candidate_contexts)
    ]
    return controls, candidates


def _fit_full_candidate(args: argparse.Namespace):
    raw = resize_items(
        load_uded(ensure_uded(Path(args.uded_root))), args.max_side_development
    )
    selection, names = prepare(raw[0::2])
    _attach_profile_maps(selection, "STAGE16J_FIT_PROFILE")
    positive, _negative = learn_banks(
        selection, names, args.seed, args.max_positive, args.max_negative, args.max_abs_corr
    )
    compact = _ordered_compact(positive)
    spec = _fit_profile_spec(selection, args.seed)
    return names, compact, spec


def _save_soft_png(score: np.ndarray, path: Path) -> None:
    x = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(x)):
        raise RuntimeError(f"non-finite candidate score for {path.stem}")
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(
        np.rint(np.clip(x, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L"
    ).save(path)


def _write_official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": VARIANTS[1],
            "export": {
                "script": "run_stage16j_step_profile_context.py",
                "args": [
                    "--export-bsds", "--image-dir", "{image_dir}",
                    "--output-dir", "{output_dir}", "--split", "{split}",
                ],
                "timeout_minutes": 240,
            },
        }],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def export_bsds(args: argparse.Namespace) -> int:
    names, compact, spec = _fit_full_candidate(args)
    image_paths = sorted(Path(args.image_dir).glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {args.image_dir}")
    output_dir = Path(args.output_dir)
    diagnostics = []
    for index, path in enumerate(image_paths, start=1):
        print(f"STAGE16J_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {path.stem}", flush=True)
        prepared, candidate_names = prepare([{"id": path.stem, "img": imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        _attach_profile_maps(prepared, "STAGE16J_BSDS_PROFILE")
        incumbent, candidate = [maps[0] for maps in _score_pairs(prepared, names, compact, spec)]
        _save_soft_png(candidate, output_dir / f"{path.stem}.png")
        profile = prepared[0]["step_profile_preference"]
        diagnostics.append({
            "image_id": path.stem,
            "profile_mean": float(np.mean(profile)),
            "profile_q90": float(np.quantile(profile, 0.9)),
            "mean_abs_score_delta": float(np.mean(np.abs(candidate - incumbent))),
        })
    pd.DataFrame(diagnostics).to_csv(output_dir / "step_profile_diagnostics.csv", index=False)
    metadata = {
        "method": VARIANTS[1],
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "development_source": "UDED selection only",
        "output": "direct 8-bit soft PNG without per-image normalization",
        "profile_contract": {
            "offsets": PROFILE_OFFSETS.tolist(),
            "step_widths": list(STEP_WIDTHS),
            "interpolation_order": PROFILE_ORDER,
            "boundary_mode": PROFILE_BOUNDARY_MODE,
            "membership_fit": spec,
            "localizer": "unchanged median-conditioned grayscale Scharr+NMS",
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
        raise RuntimeError(f"expected 15 UDED selection images, found {len(selection)}")
    _attach_profile_maps(selection)

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts: dict[str, list] = defaultdict(list)
    fold_f1: dict[str, list[float]] = defaultdict(list)
    thresholds: dict[str, list[float]] = defaultdict(list)
    fold_rows, image_rows, calibration_rows = [], [], []
    first_repeat_predictions: dict[str, dict[int, np.ndarray]] = {name: {} for name in VARIANTS}

    for split_no, (repeat, fold, tr_idx, va_idx) in enumerate(splits, start=1):
        train = [selection[index] for index in tr_idx]
        valid = [selection[index] for index in va_idx]
        positive, _negative = learn_banks(
            train, names, args.seed + 10000 * repeat + fold,
            args.max_positive, args.max_negative, args.max_abs_corr,
        )
        compact = _ordered_compact(positive)
        spec = _fit_profile_spec(train, args.seed + 20000 * repeat + fold)
        calibration_rows.append({"repeat": repeat + 1, "fold": fold + 1, **spec})
        train_maps = _score_pairs(train, names, compact, spec)
        valid_maps = _score_pairs(valid, names, compact, spec)
        print(
            f"STAGE16J_SPLIT {split_no:02d}/{len(splits)} repeat={repeat + 1} "
            f"fold={fold + 1} profile_auc={spec['texture_auc']:.4f}", flush=True,
        )
        for variant_index, variant in enumerate(VARIANTS):
            threshold = float(selection_metric(train_maps[variant_index], train, args.thresholds)["threshold"])
            metric, event_counts, per_image = fixed_eval(
                valid_maps[variant_index], valid, threshold
            )
            counts[variant].extend(event_counts)
            fold_f1[variant].append(float(metric["F1"]))
            thresholds[variant].append(threshold)
            fold_rows.append({
                "repeat": repeat + 1, "fold": fold + 1, "variant": variant,
                "train_threshold": threshold, "profile_eligible": bool(spec["eligible"]),
                **metric,
            })
            image_rows.extend({
                "repeat": repeat + 1, "fold": fold + 1, "variant": variant, **row,
            } for row in per_image)
            if repeat == 0:
                for global_index, score in zip(va_idx, valid_maps[variant_index]):
                    first_repeat_predictions[variant][int(global_index)] = score >= threshold

    aggregate = {name: aggregate_counts(counts[name]) for name in VARIANTS}
    incumbent_folds = np.asarray(fold_f1[VARIANTS[0]], dtype=np.float64)
    candidate_folds = np.asarray(fold_f1[VARIANTS[1]], dtype=np.float64)
    eligible_folds = int(sum(bool(row["eligible"]) for row in calibration_rows))
    deltas = {
        "aggregate_F1": float(aggregate[VARIANTS[1]]["F1"] - aggregate[VARIANTS[0]]["F1"]),
        "aggregate_precision": float(aggregate[VARIANTS[1]]["precision"] - aggregate[VARIANTS[0]]["precision"]),
        "aggregate_recall": float(aggregate[VARIANTS[1]]["recall"] - aggregate[VARIANTS[0]]["recall"]),
        "mean_fold_F1": float(np.mean(candidate_folds - incumbent_folds)),
        "fold_wins": int(np.sum(candidate_folds > incumbent_folds)),
        "eligible_folds": eligible_folds,
    }
    uded_gate = bool(
        deltas["aggregate_F1"] >= 0.002
        and deltas["aggregate_precision"] >= -0.002
        and deltas["aggregate_recall"] >= -0.003
        and deltas["mean_fold_F1"] >= 0.0
        and deltas["fold_wins"] >= 9
        and eligible_folds >= 12
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
    pd.DataFrame(calibration_rows).to_csv(out / "step_profile_calibration.csv", index=False)

    if any(len(first_repeat_predictions[name]) != len(selection) for name in VARIANTS):
        raise RuntimeError("first-repeat out-of-fold preview predictions are incomplete")
    rows = [[
        selection[position]["img"],
        selection[position]["gt"],
        first_repeat_predictions[VARIANTS[0]][position],
        first_repeat_predictions[VARIANTS[1]][position],
        selection[position]["step_profile_preference"],
    ] for position in PREVIEW_POSITIONS]
    preview_path = write_panel_grid(out / "best_method_preview.png", rows)
    manifest_path = _write_official_manifest(out)
    summary = {
        "stage": "16j-step-profile-context",
        "role": "generation_2_local_profile_model_falsification",
        "architecture_changed": False,
        "protected_split_used": False,
        "datasets": {
            "UDED_selection": {"n_images": len(selection), "role": "development repeated leakage-free CV", "repeats": args.repeats, "folds": args.folds},
            "BSDS500_validation": {"role": "development official attachment", "status": "pending controller attachment"},
        },
        "mechanism": {
            "description": "one positive context membership measuring fixed blurred-step fit improvement over smooth linear shading along the incumbent edge normal",
            "implementation_fidelity": "repository-specific bounded surrogate of Nalwa-Binford one-dimensional surface model selection",
            "parameters": {"offsets": PROFILE_OFFSETS.tolist(), "step_widths": list(STEP_WIDTHS), "interpolation_order": PROFILE_ORDER, "boundary_mode": PROFILE_BOUNDARY_MODE, "eligibility_auc": ELIGIBILITY_AUC},
            "unchanged": ["five retained memberships", "distorted-Choquet gamma 0.55", "gate strength 2.0 and floor 0.10", "median-conditioned grayscale Scharr+NMS localizer"],
        },
        "promotion_rule": (
            "Conjunctive: UDED aggregate F1 delta at least +0.002, precision delta "
            "at least -0.002, recall delta at least -0.003, mean paired fold-F1 "
            "nonnegative, at least 9/15 fold wins, and profile eligibility in at "
            "least 12/15 folds. The official attachment must complete; BSDS500-"
            "validation ODS delta must be at least +0.002 and OIS/AP deltas must "
            "both be nonnegative. All conditions are required."
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
            "columns": ["input", "ground_truth", "compact_MFI_out_of_fold_prediction", "candidate_out_of_fold_prediction", "step_profile_preference"],
            "use": "documentary only; not an optimization signal",
        },
        "files": ["summary.json", "variant_ranking.csv", "fold_results.csv", "per_image_metrics.csv", "step_profile_calibration.csv", "best_method_preview.png", "official_eval_manifest.json"],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE16J_STEP_PROFILE_CONTEXT_COMPLETE", flush=True)
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
