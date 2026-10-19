from __future__ import annotations

"""Stage 19B: frozen-descriptor relevance atlas on development-only data.

This is an explanatory experiment, not a detector or feature-selection stage.
It reads pinned BSDS500 *train* blobs directly from the local Git object store,
preserves every human boundary annotation, and uses overlap-clean UDED
selection as the second development domain.  BSDS validation/test image and
ground-truth bytes are never read.
"""

from pathlib import Path
import argparse
import hashlib
import io
import json
import math
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage as ndi
from scipy.io import loadmat

from benchmark_uded import DEFAULT_UDED, SCALES, load_uded
from run_stage12b_fuzzy_signature import ensure_uded
from src.bsds import _extract_boundaries
from src.conditioning import apply_conditioning
from src.discriminative_patch_recurrence import discriminative_patch_recurrence_evidence
from src.edge_signature_relational import relational_signature_tensor
from src.frei_chen_subspace import frei_chen_edge_subspace_evidence
from src.image_torque_context import image_torque_context
from src.local_brightness_entropy import local_brightness_entropy_deficit
from src.pipeline import precompute_multiscale_features
from src.pmi_dependency_context import pmi_dependency_context
from src.semiglobal_changepoint import semiglobal_changepoint_evidence
from src.structure_tensor_orientation import structure_tensor_orientation_evidence


EXPERIMENT_ID = "stage19b_descriptor_relevance_atlas"
OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
BSDS_REPO = ROOT / "evaluation" / "bsds_official" / "vendor" / "BSDS500"
BSDS_COMMIT = "a04b7c6c3a9f0ace74bf205c72a43d32e1c72722"
MAX_DIST = 0.0075
SEED = 20261019
SAMPLES_PER_IMAGE = 4096
BOOTSTRAP_REPLICATES = 1000
PROBABILITY_BINS = 12
PREVIEW_POSITIONS = (0, 99, 199)

DESCRIPTORS = (
    "gabor4_s5",
    "hessian_s7",
    "gabor4_s13",
    "hessian_s13",
    "gabor4_scale_persistence",
    "structure_tensor_coherence",
    "brightness_entropy",
    "directional_patch_recurrence",
    "semiglobal_changepoint",
    "frei_chen_edge_subspace",
    "pmi_dependency",
    "image_torque_closure",
)


def _run_git(*args: str, binary: bool = False) -> str | bytes:
    command = ["git", "-C", str(BSDS_REPO), *args]
    completed = subprocess.run(command, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Git command failed ({completed.returncode}): {command!r}\n"
            f"{completed.stderr.decode('utf-8', errors='replace')}"
        )
    return completed.stdout if binary else completed.stdout.decode("utf-8")


def _verify_bsds_source() -> None:
    if not (BSDS_REPO / ".git").exists():
        raise RuntimeError(f"pinned BSDS repository is missing: {BSDS_REPO}")
    head = str(_run_git("rev-parse", "HEAD")).strip()
    if head != BSDS_COMMIT:
        raise RuntimeError(f"BSDS commit mismatch: expected {BSDS_COMMIT}, got {head}")


def _tree_paths(prefix: str) -> list[str]:
    lines = str(
        _run_git("ls-tree", "-r", "--name-only", BSDS_COMMIT, prefix)
    ).splitlines()
    return sorted(line.strip() for line in lines if line.strip())


def _train_blob(path: str) -> bytes:
    normalized = str(path).replace("\\", "/")
    if "/train/" not in normalized:
        raise RuntimeError(f"Stage 19B refuses non-train BSDS blob access: {normalized}")
    return bytes(_run_git("show", f"{BSDS_COMMIT}:{normalized}", binary=True))


def _load_bsds_train(image_id: str) -> tuple[np.ndarray, list[np.ndarray]]:
    image_bytes = _train_blob(f"BSDS500/data/images/train/{image_id}.jpg")
    gt_bytes = _train_blob(f"BSDS500/data/groundTruth/train/{image_id}.mat")
    with Image.open(io.BytesIO(image_bytes)) as handle:
        image = np.asarray(handle.convert("RGB"))
    boundaries = [
        np.asarray(value, dtype=bool)
        for value in _extract_boundaries(loadmat(io.BytesIO(gt_bytes)))
    ]
    if not boundaries:
        raise RuntimeError(f"no BSDS annotations parsed for train image {image_id}")
    if any(boundary.shape != boundaries[0].shape for boundary in boundaries):
        raise RuntimeError(f"annotation shape mismatch for BSDS train image {image_id}")
    if image.shape[:2] != boundaries[0].shape:
        raise RuntimeError(f"image/annotation shape mismatch for BSDS train image {image_id}")
    return image, boundaries


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _overlap_clean_uded(root: Path) -> tuple[list[dict], dict[str, object]]:
    all_items = load_uded(ensure_uded(root))
    selection = all_items[0::2]
    split_ids: dict[str, set[str]] = {}
    for split in ("train", "val", "test"):
        prefix = f"BSDS500/data/images/{split}"
        split_ids[split] = {Path(path).stem for path in _tree_paths(prefix)}

    rows: list[dict[str, object]] = []
    retained: list[dict] = []
    for item in selection:
        image_id = str(item["id"])
        hits = [
            {"bsds_id": bsds_id, "split": split}
            for split, identifiers in split_ids.items()
            for bsds_id in sorted(identifiers)
            if bsds_id in image_id
        ]
        excluded = bool(hits)
        image_path = root / str(item["img_path"])
        rows.append(
            {
                "uded_id": image_id,
                "selection_position": int(item["index"]),
                "image_path": str(item["img_path"]).replace("\\", "/"),
                "image_sha256": _sha256(image_path),
                "excluded": excluded,
                "reason": "BSDS filename-lineage overlap" if excluded else "none",
                "bsds_matches": hits,
            }
        )
        if not excluded:
            retained.append(item)

    manifest = {
        "schema_version": 1,
        "policy": "Stage 19 overlap-clean UDED selection",
        "detection": (
            "Exact BSDS canonical image identifiers were matched against UDED "
            "selection filenames using only the pinned Git tree. No BSDS val/test "
            "image or ground-truth blob was read."
        ),
        "bsds_commit": BSDS_COMMIT,
        "selection_count_before": len(selection),
        "selection_count_after": len(retained),
        "excluded_count": len(selection) - len(retained),
        "records": rows,
    }
    return retained, manifest


def _incumbent_maps(pre_img: np.ndarray) -> dict[str, np.ndarray]:
    features, feature_names = precompute_multiscale_features(
        pre_img, SCALES, feature_mode="oriented_ms"
    )
    tensor, names = relational_signature_tensor(
        {"pre_img": pre_img, "features": features}, feature_names
    )
    index = {name: position for position, name in enumerate(names)}
    missing = [name for name in DESCRIPTORS[:5] if name not in index]
    if missing:
        raise RuntimeError(f"frozen incumbent descriptor(s) missing: {missing}")
    return {
        name: np.asarray(tensor[..., index[name]], dtype=np.float32)
        for name in DESCRIPTORS[:5]
    }


def _descriptor_maps(image: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, float]]:
    pre_img = apply_conditioning(image, "median", size=3)
    started = time.perf_counter()
    maps = _incumbent_maps(pre_img)
    runtimes = {"incumbent_five_joint_seconds": time.perf_counter() - started}

    functions = (
        ("structure_tensor_coherence", lambda x: (structure_tensor_orientation_evidence(x), {})),
        ("brightness_entropy", local_brightness_entropy_deficit),
        ("directional_patch_recurrence", discriminative_patch_recurrence_evidence),
        ("semiglobal_changepoint", semiglobal_changepoint_evidence),
        ("frei_chen_edge_subspace", frei_chen_edge_subspace_evidence),
        ("pmi_dependency", pmi_dependency_context),
        ("image_torque_closure", image_torque_context),
    )
    for name, function in functions:
        started = time.perf_counter()
        cue, _diagnostics = function(pre_img)
        runtimes[f"{name}_seconds"] = time.perf_counter() - started
        cue = np.asarray(cue, dtype=np.float32)
        if cue.shape != pre_img.shape or not np.all(np.isfinite(cue)):
            raise RuntimeError(f"invalid frozen descriptor map: {name}")
        maps[name] = cue

    if tuple(maps) != DESCRIPTORS:
        raise RuntimeError(f"descriptor pool drifted: {tuple(maps)}")
    return np.asarray(pre_img, dtype=np.float32), maps, runtimes


def _targets(boundaries: list[np.ndarray]) -> dict[str, np.ndarray | list[np.ndarray] | float]:
    stack = np.stack([np.asarray(value, dtype=bool) for value in boundaries], axis=0)
    height, width = stack.shape[1:]
    tolerance = max(1.0, MAX_DIST * math.hypot(height, width))
    distances = np.stack([ndi.distance_transform_edt(~value) for value in stack], axis=0)
    soft_per_annotator = np.clip(1.0 - distances / tolerance, 0.0, 1.0)
    return {
        "annotations": [stack[i] for i in range(stack.shape[0])],
        "exact_consensus": np.mean(stack, axis=0, dtype=np.float64),
        "exact_union": np.any(stack, axis=0),
        "tolerant_soft": np.mean(soft_per_annotator, axis=0),
        "tolerant_union": np.any(distances <= tolerance, axis=0),
        "tolerance_pixels": float(tolerance),
    }


def _sample_indices(dataset: str, image_id: str, size: int, count: int) -> np.ndarray:
    token = hashlib.sha256(f"{SEED}:{dataset}:{image_id}".encode("utf-8")).digest()
    rng = np.random.default_rng(int.from_bytes(token[:8], "little"))
    return np.sort(rng.choice(size, size=min(int(count), size), replace=False))


def _auc(labels: np.ndarray, scores: np.ndarray) -> float:
    y = np.asarray(labels, dtype=bool)
    x = np.asarray(scores, dtype=np.float64)
    positive = int(np.sum(y))
    negative = int(y.size - positive)
    if positive == 0 or negative == 0:
        return float("nan")
    order = np.argsort(x, kind="mergesort")
    sorted_x = x[order]
    ranks = np.empty(x.size, dtype=np.float64)
    start = 0
    while start < x.size:
        stop = start + 1
        while stop < x.size and sorted_x[stop] == sorted_x[start]:
            stop += 1
        ranks[order[start:stop]] = 0.5 * (start + stop - 1) + 1.0
        start = stop
    return float((np.sum(ranks[y]) - positive * (positive + 1) / 2.0) / (positive * negative))


def _average_precision(labels: np.ndarray, scores: np.ndarray) -> float:
    y = np.asarray(labels, dtype=bool)
    x = np.asarray(scores, dtype=np.float64)
    positives = int(np.sum(y))
    if positives == 0:
        return float("nan")
    order = np.argsort(-x, kind="mergesort")
    ranked_y = y[order]
    ranked_x = x[order]
    cumulative = np.cumsum(ranked_y)
    ends = np.r_[np.flatnonzero(np.diff(ranked_x) != 0), len(ranked_x) - 1]
    precision = cumulative[ends] / (ends + 1)
    recall = cumulative[ends] / positives
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))


def _mutual_information(labels: np.ndarray, scores: np.ndarray, bins: int = 16) -> float:
    y = np.asarray(labels, dtype=np.uint8)
    x = np.asarray(scores, dtype=np.float64)
    if len(np.unique(y)) < 2 or len(np.unique(x)) < 2:
        return 0.0
    edges = np.unique(np.quantile(x, np.linspace(0.0, 1.0, int(bins) + 1)))
    if edges.size < 3:
        return 0.0
    xb = np.searchsorted(edges[1:-1], x, side="right")
    table = np.zeros((edges.size - 1, 2), dtype=np.float64)
    np.add.at(table, (xb, y), 1.0)
    joint = table / max(float(np.sum(table)), 1.0)
    px = np.sum(joint, axis=1, keepdims=True)
    py = np.sum(joint, axis=0, keepdims=True)
    expected = px @ py
    valid = joint > 0.0
    return float(np.sum(joint[valid] * np.log(joint[valid] / expected[valid])))


def _metric_row(
    dataset: str,
    image_id: str,
    descriptor: str,
    target_view: str,
    labels: np.ndarray,
    scores: np.ndarray,
    annotator_index: int | None = None,
) -> dict[str, object]:
    y = np.asarray(labels, dtype=bool)
    x = np.asarray(scores, dtype=np.float64)
    auc = _auc(y, x)
    positive = x[y]
    negative = x[~y]
    q25, q75 = np.quantile(x, (0.25, 0.75))
    scale = max(float(q75 - q25), 1.0e-12)
    effect = (
        float((np.median(positive) - np.median(negative)) / scale)
        if positive.size and negative.size
        else float("nan")
    )
    return {
        "dataset": dataset,
        "image_id": image_id,
        "descriptor": descriptor,
        "target_view": target_view,
        "annotator_index": annotator_index,
        "sample_count": int(y.size),
        "positive_count": int(np.sum(y)),
        "positive_fraction": float(np.mean(y)),
        "roc_auc": auc,
        "average_precision": _average_precision(y, x),
        "mutual_information_nats": _mutual_information(y, x),
        "rank_biserial_effect": float(2.0 * auc - 1.0) if np.isfinite(auc) else float("nan"),
        "robust_median_effect": effect,
    }


def _process_record(
    dataset: str,
    image_id: str,
    image: np.ndarray,
    boundaries: list[np.ndarray],
) -> tuple[pd.DataFrame, list[dict[str, object]], list[dict[str, object]], dict[str, np.ndarray], np.ndarray]:
    pre_img, maps, runtimes = _descriptor_maps(image)
    target = _targets(boundaries)
    indices = _sample_indices(dataset, image_id, pre_img.size, SAMPLES_PER_IMAGE)
    sample = {
        "dataset": np.full(indices.size, dataset, dtype=object),
        "image_id": np.full(indices.size, image_id, dtype=object),
        "exact_consensus": np.asarray(target["exact_consensus"]).ravel()[indices],
        "exact_union": np.asarray(target["exact_union"]).ravel()[indices].astype(np.uint8),
        "tolerant_soft": np.asarray(target["tolerant_soft"]).ravel()[indices],
        "tolerant_union": np.asarray(target["tolerant_union"]).ravel()[indices].astype(np.uint8),
        "annotation_count": np.full(indices.size, len(boundaries), dtype=np.uint8),
    }
    for descriptor, values in maps.items():
        sample[descriptor] = np.asarray(values).ravel()[indices].astype(np.float32)
    frame = pd.DataFrame(sample)

    metric_rows: list[dict[str, object]] = []
    for descriptor in DESCRIPTORS:
        values = frame[descriptor].to_numpy(dtype=np.float64)
        for view in ("exact_union", "tolerant_union"):
            metric_rows.append(
                _metric_row(dataset, image_id, descriptor, view, frame[view], values)
            )
        for annotator_index, annotation in enumerate(target["annotations"]):
            metric_rows.append(
                _metric_row(
                    dataset,
                    image_id,
                    descriptor,
                    "annotator_exact",
                    np.asarray(annotation).ravel()[indices],
                    values,
                    annotator_index,
                )
            )

    support_rows = [
        {
            "dataset": dataset,
            "image_id": image_id,
            "annotator_index": index,
            "boundary_pixels": int(np.sum(annotation)),
            "boundary_fraction": float(np.mean(annotation)),
            "tolerance_pixels": float(target["tolerance_pixels"]),
        }
        for index, annotation in enumerate(target["annotations"])
    ]
    runtime_rows = [
        {
            "dataset": dataset,
            "image_id": image_id,
            "descriptor": name.removesuffix("_seconds"),
            "runtime_seconds": float(value),
        }
        for name, value in runtimes.items()
    ]
    return frame, metric_rows, support_rows + runtime_rows, maps, pre_img


def _distribution_table(samples: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    quantiles = (0.05, 0.25, 0.5, 0.75, 0.95)
    for dataset, table in samples.groupby("dataset", sort=True):
        for target_view in ("exact_union", "tolerant_union"):
            labels = table[target_view].to_numpy(dtype=bool)
            for descriptor in DESCRIPTORS:
                values = table[descriptor].to_numpy(dtype=np.float64)
                for class_name, mask in (("edge", labels), ("non_edge", ~labels)):
                    selected = values[mask]
                    q = np.quantile(selected, quantiles) if selected.size else np.full(5, np.nan)
                    rows.append(
                        {
                            "dataset": dataset,
                            "target_view": target_view,
                            "descriptor": descriptor,
                            "class": class_name,
                            "count": int(selected.size),
                            "mean": float(np.mean(selected)) if selected.size else float("nan"),
                            "std": float(np.std(selected)) if selected.size else float("nan"),
                            **{f"q{int(level * 100):02d}": float(value) for level, value in zip(quantiles, q)},
                        }
                    )
    return pd.DataFrame(rows)


def _pav(values: np.ndarray, weights: np.ndarray, increasing: bool) -> np.ndarray:
    y = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    signed = y if increasing else -y
    levels: list[float] = []
    masses: list[float] = []
    starts: list[int] = []
    ends: list[int] = []
    for index, (level, mass) in enumerate(zip(signed, w)):
        levels.append(float(level)); masses.append(float(mass)); starts.append(index); ends.append(index + 1)
        while len(levels) >= 2 and levels[-2] > levels[-1]:
            combined_mass = masses[-2] + masses[-1]
            combined_level = (masses[-2] * levels[-2] + masses[-1] * levels[-1]) / combined_mass
            levels[-2:] = [combined_level]
            masses[-2:] = [combined_mass]
            ends[-2:] = [ends[-1]]
            starts.pop()
    fitted = np.empty_like(y)
    for level, start, end in zip(levels, starts, ends):
        fitted[start:end] = level
    return fitted if increasing else -fitted


def _probability_curves(samples: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dataset, table in samples.groupby("dataset", sort=True):
        for descriptor in DESCRIPTORS:
            x = table[descriptor].to_numpy(dtype=np.float64)
            edges = np.unique(np.quantile(x, np.linspace(0.0, 1.0, PROBABILITY_BINS + 1)))
            if edges.size < 3:
                continue
            bins = np.searchsorted(edges[1:-1], x, side="right")
            aggregate: list[dict[str, float]] = []
            for bin_index in range(edges.size - 1):
                mask = bins == bin_index
                if not np.any(mask):
                    continue
                aggregate.append(
                    {
                        "bin": float(bin_index),
                        "count": float(np.sum(mask)),
                        "descriptor_mean": float(np.mean(x[mask])),
                        "exact_probability": float(np.mean(table.loc[mask, "exact_consensus"])),
                        "tolerant_probability": float(np.mean(table.loc[mask, "tolerant_soft"])),
                    }
                )
            counts = np.asarray([row["count"] for row in aggregate], dtype=np.float64)
            for target_name in ("exact_probability", "tolerant_probability"):
                raw = np.asarray([row[target_name] for row in aggregate], dtype=np.float64)
                increasing = _pav(raw, counts, True)
                decreasing = _pav(raw, counts, False)
                inc_error = float(np.sum(counts * np.square(raw - increasing)))
                dec_error = float(np.sum(counts * np.square(raw - decreasing)))
                direction = "increasing" if inc_error <= dec_error else "decreasing"
                fitted = increasing if direction == "increasing" else decreasing
                for row, fitted_value in zip(aggregate, fitted):
                    rows.append(
                        {
                            "dataset": dataset,
                            "descriptor": descriptor,
                            "target": target_name,
                            "monotone_direction": direction,
                            "bin": int(row["bin"]),
                            "count": int(row["count"]),
                            "descriptor_mean": row["descriptor_mean"],
                            "raw_probability": row[target_name],
                            "monotone_probability": float(fitted_value),
                        }
                    )
    return pd.DataFrame(rows)


def _consensus_strata(samples: pd.DataFrame) -> pd.DataFrame:
    bsds = samples[samples["dataset"] == "BSDS500_train"].copy()
    labels = ("zero", "low_(0,.25]", "medium_(.25,.5]", "high_(.5,.75]", "very_high_(.75,1]")
    bins = np.asarray([-1.0e-12, 0.0, 0.25, 0.5, 0.75, 1.0 + 1.0e-12])
    bsds["consensus_stratum"] = pd.cut(
        bsds["exact_consensus"], bins=bins, labels=labels, include_lowest=True
    )
    rows: list[dict[str, object]] = []
    for stratum, table in bsds.groupby("consensus_stratum", observed=False, sort=False):
        for descriptor in DESCRIPTORS:
            values = table[descriptor].to_numpy(dtype=np.float64)
            rows.append(
                {
                    "consensus_stratum": str(stratum),
                    "descriptor": descriptor,
                    "count": int(values.size),
                    "mean": float(np.mean(values)) if values.size else float("nan"),
                    "median": float(np.median(values)) if values.size else float("nan"),
                    "q25": float(np.quantile(values, 0.25)) if values.size else float("nan"),
                    "q75": float(np.quantile(values, 0.75)) if values.size else float("nan"),
                }
            )
    return pd.DataFrame(rows)


def _bootstrap_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    eligible = metrics[metrics["target_view"].isin(("exact_union", "tolerant_union"))]
    columns = ("roc_auc", "average_precision", "mutual_information_nats", "rank_biserial_effect", "robust_median_effect")
    rows: list[dict[str, object]] = []
    for (dataset, descriptor, target_view), table in eligible.groupby(
        ["dataset", "descriptor", "target_view"], sort=True
    ):
        table = table.sort_values("image_id").reset_index(drop=True)
        rng_seed = int.from_bytes(
            hashlib.sha256(f"{SEED}:{dataset}:{descriptor}:{target_view}".encode()).digest()[:8],
            "little",
        )
        rng = np.random.default_rng(rng_seed)
        n_images = len(table)
        draws = rng.integers(0, n_images, size=(BOOTSTRAP_REPLICATES, n_images))
        for column in columns:
            values = table[column].to_numpy(dtype=np.float64)
            finite = np.isfinite(values)
            observed = float(np.nanmean(values))
            bootstrap = np.empty(BOOTSTRAP_REPLICATES, dtype=np.float64)
            for replicate, ids in enumerate(draws):
                chosen = values[ids]
                bootstrap[replicate] = np.nanmean(chosen)
            rows.append(
                {
                    "dataset": dataset,
                    "descriptor": descriptor,
                    "target_view": target_view,
                    "metric": column,
                    "image_count": int(n_images),
                    "finite_image_count": int(np.sum(finite)),
                    "mean": observed,
                    "bootstrap_ci_low": float(np.nanquantile(bootstrap, 0.025)),
                    "bootstrap_ci_high": float(np.nanquantile(bootstrap, 0.975)),
                    "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                }
            )
    return pd.DataFrame(rows)


def _write_preview(records: list[tuple[str, np.ndarray, np.ndarray, dict[str, np.ndarray]]]) -> dict[str, object]:
    columns = ("input", "mean_human_GT", *DESCRIPTORS)
    fig, axes = plt.subplots(len(records), len(columns), figsize=(2.2 * len(columns), 2.5 * len(records)), squeeze=False)
    for row, (image_id, image, consensus, maps) in enumerate(records):
        panels = (image, consensus, *(maps[name] for name in DESCRIPTORS))
        for column, (name, panel) in enumerate(zip(columns, panels)):
            axis = axes[row, column]
            axis.imshow(panel, cmap=None if column == 0 else "magma", vmin=None if column == 0 else 0.0, vmax=None if column == 0 else 1.0)
            if row == 0:
                axis.set_title(name.replace("_", "\n"), fontsize=7)
            if column == 0:
                axis.set_ylabel(image_id)
            axis.set_xticks([]); axis.set_yticks([])
    fig.suptitle("Stage 19B frozen descriptor atlas; BSDS500-train positions 1, 100, 200", fontsize=12)
    fig.tight_layout()
    path = OUT / "best_method_preview.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "selection": "sorted BSDS500-train positions 1, 100, and 200, fixed before results",
        "panel_order": list(columns),
        "optimization_use": "none; deterministic qualitative atlas only",
    }


def _write_official_manifest() -> None:
    manifest = {
        "schema_version": 1,
        "split": "train",
        "include_incumbent": True,
        "methods": [],
        "analysis_only_note": (
            "Stage 19B creates descriptor diagnostics rather than a detector map. "
            "The default-on attachment therefore scores only the unchanged incumbent "
            "on allowed BSDS train; it cannot promote or select a descriptor."
        ),
    }
    (OUT / "official_eval_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def _smoke() -> int:
    size = 65
    synthetic = np.zeros((size, size, 3), dtype=np.uint8)
    synthetic[:, size // 2 :, :] = 255
    _pre, maps, runtimes = _descriptor_maps(synthetic)
    if tuple(maps) != DESCRIPTORS or any(value.shape != (size, size) for value in maps.values()):
        raise RuntimeError("Stage 19B smoke descriptor contract failed")
    if not all(np.isfinite(value) for value in runtimes.values()):
        raise RuntimeError("Stage 19B smoke runtime contract failed")
    print("STAGE19B_DESCRIPTOR_RELEVANCE_ATLAS_SMOKE_OK")
    return 0


def main() -> int:
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--uded-root", default=str(DEFAULT_UDED))
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        return _smoke()

    OUT = Path(args.out)
    OUT.mkdir(parents=True, exist_ok=True)
    _verify_bsds_source()
    uded_items, overlap_manifest = _overlap_clean_uded(Path(args.uded_root))
    (OUT / "overlap_clean_dataset_manifest.json").write_text(
        json.dumps(overlap_manifest, indent=2), encoding="utf-8"
    )

    train_paths = _tree_paths("BSDS500/data/images/train")
    bsds_ids = [Path(path).stem for path in train_paths if path.lower().endswith(".jpg")]
    if len(bsds_ids) != 200:
        raise RuntimeError(f"expected 200 pinned BSDS train images, found {len(bsds_ids)}")

    sample_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []
    support_rows: list[dict[str, object]] = []
    runtime_rows: list[dict[str, object]] = []
    preview_records: list[tuple[str, np.ndarray, np.ndarray, dict[str, np.ndarray]]] = []

    for position, image_id in enumerate(bsds_ids):
        print(f"STAGE19B_BSDS_TRAIN {position + 1:03d}/{len(bsds_ids):03d} {image_id}", flush=True)
        image, boundaries = _load_bsds_train(image_id)
        frame, image_metrics, mixed_rows, maps, _pre = _process_record(
            "BSDS500_train", image_id, image, boundaries
        )
        sample_frames.append(frame); metric_rows.extend(image_metrics)
        support_rows.extend(row for row in mixed_rows if "annotator_index" in row)
        runtime_rows.extend(row for row in mixed_rows if "runtime_seconds" in row)
        if position in PREVIEW_POSITIONS:
            preview_records.append(
                (image_id, image, np.mean(np.stack(boundaries), axis=0), {name: maps[name].copy() for name in DESCRIPTORS})
            )

    for position, item in enumerate(uded_items):
        image_id = str(item["id"])
        print(f"STAGE19B_UDED_CLEAN {position + 1:02d}/{len(uded_items):02d} {image_id}", flush=True)
        frame, image_metrics, mixed_rows, _maps, _pre = _process_record(
            "UDED_selection_overlap_clean", image_id, np.asarray(item["img"]), [np.asarray(item["gt"], dtype=bool)]
        )
        sample_frames.append(frame); metric_rows.extend(image_metrics)
        support_rows.extend(row for row in mixed_rows if "annotator_index" in row)
        runtime_rows.extend(row for row in mixed_rows if "runtime_seconds" in row)

    samples = pd.concat(sample_frames, ignore_index=True)
    metrics = pd.DataFrame(metric_rows)
    support = pd.DataFrame(support_rows)
    runtimes = pd.DataFrame(runtime_rows)
    distributions = _distribution_table(samples)
    curves = _probability_curves(samples)
    strata = _consensus_strata(samples)
    bootstrap = _bootstrap_summary(metrics)

    metrics.to_csv(OUT / "descriptor_image_metrics.csv", index=False)
    bootstrap.to_csv(OUT / "descriptor_bootstrap_summary.csv", index=False)
    distributions.to_csv(OUT / "descriptor_distribution_stats.csv", index=False)
    curves.to_csv(OUT / "descriptor_probability_curves.csv", index=False)
    strata.to_csv(OUT / "bsds_consensus_strata.csv", index=False)
    support.to_csv(OUT / "annotator_boundary_support.csv", index=False)
    runtimes.to_csv(OUT / "descriptor_runtime.csv", index=False)
    preview = _write_preview(preview_records)
    _write_official_manifest()

    summary = {
        "stage": "19b-descriptor-relevance-atlas",
        "role": "bounded_gt_guided_analysis_experiment_1_of_3",
        "architecture_changed": False,
        "promotion_allowed": False,
        "protected_split_used": False,
        "dataset_contract": {
            "BSDS500_train_images": len(bsds_ids),
            "BSDS500_validation_read": False,
            "BSDS500_test_blob_read": False,
            "UDED_selection_before_overlap_filter": overlap_manifest["selection_count_before"],
            "UDED_selection_after_overlap_filter": overlap_manifest["selection_count_after"],
            "grouping_unit": "image",
        },
        "descriptor_pool": list(DESCRIPTORS),
        "sampling": {
            "scheme": "deterministic uniform-without-replacement pixels within each image",
            "samples_per_image": SAMPLES_PER_IMAGE,
            "seed": SEED,
            "random_pixel_train_test_split": False,
        },
        "target_contract": {
            "exact_consensus": "mean of preserved per-annotator binary boundary rasters",
            "exact_union": "any preserved annotator marks the exact pixel",
            "tolerant_soft": "mean across annotators of max(1-distance/tolerance,0)",
            "tolerant_union": "any annotator boundary within tolerance",
            "tolerance": "0.0075 of image diagonal, fixed before results",
            "official_metric_replacement": False,
        },
        "uncertainty": {
            "unit": "image",
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "interval": "percentile 95%",
        },
        "visual_preview": preview,
        "official_attachment": (
            "Incumbent-only BSDS500-train attachment. Stage 19B has no candidate "
            "detector map and does not read BSDS validation."
        ),
        "decision_rule": (
            "No cue selection or architecture change is permitted here. Stage 19C "
            "must consume the frozen pool and these atlas outputs under the registered "
            "pairwise redundancy/complementarity rules."
        ),
        "files": [
            "summary.json",
            "overlap_clean_dataset_manifest.json",
            "descriptor_image_metrics.csv",
            "descriptor_bootstrap_summary.csv",
            "descriptor_distribution_stats.csv",
            "descriptor_probability_curves.csv",
            "bsds_consensus_strata.csv",
            "annotator_boundary_support.csv",
            "descriptor_runtime.csv",
            "best_method_preview.png",
            "official_eval_manifest.json",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE19B_DESCRIPTOR_RELEVANCE_ATLAS_COMPLETE")
    print(OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
