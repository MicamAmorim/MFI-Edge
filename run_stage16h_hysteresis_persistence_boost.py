from __future__ import annotations

"""Stage 16h: connected all-threshold hysteresis persistence over compact MFI.

The compact Choquet context and Scharr+NMS localizer are unchanged.  The sole
candidate change is a deterministic soft transform that assigns each supported
pixel the largest high threshold at which it remains connected, through pixels
above half that threshold, to a strong seed.
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
from skimage.io import imread

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12b_fuzzy_signature import prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage16f_rolling_guidance_localizer import (
    _contexts,
    _fit_full_context,
    _ordered_compact,
)
from src.bipolar_fuzzy import context_gate
from run_stage14c_positive_bank_pruning import FLOOR, STRENGTH


EXPERIMENT_ID = "stage16h_hysteresis_persistence_boost"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
VARIANTS = ("compact_mfi", "hysteresis_persistence_boost")
PREVIEW_POSITIONS = (0, 7, 14)
CONNECTIVITY = 8
LOW_TO_HIGH_RATIO = 0.5
SERIALIZATION_LEVELS = 255


def hysteresis_persistence_boost(score: np.ndarray) -> np.ndarray:
    """Return the exact 8-bit all-threshold 2:1 hysteresis reconstruction.

    For high threshold h, weak pixels have q >= ceil(h/2) and are retained when
    8-connected to any q >= h seed.  The output at a pixel is the largest h for
    which that condition holds.  A descending bucket propagation computes all
    255 hysteresis reconstructions together.  Because every pixel seeds itself
    at h=q, the output is pointwise no smaller than q; q=0 support stays zero.
    """
    x = np.asarray(score, dtype=np.float32)
    if x.ndim != 2 or not np.all(np.isfinite(x)):
        raise ValueError("hysteresis persistence requires a finite 2-D score")
    q = np.rint(np.clip(x, 0.0, 1.0) * SERIALIZATION_LEVELS).astype(np.uint8)
    out = q.copy()
    height, width = q.shape
    buckets: list[list[int]] = [[] for _ in range(SERIALIZATION_LEVELS + 1)]
    flat_q = q.ravel()
    flat_out = out.ravel()
    for flat_index in np.flatnonzero(flat_q):
        buckets[int(flat_q[flat_index])].append(int(flat_index))

    offsets = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1),
    )
    for level in range(SERIALIZATION_LEVELS, 0, -1):
        bucket = buckets[level]
        cursor = 0
        while cursor < len(bucket):
            flat_index = bucket[cursor]
            cursor += 1
            if int(flat_out[flat_index]) != level:
                continue
            y, x_coord = divmod(flat_index, width)
            for dy, dx in offsets:
                ny, nx = y + dy, x_coord + dx
                if ny < 0 or ny >= height or nx < 0 or nx >= width:
                    continue
                neighbor = ny * width + nx
                candidate = min(level, 2 * int(flat_q[neighbor]))
                if candidate > int(flat_out[neighbor]):
                    flat_out[neighbor] = candidate
                    buckets[candidate].append(neighbor)

    if np.any(out < q) or np.any((q == 0) != (out == 0)):
        raise RuntimeError("hysteresis persistence violated its support/floor invariant")
    return out.astype(np.float32) / float(SERIALIZATION_LEVELS)


def _base_maps(items: list[dict], contexts: list[np.ndarray]) -> list[np.ndarray]:
    return [
        context_gate(item["scharr"], context, STRENGTH, FLOOR).astype(np.float32)
        for item, context in zip(items, contexts)
    ]


def _score_maps(items: list[dict], contexts: list[np.ndarray]):
    incumbents = _base_maps(items, contexts)
    candidates = [hysteresis_persistence_boost(score) for score in incumbents]
    return incumbents, candidates


def _diagnostic(image_id: str, incumbent: np.ndarray, candidate: np.ndarray) -> dict:
    base_q = np.rint(np.clip(incumbent, 0.0, 1.0) * 255.0).astype(np.uint8)
    candidate_q = np.rint(np.clip(candidate, 0.0, 1.0) * 255.0).astype(np.uint8)
    delta = candidate_q.astype(np.int16) - base_q.astype(np.int16)
    support = base_q > 0
    return {
        "image_id": image_id,
        "supported_pixels": int(np.sum(support)),
        "boosted_pixels": int(np.sum(delta > 0)),
        "boosted_supported_fraction": float(
            np.sum(delta > 0) / max(int(np.sum(support)), 1)
        ),
        "mean_positive_boost_levels": float(
            np.mean(delta[delta > 0]) if np.any(delta > 0) else 0.0
        ),
        "max_boost_levels": int(np.max(delta)),
        "pointwise_floor_preserved": bool(np.all(delta >= 0)),
        "support_exactly_preserved": bool(np.array_equal(base_q > 0, candidate_q > 0)),
    }


def _save_soft_png(score: np.ndarray, path: Path) -> None:
    x = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(x)):
        raise RuntimeError(f"non-finite candidate score for {path.stem}")
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.rint(np.clip(x, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L").save(path)


def _write_official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": VARIANTS[1],
            "export": {
                "script": "run_stage16h_hysteresis_persistence_boost.py",
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
    names, compact = _fit_full_context(args)
    image_paths = sorted(Path(args.image_dir).glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {args.image_dir}")
    output_dir = Path(args.output_dir)
    diagnostics = []
    for index, path in enumerate(image_paths, start=1):
        print(f"STAGE16H_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {path.stem}", flush=True)
        prepared, candidate_names = prepare([{"id": path.stem, "img": imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        incumbent, candidate = [maps[0] for maps in _score_maps(
            prepared, _contexts(prepared, names, compact)
        )]
        _save_soft_png(candidate, output_dir / f"{path.stem}.png")
        diagnostics.append(_diagnostic(path.stem, incumbent, candidate))
    pd.DataFrame(diagnostics).to_csv(output_dir / "persistence_diagnostics.csv", index=False)
    metadata = {
        "method": VARIANTS[1],
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "development_source": "UDED selection only",
        "output": "direct 8-bit soft PNG without per-image normalization",
        "mechanism": {
            "implementation_fidelity": "repository-specific all-threshold hysteresis connected transform",
            "low_to_high_ratio": LOW_TO_HIGH_RATIO,
            "connectivity": CONNECTIVITY,
            "levels": SERIALIZATION_LEVELS,
            "input": "unchanged compact-MFI score",
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

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts: dict[str, list] = defaultdict(list)
    fold_f1: dict[str, list[float]] = defaultdict(list)
    thresholds: dict[str, list[float]] = defaultdict(list)
    fold_rows, image_rows, diagnostic_rows = [], [], []
    first_repeat_predictions: dict[str, dict[int, np.ndarray]] = {name: {} for name in VARIANTS}
    first_repeat_boost: dict[int, np.ndarray] = {}

    for split_no, (repeat, fold, tr_idx, va_idx) in enumerate(splits, start=1):
        train = [selection[index] for index in tr_idx]
        valid = [selection[index] for index in va_idx]
        positive, _negative = learn_banks(
            train, names, args.seed + 10000 * repeat + fold,
            args.max_positive, args.max_negative, args.max_abs_corr,
        )
        compact = _ordered_compact(positive)
        train_maps = _score_maps(train, _contexts(train, names, compact))
        valid_maps = _score_maps(valid, _contexts(valid, names, compact))
        print(
            f"STAGE16H_SPLIT {split_no:02d}/{len(splits)} repeat={repeat + 1} fold={fold + 1}",
            flush=True,
        )
        for variant_index, variant in enumerate(VARIANTS):
            train_scores = train_maps[variant_index]
            valid_scores = valid_maps[variant_index]
            threshold = float(selection_metric(train_scores, train, args.thresholds)["threshold"])
            metric, event_counts, per_image = fixed_eval(valid_scores, valid, threshold)
            counts[variant].extend(event_counts)
            fold_f1[variant].append(float(metric["F1"]))
            thresholds[variant].append(threshold)
            fold_rows.append({
                "repeat": repeat + 1, "fold": fold + 1, "variant": variant,
                "train_threshold": threshold, **metric,
            })
            image_rows.extend({
                "repeat": repeat + 1, "fold": fold + 1, "variant": variant, **row,
            } for row in per_image)
            if repeat == 0:
                for global_index, score in zip(va_idx, valid_scores):
                    first_repeat_predictions[variant][int(global_index)] = score >= threshold
        for local_index, global_index in enumerate(va_idx):
            diag = _diagnostic(
                selection[int(global_index)]["id"],
                valid_maps[0][local_index], valid_maps[1][local_index],
            )
            diagnostic_rows.append({
                "repeat": repeat + 1, "fold": fold + 1,
                "image_index": int(global_index), **diag,
            })
            if repeat == 0:
                first_repeat_boost[int(global_index)] = valid_maps[1][local_index] - np.rint(
                    np.clip(valid_maps[0][local_index], 0.0, 1.0) * 255.0
                ).astype(np.float32) / 255.0

    aggregate = {name: aggregate_counts(counts[name]) for name in VARIANTS}
    candidate_folds = np.asarray(fold_f1[VARIANTS[1]], dtype=np.float64)
    incumbent_folds = np.asarray(fold_f1[VARIANTS[0]], dtype=np.float64)
    deltas = {
        "aggregate_F1": float(aggregate[VARIANTS[1]]["F1"] - aggregate[VARIANTS[0]]["F1"]),
        "aggregate_precision": float(aggregate[VARIANTS[1]]["precision"] - aggregate[VARIANTS[0]]["precision"]),
        "aggregate_recall": float(aggregate[VARIANTS[1]]["recall"] - aggregate[VARIANTS[0]]["recall"]),
        "mean_fold_F1": float(np.mean(candidate_folds - incumbent_folds)),
        "fold_wins": int(np.sum(candidate_folds > incumbent_folds)),
    }
    uded_gate = bool(
        deltas["aggregate_F1"] >= 0.002
        and deltas["aggregate_recall"] >= 0.002
        and deltas["aggregate_precision"] >= -0.003
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
    pd.DataFrame(diagnostic_rows).to_csv(out / "persistence_diagnostics.csv", index=False)

    if any(len(first_repeat_predictions[name]) != len(selection) for name in VARIANTS):
        raise RuntimeError("first-repeat out-of-fold preview predictions are incomplete")
    rows = []
    for position in PREVIEW_POSITIONS:
        rows.append([
            selection[position]["img"], selection[position]["gt"],
            first_repeat_predictions[VARIANTS[0]][position],
            first_repeat_predictions[VARIANTS[1]][position],
            first_repeat_boost[position],
        ])
    preview_path = write_panel_grid(out / "best_method_preview.png", rows)
    manifest_path = _write_official_manifest(out)
    summary = {
        "stage": "16h-hysteresis-persistence-boost",
        "role": "generation_2_connected_threshold_persistence_falsification",
        "architecture_changed": False,
        "protected_split_used": False,
        "datasets": {
            "UDED_selection": {"n_images": len(selection), "role": "development repeated leakage-free CV", "repeats": args.repeats, "folds": args.folds},
            "BSDS500_validation": {"role": "development official attachment", "status": "pending controller attachment"},
        },
        "mechanism": {
            "description": "all-threshold 2:1 hysteresis persistence boosts weak incumbent pixels connected to stronger seeds without changing support",
            "implementation_fidelity": "repository-specific soft extension of Canny hysteresis using a connected upper-level-set transform",
            "parameters": {"low_to_high_ratio": LOW_TO_HIGH_RATIO, "connectivity": CONNECTIVITY, "levels": SERIALIZATION_LEVELS},
            "invariants": ["candidate >= serialized incumbent pointwise", "candidate support equals serialized incumbent support", "Scharr+NMS and compact Choquet context unchanged"],
        },
        "promotion_rule": (
            "Conjunctive: UDED aggregate F1 and recall deltas at least +0.002, "
            "precision delta at least -0.003, mean paired fold-F1 nonnegative, "
            "and at least 9/15 fold wins. The official attachment must complete; "
            "BSDS500-validation ODS delta must be at least +0.002 and OIS/AP "
            "deltas must both be nonnegative. All conditions are required."
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
            "columns": ["input", "ground_truth", "compact_MFI_out_of_fold_prediction", "candidate_out_of_fold_prediction", "candidate_minus_serialized_incumbent_score"],
            "use": "documentary only; not an optimization signal",
        },
        "files": ["summary.json", "variant_ranking.csv", "fold_results.csv", "per_image_metrics.csv", "persistence_diagnostics.csv", "best_method_preview.png", "official_eval_manifest.json"],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE16H_HYSTERESIS_PERSISTENCE_COMPLETE", flush=True)
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
