from __future__ import annotations

"""Stage 15l image-regime diagnosis over frozen Stage-15 outputs."""

from pathlib import Path
import csv
import json
import math
import sys


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import ndimage, stats
from scipy.io import loadmat
from skimage.color import rgb2gray
from skimage.filters import gaussian, scharr, scharr_h, scharr_v
from skimage.io import imread

from src.bsds import _extract_boundaries


EXPERIMENT_ID = "stage15l_image_regime_characterization"
OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
POSITIONS = (0, 49, 99)
METHODS = ("incumbent_mfi", "sed", "edpf", "co", "sco", "compass", "qfrd")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _gray(path: Path) -> np.ndarray:
    image = np.asarray(imread(path), dtype=np.float64)
    if image.max() > 1.0:
        image /= 255.0
    return rgb2gray(image) if image.ndim == 3 else image


def _angle_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    diff = np.abs(a - b) % np.pi
    return np.minimum(diff, np.pi - diff)


def _features(gray: np.ndarray, incumbent: np.ndarray, boundaries: list[np.ndarray], threshold: float) -> dict[str, float]:
    blur = gaussian(gray, sigma=1.5, preserve_range=True)
    local_variance = np.maximum(gaussian(gray * gray, sigma=1.5, preserve_range=True) - blur * blur, 0.0)
    binary = incumbent >= threshold
    labels, components = ndimage.label(binary, structure=np.ones((3, 3), dtype=np.uint8))
    edge_pixels = int(np.count_nonzero(binary))

    gx = scharr_h(gray)
    gy = scharr_v(gray)
    magnitude = np.hypot(gx, gy)
    orientation = np.mod(np.arctan2(gy, gx), np.pi)
    hist, _ = np.histogram(orientation, bins=12, range=(0.0, np.pi), weights=magnitude)
    probability = hist / max(float(hist.sum()), np.finfo(np.float64).eps)
    positive = probability > 0
    orientation_entropy = -float(np.sum(probability[positive] * np.log(probability[positive]))) / math.log(12.0)

    adjacent_differences: list[np.ndarray] = []
    horizontal = binary[:, :-1] & binary[:, 1:]
    vertical = binary[:-1, :] & binary[1:, :]
    if np.any(horizontal):
        adjacent_differences.append(_angle_difference(orientation[:, :-1][horizontal], orientation[:, 1:][horizontal]))
    if np.any(vertical):
        adjacent_differences.append(_angle_difference(orientation[:-1, :][vertical], orientation[1:, :][vertical]))
    curvature = float(np.mean(np.concatenate(adjacent_differences)) / np.pi) if adjacent_differences else 0.0

    fine = float(np.mean(scharr(gaussian(gray, sigma=1.0, preserve_range=True))))
    coarse = float(np.mean(scharr(gaussian(gray, sigma=4.0, preserve_range=True))))
    agreement = np.mean(np.stack(boundaries).astype(np.float64), axis=0)
    any_gt = agreement > 0
    return {
        "texture_density": float(np.mean(np.abs(gray - blur) > 0.05)),
        "local_contrast": float(np.mean(np.sqrt(local_variance))),
        "global_contrast": float(np.quantile(gray, 0.9) - np.quantile(gray, 0.1)),
        "incumbent_edge_density": float(np.mean(binary)),
        "incumbent_fragmentation_per_10k": float(components * 10000.0 / max(edge_pixels, 1)),
        "incumbent_mean_component_size": float(edge_pixels / max(components, 1)),
        "orientation_entropy": orientation_entropy,
        "curvature_complexity": curvature,
        "coarse_to_fine_gradient_ratio": coarse / max(fine, np.finfo(np.float64).eps),
        "gt_density": float(np.mean(any_gt)),
        "annotator_agreement": float(np.mean(agreement[any_gt])) if np.any(any_gt) else 0.0,
    }


def _bh_adjust(p_values: list[float]) -> list[float]:
    values = np.asarray(p_values, dtype=np.float64)
    order = np.argsort(values, kind="stable")
    adjusted = np.empty_like(values)
    running = 1.0
    count = len(values)
    for rank_index in range(count - 1, -1, -1):
        original_index = int(order[rank_index])
        rank = rank_index + 1
        running = min(running, float(values[original_index]) * count / rank)
        adjusted[original_index] = min(running, 1.0)
    return adjusted.tolist()


def _preview(image_dir: Path, gt_dir: Path, incumbent_dir: Path, sed_dir: Path, rows: list[dict[str, object]]) -> dict[str, object]:
    selected = [rows[index] for index in POSITIONS]
    fig, axes = plt.subplots(3, 4, figsize=(12, 8), squeeze=False)
    for row_index, row in enumerate(selected):
        image_id = str(row["image_id"])
        image = imread(image_dir / f"{image_id}.jpg")
        agreement = np.mean(np.stack(_extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))), axis=0)
        incumbent = np.asarray(Image.open(incumbent_dir / f"{image_id}.png"), dtype=np.float64) / 255.0
        sed = np.asarray(Image.open(sed_dir / f"{image_id}.png"), dtype=np.float64) / 255.0
        for column, (panel, title) in enumerate(zip((image, agreement, incumbent, sed), ("Input", "Mean GT", "MFI incumbent", "Exact SED"))):
            axis = axes[row_index, column]
            axis.imshow(panel, cmap=None if column == 0 else "gray", vmin=None if column == 0 else 0, vmax=None if column == 0 else 1)
            if row_index == 0:
                axis.set_title(title)
            axis.set_xticks([])
            axis.set_yticks([])
        axes[row_index, 0].set_ylabel(
            f"{image_id}\ntexture={float(row['texture_density']):.3f}\ncontrast={float(row['global_contrast']):.3f}\nGT={float(row['gt_density']):.3f}",
            fontsize=8,
        )
    fig.suptitle("Stage 15l fixed BSDS500-val regimes; positions 1, 50, 100; qualitative only")
    fig.tight_layout()
    path = OUT / "best_method_preview.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "selection": "sorted BSDS500-validation positions 1, 50, and 100",
        "image_ids": [str(row["image_id"]) for row in selected],
        "panel_order": ["input", "mean annotator boundary", "frozen MFI incumbent", "exact SED"],
        "optimization_use": "none; documentary regime display over frozen outputs",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stage15k = _read_json(ROOT / "results/local_dev/stage15k_per_image_oracle_matrix/summary.json")
    config = _read_json(ROOT / "evaluation/bsds_official/config.json")
    bsds_root = ROOT / str(config["sources"]["bsds500"]["vendor_dir"])
    image_dir = bsds_root / "BSDS500/data/images/val"
    gt_dir = bsds_root / "BSDS500/data/groundTruth/val"

    qfrd_summary = _read_json(ROOT / "results/official_eval/stage15i_qfrd_exact_reproduction/summary.json")
    fingerprint = str(qfrd_summary["export"]["incumbent_compact_positive_choquet"]["fingerprint"])
    incumbent_dir = ROOT / "automation/runtime/official_eval_cache/incumbent/val" / fingerprint
    sed_dir = ROOT / "results/local_dev/stage15b_sed_exact_reproduction/predictions"
    incumbent_threshold = float(stage15k["official_sources"]["incumbent_mfi"]["reported_ods_threshold"])

    metrics_rows: list[dict[str, str]] = []
    with (ROOT / "results/local_dev/stage15k_per_image_oracle_matrix/per_image_metrics.csv").open(encoding="utf-8", newline="") as handle:
        metrics_rows = list(csv.DictReader(handle))
    by_image: dict[str, dict[str, float]] = {}
    for row in metrics_rows:
        by_image.setdefault(row["image_id"], {})[row["method"]] = float(row["ods_f1"])
    oracle_winner: dict[str, str] = {}
    with (ROOT / "results/local_dev/stage15k_per_image_oracle_matrix/oracle_complementarity.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["mode"] == "ods_raw_nearest":
                oracle_winner[row["image_id"]] = row["selected_method"]

    feature_rows: list[dict[str, object]] = []
    for image_id in sorted(by_image):
        gray = _gray(image_dir / f"{image_id}.jpg")
        incumbent = np.asarray(Image.open(incumbent_dir / f"{image_id}.png"), dtype=np.float64) / 255.0
        boundaries = _extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))
        row: dict[str, object] = {"image_id": image_id, "oracle_winner": oracle_winner[image_id]}
        row.update(_features(gray, incumbent, boundaries, incumbent_threshold))
        for method in METHODS:
            row[f"f1_{method}"] = by_image[image_id][method]
        feature_rows.append(row)

    feature_path = OUT / "image_regime_features.csv"
    with feature_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(feature_rows[0]))
        writer.writeheader()
        writer.writerows(feature_rows)

    property_names = [name for name in feature_rows[0] if name not in {"image_id", "oracle_winner"} and not name.startswith("f1_")]
    association_rows: list[dict[str, object]] = []
    for reference in ("sed", "incumbent_mfi"):
        for method in METHODS:
            if method == reference:
                continue
            deltas = np.asarray([float(row[f"f1_{method}"]) - float(row[f"f1_{reference}"]) for row in feature_rows])
            for property_name in property_names:
                values = np.asarray([float(row[property_name]) for row in feature_rows])
                correlation, p_value = stats.spearmanr(values, deltas)
                order = np.argsort(values, kind="stable")
                association_rows.append({
                    "reference": reference,
                    "method": method,
                    "property": property_name,
                    "spearman_rho": float(correlation),
                    "p_value": float(p_value),
                    "high_minus_low_quartile_mean_delta": float(np.mean(deltas[order[-25:]]) - np.mean(deltas[order[:25]])),
                    "low_quartile_mean_delta": float(np.mean(deltas[order[:25]])),
                    "high_quartile_mean_delta": float(np.mean(deltas[order[-25:]])),
                })
    adjusted = _bh_adjust([float(row["p_value"]) for row in association_rows])
    for row, value in zip(association_rows, adjusted):
        row["bh_q_value"] = value
    association_path = OUT / "regime_associations.csv"
    with association_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(association_rows[0]))
        writer.writeheader()
        writer.writerows(association_rows)

    winner_rows: list[dict[str, object]] = []
    for property_name in property_names:
        order = np.argsort([float(row[property_name]) for row in feature_rows], kind="stable")
        for quartile, indices in (("low", order[:25]), ("high", order[-25:])):
            for method in METHODS:
                winner_rows.append({
                    "property": property_name,
                    "quartile": quartile,
                    "method": method,
                    "winner_count": sum(feature_rows[int(index)]["oracle_winner"] == method for index in indices),
                })
    winner_path = OUT / "quartile_winner_counts.csv"
    with winner_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(winner_rows[0]))
        writer.writeheader()
        writer.writerows(winner_rows)

    preview = _preview(image_dir, gt_dir, incumbent_dir, sed_dir, feature_rows)
    strongest = sorted(association_rows, key=lambda row: (-abs(float(row["spearman_rho"])), str(row["reference"]), str(row["method"]), str(row["property"])))[:12]
    summary = {
        "stage": "15l-image-regime-characterization",
        "role": "frozen_output_image_regime_diagnosis",
        "architecture_changed": False,
        "protected_split_used": False,
        "dataset": {"name": "BSDS500", "split": "validation", "role": "development diagnosis", "n_images": len(feature_rows)},
        "methods": list(METHODS),
        "properties": property_names,
        "analysis": "Spearman method-minus-reference fixed-threshold F1 associations with global BH correction; stable low/high 25-image quartiles",
        "strongest_absolute_correlations_descriptive": strongest,
        "decision_guard": "descriptive associations and GT-oracle labels cannot select a router, feature, threshold, or MFI architecture before Stage 15o and a separate preregistration",
        "stage15a_caveat": "performance counts derive from the stochastic, reference-uncertified Windows matcher; no matcher or detector is rerun",
        "official_eval_manifest_omission": "justified: no candidate map or evaluator invocation; frozen maps and existing official counts only",
        "preview": preview,
        "artifacts": {
            "features": feature_path.relative_to(ROOT).as_posix(),
            "associations": association_path.relative_to(ROOT).as_posix(),
            "quartile_winner_counts": winner_path.relative_to(ROOT).as_posix(),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15L_IMAGE_REGIME_CHARACTERIZATION_COMPLETE")
    print(OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
