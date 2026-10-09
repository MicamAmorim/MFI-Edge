from __future__ import annotations

"""Stage 16l: exact EDPF chain support as one compact-MFI context cue.

The author EDPF detector is executed unchanged.  Its binary chain map is
expanded by one 8-neighbourhood pixel solely to align its raster support with
the incumbent Scharr NMS map, then treated as one training-eligible positive
membership.  The compact bank, Choquet capacity, gate, and localizer stay
unchanged.
"""

from collections import defaultdict
from pathlib import Path
import argparse
import hashlib
import json
import math
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
from evaluation.bsds_official.export_stage15d_edpf import (
    AUTHOR_COMMIT,
    AUTHOR_REPOSITORY,
    _build_exporter,
    _run,
    _verify_dependencies,
    export_edpf_maps,
)
from run_stage12b_fuzzy_signature import membership_stack, prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage14c_positive_bank_pruning import FLOOR, GAMMA, STRENGTH
from run_stage16f_rolling_guidance_localizer import _ordered_compact
from src.bipolar_fuzzy import context_gate, distorted_choquet
from src.edge_signature import binary_auc, mutual_information_binary, population_masks
from src.linking import continuity_metrics


EXPERIMENT_ID = "stage16l_edpf_chain_context"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
VARIANTS = ("compact_mfi", "compact_plus_edpf_chain_support")
PREVIEW_POSITIONS = (0, 7, 14)
ALIGNMENT_DILATION = 1
ELIGIBILITY_AUC = 0.56


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _as_u8_image(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image)
    if np.issubdtype(array.dtype, np.integer):
        if array.dtype == np.uint8:
            return array
        if int(np.max(array)) <= 255:
            return np.clip(array, 0, 255).astype(np.uint8)
        maximum = float(np.iinfo(array.dtype).max)
        return np.rint(np.clip(array.astype(np.float64) / maximum, 0.0, 1.0) * 255.0).astype(np.uint8)
    values = np.asarray(array, dtype=np.float64)
    if float(np.nanmax(values)) <= 1.0 + 1.0e-9:
        values = values * 255.0
    return np.rint(np.clip(values, 0.0, 255.0)).astype(np.uint8)


def _run_exact_edpf_for_items(items: list[dict], work_dir: Path) -> dict:
    """Run the pinned author executable once on the already-sized UDED arrays."""
    dependency_hashes = _verify_dependencies()
    executable, build_log_tail = _build_exporter()
    input_dir = work_dir / "inputs"
    prediction_dir = work_dir / "predictions"
    input_dir.mkdir(parents=True, exist_ok=True)
    prediction_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, item in enumerate(items):
        path = input_dir / f"{index:03d}_{item['id']}.png"
        Image.fromarray(_as_u8_image(item["img"])).save(path)
        paths.append(path)
    manifest = work_dir / "input_manifest.txt"
    manifest.write_text("\n".join(path.resolve().as_posix() for path in paths) + "\n", encoding="utf-8")
    runtime_csv = work_dir / "per_image_runtime.csv"
    stdout = _run([str(executable), str(manifest), str(prediction_dir), str(runtime_csv)], timeout=3600)

    hashes = {}
    for item, input_path in zip(items, paths):
        output_path = prediction_dir / f"{input_path.stem}.png"
        if not output_path.exists():
            raise RuntimeError(f"missing exact EDPF output: {output_path}")
        raw = np.asarray(Image.open(output_path).convert("L"), dtype=np.uint8)
        if raw.shape != np.asarray(item["gt"]).shape or not set(np.unique(raw)).issubset({0, 255}):
            raise RuntimeError(f"invalid exact EDPF map contract: {output_path}")
        support = ndi.binary_dilation(
            raw > 0,
            structure=np.ones((3, 3), dtype=bool),
            iterations=ALIGNMENT_DILATION,
        )
        item["edpf_chain_support"] = support.astype(np.float32)
        hashes[str(item["id"])] = _sha256(output_path)
    (work_dir / "map_hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    metadata = {
        "implementation": "exact pinned unmodified author EDPF; repository batch-I/O harness",
        "author_repository": AUTHOR_REPOSITORY,
        "author_commit": AUTHOR_COMMIT,
        "alignment_adapter": "one 3x3 binary dilation after author output; author detector unchanged",
        "n_maps": len(items),
        "author_hashes": dependency_hashes["author_hashes"],
        "build_log_tail": build_log_tail,
        "stdout_tail": "\n".join(stdout.splitlines()[-20:]),
    }
    (work_dir / "export_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def _attach_existing_edpf(items: list[dict], image_paths: list[Path], prediction_dir: Path) -> None:
    for item, image_path in zip(items, image_paths):
        raw = np.asarray(Image.open(prediction_dir / f"{image_path.stem}.png").convert("L"), dtype=np.uint8)
        if raw.shape != np.asarray(item["scharr"]).shape or not set(np.unique(raw)).issubset({0, 255}):
            raise RuntimeError(f"invalid exact EDPF map for {image_path.stem}")
        item["edpf_chain_support"] = ndi.binary_dilation(
            raw > 0,
            structure=np.ones((3, 3), dtype=bool),
            iterations=ALIGNMENT_DILATION,
        ).astype(np.float32)


def _fit_chain_spec(items: list[dict], seed: int, max_samples: int = 2500) -> dict:
    values, targets = [], []
    for item_no, item in enumerate(items):
        masks = population_masks(item)
        flat = np.asarray(item["edpf_chain_support"], dtype=np.float64).ravel()
        for group_no, (group, target) in enumerate((("edge", True), ("texture", False))):
            ids = np.flatnonzero(np.asarray(masks[group], dtype=bool).ravel())
            if ids.size > int(max_samples):
                rng = np.random.default_rng(int(seed) + 1009 * item_no + 97 * group_no)
                ids = rng.choice(ids, size=int(max_samples), replace=False)
            if ids.size:
                values.append(flat[ids])
                targets.append(np.full(ids.size, target, dtype=bool))
    score = np.concatenate(values)
    target = np.concatenate(targets)
    auc = float(binary_auc(score, target))
    information = float(mutual_information_binary(score, target))
    raw_weight = max(auc - 0.5, 0.0) * (1.0 + information)
    return {
        "feature": "edpf_chain_support",
        "texture_auc": auc,
        "mutual_information": information,
        "raw_weight": float(raw_weight if auc >= ELIGIBILITY_AUC else 0.0),
        "eligible": bool(auc >= ELIGIBILITY_AUC and raw_weight > 0.0),
        "edge_support_rate": float(np.mean(score[target])),
        "texture_support_rate": float(np.mean(score[~target])),
    }


def _raw_compact(bank: list[dict]) -> list[dict]:
    rows = []
    for row in bank:
        copied = dict(row)
        copied["weight"] = max(float(row["texture_auc"]) - 0.5, 0.0) * (1.0 + float(row["mutual_information"]))
        rows.append(copied)
    return rows


def _score_pairs(items: list[dict], names: list[str], compact: list[dict], spec: dict):
    controls, candidates = [], []
    raw_compact = _raw_compact(compact)
    compact_weights = np.asarray([row["weight"] for row in raw_compact], dtype=np.float64)
    for item in items:
        memberships, weights = membership_stack(item, names, raw_compact, "edge")
        control_context = distorted_choquet(memberships, weights, GAMMA)
        controls.append(context_gate(item["scharr"], control_context, STRENGTH, FLOOR).astype(np.float32))
        if not spec["eligible"]:
            candidates.append(controls[-1].copy())
            continue
        candidate_memberships = np.concatenate(
            [memberships, np.asarray(item["edpf_chain_support"], dtype=np.float32)[..., None]], axis=-1
        )
        candidate_weights = np.concatenate([compact_weights, [float(spec["raw_weight"])]]).astype(np.float64)
        candidate_weights /= max(float(candidate_weights.sum()), 1.0e-9)
        candidate_context = distorted_choquet(candidate_memberships, candidate_weights, GAMMA)
        candidates.append(context_gate(item["scharr"], candidate_context, STRENGTH, FLOOR).astype(np.float32))
    return controls, candidates


def _fit_full_candidate(args: argparse.Namespace):
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side_development)
    selection, names = prepare(raw[0::2])
    _run_exact_edpf_for_items(selection, Path(args.out) / "edpf_exact_uded_full_fit")
    positive, _negative = learn_banks(
        selection, names, args.seed, args.max_positive, args.max_negative, args.max_abs_corr
    )
    compact = _ordered_compact(positive)
    return names, compact, _fit_chain_spec(selection, args.seed)


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
                "script": "run_stage16l_edpf_chain_context.py",
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
    edpf_dir = output_dir / "exact_edpf_maps"
    edpf_metadata = export_edpf_maps(Path(args.image_dir), edpf_dir, split=args.split)
    diagnostics = []
    for index, path in enumerate(image_paths, start=1):
        print(f"STAGE16L_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {path.stem}", flush=True)
        prepared, candidate_names = prepare([{"id": path.stem, "img": imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        _attach_existing_edpf(prepared, [path], edpf_dir)
        incumbent, candidate = [maps[0] for maps in _score_pairs(prepared, names, compact, spec)]
        _save_soft_png(candidate, output_dir / f"{path.stem}.png")
        diagnostics.append({
            "image_id": path.stem,
            "chain_support_fraction": float(np.mean(prepared[0]["edpf_chain_support"])),
            "mean_abs_score_delta": float(np.mean(np.abs(candidate - incumbent))),
        })
    pd.DataFrame(diagnostics).to_csv(output_dir / "edpf_chain_diagnostics.csv", index=False)
    metadata = {
        "method": VARIANTS[1],
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "development_source": "UDED selection only",
        "output": "direct 8-bit soft PNG without per-image normalization",
        "edpf": edpf_metadata,
        "chain_membership_fit": spec,
        "alignment_dilation": ALIGNMENT_DILATION,
        "n_maps": len(image_paths),
    }
    (output_dir / "export_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return 0


def _mean_continuity(predictions: list[np.ndarray], items: list[dict]) -> float:
    values = []
    for prediction, item in zip(predictions, items):
        tol = max(1, int(round(0.0075 * math.hypot(*np.asarray(item["gt"]).shape))))
        values.append(continuity_metrics(prediction, item["gt"], tol=tol)["largest_component_gt_coverage"])
    return float(np.mean(values))


def run_experiment(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    selection, names = prepare(raw[0::2])
    if len(selection) != 15:
        raise RuntimeError(f"expected 15 UDED selection images, found {len(selection)}")
    _run_exact_edpf_for_items(selection, out / "edpf_exact_uded")

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts: dict[str, list] = defaultdict(list)
    fold_f1: dict[str, list[float]] = defaultdict(list)
    fold_coverage: dict[str, list[float]] = defaultdict(list)
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
        spec = _fit_chain_spec(train, args.seed + 20000 * repeat + fold)
        calibration_rows.append({"repeat": repeat + 1, "fold": fold + 1, **spec})
        train_maps = _score_pairs(train, names, compact, spec)
        valid_maps = _score_pairs(valid, names, compact, spec)
        print(
            f"STAGE16L_SPLIT {split_no:02d}/{len(splits)} repeat={repeat + 1} "
            f"fold={fold + 1} chain_auc={spec['texture_auc']:.4f}", flush=True,
        )
        for variant_index, variant in enumerate(VARIANTS):
            threshold = float(selection_metric(train_maps[variant_index], train, args.thresholds)["threshold"])
            metric, event_counts, per_image = fixed_eval(valid_maps[variant_index], valid, threshold)
            predictions = [score >= threshold for score in valid_maps[variant_index]]
            coverage = _mean_continuity(predictions, valid)
            counts[variant].extend(event_counts)
            fold_f1[variant].append(float(metric["F1"]))
            fold_coverage[variant].append(coverage)
            thresholds[variant].append(threshold)
            fold_rows.append({
                "repeat": repeat + 1, "fold": fold + 1, "variant": variant,
                "train_threshold": threshold, "chain_eligible": bool(spec["eligible"]),
                "mean_largest_component_gt_coverage": coverage, **metric,
            })
            image_rows.extend({
                "repeat": repeat + 1, "fold": fold + 1, "variant": variant, **row,
            } for row in per_image)
            if repeat == 0:
                for global_index, prediction in zip(va_idx, predictions):
                    first_repeat_predictions[variant][int(global_index)] = prediction

    aggregate = {name: aggregate_counts(counts[name]) for name in VARIANTS}
    incumbent_folds = np.asarray(fold_f1[VARIANTS[0]], dtype=np.float64)
    candidate_folds = np.asarray(fold_f1[VARIANTS[1]], dtype=np.float64)
    coverage_delta = np.asarray(fold_coverage[VARIANTS[1]]) - np.asarray(fold_coverage[VARIANTS[0]])
    eligible_folds = int(sum(bool(row["eligible"]) for row in calibration_rows))
    deltas = {
        "aggregate_F1": float(aggregate[VARIANTS[1]]["F1"] - aggregate[VARIANTS[0]]["F1"]),
        "aggregate_precision": float(aggregate[VARIANTS[1]]["precision"] - aggregate[VARIANTS[0]]["precision"]),
        "aggregate_recall": float(aggregate[VARIANTS[1]]["recall"] - aggregate[VARIANTS[0]]["recall"]),
        "mean_fold_F1": float(np.mean(candidate_folds - incumbent_folds)),
        "fold_wins": int(np.sum(candidate_folds > incumbent_folds)),
        "eligible_folds": eligible_folds,
        "mean_fold_largest_component_coverage": float(np.mean(coverage_delta)),
        "coverage_wins": int(np.sum(coverage_delta > 0)),
    }
    uded_gate = bool(
        deltas["aggregate_F1"] >= 0.002
        and deltas["aggregate_precision"] >= -0.002
        and deltas["aggregate_recall"] >= -0.003
        and deltas["mean_fold_F1"] >= 0.0
        and deltas["fold_wins"] >= 9
        and eligible_folds >= 12
        and deltas["mean_fold_largest_component_coverage"] >= 0.0
        and deltas["coverage_wins"] >= 8
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
            "mean_largest_component_gt_coverage": float(np.mean(fold_coverage[variant])),
            "threshold_mean": float(np.mean(thresholds[variant])),
            "threshold_std": float(np.std(thresholds[variant])),
        })
    pd.DataFrame(ranking).sort_values("cv_F1", ascending=False).to_csv(out / "variant_ranking.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)
    pd.DataFrame(calibration_rows).to_csv(out / "edpf_chain_calibration.csv", index=False)

    if any(len(first_repeat_predictions[name]) != len(selection) for name in VARIANTS):
        raise RuntimeError("first-repeat out-of-fold preview predictions are incomplete")
    rows = [[
        selection[position]["img"],
        selection[position]["gt"],
        first_repeat_predictions[VARIANTS[0]][position],
        first_repeat_predictions[VARIANTS[1]][position],
        selection[position]["edpf_chain_support"],
    ] for position in PREVIEW_POSITIONS]
    preview_path = write_panel_grid(out / "best_method_preview.png", rows)
    manifest_path = _write_official_manifest(out)
    summary = {
        "stage": "16l-edpf-chain-context",
        "role": "generation_2_exact_chain_support_context_falsification",
        "architecture_changed": False,
        "protected_split_used": False,
        "datasets": {
            "UDED_selection": {"n_images": len(selection), "role": "development repeated leakage-free CV", "repeats": args.repeats, "folds": args.folds},
            "BSDS500_validation": {"role": "development official attachment", "status": "pending controller attachment"},
        },
        "mechanism": {
            "description": "one positive context membership from exact author EDPF contiguous chains after a fixed one-pixel 8-neighbourhood raster-alignment dilation",
            "implementation_fidelity": "exact EDPF detector plus explicitly repository-specific context integration",
            "author_repository": AUTHOR_REPOSITORY,
            "author_commit": AUTHOR_COMMIT,
            "parameters": {"alignment_dilation": ALIGNMENT_DILATION, "eligibility_auc": ELIGIBILITY_AUC},
            "unchanged": ["five retained memberships", "distorted-Choquet gamma 0.55", "gate strength 2.0 and floor 0.10", "median-conditioned grayscale Scharr+NMS localizer"],
        },
        "promotion_rule": (
            "Conjunctive: UDED aggregate F1 delta at least +0.002, precision delta "
            "at least -0.002, recall delta at least -0.003, mean paired fold-F1 "
            "nonnegative, at least 9/15 F1 wins, chain eligibility in at least "
            "12/15 folds, nonnegative mean largest-component GT-coverage delta, "
            "and at least 8/15 coverage wins. The official attachment must complete; "
            "BSDS500-validation ODS delta must be at least +0.002 and OIS/AP deltas "
            "must both be nonnegative. All conditions are required."
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
            "columns": ["input", "ground_truth", "compact_MFI_out_of_fold_prediction", "candidate_out_of_fold_prediction", "exact_EDPF_chain_support_plus_one_pixel_alignment"],
            "use": "documentary only; not an optimization signal",
        },
        "files": ["summary.json", "variant_ranking.csv", "fold_results.csv", "per_image_metrics.csv", "edpf_chain_calibration.csv", "edpf_exact_uded/export_manifest.json", "edpf_exact_uded/map_hashes.json", "edpf_exact_uded/per_image_runtime.csv", "best_method_preview.png", "official_eval_manifest.json"],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE16L_EDPF_CHAIN_CONTEXT_COMPLETE", flush=True)
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
