from __future__ import annotations

"""Stage 21D: frozen-map ranking versus localization diagnosis."""

from pathlib import Path
import csv
import importlib.util
import json
import shutil

import numpy as np
from PIL import Image
from scipy.io import loadmat
from scipy.ndimage import convolve, distance_transform_edt
from scipy.stats import rankdata


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/local_dev/stage21b_three_protocol_retrospective_benchmark"
OUT = ROOT / "results/local_dev/stage21d_ranking_localization_diagnosis"
METHODS = [
    ("incumbent_compact_positive_choquet", ROOT / "automation/runtime/official_eval_cache/incumbent/val/e4fa09acaf61ec23"),
    ("stage20a_full_shortlist_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20a_full_shortlist_2additive_choquet/stage20a_full_shortlist_2additive_choquet/val"),
    ("stage20b_interaction_core_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20b_interaction_core_2additive_choquet/stage20b_interaction_core_2additive_choquet/val"),
    ("stage20c_dominant_pair_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20c_dominant_pair_2additive_choquet/stage20c_dominant_pair_2additive_choquet/val"),
    ("stage20d_incumbent_bank_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20d_incumbent_bank_2additive_choquet/stage20d_incumbent_bank_2additive_choquet/val"),
]


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def extract_boundaries(gt: dict) -> list[np.ndarray]:
    out = []
    for item in gt["groundTruth"][0]:
        try:
            boundary = np.asarray(item[0][0][1], dtype=bool)
            if boundary.ndim == 2:
                out.append(boundary)
        except Exception:
            pass
    return out


def auc_binary(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = labels.astype(bool).ravel(); scores = scores.ravel()
    n_pos = int(labels.sum()); n_neg = int(labels.size - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = rankdata(scores, method="average")
    return float((ranks[labels].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def average_precision(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = labels.astype(bool).ravel(); scores = scores.ravel()
    positives = int(labels.sum())
    if positives == 0:
        return float("nan")
    order = np.argsort(-scores, kind="stable")
    ranked = labels[order]
    return float((np.cumsum(ranked)[ranked] / (np.flatnonzero(ranked) + 1)).sum() / positives)


def quantiles(values: np.ndarray) -> tuple[float, float, float]:
    if values.size == 0:
        return float("nan"), float("nan"), float("nan")
    return tuple(float(x) for x in np.quantile(values, [0.5, 0.9, 0.95]))


def disk(radius: float) -> np.ndarray:
    r = int(np.ceil(radius)); y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return ((x * x + y * y) <= radius * radius).astype(np.uint8)


def official_module():
    path = ROOT / "evaluation/bsds_official/run_official_bsds.py"
    spec = importlib.util.spec_from_file_location("stage21d_official", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stage21c = json.loads((ROOT / "results/local_dev/stage21c_pr_ap_anatomy/summary.json").read_text(encoding="utf-8"))
    if stage21c.get("status") != "completed":
        raise RuntimeError("Stage 21C must be complete before Stage 21D")

    mod = official_module()
    cfg = json.loads((ROOT / "evaluation/bsds_official/config.json").read_text(encoding="utf-8"))
    bsds_root, _ = mod._ensure_benchmark_sources(cfg, "val")
    image_dir = bsds_root / "BSDS500/data/images/val"
    gt_dir = bsds_root / "BSDS500/data/groundTruth/val"
    ids = sorted(path.stem for path in image_dir.glob("*.jpg"))
    if len(ids) != 100:
        raise RuntimeError("expected exactly 100 BSDS validation images")

    standard = {row["method"]: row for row in read_csv(SOURCE / "stage21b_berkeley_standard.csv")}
    score_rows, distance_rows, tolerance_rows, duplicate_rows, per_image_rows = [], [], [], [], []
    for method, pred_dir in METHODS:
        threshold = float(standard[method]["ODS_threshold"])
        all_labels, all_scores = [], []
        gt_distances, pred_distances = [], []
        for image_id in ids:
            score = np.asarray(Image.open(pred_dir / f"{image_id}.png"), dtype=np.float64) / 255.0
            boundaries = extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))
            if not boundaries:
                raise RuntimeError(f"could not parse annotations for {image_id}")
            union = np.any(np.stack(boundaries), axis=0)
            if union.shape != score.shape:
                raise RuntimeError(f"shape mismatch for {image_id}")
            diagonal = float(np.hypot(*score.shape))
            tol_standard, tol_loose = 0.0075 * diagonal, 0.025 * diagonal
            distance_to_gt = distance_transform_edt(~union)
            labels = distance_to_gt <= tol_standard
            prediction = score >= threshold
            distance_to_prediction = distance_transform_edt(~prediction)
            gt_values = distance_to_prediction[union]
            pred_values = distance_to_gt[prediction]
            gt_distances.append(gt_values); pred_distances.append(pred_values)
            all_labels.append(labels.ravel()); all_scores.append(score.ravel())

            multiplicity = convolve(prediction.astype(np.uint8), disk(tol_standard), mode="constant", cval=0)[union]
            duplicate_rows.append({
                "image_id": image_id, "method": method,
                "mean_predictions_within_standard_tolerance_per_gt_pixel": float(multiplicity.mean()),
                "fraction_gt_pixels_with_two_or_more_predictions": float(np.mean(multiplicity >= 2)),
                "definition": "near-GT multiplicity surrogate; not an oriented parallel-edge count",
            })
            per_image_rows.append({
                "image_id": image_id, "method": method,
                "pixel_tolerance_auc": auc_binary(labels, score),
                "pixel_tolerance_ap": average_precision(labels, score),
                "gt_to_prediction_mean_px": float(gt_values.mean()) if gt_values.size else float("nan"),
                "prediction_to_gt_mean_px": float(pred_values.mean()) if pred_values.size else float("nan"),
                "gt_supported_standard": float(np.mean(gt_values <= tol_standard)) if gt_values.size else float("nan"),
                "prediction_supported_standard": float(np.mean(pred_values <= tol_standard)) if pred_values.size else float("nan"),
                "gt_supported_loose": float(np.mean(gt_values <= tol_loose)) if gt_values.size else float("nan"),
                "prediction_supported_loose": float(np.mean(pred_values <= tol_loose)) if pred_values.size else float("nan"),
            })

        labels = np.concatenate(all_labels); scores = np.concatenate(all_scores)
        pos = scores[labels]; neg = scores[~labels]
        score_rows.append({
            "method": method, "pixel_tolerance_auc": auc_binary(labels, scores),
            "pixel_tolerance_average_precision": average_precision(labels, scores),
            "positive_score_mean": float(pos.mean()), "negative_score_mean": float(neg.mean()),
            "positive_score_q50": float(np.quantile(pos, 0.5)), "negative_score_q50": float(np.quantile(neg, 0.5)),
            "label_contract": "within 0.0075 diagonal of any annotation-union pixel; diagnostic, not Berkeley matching",
        })
        gt_values = np.concatenate(gt_distances); pred_values = np.concatenate(pred_distances)
        gt_q50, gt_q90, gt_q95 = quantiles(gt_values); pred_q50, pred_q90, pred_q95 = quantiles(pred_values)
        distance_rows.extend([
            {"method": method, "direction": "gt_to_prediction", "mean_px": float(gt_values.mean()), "q50_px": gt_q50, "q90_px": gt_q90, "q95_px": gt_q95},
            {"method": method, "direction": "prediction_to_gt", "mean_px": float(pred_values.mean()), "q50_px": pred_q50, "q90_px": pred_q90, "q95_px": pred_q95},
        ])
        for fraction in (0.0075, 0.025):
            # Per-image normalized tolerance is applied above; report the mean image support.
            subset = [r for r in per_image_rows if r["method"] == method]
            suffix = "standard" if fraction == 0.0075 else "loose"
            tolerance_rows.append({
                "method": method, "max_dist_fraction": fraction,
                "mean_gt_supported": float(np.mean([r[f"gt_supported_{suffix}"] for r in subset])),
                "mean_prediction_supported": float(np.mean([r[f"prediction_supported_{suffix}"] for r in subset])),
                "contract": "union-distance diagnostic at frozen standard-ODS threshold; not one-to-one Berkeley scoring",
            })

    write_csv(OUT / "score_rank_diagnostics.csv", score_rows)
    write_csv(OUT / "distance_distributions.csv", distance_rows)
    write_csv(OUT / "tolerance_support.csv", tolerance_rows)
    write_csv(OUT / "duplicate_parallel_surrogate.csv", duplicate_rows)
    write_csv(OUT / "per_image_diagnosis.csv", per_image_rows)
    shutil.copyfile(SOURCE / "best_method_preview.png", OUT / "best_method_preview.png")

    manifest = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": [{
        "name": "stage20c_dominant_pair_2additive_choquet",
        "export": {"script": "automation/stage21b_frozen_export.py", "args": ["--method", "stage20c_dominant_pair_2additive_choquet", "--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"]},
    }]}
    save_json(OUT / "official_eval_manifest.json", manifest)
    summary = {
        "stage": "stage21d_ranking_localization_diagnosis", "status": "completed",
        "architecture_changed": False, "detector_or_matcher_rerun": False, "protected_split_used": False,
        "methods": [name for name, _ in METHODS],
        "primary_protocol": "frozen Berkeley-standard serialized maps; diagnostic union-distance analyses only",
        "berkeley_reference_reproduction_verified": False,
        "interpretation_contract": "Ranking and localization evidence must be interpreted jointly; union-distance and multiplicity surrogates are not official ODS/OIS/AP.",
        "preview": {"file": "best_method_preview.png", "positions": [1, 50, 100], "columns": ["input", "annotation union", "incumbent", "20A", "20B", "20C", "20D"], "reused_byte_for_byte_from_stage21b": True, "documentary_only": True},
        "next_stage_if_complete": "stage21e_spatial_tolerance_response_curve",
    }
    save_json(OUT / "summary.json", summary)
    (OUT / "summary.md").write_text(
        "# Stage 21D ranking versus localization diagnosis\n\nFrozen score ordering, bidirectional distance, tolerance support, and near-GT multiplicity diagnostics. Union-distance quantities are descriptive surrogates and are not Berkeley one-to-one metrics.\n",
        encoding="utf-8",
    )
    print("STAGE21D_RANKING_LOCALIZATION_DIAGNOSIS_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
