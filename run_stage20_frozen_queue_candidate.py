from __future__ import annotations

"""Execute one immutable candidate from the Stage-20 frozen queue."""

from collections import defaultdict
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import time

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage as ndi
from skimage.io import imread

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12b_fuzzy_signature import membership_stack, prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage14c_positive_bank_pruning import FLOOR, GAMMA, STRENGTH
from run_stage16f_rolling_guidance_localizer import _ordered_compact
import run_stage19b_descriptor_relevance_atlas as atlas
import run_stage19d_aggregation_identification as identification
from src.bipolar_fuzzy import context_gate, distorted_choquet
from src.measure_learning import balanced_sample, learn_2additive


QUEUE_PATH = ROOT / "automation" / "stage20_frozen_queue.json"
PREVIEW_POSITIONS = (0, 6, 13)
SAMPLES_PER_IMAGE = 4096
CAPACITY_SAMPLES = 30000
CAPACITY_RIDGE = 1.0e-4
SEED = 20261009
MAX_DIST = 0.0075


def _queue() -> dict:
    data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    if not data.get("queue_is_complete") or len(data.get("candidates", [])) != 4:
        raise RuntimeError("Stage-20 queue is not the frozen four-candidate queue")
    return data


def _spec(experiment_id: str) -> dict:
    matches = [row for row in _queue()["candidates"] if row["experiment_id"] == experiment_id]
    if len(matches) != 1:
        raise RuntimeError(f"unknown or duplicated frozen candidate: {experiment_id}")
    return matches[0]


def _load_overlap_clean_uded(root: Path) -> list[dict]:
    """Load UDED selection without reading the known BSDS-test-lineage pair."""
    pairs = json.loads((root / "test_pair.lst").read_text(encoding="utf-8"))
    items = []
    for index, (image_rel, gt_rel) in enumerate(pairs, start=1):
        if index % 2 == 0:
            continue
        image_id = Path(image_rel).stem
        if "35028" in image_id:
            continue
        image = imread(root / image_rel)
        gt = imread(root / gt_rel)
        if gt.ndim == 3:
            gt = gt[..., 0]
        if np.issubdtype(gt.dtype, np.integer):
            gt = gt > (0.5 * np.iinfo(gt.dtype).max)
        else:
            gt = gt > 0.5
        items.append({
            "index": index,
            "id": image_id,
            "img_path": image_rel,
            "gt_path": gt_rel,
            "img": image,
            "gt": np.asarray(gt, dtype=bool),
        })
    if len(items) != 14 or any("35028" in str(item["id"]) for item in items):
        raise RuntimeError(f"expected 14 overlap-clean UDED selection images, got {len(items)}")
    return items


def _attach_descriptors(items: list[dict], descriptors: tuple[str, ...], prefix: str) -> None:
    allowed = set(atlas.DESCRIPTORS)
    if not set(descriptors).issubset(allowed):
        raise RuntimeError(f"descriptor outside frozen Stage-19 pool: {set(descriptors) - allowed}")
    for number, item in enumerate(items, start=1):
        print(f"{prefix} {number:03d}/{len(items):03d} {item['id']}", flush=True)
        started = time.perf_counter()
        pre_img = atlas.apply_conditioning(item["img"], "median", size=3)
        maps: dict[str, np.ndarray] = {}
        runtimes: dict[str, float] = {}
        incumbent_requested = tuple(name for name in descriptors if name in atlas.DESCRIPTORS[:5])
        if incumbent_requested:
            part_started = time.perf_counter()
            incumbent = atlas._incumbent_maps(pre_img)
            runtimes["incumbent_requested_joint_seconds"] = time.perf_counter() - part_started
            maps.update({name: incumbent[name] for name in incumbent_requested})
        functions = {
            "structure_tensor_coherence": lambda value: atlas.structure_tensor_orientation_evidence(value),
            "brightness_entropy": lambda value: atlas.local_brightness_entropy_deficit(value)[0],
            "semiglobal_changepoint": lambda value: atlas.semiglobal_changepoint_evidence(value)[0],
        }
        for name in descriptors:
            if name in maps:
                continue
            if name not in functions:
                raise RuntimeError(f"frozen Stage-20 descriptor has no exact implementation route: {name}")
            part_started = time.perf_counter()
            maps[name] = np.asarray(functions[name](pre_img), dtype=np.float32)
            runtimes[f"{name}_seconds"] = time.perf_counter() - part_started
        if pre_img.shape != item["pre_img"].shape:
            raise RuntimeError(f"descriptor/prepared shape mismatch for {item['id']}")
        if not np.allclose(pre_img, item["pre_img"], rtol=0.0, atol=1e-7):
            raise RuntimeError(f"median-conditioning drift for {item['id']}")
        if set(maps) != set(descriptors):
            raise RuntimeError(f"descriptor construction drift for {item['id']}: {sorted(maps)}")
        item["stage20_descriptors"] = {
            name: np.asarray(maps[name], dtype=np.float32) for name in descriptors
        }
        item["stage20_descriptor_runtime_seconds"] = float(time.perf_counter() - started)
        item["stage20_descriptor_runtime_parts"] = runtimes


def _tolerant_target(gt: np.ndarray) -> np.ndarray:
    gt = np.asarray(gt, dtype=bool)
    radius = max(1.0, MAX_DIST * math.hypot(*gt.shape))
    return ndi.distance_transform_edt(~gt) <= radius


def _training_samples(items: list[dict], descriptors: tuple[str, ...], seed: int) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = [], []
    for item_no, item in enumerate(items):
        tensor = np.stack([item["stage20_descriptors"][name] for name in descriptors], axis=-1)
        target = _tolerant_target(item["gt"])
        size = target.size
        count = min(SAMPLES_PER_IMAGE, size)
        token = hashlib.sha256(f"{seed}:stage20:{item_no}:{item['id']}".encode()).digest()
        rng = np.random.default_rng(int.from_bytes(token[:8], "little"))
        chosen = np.sort(rng.choice(size, size=count, replace=False))
        xs.append(tensor.reshape(-1, len(descriptors))[chosen])
        ys.append(target.ravel()[chosen].astype(np.float64))
    return np.concatenate(xs), np.concatenate(ys)


def _fit_candidate(items: list[dict], descriptors: tuple[str, ...], seed: int) -> dict:
    raw, target = _training_samples(items, descriptors, seed)
    membership = identification._fit_memberships(raw, target)
    memberships = identification._apply_memberships(raw, membership)
    balanced_x, balanced_y = balanced_sample(
        memberships, target, max_samples=CAPACITY_SAMPLES, seed=seed + 17
    )
    capacity = learn_2additive(balanced_x, balanced_y, ridge=CAPACITY_RIDGE)
    raw_context = identification._choquet_from_table(
        memberships, np.asarray(capacity["capacity_table"], dtype=np.float64)
    )
    calibration = identification._fit_scalar_calibration(raw_context, target)
    return {
        "descriptors": descriptors,
        "membership": membership,
        "capacity": capacity,
        "calibration": calibration,
        "training_samples": int(len(target)),
        "balanced_capacity_samples": int(len(balanced_y)),
    }


def _candidate_context(item: dict, model: dict) -> np.ndarray:
    descriptors = tuple(model["descriptors"])
    raw = np.stack([item["stage20_descriptors"][name] for name in descriptors], axis=-1)
    shape = raw.shape[:2]
    memberships = identification._apply_memberships(raw.reshape(-1, len(descriptors)), model["membership"])
    raw_context = identification._choquet_from_table(
        memberships, np.asarray(model["capacity"]["capacity_table"], dtype=np.float64)
    )
    beta = np.asarray(model["calibration"], dtype=np.float64)
    context = identification.expit(beta[0] + beta[1] * raw_context).reshape(shape)
    return np.clip(context, 0.0, 1.0).astype(np.float32)


def _raw_compact(bank: list[dict]) -> list[dict]:
    rows = []
    for row in bank:
        copied = dict(row)
        copied["weight"] = max(float(row["texture_auc"]) - 0.5, 0.0) * (
            1.0 + float(row["mutual_information"])
        )
        rows.append(copied)
    return rows


def _score_pairs(items: list[dict], names: list[str], compact: list[dict], model: dict):
    raw_compact = _raw_compact(compact)
    weights = np.asarray([row["weight"] for row in raw_compact], dtype=np.float64)
    controls, candidates, contexts, runtimes = [], [], [], []
    for item in items:
        started = time.perf_counter()
        memberships, _ = membership_stack(item, names, raw_compact, "edge")
        control_context = distorted_choquet(memberships, weights, GAMMA)
        candidate_context = _candidate_context(item, model)
        control_score = context_gate(item["scharr"], control_context, STRENGTH, FLOOR).astype(np.float32)
        candidate_score = context_gate(item["scharr"], candidate_context, STRENGTH, FLOOR).astype(np.float32)
        for label, score in (("control", control_score), ("candidate", candidate_score)):
            if not np.all(np.isfinite(score)) or float(score.min()) < 0.0 or float(score.max()) > 1.0 + 1e-6:
                raise RuntimeError(f"invalid {label} score for {item['id']}")
        controls.append(control_score)
        candidates.append(candidate_score)
        contexts.append(candidate_context)
        runtimes.append(float(time.perf_counter() - started))
    return controls, candidates, contexts, runtimes


def _model_rows(model: dict, repeat: int | str, fold: int | str) -> list[dict]:
    descriptors = tuple(model["descriptors"])
    rows = []
    for name, value in zip(descriptors, model["capacity"]["shapley"]):
        rows.append({"repeat": repeat, "fold": fold, "kind": "shapley", "term_a": name, "term_b": "", "value": float(value)})
    matrix = np.asarray(model["capacity"]["interaction"], dtype=float)
    for i, left in enumerate(descriptors):
        for j in range(i + 1, len(descriptors)):
            rows.append({"repeat": repeat, "fold": fold, "kind": "interaction", "term_a": left, "term_b": descriptors[j], "value": float(matrix[i, j])})
    for name, midpoint, scale, direction in zip(
        descriptors,
        model["membership"]["midpoint"],
        model["membership"]["scale"],
        model["membership"]["direction"],
    ):
        rows.extend([
            {"repeat": repeat, "fold": fold, "kind": "membership_midpoint", "term_a": name, "term_b": "", "value": float(midpoint)},
            {"repeat": repeat, "fold": fold, "kind": "membership_scale", "term_a": name, "term_b": "", "value": float(scale)},
            {"repeat": repeat, "fold": fold, "kind": "membership_direction", "term_a": name, "term_b": "", "value": float(direction)},
        ])
    rows.extend([
        {"repeat": repeat, "fold": fold, "kind": "calibration_intercept", "term_a": "context", "term_b": "", "value": float(model["calibration"][0])},
        {"repeat": repeat, "fold": fold, "kind": "calibration_slope", "term_a": "context", "term_b": "", "value": float(model["calibration"][1])},
    ])
    return rows


def _model_hash(model: dict) -> str:
    payload = {
        "descriptors": list(model["descriptors"]),
        "membership": {key: np.asarray(value).tolist() for key, value in model["membership"].items()},
        "calibration": np.asarray(model["calibration"]).tolist(),
        "capacity": {
            "fit_success": bool(model["capacity"]["fit_success"]),
            "singletons": model["capacity"]["singletons"],
            "pairs": model["capacity"]["pairs"],
            "capacity_table": model["capacity"]["capacity_table"],
        },
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _save_soft_png(score: np.ndarray, path: Path) -> None:
    array = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(array)) or float(array.min()) < 0.0 or float(array.max()) > 1.0 + 1e-6:
        raise RuntimeError(f"invalid candidate score for {path.stem}")
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.rint(np.clip(array, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L").save(path)


def _official_manifest(out: Path, experiment_id: str) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": experiment_id,
            "export": {
                "script": "automation/stage20_candidate_venv_launcher.py",
                "args": [
                    "--candidate-id", experiment_id,
                    "--export-bsds", "--image-dir", "{image_dir}",
                    "--output-dir", "{output_dir}", "--split", "{split}"
                ],
                "timeout_minutes": 360,
            },
        }],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _fit_full(args: argparse.Namespace, descriptors: tuple[str, ...]):
    root = ensure_uded(Path(args.uded_root))
    raw = resize_items(_load_overlap_clean_uded(root), args.max_side_development)
    items, names = prepare(raw)
    _attach_descriptors(items, descriptors, "STAGE20_FULL_FIT_DESCRIPTOR")
    positive, _ = learn_banks(items, names, args.seed, args.max_positive, args.max_negative, args.max_abs_corr)
    compact = _ordered_compact(positive)
    model = _fit_candidate(items, descriptors, args.seed)
    return items, names, compact, model


def export_bsds(args: argparse.Namespace, spec: dict) -> int:
    descriptors = tuple(spec["descriptors"])
    training, names, compact, model = _fit_full(args, descriptors)
    image_paths = sorted(Path(args.image_dir).glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {args.image_dir}")
    output_dir = Path(args.output_dir)
    rows = []
    for number, path in enumerate(image_paths, start=1):
        print(f"STAGE20_BSDS_EXPORT {number:03d}/{len(image_paths):03d} {path.stem}", flush=True)
        prepared, candidate_names = prepare([{"id": path.stem, "img": imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        _attach_descriptors(prepared, descriptors, "STAGE20_BSDS_DESCRIPTOR")
        control, candidate, _context, runtimes = _score_pairs(prepared, names, compact, model)
        _save_soft_png(candidate[0], output_dir / f"{path.stem}.png")
        rows.append({
            "image_id": path.stem,
            "descriptor_runtime_seconds": prepared[0]["stage20_descriptor_runtime_seconds"],
            "score_runtime_seconds": runtimes[0],
            "mean_abs_score_delta": float(np.mean(np.abs(candidate[0] - control[0]))),
            "support_equal": bool(np.array_equal(candidate[0] > 0.0, control[0] > 0.0)),
        })
    pd.DataFrame(rows).to_csv(output_dir / "runtime.csv", index=False)
    metadata = {
        "method": spec["experiment_id"],
        "candidate_label": spec["label"],
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution_output": True,
        "development_source": "14-image overlap-clean UDED selection only",
        "excluded_lineage": "03-35028 / protected BSDS500-test 35028",
        "descriptors": list(descriptors),
        "aggregation": "fold-fitted monotone 2-additive Choquet",
        "scalar_calibration": np.asarray(model["calibration"]).tolist(),
        "capacity_ridge": CAPACITY_RIDGE,
        "capacity_samples": CAPACITY_SAMPLES,
        "gate_strength": STRENGTH,
        "gate_floor": FLOOR,
        "capacity_fit_success": bool(model["capacity"]["fit_success"]),
        "model_sha256": _model_hash(model),
        "training_images": len(training),
        "output": "direct 8-bit soft PNG without per-image normalization",
        "n_maps": len(image_paths),
    }
    (output_dir / "export_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return 0


def run_experiment(args: argparse.Namespace, spec: dict) -> int:
    experiment_id = spec["experiment_id"]
    descriptors = tuple(spec["descriptors"])
    out = Path(args.out) if args.out else ROOT / "results" / "local_dev" / experiment_id
    out.mkdir(parents=True, exist_ok=True)

    raw = resize_items(_load_overlap_clean_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    selection, names = prepare(raw)
    _attach_descriptors(selection, descriptors, "STAGE20_DESCRIPTOR")
    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)

    variants = ("compact_mfi", spec["label"])
    counts: dict[str, list] = defaultdict(list)
    fold_f1: dict[str, list[float]] = defaultdict(list)
    thresholds: dict[str, list[float]] = defaultdict(list)
    fold_rows, image_rows, parameter_rows = [], [], []
    runtime_rows = [{
        "phase": "descriptor",
        "image_id": item["id"],
        "descriptor_runtime_seconds": float(item["stage20_descriptor_runtime_seconds"]),
    } for item in selection]
    support_violations = 0
    first_predictions = {name: {} for name in variants}
    first_scores: dict[int, np.ndarray] = {}
    model_hashes = []
    fit_successes = 0

    for split_no, (repeat, fold, train_indices, valid_indices) in enumerate(splits, start=1):
        train = [selection[index] for index in train_indices]
        valid = [selection[index] for index in valid_indices]
        positive, _ = learn_banks(
            train, names, args.seed + 10000 * repeat + fold,
            args.max_positive, args.max_negative, args.max_abs_corr,
        )
        compact = _ordered_compact(positive)
        fit_started = time.perf_counter()
        model = _fit_candidate(train, descriptors, args.seed + 20000 * repeat + fold)
        fit_seconds = time.perf_counter() - fit_started
        model_hashes.append(_model_hash(model))
        fit_successes += int(bool(model["capacity"]["fit_success"]))
        parameter_rows.extend(_model_rows(model, repeat + 1, fold + 1))
        train_maps = _score_pairs(train, names, compact, model)
        valid_maps = _score_pairs(valid, names, compact, model)
        support_violations += sum(
            not np.array_equal(control > 0.0, candidate > 0.0)
            for maps in (train_maps, valid_maps)
            for control, candidate in zip(maps[0], maps[1])
        )
        runtime_rows.append({
            "phase": "fold_fit_and_score",
            "repeat": repeat + 1,
            "fold": fold + 1,
            "capacity_fit_seconds": float(fit_seconds),
            "train_score_seconds": float(sum(train_maps[3])),
            "validation_score_seconds": float(sum(valid_maps[3])),
            "model_sha256": model_hashes[-1],
        })
        print(f"STAGE20_SPLIT {split_no:02d}/{len(splits):02d} repeat={repeat + 1} fold={fold + 1}", flush=True)
        for variant_index, variant in enumerate(variants):
            threshold = float(selection_metric(train_maps[variant_index], train, args.thresholds)["threshold"])
            metric, event_counts, per_image = fixed_eval(valid_maps[variant_index], valid, threshold)
            counts[variant].extend(event_counts)
            fold_f1[variant].append(float(metric["F1"]))
            thresholds[variant].append(threshold)
            fold_rows.append({
                "repeat": repeat + 1,
                "fold": fold + 1,
                "variant": variant,
                "train_threshold": threshold,
                "capacity_fit_success": bool(model["capacity"]["fit_success"]),
                "model_sha256": model_hashes[-1],
                **metric,
            })
            image_rows.extend({"repeat": repeat + 1, "fold": fold + 1, "variant": variant, **row} for row in per_image)
            if repeat == 0:
                for global_index, score in zip(valid_indices, valid_maps[variant_index]):
                    first_predictions[variant][int(global_index)] = score >= threshold
                    if variant_index == 1:
                        first_scores[int(global_index)] = score

    aggregate = {name: aggregate_counts(counts[name]) for name in variants}
    incumbent_folds = np.asarray(fold_f1[variants[0]], dtype=float)
    candidate_folds = np.asarray(fold_f1[variants[1]], dtype=float)
    deltas = {
        "aggregate_F1": float(aggregate[variants[1]]["F1"] - aggregate[variants[0]]["F1"]),
        "aggregate_precision": float(aggregate[variants[1]]["precision"] - aggregate[variants[0]]["precision"]),
        "aggregate_recall": float(aggregate[variants[1]]["recall"] - aggregate[variants[0]]["recall"]),
        "mean_fold_F1": float(np.mean(candidate_folds - incumbent_folds)),
        "fold_wins": int(np.sum(candidate_folds > incumbent_folds)),
        "capacity_fit_successes": int(fit_successes),
        "support_violations": int(support_violations),
    }
    uded_gate = bool(
        deltas["aggregate_F1"] >= 0.002
        and deltas["aggregate_precision"] >= 0.0
        and deltas["aggregate_recall"] >= -0.003
        and deltas["mean_fold_F1"] >= 0.0
        and deltas["fold_wins"] >= 9
        and deltas["capacity_fit_successes"] == 15
        and deltas["support_violations"] == 0
    )

    ranking = []
    for variant in variants:
        values = np.asarray(fold_f1[variant], dtype=float)
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
    pd.DataFrame(parameter_rows).to_csv(out / "capacity_parameters.csv", index=False)
    pd.DataFrame(runtime_rows).to_csv(out / "runtime.csv", index=False)

    if any(len(first_predictions[name]) != len(selection) for name in variants) or len(first_scores) != len(selection):
        raise RuntimeError("first-repeat out-of-fold preview predictions are incomplete")
    rows = [[
        selection[position]["img"],
        selection[position]["gt"],
        first_predictions[variants[0]][position],
        first_predictions[variants[1]][position],
        first_scores[position],
    ] for position in PREVIEW_POSITIONS]
    preview_path = write_panel_grid(out / "best_method_preview.png", rows)
    manifest_path = _official_manifest(out, experiment_id)
    summary = {
        "stage": experiment_id,
        "role": "bounded_stage20_candidate",
        "queue_order": spec["order"],
        "architecture_changed": False,
        "protected_split_used": False,
        "known_overlap_excluded_without_blob_read": "03-35028 / BSDS500-test 35028",
        "candidate": {
            "label": spec["label"],
            "descriptors": list(descriptors),
            "aggregation": "fold-fitted monotone 2-additive Choquet",
            "membership": "Stage-19D training-fold median/IQR logistic mapping",
            "calibration": "Stage-19D class-balanced scalar logistic calibration fitted inside the outer training fold",
            "capacity_ridge": CAPACITY_RIDGE,
            "capacity_samples": CAPACITY_SAMPLES,
            "unchanged": [
                "median conditioning",
                "grayscale Scharr+NMS localizer",
                "context gate strength 2.0 and floor 0.10",
                "fold-fitted threshold grid",
            ],
        },
        "datasets": {
            "UDED_selection_overlap_clean": {"n_images": len(selection), "repeats": args.repeats, "folds": args.folds},
            "BSDS500_validation": {"role": "official development attachment", "status": "pending controller attachment"},
        },
        "promotion_rule": (
            "Conjunctive: UDED aggregate F1 delta >= +0.002, precision delta >= 0, "
            "recall delta >= -0.003, mean paired fold-F1 delta >= 0, at least 9/15 "
            "fold wins, 15/15 converged capacity fits, exact score-support preservation, "
            "completed official BSDS500-validation attachment with ODS delta >= +0.002 "
            "and nonnegative OIS/AP deltas."
        ),
        "uded_gate": {"met": uded_gate, "deltas": deltas},
        "metrics": aggregate,
        "promotion_pending_official_bsds_val": True,
        "official_evaluation": {
            "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
            "required_before_promotion": True,
            "stage15a_caveat": "unmodified Windows matcher remains stochastic and reference-uncertified; fixed-seed diagnostic matcher is forbidden",
        },
        "visual_preview": {
            "file": preview_path.name,
            "selection": "fixed overlap-clean UDED positions 1, 7, and 14",
            "columns": ["input", "ground_truth", "compact_MFI_OOF_prediction", "candidate_OOF_prediction", "candidate_continuous_score"],
            "use": "documentary only; not an optimization signal",
        },
        "frozen_queue": "automation/stage20_frozen_queue.json",
        "files": [
            "summary.json", "variant_ranking.csv", "fold_results.csv",
            "per_image_metrics.csv", "capacity_parameters.csv", "runtime.csv",
            "best_method_preview.png", "official_eval_manifest.json",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"STAGE20_CANDIDATE_COMPLETE {experiment_id}", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--uded-root", default=str(DEFAULT_UDED))
    parser.add_argument("--out")
    parser.add_argument("--max-side", type=int, default=256)
    parser.add_argument("--thresholds", type=int, default=41)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-positive", type=int, default=10)
    parser.add_argument("--max-negative", type=int, default=8)
    parser.add_argument("--max-abs-corr", type=float, default=0.88)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--export-bsds", action="store_true")
    parser.add_argument("--image-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--split", default="val")
    parser.add_argument("--max-side-development", type=int, default=256)
    args = parser.parse_args()
    spec = _spec(args.candidate_id)
    if args.export_bsds:
        if not args.image_dir or not args.output_dir:
            parser.error("--export-bsds requires --image-dir and --output-dir")
        return export_bsds(args, spec)
    return run_experiment(args, spec)


if __name__ == "__main__":
    raise SystemExit(main())
