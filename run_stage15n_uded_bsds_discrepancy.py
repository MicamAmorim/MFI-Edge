from __future__ import annotations

"""Stage 15n frozen-result UDED/BSDS discrepancy audit."""

from pathlib import Path
import csv
import json
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage, stats
from scipy.io import loadmat
from skimage.color import rgb2gray
from skimage.filters import gaussian, scharr
from skimage.io import imread

from benchmark_uded import DEFAULT_UDED, load_uded
from src.bsds import _extract_boundaries


EXPERIMENT_ID = "stage15n_uded_bsds_discrepancy_audit"
OUT = ROOT / "results/local_dev" / EXPERIMENT_ID
FEATURES = (
    "intensity_std", "gradient_mean", "gradient_q90", "gradient_density",
    "texture_residual_mean", "gt_density", "gt_components_per_mpix",
    "mean_gt_component_size",
)
MECHANISMS = {
    "se2": {
        "uded": ROOT / "results/local_dev/stage14r_se2_contour_enhancement/per_image_metrics.csv",
        "incumbent": "compact_incumbent",
        "candidate": "fixed_se2_contour_enhancement",
        "official": "stage14r_se2_contour_enhancement",
        "official_candidate": "fixed_se2_contour_enhancement",
    },
    "riesz": {
        "uded": ROOT / "results/local_dev/stage14s_fractional_riesz_localizer/per_image_metrics.csv",
        "incumbent": "compact_scharr_incumbent",
        "candidate": "fixed_half_order_riesz",
        "official": "stage14s_fractional_riesz_localizer",
        "official_candidate": "fixed_half_order_riesz",
    },
}


def _gray(image: np.ndarray) -> np.ndarray:
    arr = np.asarray(image)
    if arr.ndim == 3:
        arr = rgb2gray(arr[..., :3])
    arr = arr.astype(np.float64)
    if arr.max(initial=0.0) > 1.0:
        arr /= 255.0
    return np.clip(arr, 0.0, 1.0)


def _features(dataset: str, image_id: str, image: np.ndarray, gt: np.ndarray) -> dict[str, object]:
    gray = _gray(image)
    grad = scharr(gray)
    residual = np.abs(gray - gaussian(gray, sigma=2.0, preserve_range=True))
    labels, count = ndimage.label(gt, structure=np.ones((3, 3), dtype=np.uint8))
    sizes = np.bincount(labels.ravel(), minlength=count + 1)[1:]
    pixels = float(gt.size)
    return {
        "dataset": dataset,
        "id": image_id,
        "height": int(gt.shape[0]),
        "width": int(gt.shape[1]),
        "intensity_std": float(np.std(gray)),
        "gradient_mean": float(np.mean(grad)),
        "gradient_q90": float(np.quantile(grad, 0.90)),
        "gradient_density": float(np.mean(grad >= 0.10)),
        "texture_residual_mean": float(np.mean(residual)),
        "gt_density": float(np.mean(gt)),
        "gt_components_per_mpix": float(count * 1_000_000.0 / pixels),
        "mean_gt_component_size": float(np.mean(sizes)) if sizes.size else 0.0,
    }


def _safe_f1(row: np.ndarray) -> float:
    _, cnt_r, sum_r, cnt_p, sum_p = (float(value) for value in row)
    recall = cnt_r / sum_r if sum_r else 0.0
    precision = cnt_p / sum_p if sum_p else 0.0
    return 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0


def _bsds_deltas(mechanism: dict[str, object]) -> dict[str, float]:
    base = ROOT / "results/official_eval" / str(mechanism["official"])
    summary = json.loads((base / "summary.json").read_text(encoding="utf-8"))
    inc_name = "incumbent_compact_positive_choquet"
    cand_name = str(mechanism["official_candidate"])
    inc_threshold = float(summary["methods"][inc_name]["ODS_threshold"])
    cand_threshold = float(summary["methods"][cand_name]["ODS_threshold"])
    result: dict[str, float] = {}
    inc_dir = base / "matlab" / inc_name
    cand_dir = base / "matlab" / cand_name
    for inc_file in sorted(inc_dir.glob("*_ev1.txt")):
        image_id = inc_file.stem.removesuffix("_ev1")
        inc = np.atleast_2d(np.loadtxt(inc_file))
        cand = np.atleast_2d(np.loadtxt(cand_dir / inc_file.name))
        inc_row = inc[int(np.argmin(np.abs(inc[:, 0] - inc_threshold)))]
        cand_row = cand[int(np.argmin(np.abs(cand[:, 0] - cand_threshold)))]
        result[image_id] = _safe_f1(cand_row) - _safe_f1(inc_row)
    return result


def _uded_deltas(mechanism: dict[str, object]) -> dict[str, float]:
    table = pd.read_csv(Path(mechanism["uded"]))
    pivot = table.pivot_table(index=["repeat", "fold", "id"], columns="variant", values="F1")
    delta = pivot[str(mechanism["candidate"])] - pivot[str(mechanism["incumbent"])]
    return {str(key): float(value) for key, value in delta.groupby(level="id").mean().items()}


def _bh(values: list[float]) -> list[float]:
    p = np.asarray(values, dtype=float)
    order = np.argsort(p)
    ranked = p[order]
    adjusted = np.minimum.accumulate((ranked * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    out = np.empty_like(adjusted)
    out[order] = np.clip(adjusted, 0.0, 1.0)
    return out.tolist()


def _preview(uded: list[dict[str, object]], bsds_ids: list[str], image_dir: Path, gt_dir: Path) -> dict[str, object]:
    uded_positions = (0, 7, 14)
    bsds_positions = (0, 49, 99)
    fig, axes = plt.subplots(3, 4, figsize=(12, 9), squeeze=False)
    for row, (u_idx, b_idx) in enumerate(zip(uded_positions, bsds_positions)):
        u = uded[u_idx]
        b_id = bsds_ids[b_idx]
        b_gt = np.mean(np.stack(_extract_boundaries(loadmat(gt_dir / f"{b_id}.mat"))), axis=0)
        panels = (u["img"], u["gt"], imread(image_dir / f"{b_id}.jpg"), b_gt)
        for column, (panel, title) in enumerate(zip(panels, ("UDED input", "UDED GT", "BSDS input", "BSDS mean GT"))):
            ax = axes[row, column]
            ax.imshow(panel, cmap=None if column in (0, 2) else "gray")
            if row == 0:
                ax.set_title(title)
            ax.set_xticks([]); ax.set_yticks([])
        axes[row, 0].set_ylabel(f"{u['id']} / {b_id}")
    fig.suptitle("Stage 15n fixed dataset examples; UDED positions 1/8/15, BSDS positions 1/50/100")
    fig.tight_layout()
    path = OUT / "best_method_preview.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "selection": "UDED selection positions 1, 8, 15 and sorted BSDS-validation positions 1, 50, 100",
        "panel_order": ["UDED input", "UDED GT", "BSDS input", "BSDS mean annotator boundary"],
        "optimization_use": "none; documentary dataset comparison",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": []}
    (OUT / "official_eval_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    uded = load_uded(DEFAULT_UDED)[0::2]
    if len(uded) != 15:
        raise RuntimeError(f"Expected 15 UDED selection images, found {len(uded)}")
    config = json.loads((ROOT / "evaluation/bsds_official/config.json").read_text(encoding="utf-8"))
    bsds_root = ROOT / str(config["sources"]["bsds500"]["vendor_dir"])
    image_dir = bsds_root / "BSDS500/data/images/val"
    gt_dir = bsds_root / "BSDS500/data/groundTruth/val"
    bsds_ids = sorted(path.stem for path in image_dir.glob("*.jpg"))

    feature_rows = [_features("UDED_selection", str(item["id"]), item["img"], np.asarray(item["gt"], bool)) for item in uded]
    for image_id in bsds_ids:
        boundaries = _extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))
        feature_rows.append(_features("BSDS500_val", image_id, imread(image_dir / f"{image_id}.jpg"), np.any(np.stack(boundaries), axis=0)))
    feature_table = pd.DataFrame(feature_rows)
    feature_table.to_csv(OUT / "dataset_regime_features.csv", index=False)

    shift_rows: list[dict[str, object]] = []
    for feature in FEATURES:
        a = feature_table.loc[feature_table.dataset == "UDED_selection", feature].to_numpy(float)
        b = feature_table.loc[feature_table.dataset == "BSDS500_val", feature].to_numpy(float)
        pooled = np.sqrt(((len(a) - 1) * np.var(a, ddof=1) + (len(b) - 1) * np.var(b, ddof=1)) / (len(a) + len(b) - 2))
        ks = stats.ks_2samp(a, b, alternative="two-sided", method="auto")
        shift_rows.append({"feature": feature, "uded_mean": float(np.mean(a)), "bsds_mean": float(np.mean(b)), "standardized_mean_difference_bsds_minus_uded": float((np.mean(b) - np.mean(a)) / pooled) if pooled else 0.0, "ks_statistic": float(ks.statistic), "p_value": float(ks.pvalue)})
    q = _bh([float(row["p_value"]) for row in shift_rows])
    for row, value in zip(shift_rows, q):
        row["bh_q"] = value
    pd.DataFrame(shift_rows).to_csv(OUT / "dataset_distribution_shifts.csv", index=False)

    delta_rows: list[dict[str, object]] = []
    for name, mechanism in MECHANISMS.items():
        for dataset, deltas in (("UDED_selection", _uded_deltas(mechanism)), ("BSDS500_val", _bsds_deltas(mechanism))):
            for image_id, delta in deltas.items():
                delta_rows.append({"mechanism": name, "dataset": dataset, "id": image_id, "candidate_minus_incumbent_f1": delta})
    delta_table = pd.DataFrame(delta_rows)
    delta_table.to_csv(OUT / "per_image_mechanism_deltas.csv", index=False)

    joined = feature_table.merge(delta_table, on=["dataset", "id"], how="inner")
    assoc_rows: list[dict[str, object]] = []
    for (mechanism, dataset), group in joined.groupby(["mechanism", "dataset"]):
        for feature in FEATURES:
            rho, p_value = stats.spearmanr(group[feature], group["candidate_minus_incumbent_f1"])
            assoc_rows.append({"mechanism": mechanism, "dataset": dataset, "feature": feature, "n": len(group), "spearman_rho": float(rho), "p_value": float(p_value)})
    q = _bh([float(row["p_value"]) if np.isfinite(row["p_value"]) else 1.0 for row in assoc_rows])
    for row, value in zip(assoc_rows, q):
        row["global_bh_q"] = value
    pd.DataFrame(assoc_rows).to_csv(OUT / "mechanism_regime_associations.csv", index=False)

    mechanism_summary = []
    for (mechanism, dataset), group in delta_table.groupby(["mechanism", "dataset"]):
        values = group.candidate_minus_incumbent_f1.to_numpy(float)
        mechanism_summary.append({"mechanism": mechanism, "dataset": dataset, "n": len(values), "mean_f1_delta": float(np.mean(values)), "median_f1_delta": float(np.median(values)), "positive_images": int(np.sum(values > 0))})
    preview = _preview(uded, bsds_ids, image_dir, gt_dir)
    summary = {
        "stage": "15n-uded-bsds-discrepancy-audit",
        "role": "frozen_result_cross_development_dataset_diagnosis",
        "architecture_changed": False,
        "protected_split_used": False,
        "datasets": {"UDED_selection": 15, "BSDS500_validation": len(bsds_ids)},
        "mechanisms": ["fixed Stage-14r SE(2)", "fixed Stage-14s half-order Riesz"],
        "mechanism_summary": mechanism_summary,
        "analysis_contract": "Image-internal fixed regime measures; UDED deltas averaged across the existing five repeated-CV validations; BSDS deltas reconstructed at each frozen method's reported raw ODS threshold from existing official count tables. No detector or matcher is rerun and no router is fitted.",
        "metric_warning": "UDED tolerant F1 and BSDS Berkeley per-image count F1 remain protocol-specific; compare delta direction and regime association, not absolute F1 levels.",
        "decision_guard": "Diagnostic evidence may inform Stage 15o decomposition but cannot itself select a feature, threshold, router, or architecture.",
        "official_attachment": "Required manifest re-evaluates only the already frozen incumbent; its result is redundant to this audit and matcher failure does not invalidate the frozen-table diagnosis.",
        "preview": preview,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15N_UDED_BSDS_DISCREPANCY_AUDIT_COMPLETE")
    print(OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
