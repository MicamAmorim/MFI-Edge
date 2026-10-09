from __future__ import annotations

"""Stage 16d: fixed stable-region-boundary context gate.

The incumbent score and all fold fitting remain unchanged.  The sole candidate
change is a fixed component-tree-inspired shape-stability support map applied
through the already retained context-gate exponent and floor.
"""

from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from PIL import Image

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from evaluation.bsds_official.run_official_bsds import (
    DEFAULT_CONFIG,
    _incumbent_predictions,
    _load_json,
)
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
from src.stable_region_boundary import (
    CHAMFER_DISTANCE_MAX,
    FRAGMENT_LENGTH_MIN,
    LEVEL_DELTA,
    QUANTIZATION_LEVELS,
    REGION_AREA_MIN,
    stable_region_boundary_support,
)


EXPERIMENT_ID = "stage16d_stable_region_boundary_gate"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
VARIANTS = ("compact_mfi", "stable_region_boundary_gate")
PREVIEW_POSITIONS = (0, 7, 14)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ordered_compact(bank: list[dict]) -> list[dict]:
    selected = _filter_bank(bank, COMPACT_FEATURES)
    by_feature = {str(row["feature"]): row for row in selected}
    missing = [name for name in COMPACT_FEATURES if name not in by_feature]
    if missing:
        raise RuntimeError(f"compact bank missing features: {missing}")
    return [by_feature[name] for name in COMPACT_FEATURES]


def _incumbent_scores(
    items: list[dict], names: list[str], compact: list[dict]
) -> list[np.ndarray]:
    scores: list[np.ndarray] = []
    for item in items:
        memberships, weights = membership_stack(item, names, compact, "edge")
        context = distorted_choquet(memberships, weights, GAMMA)
        raw = context_gate(item["scharr"], context, STRENGTH, FLOOR)
        scores.append(
            np.rint(np.clip(raw, 0.0, 1.0) * 255.0).astype(np.float32) / 255.0
        )
    return scores


def _candidate_from_incumbent(
    incumbent: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict]:
    support, diagnostic = stable_region_boundary_support(incumbent)
    candidate = context_gate(incumbent, support, STRENGTH, FLOOR)
    metadata = asdict(diagnostic)
    metadata["candidate_to_incumbent_mass_ratio"] = float(
        np.sum(candidate) / max(float(np.sum(incumbent)), np.finfo(float).tiny)
    )
    return candidate.astype(np.float32), support.astype(np.float32), metadata


def _score_maps(items: list[dict], names: list[str], compact: list[dict]):
    incumbents = _incumbent_scores(items, names, compact)
    candidates, supports, diagnostics = [], [], []
    for incumbent in incumbents:
        candidate, support, diagnostic = _candidate_from_incumbent(incumbent)
        candidates.append(candidate)
        supports.append(support)
        diagnostics.append(diagnostic)
    return incumbents, candidates, supports, diagnostics


def _save_soft_png(score: np.ndarray, path: Path) -> None:
    x = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(x)):
        raise RuntimeError(f"non-finite candidate score for {path.stem}")
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(
        np.rint(np.clip(x, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L"
    ).save(path)


def _write_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [
            {
                "name": VARIANTS[1],
                "export": {
                    "script": "run_stage16d_stable_region_boundary_gate.py",
                    "args": [
                        "--export-bsds",
                        "--image-dir", "{image_dir}",
                        "--gt-dir", "{gt_dir}",
                        "--output-dir", "{output_dir}",
                        "--split", "{split}",
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
    image_dir = Path(args.image_dir).resolve()
    gt_dir = Path(args.gt_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg = _load_json(DEFAULT_CONFIG)
    incumbent_dir, incumbent_meta = _incumbent_predictions(
        cfg, image_dir=image_dir, gt_dir=gt_dir, split=args.split
    )
    hashes: dict[str, str] = {}
    diagnostics: list[dict] = []
    image_paths = sorted(image_dir.glob("*.jpg"))
    for index, image_path in enumerate(image_paths, start=1):
        print(
            f"STAGE16D_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {image_path.stem}",
            flush=True,
        )
        incumbent = np.asarray(
            Image.open(incumbent_dir / f"{image_path.stem}.png").convert("L"),
            dtype=np.float32,
        ) / 255.0
        candidate, _support, diagnostic = _candidate_from_incumbent(incumbent)
        output = output_dir / f"{image_path.stem}.png"
        _save_soft_png(candidate, output)
        hashes[image_path.stem] = _sha256(output)
        diagnostics.append({"image_id": image_path.stem, **diagnostic})
    pd.DataFrame(diagnostics).to_csv(output_dir / "stability_diagnostics.csv", index=False)
    metadata = {
        "method": "fixed component-tree-inspired stable-region-boundary gate",
        "implementation_fidelity": (
            "repository-specific surrogate of the published shape-stability mechanism; "
            "not an exact reproduction of unpublished node selection"
        ),
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "incumbent": incumbent_meta,
        "parameters": {
            "quantization_levels": QUANTIZATION_LEVELS,
            "region_connectivity": 4,
            "region_area_min": REGION_AREA_MIN,
            "level_delta": LEVEL_DELTA,
            "chamfer_distance_max": CHAMFER_DISTANCE_MAX,
            "fragment_connectivity": 8,
            "fragment_length_min": FRAGMENT_LENGTH_MIN,
            "gate_strength_inherited": STRENGTH,
            "gate_floor_inherited": FLOOR,
        },
        "n_maps": len(hashes),
        "map_hashes": hashes,
        "output": "8-bit soft PNG without per-image normalization",
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
        raise RuntimeError(f"expected 15 UDED selection images, found {len(selection)}")

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts: dict[str, list] = defaultdict(list)
    fold_f1: dict[str, list[float]] = defaultdict(list)
    thresholds: dict[str, list[float]] = defaultdict(list)
    fold_rows: list[dict] = []
    image_rows: list[dict] = []
    diagnostic_rows: list[dict] = []
    first_repeat_predictions: dict[str, dict[int, np.ndarray]] = {
        name: {} for name in VARIANTS
    }
    first_repeat_supports: dict[int, np.ndarray] = {}

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
        train_maps = _score_maps(train, names, compact)
        valid_maps = _score_maps(valid, names, compact)
        print(
            f"STAGE16D_SPLIT {split_no:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1}",
            flush=True,
        )
        for variant_index, variant in enumerate(VARIANTS):
            train_scores = train_maps[variant_index]
            valid_scores = valid_maps[variant_index]
            threshold = float(
                selection_metric(train_scores, train, args.thresholds)["threshold"]
            )
            metric, event_counts, per_image = fixed_eval(
                valid_scores, valid, threshold
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
                {
                    "repeat": repeat + 1,
                    "fold": fold + 1,
                    "variant": variant,
                    **row,
                }
                for row in per_image
            )
            if repeat == 0:
                for global_index, score in zip(va_idx, valid_scores):
                    first_repeat_predictions[variant][int(global_index)] = score >= threshold
        for local_index, diagnostic in enumerate(valid_maps[3]):
            global_index = int(va_idx[local_index])
            diagnostic_rows.append(
                {
                    "repeat": repeat + 1,
                    "fold": fold + 1,
                    "image_index": global_index,
                    "image_id": selection[global_index]["id"],
                    **diagnostic,
                }
            )
            if repeat == 0:
                first_repeat_supports[global_index] = valid_maps[2][local_index]

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
        and deltas["aggregate_precision"] >= 0.0
        and deltas["aggregate_recall"] >= -0.01
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
    pd.DataFrame(diagnostic_rows).to_csv(out / "stability_diagnostics.csv", index=False)

    if any(len(first_repeat_predictions[name]) != len(selection) for name in VARIANTS):
        raise RuntimeError("first-repeat out-of-fold preview predictions are incomplete")
    if len(first_repeat_supports) != len(selection):
        raise RuntimeError("first-repeat out-of-fold support maps are incomplete")
    rows = []
    for position in PREVIEW_POSITIONS:
        item = selection[position]
        rows.append(
            [
                item["img"],
                item["gt"],
                first_repeat_predictions[VARIANTS[0]][position],
                first_repeat_supports[position],
                first_repeat_predictions[VARIANTS[1]][position],
            ]
        )
    preview_path = write_panel_grid(out / "best_method_preview.png", rows)
    manifest_path = _write_manifest(out)
    summary = {
        "stage": "16d-stable-region-boundary-gate",
        "role": "generation_2_bounded_structural_stability_falsification",
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
                "fixed component-tree-inspired shape stability of low-response regions "
                "separated by the serialized incumbent edge score"
            ),
            "implementation_fidelity": (
                "registered repository-specific surrogate; not an exact reproduction "
                "of unpublished author node-selection code"
            ),
            "parameters": {
                "quantization_levels": QUANTIZATION_LEVELS,
                "region_connectivity": 4,
                "region_area_min": REGION_AREA_MIN,
                "level_delta": LEVEL_DELTA,
                "chamfer_distance_max": CHAMFER_DISTANCE_MAX,
                "fragment_connectivity": 8,
                "fragment_length_min": FRAGMENT_LENGTH_MIN,
                "gate_strength_inherited": STRENGTH,
                "gate_floor_inherited": FLOOR,
            },
            "formula": "candidate = incumbent * [0.10 + 0.90 * support^2]",
            "parameter_selection": "published fixed stability settings plus unchanged incumbent gate; no search",
        },
        "promotion_rule": (
            "Conjunctive: UDED aggregate F1 delta at least +0.002, aggregate precision "
            "nonnegative, aggregate recall no worse than -0.01, mean paired fold-F1 "
            "delta nonnegative, and at least 9/15 fold wins. The official attachment "
            "must complete; BSDS500-validation ODS delta must be at least +0.002 and "
            "OIS/AP deltas must both be nonnegative. All conditions are required."
        ),
        "uded_gate": {"met": uded_gate, "deltas": deltas},
        "metrics": aggregate,
        "promotion_pending_official_bsds_val": True,
        "official_evaluation": {
            "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
            "required_before_promotion": True,
            "stage15a_caveat": (
                "the unmodified Windows matcher remains stochastic and reference-uncertified; "
                "the fixed-seed diagnostic matcher is forbidden"
            ),
        },
        "visual_preview": {
            "file": preview_path.name,
            "selection": "fixed UDED-selection positions 1, 8, and 15",
            "columns": [
                "input",
                "ground_truth",
                "compact_MFI_out_of_fold_prediction",
                "stable_region_boundary_support",
                "candidate_out_of_fold_prediction",
            ],
            "use": "documentary only; not an optimization signal",
        },
        "files": [
            "summary.json",
            "variant_ranking.csv",
            "fold_results.csv",
            "per_image_metrics.csv",
            "stability_diagnostics.csv",
            "best_method_preview.png",
            "official_eval_manifest.json",
        ],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("STAGE16D_STABLE_REGION_BOUNDARY_GATE_COMPLETE", flush=True)
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
    parser.add_argument("--gt-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--split", default="val")
    args = parser.parse_args()
    if args.export_bsds:
        if not args.image_dir or not args.gt_dir or not args.output_dir:
            parser.error("--export-bsds requires --image-dir, --gt-dir, and --output-dir")
        return export_bsds(args)
    return run_experiment(args)


if __name__ == "__main__":
    raise SystemExit(main())
