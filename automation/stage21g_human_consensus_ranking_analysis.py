from __future__ import annotations

"""Stage 21G: frozen-map ranking against BSDS annotator consensus."""

from pathlib import Path
import csv
import json
import sys

import numpy as np
from PIL import Image
from scipy.io import loadmat
from scipy.ndimage import distance_transform_edt
from scipy.stats import kendalltau, spearmanr
from skimage.io import imread

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.stage21d_ranking_localization_diagnosis import METHODS, extract_boundaries, official_module
from automation.visual_report import write_panel_grid

OUT = ROOT / "results/local_dev/stage21g_human_consensus_ranking_analysis"
STANDARD = ROOT / "results/local_dev/stage21b_three_protocol_retrospective_benchmark/stage21b_berkeley_standard.csv"
PREVIEW_POSITIONS = (0, 49, 99)
CONSENSUS_RADIUS_PX = 1.5


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def read_thresholds() -> dict[str, float]:
    with STANDARD.open(newline="", encoding="utf-8") as handle:
        return {row["method"]: float(row["ODS_threshold"]) for row in csv.DictReader(handle)}


def consensus_map(boundaries: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    near = [distance_transform_edt(~boundary) <= CONSENSUS_RADIUS_PX for boundary in boundaries]
    union = np.any(np.stack(boundaries), axis=0)
    consensus = np.mean(np.stack(near), axis=0, dtype=np.float64)
    consensus[~union] = 0.0
    return union, consensus


def pairwise_accuracy(consensus: np.ndarray, score: np.ndarray) -> tuple[float, int]:
    levels = np.unique(consensus)
    correct = 0.0; pairs = 0
    lower = np.empty(0, dtype=np.float64)
    for level in levels:
        high_scores = score[consensus == level]
        if lower.size:
            ordered = np.sort(lower)
            left = np.searchsorted(ordered, high_scores, side="left")
            right = np.searchsorted(ordered, high_scores, side="right")
            correct += float(np.sum(left + 0.5 * (right - left)))
            pairs += int(lower.size * high_scores.size)
        lower = np.concatenate([lower, high_scores])
    return (correct / pairs if pairs else float("nan")), pairs


def safe_corr(function, x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 2 or np.all(x == x[0]) or np.all(y == y[0]):
        return float("nan")
    return float(function(x, y).statistic)


def stratum_name(values: np.ndarray) -> np.ndarray:
    out = np.full(values.shape, "low", dtype="<U6")
    out[values > (1.0 / 3.0)] = "medium"
    out[values > (2.0 / 3.0)] = "high"
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    prior = json.loads((ROOT / "results/local_dev/stage21f_context_localizer_nms_decomposition/summary.json").read_text(encoding="utf-8"))
    if prior.get("status") != "completed" or prior.get("final_map_byte_checks") != {"incumbent": 100, "stage20c": 100}:
        raise RuntimeError("Stage 21F must complete its frozen-map byte contract before Stage 21G")

    mod = official_module()
    cfg = json.loads((ROOT / "evaluation/bsds_official/config.json").read_text(encoding="utf-8"))
    bsds_root, _ = mod._ensure_benchmark_sources(cfg, "val")
    image_dir = bsds_root / "BSDS500/data/images/val"
    gt_dir = bsds_root / "BSDS500/data/groundTruth/val"
    image_paths = sorted(image_dir.glob("*.jpg"))
    if len(image_paths) != 100:
        raise RuntimeError("expected exactly 100 BSDS validation images")
    thresholds = read_thresholds()

    per_image, strata_rows, failure_rows, preview_rows = [], [], [], []
    pooled = {name: {"consensus": [], "score": []} for name, _ in METHODS}
    for number, image_path in enumerate(image_paths, start=1):
        image_id = image_path.stem
        print(f"STAGE21G_CONSENSUS {number:03d}/100 {image_id}", flush=True)
        boundaries = extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))
        if not boundaries:
            raise RuntimeError(f"could not parse annotations for {image_id}")
        union, consensus_full = consensus_map(boundaries)
        c = consensus_full[union]
        strata = stratum_name(c)
        preview_scores = {}
        for method, pred_dir in METHODS:
            score_full = np.asarray(Image.open(pred_dir / f"{image_id}.png"), dtype=np.float64) / 255.0
            if score_full.shape != union.shape:
                raise RuntimeError(f"shape mismatch for {method}/{image_id}")
            score = score_full[union]
            pooled[method]["consensus"].append(c); pooled[method]["score"].append(score)
            accuracy, pairs = pairwise_accuracy(c, score)
            per_image.append({"image_id": image_id, "method": method,
                              "spearman_rho": safe_corr(spearmanr, c, score),
                              "kendall_tau_b": safe_corr(kendalltau, c, score),
                              "higher_consensus_pairwise_accuracy": accuracy,
                              "ordered_pairs": pairs, "n_union_pixels": int(c.size),
                              "contract": "annotation-union pixels; consensus is fraction of annotators within fixed 1.5px radius"})
            detected = score >= thresholds[method]
            for stratum in ("low", "medium", "high"):
                mask = strata == stratum; values = score[mask]
                strata_rows.append({"image_id": image_id, "method": method, "consensus_stratum": stratum,
                                    "n_pixels": int(mask.sum()),
                                    "score_mean": float(values.mean()) if values.size else float("nan"),
                                    "score_median": float(np.median(values)) if values.size else float("nan"),
                                    "frozen_ods_detection_rate": float(detected[mask].mean()) if values.size else float("nan")})
            strong = c > (2.0 / 3.0); weak = c <= (1.0 / 3.0)
            strong_mean = float(score[strong].mean()) if strong.any() else float("nan")
            weak_mean = float(score[weak].mean()) if weak.any() else float("nan")
            failure_rows.append({"image_id": image_id, "method": method,
                                 "strong_minus_weak_score_mean": strong_mean - weak_mean,
                                 "strong_score_mean": strong_mean, "weak_score_mean": weak_mean,
                                 "strong_pixels": int(strong.sum()), "weak_pixels": int(weak.sum()),
                                 "selection_note": "ascending margin identifies deterministic weak-consensus-outranking cases; diagnostic only"})
            if method in (METHODS[0][0], METHODS[3][0]):
                preview_scores[method] = score_full
        if number - 1 in PREVIEW_POSITIONS:
            preview_rows.append([imread(image_path), consensus_full,
                                 preview_scores[METHODS[0][0]], preview_scores[METHODS[3][0]]])

    aggregate_rows = []
    for method, values in pooled.items():
        c = np.concatenate(values["consensus"]); score = np.concatenate(values["score"])
        accuracy, pairs = pairwise_accuracy(c, score)
        rows = [row for row in per_image if row["method"] == method]
        aggregate_rows.append({"method": method,
                               "pooled_spearman_rho": safe_corr(spearmanr, c, score),
                               "pooled_kendall_tau_b": safe_corr(kendalltau, c, score),
                               "pooled_higher_consensus_pairwise_accuracy": accuracy,
                               "pooled_ordered_pairs": pairs,
                               "mean_image_spearman_rho": float(np.nanmean([r["spearman_rho"] for r in rows])),
                               "mean_image_kendall_tau_b": float(np.nanmean([r["kendall_tau_b"] for r in rows])),
                               "mean_image_pairwise_accuracy": float(np.nanmean([r["higher_consensus_pairwise_accuracy"] for r in rows])),
                               "n_images": len(rows),
                               "contract": "descriptive annotator-consensus ranking; not Berkeley ODS/OIS/AP"})

    failure_rows.sort(key=lambda row: (row["method"], row["strong_minus_weak_score_mean"], row["image_id"]))
    write_csv(OUT / "consensus_rank_metrics.csv", aggregate_rows)
    write_csv(OUT / "per_image_consensus_rank_metrics.csv", per_image)
    write_csv(OUT / "consensus_strata.csv", strata_rows)
    write_csv(OUT / "weak_over_strong_failure_cases.csv", failure_rows)
    write_panel_grid(OUT / "best_method_preview.png", preview_rows, panel_height=180, panel_width=180)

    save_json(OUT / "official_eval_manifest.json", {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": [{
        "name": "stage20c_dominant_pair_2additive_choquet",
        "export": {"script": "automation/stage21b_frozen_export.py", "args": ["--method", "stage20c_dominant_pair_2additive_choquet", "--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"]},
    }]})
    save_json(OUT / "summary.json", {
        "stage": "stage21g_human_consensus_ranking_analysis", "status": "completed",
        "architecture_changed": False, "new_detector_or_parameter_fit": False, "protected_split_used": False,
        "methods": [name for name, _ in METHODS],
        "consensus_definition": "At each exact annotation-union pixel, fraction of human annotations with any boundary within 1.5 Euclidean pixels.",
        "strata": {"low": "(0,1/3]", "medium": "(1/3,2/3]", "high": "(2/3,1]"},
        "diagnostic_contract": "Consensus correlations, pairwise accuracy, strata and failure cases are diagnostic and not official Berkeley metrics.",
        "berkeley_reference_reproduction_verified": False,
        "preview": {"file": "best_method_preview.png", "positions": [1, 50, 100],
                    "columns": ["input", "consensus_strength", "incumbent_final_score", "stage20c_final_score"], "documentary_only": True},
        "next_stage_if_complete": "stage21h_causally_justified_mechanism_preregistration",
    })
    (OUT / "summary.md").write_text("# Stage 21G human-consensus ranking analysis\n\nFrozen maps are compared against a fixed multi-annotator consensus signal. All endpoints are diagnostic and non-promotional.\n", encoding="utf-8")
    print("STAGE21G_HUMAN_CONSENSUS_RANKING_ANALYSIS_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
