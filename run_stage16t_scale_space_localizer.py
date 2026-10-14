from __future__ import annotations

"""Stage 16t: fixed gamma-normalized automatic edge-scale localizer."""

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
from src.scale_space_localizer import scale_normalized_edge_localizer


EXPERIMENT_ID = "stage16t_scale_space_localizer"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
VARIANTS = ("compact_mfi", "scale_selected_compact_mfi")
PREVIEW_POSITIONS = (0, 7, 14)
SIGMAS = (1.0, 2.0, 4.0)
GAMMA_EDGE = 0.5


def _scale_contract_checks() -> dict:
    sharp = np.zeros((129, 129), dtype=np.float32)
    sharp[:, 64:] = 1.0
    diffuse = ndi.gaussian_filter(sharp, sigma=3.0, mode="reflect")
    sharp_result = scale_normalized_edge_localizer(
        sharp, sigmas=SIGMAS, gamma_edge=GAMMA_EDGE
    )
    repeat_result = scale_normalized_edge_localizer(
        sharp, sigmas=SIGMAS, gamma_edge=GAMMA_EDGE
    )
    diffuse_result = scale_normalized_edge_localizer(
        diffuse, sigmas=SIGMAS, gamma_edge=GAMMA_EDGE
    )

    def supported_mean_scale(result) -> float:
        support = result.selected_strength > 0.0
        if not np.any(support):
            return float("nan")
        weights = result.selected_strength[support].astype(np.float64)
        return float(
            np.average(result.selected_sigma[support].astype(np.float64), weights=weights)
        )

    sharp_scale = supported_mean_scale(sharp_result)
    diffuse_scale = supported_mean_scale(diffuse_result)
    valid_scales = np.asarray(SIGMAS, dtype=np.float32)
    checks = {
        "finite_and_bounded": bool(
            np.all(np.isfinite(sharp_result.localizer))
            and np.all((sharp_result.localizer >= 0.0) & (sharp_result.localizer <= 1.0))
            and np.all(np.isfinite(diffuse_result.localizer))
            and np.all((diffuse_result.localizer >= 0.0) & (diffuse_result.localizer <= 1.0))
        ),
        "repeat_bitwise_equal": bool(
            np.array_equal(sharp_result.localizer, repeat_result.localizer)
            and np.array_equal(sharp_result.selected_sigma, repeat_result.selected_sigma)
        ),
        "scale_values_from_fixed_bank": bool(
            np.all(np.isin(np.unique(sharp_result.selected_sigma), valid_scales))
            and np.all(np.isin(np.unique(diffuse_result.selected_sigma), valid_scales))
        ),
        "nonempty_spatial_maxima": bool(
            np.any(sharp_result.selected_strength > 0.0)
            and np.any(diffuse_result.selected_strength > 0.0)
        ),
        "diffuse_step_selects_no_finer_mean_scale": bool(diffuse_scale >= sharp_scale),
        "sharp_weighted_mean_sigma": sharp_scale,
        "diffuse_weighted_mean_sigma": diffuse_scale,
    }
    boolean_checks = [value for value in checks.values() if isinstance(value, bool)]
    if not all(boolean_checks):
        raise RuntimeError(f"scale-space localizer contract failure: {checks}")
    return checks


def _add_candidate_localizers(items: list[dict]) -> None:
    for index, item in enumerate(items, start=1):
        print(
            f"STAGE16T_SCALE_SELECTION {index:03d}/{len(items):03d} {item['id']}",
            flush=True,
        )
        result = scale_normalized_edge_localizer(
            item["pre_img"], sigmas=SIGMAS, gamma_edge=GAMMA_EDGE
        )
        support = result.selected_strength > 0.0
        item["scale_selected_scharr"] = result.localizer
        item["selected_sigma"] = result.selected_sigma
        item["scale_diagnostic"] = {
            "candidate_nonzero_fraction": float(np.mean(result.localizer > 0.0)),
            "incumbent_nonzero_fraction": float(np.mean(item["scharr"] > 0.0)),
            "mean_selected_sigma_all_pixels": float(np.mean(result.selected_sigma)),
            "mean_selected_sigma_on_spatial_maxima": (
                float(np.mean(result.selected_sigma[support])) if np.any(support) else float("nan")
            ),
            "sigma1_fraction": float(np.mean(result.selected_sigma == 1.0)),
            "sigma2_fraction": float(np.mean(result.selected_sigma == 2.0)),
            "sigma4_fraction": float(np.mean(result.selected_sigma == 4.0)),
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
            context_gate(
                item["scale_selected_scharr"], context, STRENGTH, FLOOR
            ).astype(np.float32)
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
                    "script": "run_stage16t_scale_space_localizer.py",
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
    checks = _scale_contract_checks()
    names, compact = _fit_full_context(args)
    image_paths = sorted(Path(args.image_dir).glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {args.image_dir}")
    output_dir = Path(args.output_dir)
    diagnostics = []
    for index, path in enumerate(image_paths, start=1):
        print(
            f"STAGE16T_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {path.stem}",
            flush=True,
        )
        with Image.open(path) as image:
            rgb = np.asarray(image.convert("RGB"))
        prepared, candidate_names = prepare([{"id": path.stem, "img": rgb}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        _add_candidate_localizers(prepared)
        candidate = _score_maps(prepared, _contexts(prepared, names, compact))[1][0]
        _save_soft_png(candidate, output_dir / f"{path.stem}.png")
        diagnostics.append({"image_id": path.stem, **prepared[0]["scale_diagnostic"]})
    pd.DataFrame(diagnostics).to_csv(output_dir / "scale_diagnostics.csv", index=False)
    metadata = {
        "method": VARIANTS[1],
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "development_source": "UDED selection only",
        "output": "direct 8-bit soft PNG without export-time per-image normalization",
        "mechanism": {
            "implementation_fidelity": (
                "fixed finite-scale repository surrogate of Lindeberg automatic "
                "edge-scale selection; not full continuous scale-space curve tracing"
            ),
            "variance_levels_t": [1.0, 4.0, 16.0],
            "sigmas": list(SIGMAS),
            "gamma_edge": GAMMA_EDGE,
            "input": "incumbent median-conditioned grayscale",
            "downstream": "unchanged compact Choquet context gate",
            "contract_checks": checks,
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
    contract_checks = _scale_contract_checks()
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
            f"STAGE16T_SPLIT {split_no:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1}",
            flush=True,
        )
        for variant_index, variant in enumerate(VARIANTS):
            threshold = float(
                selection_metric(train_maps[variant_index], train, args.thresholds)[
                    "threshold"
                ]
            )
            metric, event_counts, per_image = fixed_eval(
                valid_maps[variant_index], valid, threshold
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
                {"repeat": repeat + 1, "fold": fold + 1, "variant": variant, **row}
                for row in per_image
            )
            if repeat == 0:
                for global_index, score in zip(va_idx, valid_maps[variant_index]):
                    first_repeat_predictions[variant][int(global_index)] = score >= threshold
        for global_index in va_idx:
            diagnostic_rows.append(
                {
                    "repeat": repeat + 1,
                    "fold": fold + 1,
                    "image_index": int(global_index),
                    "image_id": selection[int(global_index)]["id"],
                    **selection[int(global_index)]["scale_diagnostic"],
                }
            )

    aggregate = {name: aggregate_counts(counts[name]) for name in VARIANTS}
    candidate_folds = np.asarray(fold_f1[VARIANTS[1]], dtype=np.float64)
    incumbent_folds = np.asarray(fold_f1[VARIANTS[0]], dtype=np.float64)
    deltas = {
        "aggregate_F1": float(aggregate[VARIANTS[1]]["F1"] - aggregate[VARIANTS[0]]["F1"]),
        "aggregate_precision": float(
            aggregate[VARIANTS[1]]["precision"] - aggregate[VARIANTS[0]]["precision"]
        ),
        "aggregate_recall": float(
            aggregate[VARIANTS[1]]["recall"] - aggregate[VARIANTS[0]]["recall"]
        ),
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
    pd.DataFrame(diagnostic_rows).to_csv(out / "scale_diagnostics.csv", index=False)

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
                first_repeat_predictions[VARIANTS[1]][position],
                (item["selected_sigma"] - min(SIGMAS)) / (max(SIGMAS) - min(SIGMAS)),
            ]
        )
    preview_path = write_panel_grid(out / "best_method_preview.png", rows)
    manifest_path = _write_official_manifest(out)
    summary = {
        "stage": "16t-scale-space-localizer",
        "role": "generation_2_automatic_scale_selection_falsification",
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
                "gamma-normalized first-order Gaussian gradient scale selection "
                "combined with spatial NMS at the selected scale"
            ),
            "implementation_fidelity": (
                "fixed three-level repository surrogate of Lindeberg automatic "
                "edge-scale selection, not full continuous curve tracing or saliency"
            ),
            "parameters": {
                "variance_levels_t": [1.0, 4.0, 16.0],
                "sigmas": list(SIGMAS),
                "gamma_edge": GAMMA_EDGE,
                "input": "incumbent median-conditioned grayscale",
            },
            "unchanged": (
                "five-member compact Choquet context, gamma 0.55, gate strength 2.0, "
                "floor 0.10, outer-fold fitting, and threshold grid"
            ),
            "contract_checks": contract_checks,
        },
        "promotion_rule": (
            "Conjunctive: UDED aggregate F1 delta at least +0.002, precision delta "
            "at least -0.002, recall delta at least -0.003, nonnegative mean paired "
            "fold-F1 delta, and at least 9/15 fold wins. The official attachment "
            "must complete; BSDS500-validation ODS delta must be at least +0.002 "
            "and OIS/AP deltas must both be nonnegative. Synthetic scale-contract "
            "checks and the deterministic preview must pass."
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
                "candidate_out_of_fold_prediction",
                "selected_sigma_linear_display_1_to_4",
            ],
            "use": "documentary only; not an optimization signal",
        },
        "files": [
            "summary.json",
            "variant_ranking.csv",
            "fold_results.csv",
            "per_image_metrics.csv",
            "scale_diagnostics.csv",
            "best_method_preview.png",
            "official_eval_manifest.json",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE16T_SCALE_SPACE_LOCALIZER_COMPLETE", flush=True)
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
