from __future__ import annotations

"""Stage 22C: frozen-map inter-image score-calibration diagnosis."""

import csv
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy.io import loadmat
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.stage21d_ranking_localization_diagnosis import (
    auc_binary, average_precision, extract_boundaries, official_module,
)
from automation.visual_report import write_panel_grid

OUT = ROOT / "results/local_dev/stage22c_inter_image_score_calibration_diagnosis"
COUNTS = ROOT / "results/local_dev/stage21b_three_protocol_retrospective_benchmark/berkeley_standard"
METHODS = [
    ("incumbent_compact_positive_choquet", ROOT / "automation/runtime/official_eval_cache/incumbent/val/e4fa09acaf61ec23"),
    ("stage20c_dominant_pair_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20c_dominant_pair_2additive_choquet/stage20c_dominant_pair_2additive_choquet/val"),
]
PREVIEW_POSITIONS = (0, 49, 99)
TOLERANCE = 0.0075
ODS_THRESHOLDS = {
    "incumbent_compact_positive_choquet": 0.18,
    "stage20c_dominant_pair_2additive_choquet": 0.25282828282828285,
}
CALIBRATION_THRESHOLDS = {
    "threshold_iqr_scale": 0.20, "oracle_ap_scale": 0.02,
    "rank_discrepancy_scale": 0.05, "dominance_score": 0.60,
    "component_floor": 0.50, "minimum_components": 2,
}


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def entropy(values: np.ndarray) -> float:
    hist = np.bincount(values.astype(np.uint8).ravel(), minlength=256).astype(float)
    p = hist[hist > 0] / hist.sum()
    return float(-(p * np.log2(p)).sum())


def curve_area(recall: np.ndarray, precision: np.ndarray) -> float:
    order = np.argsort(recall)
    r, p = np.asarray(recall[order], float), np.asarray(precision[order], float)
    unique = np.unique(r)
    envelope = np.asarray([np.max(p[r == value]) for value in unique])
    envelope = np.maximum.accumulate(envelope[::-1])[::-1]
    return float(np.trapezoid(envelope, unique)) if unique.size > 1 else 0.0


def count_table(method: str, image_id: str) -> np.ndarray:
    table = np.atleast_2d(np.loadtxt(COUNTS / method / f"{image_id}_ev1.txt"))
    if table.shape != (99, 5):
        raise RuntimeError(f"unexpected count table for {method}/{image_id}: {table.shape}")
    return table


def count_metrics(table: np.ndarray) -> dict:
    threshold, cnt_r, sum_r, cnt_p, sum_p = table.T
    recall = np.divide(cnt_r, sum_r, out=np.zeros_like(cnt_r), where=sum_r > 0)
    precision = np.divide(cnt_p, sum_p, out=np.ones_like(cnt_p), where=sum_p > 0)
    f = np.divide(2 * recall * precision, recall + precision, out=np.zeros_like(recall), where=(recall + precision) > 0)
    index = int(np.argmax(f))
    return {"best_threshold": float(threshold[index]), "best_f": float(f[index]),
            "ap_area": curve_area(recall, precision)}


def inverse_best_threshold_map(q: float, best: float) -> float:
    return float(2 * best * q if q <= 0.5 else best + 2 * (1 - best) * (q - 0.5))


def aggregate_count_curve(tables: list[np.ndarray], bests: list[float] | None) -> float:
    recalls, precisions = [], []
    for q in np.arange(1, 100, dtype=float) / 100:
        rows = []
        for index, table in enumerate(tables):
            raw = q if bests is None else inverse_best_threshold_map(float(q), bests[index])
            rows.append(table[int(np.argmin(np.abs(table[:, 0] - raw)))])
        values = np.asarray(rows)
        cnt_r, sum_r = values[:, 1].sum(), values[:, 2].sum()
        cnt_p, sum_p = values[:, 3].sum(), values[:, 4].sum()
        recalls.append(float(cnt_r / sum_r) if sum_r else 0.0)
        precisions.append(float(cnt_p / sum_p) if sum_p else 1.0)
    return curve_area(np.asarray(recalls), np.asarray(precisions))


def normalize(score: np.ndarray, family: str) -> np.ndarray:
    values = np.asarray(score, dtype=float)
    if family == "identity":
        return values
    if family == "empirical_cdf_midrank":
        return (rankdata(values.ravel(), method="average").reshape(values.shape) - 0.5) / values.size
    if family == "q01_q99":
        lo, hi = np.quantile(values, [0.01, 0.99])
        return np.clip((values - lo) / max(float(hi - lo), 1e-12), 0, 1)
    if family == "mean_sd_logistic":
        z = (values - values.mean()) / max(float(values.std()), 1e-12)
    elif family == "median_mad_logistic":
        center = float(np.median(values))
        z = (values - center) / max(1.4826 * float(np.median(np.abs(values - center))), 1e-12)
    else:
        raise ValueError(family)
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))


def isotonic_oracle(score_u8: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Weighted PAVA over exact serialized levels; GT-derived diagnostic only."""
    levels = score_u8.ravel().astype(np.int64)
    y = labels.ravel().astype(float)
    count = np.bincount(levels, minlength=256).astype(float)
    positive = np.bincount(levels, weights=y, minlength=256).astype(float)
    blocks = []
    for level in np.flatnonzero(count):
        blocks.append([int(level), int(level), count[level], positive[level]])
        while len(blocks) >= 2 and blocks[-2][3] / blocks[-2][2] > blocks[-1][3] / blocks[-1][2]:
            right = blocks.pop(); left = blocks.pop()
            blocks.append([left[0], right[1], left[2] + right[2], left[3] + right[3]])
    mapping = np.zeros(256, dtype=np.float32)
    for lo, hi, weight, total in blocks:
        mapping[lo:hi + 1] = total / weight
    return mapping[score_u8]


def association_rows(per_image: list[dict]) -> list[dict]:
    variables = ["positive_support_density", "ods_edge_density", "score_entropy_bits",
                 "score_dynamic_range", "image_entropy_bits", "gradient_mean", "gradient_q90",
                 "delta_best_f_vs_incumbent", "delta_ap_area_vs_incumbent"]
    rows = []
    for method, _ in METHODS:
        subset = [row for row in per_image if row["method"] == method]
        threshold = np.asarray([row["best_threshold"] for row in subset], float)
        for variable in variables:
            values = np.asarray([row[variable] for row in subset], float)
            rho, p = spearmanr(threshold, values)
            rows.append({"method": method, "outcome": "per_image_best_threshold", "variable": variable,
                         "spearman_rho": float(rho), "p_value_unadjusted": float(p), "n_images": len(subset)})
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    prior = json.loads((ROOT / "results/local_dev/stage22b_thesis_legacy_retrospective_benchmark/summary.json").read_text(encoding="utf-8"))
    if prior.get("status") != "completed":
        raise RuntimeError("Stage 22B must be complete before Stage 22C")
    mod = official_module()
    cfg = json.loads((ROOT / "evaluation/bsds_official/config.json").read_text(encoding="utf-8"))
    bsds_root, _ = mod._ensure_benchmark_sources(cfg, "val")
    image_dir, gt_dir = bsds_root / "BSDS500/data/images/val", bsds_root / "BSDS500/data/groundTruth/val"
    image_paths = sorted(image_dir.glob("*.jpg"))
    if len(image_paths) != 100:
        raise RuntimeError("expected exactly 100 BSDS validation images")

    families = ("identity", "empirical_cdf_midrank", "q01_q99", "mean_sd_logistic", "median_mad_logistic")
    per_image, preview_rows = [], []
    rank_store = {name: {"labels": [], "scores": [], "within_auc": [], "within_ap": []} for name, _ in METHODS}
    simulations = {(name, family): [] for name, _ in METHODS for family in families}
    oracle_scores = {name: [] for name, _ in METHODS}
    tables_by_method = {name: [] for name, _ in METHODS}
    bests_by_method = {name: [] for name, _ in METHODS}

    for position, image_path in enumerate(image_paths):
        image_id = image_path.stem
        rgb = np.asarray(Image.open(image_path).convert("RGB"))
        image = np.asarray(Image.open(image_path).convert("L"), dtype=np.uint8)
        gray = image.astype(float) / 255
        gy, gx = np.gradient(gray); gradient = np.hypot(gx, gy)
        boundaries = extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))
        if not boundaries:
            raise RuntimeError(f"could not parse annotations for {image_id}")
        union = np.any(np.stack(boundaries), axis=0)
        labels = distance_transform_edt(~union) <= TOLERANCE * float(np.hypot(*union.shape))
        preview, image_rows = [rgb, union], {}
        for method, pred_dir in METHODS:
            score_u8 = np.asarray(Image.open(pred_dir / f"{image_id}.png"), dtype=np.uint8)
            score = score_u8.astype(float) / 255
            if score.shape != labels.shape:
                raise RuntimeError(f"shape mismatch for {method}/{image_id}")
            table = count_table(method, image_id); metrics = count_metrics(table)
            tables_by_method[method].append(table); bests_by_method[method].append(metrics["best_threshold"])
            nonzero = score_u8[score_u8 > 0]
            q = np.quantile(score, [0.01, 0.10, 0.25, 0.50, 0.75, 0.90, 0.99])
            row = {"image_id": image_id, "method": method, "best_threshold": metrics["best_threshold"],
                   "per_image_best_f": metrics["best_f"], "per_image_ap_area": metrics["ap_area"],
                   "positive_support_density": float(np.mean(score_u8 > 0)),
                   "ods_edge_density": float(np.mean(score >= ODS_THRESHOLDS[method])),
                   "score_entropy_bits": entropy(score_u8),
                   "score_dynamic_range": float((nonzero.max() - nonzero.min()) / 255) if nonzero.size else 0.0,
                   "q01": float(q[0]), "q10": float(q[1]), "q25": float(q[2]), "q50": float(q[3]),
                   "q75": float(q[4]), "q90": float(q[5]), "q99": float(q[6]),
                   "image_entropy_bits": entropy(image), "gradient_mean": float(gradient.mean()),
                   "gradient_q90": float(np.quantile(gradient, 0.9)),
                   "within_image_tolerant_auc": auc_binary(labels, score),
                   "within_image_tolerant_ap": average_precision(labels, score)}
            image_rows[method] = row
            store = rank_store[method]
            store["labels"].append(labels.ravel()); store["scores"].append(score.astype(np.float32).ravel())
            store["within_auc"].append(row["within_image_tolerant_auc"]); store["within_ap"].append(row["within_image_tolerant_ap"])
            for family in families:
                transformed = normalize(score, family)
                simulations[(method, family)].append(transformed.astype(np.float32).ravel())
            oracle_scores[method].append(isotonic_oracle(score_u8, labels).ravel())
            preview.append(score)
        base = image_rows[METHODS[0][0]]
        for method, _ in METHODS:
            row = image_rows[method]
            row["delta_best_f_vs_incumbent"] = row["per_image_best_f"] - base["per_image_best_f"]
            row["delta_ap_area_vs_incumbent"] = row["per_image_ap_area"] - base["per_image_ap_area"]
            per_image.append(row)
        if position in PREVIEW_POSITIONS:
            preview_rows.append(preview)

    write_csv(OUT / "per_image_score_threshold_metrics.csv", per_image)
    write_csv(OUT / "threshold_associations.csv", association_rows(per_image))
    rank_rows, oracle_rows, simulation_rows = [], [], []
    for method, _ in METHODS:
        labels = np.concatenate(rank_store[method]["labels"]); scores = np.concatenate(rank_store[method]["scores"])
        pooled_auc, pooled_ap = auc_binary(labels, scores), average_precision(labels, scores)
        mean_auc, mean_ap = float(np.nanmean(rank_store[method]["within_auc"])), float(np.nanmean(rank_store[method]["within_ap"]))
        rank_rows.append({"method": method, "pooled_tolerant_auc": pooled_auc, "pooled_tolerant_ap": pooled_ap,
                          "mean_within_image_auc": mean_auc, "mean_within_image_ap": mean_ap,
                          "cross_image_auc_discrepancy": mean_auc - pooled_auc,
                          "contract": "0.0075 tolerant annotation union; diagnostic, not Berkeley matching"})
        raw_ap = aggregate_count_curve(tables_by_method[method], None)
        oracle_ap = aggregate_count_curve(tables_by_method[method], bests_by_method[method])
        thresholds = np.asarray(bests_by_method[method])
        isotonic_ap = average_precision(labels, np.concatenate(oracle_scores[method]))
        oracle_rows.append({"method": method, "best_threshold_variance": float(np.var(thresholds)),
                            "best_threshold_iqr": float(np.quantile(thresholds, .75) - np.quantile(thresholds, .25)),
                            "raw_count_curve_ap_area": raw_ap, "oracle_rescaled_count_curve_ap_area": oracle_ap,
                            "count_curve_recoverable_ap_gap": oracle_ap - raw_ap,
                            "raw_pooled_tolerant_ap": pooled_ap, "oracle_isotonic_pooled_tolerant_ap": isotonic_ap,
                            "oracle_recoverable_ap_gap": isotonic_ap - pooled_ap,
                            "contract": "GT-derived best-threshold alignment plus per-image PAVA; upper-bound diagnostics only"})
        for family in families:
            sim_labels, sim_scores = labels, np.concatenate(simulations[(method, family)])
            simulation_rows.append({"method": method, "family": family,
                                    "pooled_tolerant_auc": auc_binary(sim_labels, sim_scores),
                                    "pooled_tolerant_ap": average_precision(sim_labels, sim_scores),
                                    "ordering_preserving_within_image": True,
                                    "contract": "unlabeled diagnostic simulation; not selected or promotional"})
    write_csv(OUT / "rank_decomposition.csv", rank_rows)
    write_csv(OUT / "oracle_rescaling.csv", oracle_rows)
    write_csv(OUT / "unlabeled_normalization_simulations.csv", simulation_rows)

    candidate = METHODS[1][0]
    rank = next(row for row in rank_rows if row["method"] == candidate)
    oracle = next(row for row in oracle_rows if row["method"] == candidate)
    components = {
        "threshold_dispersion_component": float(np.clip(oracle["best_threshold_iqr"] / CALIBRATION_THRESHOLDS["threshold_iqr_scale"], 0, 1)),
        "oracle_recovery_component": float(np.clip(oracle["oracle_recoverable_ap_gap"] / CALIBRATION_THRESHOLDS["oracle_ap_scale"], 0, 1)),
        "cross_image_rank_component": float(np.clip(rank["cross_image_auc_discrepancy"] / CALIBRATION_THRESHOLDS["rank_discrepancy_scale"], 0, 1)),
    }
    score = float(np.mean(list(components.values())))
    count = int(sum(value >= CALIBRATION_THRESHOLDS["component_floor"] for value in components.values()))
    dominance = {"method": candidate, **components, "calibration_dominance_score": score,
                 "components_at_or_above_floor": count,
                 "calibration_dominant": bool(score >= CALIBRATION_THRESHOLDS["dominance_score"] and count >= CALIBRATION_THRESHOLDS["minimum_components"])}
    write_csv(OUT / "calibration_dominance.csv", [dominance])

    write_panel_grid(OUT / "best_method_preview.png", preview_rows,
                     ["input", "annotation union", "incumbent frozen score", "Stage 20C frozen score"])
    manifest = {"schema_version": 1, "split": "val", "include_incumbent": True,
                "methods": [{"name": candidate, "export": {"script": "automation/stage22b_frozen_export.py",
                "args": ["--method", candidate, "--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"]}}],
                "stage22_note": "Documentary unchanged frozen-map attachment; Stage 22C fits and promotes nothing."}
    save_json(OUT / "official_eval_manifest.json", manifest)
    summary = {"stage": "stage22c_inter_image_score_calibration_diagnosis", "status": "completed",
               "scientific_experiment_index": "3/5", "architecture_changed": False, "detector_fitted": False,
               "matcher_rerun": False, "promotion_allowed": False, "protected_split_used": False,
               "berkeley_reference_reproduction_verified": False,
               "calibration_dominance_contract": CALIBRATION_THRESHOLDS, "calibration_dominance": dominance,
               "oracle_warning": "GT-derived per-image mapping is an upper-bound diagnostic and is forbidden as a candidate.",
               "normalization_warning": "Unlabeled simulations are diagnostic only and cannot be selected from validation results.",
               "preview": {"file": "best_method_preview.png", "positions": [1, 50, 100],
                           "columns": ["input", "annotation union", "incumbent frozen score", "Stage 20C frozen score"],
                           "documentary_only": True},
               "next_stage_if_complete": "stage22d_local_competition_nms_rank_swap_diagnosis"}
    save_json(OUT / "summary.json", summary)
    (OUT / "summary.md").write_text("# Stage 22C inter-image calibration diagnosis\n\nFrozen-map and frozen-count diagnostics only. Oracle and normalization rows are non-promotional; no matcher or detector is rerun.\n", encoding="utf-8")
    print("STAGE22C_INTER_IMAGE_CALIBRATION_COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
