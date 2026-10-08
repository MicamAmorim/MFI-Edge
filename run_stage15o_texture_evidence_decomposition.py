from __future__ import annotations

"""Stage 15o diagnostic decomposition of fixed analytic boundary cues."""

from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import ndimage
from scipy.io import loadmat
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
from skimage.color import rgb2gray
from skimage.filters import gaussian, scharr, scharr_h, scharr_v
from skimage.io import imread

from benchmark_uded import DEFAULT_UDED, load_uded
from src.bsds import _extract_boundaries
from src.edge_signature import structural_signature_maps


EXPERIMENT_ID = "stage15o_texture_evidence_decomposition"
OUT = ROOT / "results/local_dev" / EXPERIMENT_ID
CUE_NAMES = (
    "local_gradient",
    "interior_texture_activity",
    "cross_boundary_texture_contrast",
    "multiscale_persistence",
    "structural_chain_support",
)
MODELS = {
    "gradient_only": ("local_gradient",),
    "gradient_plus_persistence": ("local_gradient", "multiscale_persistence"),
    "plus_interior_texture": ("local_gradient", "multiscale_persistence", "interior_texture_activity"),
    "plus_cross_boundary_texture": ("local_gradient", "multiscale_persistence", "cross_boundary_texture_contrast"),
    "plus_chain_support": ("local_gradient", "multiscale_persistence", "structural_chain_support"),
    "all_without_cross_boundary": (
        "local_gradient", "multiscale_persistence", "interior_texture_activity", "structural_chain_support",
    ),
    "all_five_cues": CUE_NAMES,
}
SAMPLES_PER_CLASS = 512


def _gray(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image, dtype=np.float64)
    if array.max(initial=0.0) > 1.0:
        array /= 255.0
    return rgb2gray(array[..., :3]) if array.ndim == 3 else array


def _cue_maps(image: np.ndarray) -> dict[str, np.ndarray]:
    gray = _gray(image)
    gx, gy = scharr_h(gray), scharr_v(gray)
    gradient = np.hypot(gx, gy)
    magnitude = np.maximum(gradient, np.finfo(np.float64).eps)
    nx, ny = gx / magnitude, gy / magnitude
    residual = np.abs(gray - gaussian(gray, sigma=1.5, preserve_range=True))
    activity = gaussian(residual, sigma=2.0, preserve_range=True)
    yy, xx = np.mgrid[: gray.shape[0], : gray.shape[1]]
    plus = ndimage.map_coordinates(activity, [yy + 4.0 * ny, xx + 4.0 * nx], order=1, mode="reflect")
    minus = ndimage.map_coordinates(activity, [yy - 4.0 * ny, xx - 4.0 * nx], order=1, mode="reflect")
    cross = np.abs(plus - minus) / (plus + minus + np.finfo(np.float64).eps)
    persistence = structural_signature_maps(image, (5, 7, 13))["gradient_scale_persistence"].astype(np.float64)
    binary = gradient >= 0.10
    labels, count = ndimage.label(binary, structure=np.ones((3, 3), dtype=np.uint8))
    sizes = np.bincount(labels.ravel(), minlength=count + 1)
    chain = np.zeros_like(gray)
    if count:
        chain[binary] = np.log1p(sizes[labels[binary]]) / np.log1p(float(np.hypot(*gray.shape)))
    return {
        "local_gradient": gradient,
        "interior_texture_activity": activity,
        "cross_boundary_texture_contrast": cross,
        "multiscale_persistence": persistence,
        "structural_chain_support": np.clip(chain, 0.0, 1.0),
    }


def _sample(dataset: str, image_id: str, image: np.ndarray, gt: np.ndarray) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    cues = _cue_maps(image)
    boundary = ndimage.binary_dilation(gt.astype(bool), iterations=1)
    interior = ndimage.distance_transform_edt(~gt.astype(bool)) > 5.0
    activity = cues["interior_texture_activity"]
    high_texture = interior & (activity >= np.quantile(activity[interior], 0.75))
    seed = int.from_bytes(hashlib.sha256(f"{dataset}:{image_id}".encode()).digest()[:8], "little")
    rng = np.random.default_rng(seed)

    def choose(mask: np.ndarray, count: int) -> np.ndarray:
        indices = np.flatnonzero(mask)
        if not len(indices):
            raise RuntimeError(f"Empty diagnostic stratum for {dataset}/{image_id}")
        return rng.choice(indices, size=count, replace=len(indices) < count)

    positive = choose(boundary, SAMPLES_PER_CLASS)
    textured = choose(high_texture, SAMPLES_PER_CLASS // 2)
    general = choose(interior, SAMPLES_PER_CLASS // 2)
    selected = np.concatenate((positive, textured, general))
    labels = np.concatenate((np.ones(SAMPLES_PER_CLASS, dtype=np.uint8), np.zeros(SAMPLES_PER_CLASS, dtype=np.uint8)))
    rows = {
        "dataset": dataset,
        "id": image_id,
        "label": labels,
        "negative_stratum": np.concatenate((np.full(SAMPLES_PER_CLASS, "boundary"), np.full(SAMPLES_PER_CLASS // 2, "high_texture"), np.full(SAMPLES_PER_CLASS // 2, "general_interior"))),
    }
    for name, cue in cues.items():
        rows[name] = cue.ravel()[selected]
    return pd.DataFrame(rows), cues


def _cross_validated_models(samples: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dataset, table in samples.groupby("dataset", sort=True):
        image_ids = sorted(table.id.unique())
        fold_by_id = {image_id: index % 5 for index, image_id in enumerate(image_ids)}
        for fold in range(5):
            test_mask = table.id.map(fold_by_id).to_numpy() == fold
            train, test = table.loc[~test_mask], table.loc[test_mask]
            for model_name, features in MODELS.items():
                scaler = StandardScaler().fit(train[list(features)])
                model = LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000, solver="lbfgs")
                model.fit(scaler.transform(train[list(features)]), train.label)
                score = model.predict_proba(scaler.transform(test[list(features)]))[:, 1]
                rows.append({
                    "dataset": dataset,
                    "fold": fold,
                    "model": model_name,
                    "features": "+".join(features),
                    "n_test": len(test),
                    "roc_auc": float(roc_auc_score(test.label, score)),
                    "average_precision": float(average_precision_score(test.label, score)),
                })
    return pd.DataFrame(rows)


def _preview(records: list[tuple[str, np.ndarray, np.ndarray, dict[str, np.ndarray]]]) -> dict[str, object]:
    positions = (0, 49, 99)
    fig, axes = plt.subplots(3, 7, figsize=(17, 8), squeeze=False)
    titles = ("Input", "Mean GT", "Interior activity", "Cross-texture", "Gradient", "Persistence", "Chain support")
    for row, position in enumerate(positions):
        image_id, image, gt, cues = records[position]
        panels = (image, gt, cues["interior_texture_activity"], cues["cross_boundary_texture_contrast"], cues["local_gradient"], cues["multiscale_persistence"], cues["structural_chain_support"])
        for column, (panel, title) in enumerate(zip(panels, titles)):
            axis = axes[row, column]
            axis.imshow(panel, cmap=None if column == 0 else "gray")
            if row == 0:
                axis.set_title(title)
            axis.set_xticks([]); axis.set_yticks([])
        axes[row, 0].set_ylabel(image_id)
    fig.suptitle("Stage 15o fixed analytic cue decomposition; BSDS-val positions 1, 50, 100")
    fig.tight_layout()
    path = OUT / "best_method_preview.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "selection": "sorted BSDS500-validation positions 1, 50, and 100",
        "panel_order": list(titles),
        "optimization_use": "none; documentary visualization of preregistered diagnostic cues",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": []}
    (OUT / "official_eval_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    config = json.loads((ROOT / "evaluation/bsds_official/config.json").read_text(encoding="utf-8"))
    bsds_root = ROOT / str(config["sources"]["bsds500"]["vendor_dir"])
    image_dir = bsds_root / "BSDS500/data/images/val"
    gt_dir = bsds_root / "BSDS500/data/groundTruth/val"

    sample_tables: list[pd.DataFrame] = []
    previews: list[tuple[str, np.ndarray, np.ndarray, dict[str, np.ndarray]]] = []
    uded = load_uded(DEFAULT_UDED)[0::2]
    if len(uded) != 15:
        raise RuntimeError(f"Expected 15 UDED selection images, found {len(uded)}")
    for item in uded:
        table, _ = _sample("UDED_selection", str(item["id"]), item["img"], np.asarray(item["gt"], bool))
        sample_tables.append(table)
    bsds_ids = sorted(path.stem for path in image_dir.glob("*.jpg"))
    for image_id in bsds_ids:
        image = imread(image_dir / f"{image_id}.jpg")
        boundaries = _extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))
        gt_stack = np.stack(boundaries).astype(bool)
        table, cues = _sample("BSDS500_val", image_id, image, np.any(gt_stack, axis=0))
        sample_tables.append(table)
        previews.append((image_id, image, np.mean(gt_stack, axis=0), cues))
    samples = pd.concat(sample_tables, ignore_index=True)
    samples.to_csv(OUT / "cue_samples.csv", index=False)

    group_summary = samples.groupby(["dataset", "label", "negative_stratum"], as_index=False)[list(CUE_NAMES)].mean()
    group_summary.to_csv(OUT / "cue_group_summary.csv", index=False)
    metrics = _cross_validated_models(samples)
    metrics.to_csv(OUT / "diagnostic_cv_metrics.csv", index=False)
    aggregate = metrics.groupby(["dataset", "model", "features"], as_index=False).agg(
        mean_roc_auc=("roc_auc", "mean"), mean_average_precision=("average_precision", "mean"),
        min_fold_roc_auc=("roc_auc", "min"), folds=("fold", "count"),
    )
    aggregate.to_csv(OUT / "diagnostic_cv_aggregate.csv", index=False)
    preview = _preview(previews)
    summary = {
        "stage": "15o-texture-evidence-decomposition",
        "role": "development_diagnostic_feature_decomposition",
        "architecture_changed": False,
        "protected_split_used": False,
        "datasets": {"UDED_selection": len(uded), "BSDS500_validation": len(bsds_ids)},
        "cue_contract": {
            "interior_texture_activity": "absolute sigma-1.5 residual smoothed at sigma 2",
            "cross_boundary_texture_contrast": "normalized difference of texture activity sampled at +/-4 pixels along the local Scharr normal",
            "local_gradient": "Scharr magnitude",
            "multiscale_persistence": "existing diagnostic structural signature at fixed scales 5, 7, 13",
            "structural_chain_support": "log component-size support on a fixed Scharr>=0.10 8-connected map; a chain-support surrogate, not Edge Drawing/EDPF",
        },
        "sampling_contract": "Per image: 512 one-pixel-dilated GT-boundary samples and 512 >5-pixel interior samples, half from the upper quartile of fixed texture activity; deterministic hash seed.",
        "model_contract": "Diagnostic-only five-fold image-blocked class-balanced L2 logistic models; scaling is fit inside each fold. These models are not detector candidates or routers.",
        "decision_rule": "Stage 15p is justified only if cross-boundary texture contrast adds directionally consistent held-out AUC/AP beyond gradient+persistence and beyond the all-without-cross model on both development datasets. Otherwise do not register Stage 15p; use the decomposition to choose at most one preregistered Stage-16 mechanism or a live-literature checkpoint.",
        "official_attachment": "Required manifest re-evaluates only the frozen incumbent; no new detector map is created.",
        "preview": preview,
        "artifacts": {
            "cue_samples": "results/local_dev/stage15o_texture_evidence_decomposition/cue_samples.csv",
            "cue_group_summary": "results/local_dev/stage15o_texture_evidence_decomposition/cue_group_summary.csv",
            "diagnostic_cv_metrics": "results/local_dev/stage15o_texture_evidence_decomposition/diagnostic_cv_metrics.csv",
            "diagnostic_cv_aggregate": "results/local_dev/stage15o_texture_evidence_decomposition/diagnostic_cv_aggregate.csv",
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15O_TEXTURE_EVIDENCE_DECOMPOSITION_COMPLETE")
    print(OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
