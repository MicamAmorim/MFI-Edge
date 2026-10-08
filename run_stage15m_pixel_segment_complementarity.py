from __future__ import annotations

"""Stage 15m spatial complementarity diagnosis over frozen BSDS-val maps."""

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
import csv
import json
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.io import loadmat
from skimage.filters import scharr
from skimage.io import imread

from src.bsds import _extract_boundaries


EXPERIMENT_ID = "stage15m_pixel_segment_complementarity"
OUT = ROOT / "results/local_dev" / EXPERIMENT_ID
POSITIONS = (0, 49, 99)
METHODS = ("incumbent_mfi", "sed", "edpf", "co", "sco", "compass", "qfrd")
OVERLAP_RADIUS = 2.0
SUPPORTED_COMPONENT_FRACTION = 0.5


@dataclass(frozen=True)
class MethodState:
    name: str
    path: Path
    threshold: float


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ratio(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _prediction_dirs(fingerprint: str) -> dict[str, Path]:
    return {
        "incumbent_mfi": ROOT / "automation/runtime/official_eval_cache/incumbent/val" / fingerprint,
        "sed": ROOT / "results/local_dev/stage15b_sed_exact_reproduction/predictions",
        "edpf": ROOT / "results/local_dev/stage15d_edpf_exact_reproduction/predictions",
        "co": ROOT / "results/local_dev/stage15e_co_sco_exact_reproduction/predictions/co",
        "sco": ROOT / "results/local_dev/stage15e_co_sco_exact_reproduction/predictions/sco",
        "compass": ROOT / "results/local_dev/stage15f_compass_exact_reproduction/predictions/compass",
        "qfrd": ROOT / "results/local_dev/stage15i_qfrd_exact_reproduction/predictions",
    }


def _preview(image_dir: Path, gt_dir: Path, states: dict[str, MethodState], ids: list[str]) -> dict[str, object]:
    selected = [ids[index] for index in POSITIONS]
    shown = ("incumbent_mfi", "sed", "sco")
    fig, axes = plt.subplots(3, 5, figsize=(14, 8), squeeze=False)
    for row, image_id in enumerate(selected):
        image = imread(image_dir / f"{image_id}.jpg")
        gt = np.mean(np.stack(_extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))), axis=0)
        panels: list[np.ndarray] = [image, gt]
        for name in shown:
            state = states[name]
            score = np.asarray(Image.open(state.path / f"{image_id}.png"), dtype=np.float64) / 255.0
            panels.append(score >= state.threshold)
        for col, (panel, title) in enumerate(zip(panels, ("Input", "Mean GT", "MFI", "SED", "SCO"))):
            ax = axes[row, col]
            ax.imshow(panel, cmap=None if col == 0 else "gray", vmin=None if col == 0 else 0, vmax=None if col == 0 else 1)
            if row == 0:
                ax.set_title(title)
            ax.set_xticks([])
            ax.set_yticks([])
            if col == 0:
                ax.set_ylabel(image_id)
    fig.suptitle("Stage 15m frozen maps at registered ODS thresholds; positions 1, 50, 100")
    fig.tight_layout()
    path = OUT / "best_method_preview.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "selection": "sorted BSDS500-validation positions 1, 50, and 100",
        "image_ids": selected,
        "panel_order": ["input", "mean annotator boundary", "thresholded MFI", "thresholded SED", "thresholded SCO"],
        "optimization_use": "none; documentary display of frozen outputs",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    official_manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": "stage15m_frozen_exact_sed_reference",
            "prediction_dir": "results/local_dev/stage15b_sed_exact_reproduction/predictions",
        }],
    }
    (OUT / "official_eval_manifest.json").write_text(
        json.dumps(official_manifest, indent=2), encoding="utf-8"
    )
    stage15k = _read_json(ROOT / "results/local_dev/stage15k_per_image_oracle_matrix/summary.json")
    config = _read_json(ROOT / "evaluation/bsds_official/config.json")
    bsds_root = ROOT / str(config["sources"]["bsds500"]["vendor_dir"])
    image_dir = bsds_root / "BSDS500/data/images/val"
    gt_dir = bsds_root / "BSDS500/data/groundTruth/val"
    qfrd = _read_json(ROOT / "results/official_eval/stage15i_qfrd_exact_reproduction/summary.json")
    fingerprint = str(qfrd["export"]["incumbent_compact_positive_choquet"]["fingerprint"])
    paths = _prediction_dirs(fingerprint)
    sources = stage15k["official_sources"]
    states = {name: MethodState(name, paths[name], float(sources[name]["reported_ods_threshold"])) for name in METHODS}
    image_ids = sorted(path.stem for path in image_dir.glob("*.jpg"))

    method_totals = {name: {key: 0.0 for key in ("pixels", "supported_pixels", "false_pixels", "components", "supported_components", "supported_component_pixels", "weak_support_gradient_sum")} for name in METHODS}
    pair_totals = {(a, b): {key: 0.0 for key in ("a_supported", "b_supported", "a_unique_supported", "b_unique_supported", "a_shared_false", "b_shared_false", "a_false", "b_false")} for a, b in combinations(METHODS, 2)}

    for image_id in image_ids:
        boundaries = _extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))
        gt = np.any(np.stack(boundaries).astype(bool), axis=0)
        tolerance = 0.0075 * float(np.hypot(*gt.shape))
        near_gt = ndimage.distance_transform_edt(~gt) <= tolerance
        gray = np.asarray(Image.open(image_dir / f"{image_id}.jpg").convert("L"), dtype=np.float64) / 255.0
        gradient = scharr(gray)
        predictions: dict[str, np.ndarray] = {}
        supported: dict[str, np.ndarray] = {}
        false: dict[str, np.ndarray] = {}
        for name, state in states.items():
            score = np.asarray(Image.open(state.path / f"{image_id}.png"), dtype=np.float64) / 255.0
            pred = score >= state.threshold
            predictions[name] = pred
            supported[name] = pred & near_gt
            false[name] = pred & ~near_gt
            labels, count = ndimage.label(pred, structure=np.ones((3, 3), dtype=np.uint8))
            totals = method_totals[name]
            totals["pixels"] += int(pred.sum())
            totals["supported_pixels"] += int(supported[name].sum())
            totals["false_pixels"] += int(false[name].sum())
            totals["components"] += count
            totals["weak_support_gradient_sum"] += float(gradient[supported[name]].sum())
            sizes = np.bincount(labels.ravel(), minlength=count + 1)[1:]
            support_counts = np.bincount(
                labels.ravel(), weights=near_gt.ravel().astype(np.float64), minlength=count + 1
            )[1:]
            accepted = support_counts >= SUPPORTED_COMPONENT_FRACTION * sizes
            totals["supported_components"] += int(accepted.sum())
            totals["supported_component_pixels"] += int(sizes[accepted].sum())

        near_prediction = {
            name: ndimage.distance_transform_edt(~prediction) <= OVERLAP_RADIUS
            for name, prediction in predictions.items()
        }
        for a, b in combinations(METHODS, 2):
            near_a = near_prediction[a]
            near_b = near_prediction[b]
            row = pair_totals[(a, b)]
            row["a_supported"] += int(supported[a].sum())
            row["b_supported"] += int(supported[b].sum())
            row["a_unique_supported"] += int((supported[a] & ~near_b).sum())
            row["b_unique_supported"] += int((supported[b] & ~near_a).sum())
            row["a_shared_false"] += int((false[a] & near_b).sum())
            row["b_shared_false"] += int((false[b] & near_a).sum())
            row["a_false"] += int(false[a].sum())
            row["b_false"] += int(false[b].sum())

    method_rows: list[dict[str, object]] = []
    for name in METHODS:
        total = method_totals[name]
        method_rows.append({
            "method": name,
            **{key: int(value) if key != "weak_support_gradient_sum" else value for key, value in total.items()},
            "supported_pixel_fraction": _ratio(total["supported_pixels"], total["pixels"]),
            "supported_component_fraction": _ratio(total["supported_components"], total["components"]),
            "mean_supported_component_size": _ratio(total["supported_component_pixels"], total["supported_components"]),
            "mean_gradient_on_supported_pixels": _ratio(total["weak_support_gradient_sum"], total["supported_pixels"]),
        })
    with (OUT / "method_segment_profiles.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(method_rows[0]))
        writer.writeheader(); writer.writerows(method_rows)

    pair_rows: list[dict[str, object]] = []
    for (a, b), total in pair_totals.items():
        pair_rows.append({
            "method_a": a, "method_b": b, **{key: int(value) for key, value in total.items()},
            "a_unique_supported_fraction": _ratio(total["a_unique_supported"], total["a_supported"]),
            "b_unique_supported_fraction": _ratio(total["b_unique_supported"], total["b_supported"]),
            "a_shared_false_fraction": _ratio(total["a_shared_false"], total["a_false"]),
            "b_shared_false_fraction": _ratio(total["b_shared_false"], total["b_false"]),
        })
    with (OUT / "pairwise_spatial_complementarity.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pair_rows[0]))
        writer.writeheader(); writer.writerows(pair_rows)

    preview = _preview(image_dir, gt_dir, states, image_ids)
    sed_pairs = [row for row in pair_rows if "sed" in (row["method_a"], row["method_b"])]
    summary = {
        "stage": "15m-pixel-segment-complementarity",
        "role": "frozen_output_spatial_complementarity_diagnosis",
        "architecture_changed": False,
        "protected_split_used": False,
        "dataset": {"name": "BSDS500", "split": "validation", "role": "development diagnosis", "n_images": len(image_ids)},
        "methods": list(METHODS),
        "spatial_contract": {
            "thresholds": "each method's previously reported raw ODS threshold from Stage 15k",
            "gt_support": "prediction pixel within 0.0075 image-diagonal Euclidean distance of the union of validation annotations",
            "pairwise_overlap_radius_pixels": OVERLAP_RADIUS,
            "supported_component_fraction": SUPPORTED_COMPONENT_FRACTION,
            "warning": "diagnostic proximity accounting is not Berkeley one-to-one matching and must not be reported as ODS/OIS/AP",
        },
        "sed_pairwise_profiles": sed_pairs,
        "decision_guard": "results may characterize localization, weak-gradient support, false-positive sharing, and component continuity, but cannot fit a router or change MFI before Stage 15o and a separate preregistration",
        "stage15a_caveat": "thresholds originate from the stochastic, reference-uncertified Windows official path",
        "official_evaluation": "manifest reuses frozen MFI and SED maps; it does not regenerate a detector",
        "preview": preview,
        "artifacts": {
            "method_segment_profiles": "results/local_dev/stage15m_pixel_segment_complementarity/method_segment_profiles.csv",
            "pairwise_spatial_complementarity": "results/local_dev/stage15m_pixel_segment_complementarity/pairwise_spatial_complementarity.csv",
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15M_PIXEL_SEGMENT_COMPLEMENTARITY_COMPLETE")
    print(OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
