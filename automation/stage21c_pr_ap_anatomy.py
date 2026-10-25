from __future__ import annotations

"""Stage 21C: frozen-map anatomy of Berkeley PR and AP degradation."""

from pathlib import Path
import csv
import json
import shutil

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/local_dev/stage21b_three_protocol_retrospective_benchmark"
OUT = ROOT / "results/local_dev/stage21c_pr_ap_anatomy"
METHODS = [
    ("incumbent_compact_positive_choquet", ROOT / "automation/runtime/official_eval_cache/incumbent/val/e4fa09acaf61ec23"),
    ("stage20a_full_shortlist_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20a_full_shortlist_2additive_choquet/stage20a_full_shortlist_2additive_choquet/val"),
    ("stage20b_interaction_core_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20b_interaction_core_2additive_choquet/stage20b_interaction_core_2additive_choquet/val"),
    ("stage20c_dominant_pair_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20c_dominant_pair_2additive_choquet/stage20c_dominant_pair_2additive_choquet/val"),
    ("stage20d_incumbent_bank_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20d_incumbent_bank_2additive_choquet/stage20d_incumbent_bank_2additive_choquet/val"),
]
RECALL_TARGETS = (0.25, 0.50, 0.75, 0.90)
RECALL_BANDS = ((0.0, 0.25), (0.25, 0.50), (0.50, 0.75), (0.75, 1.0))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def pr_envelope(recall: np.ndarray, precision: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(recall)
    r = np.asarray(recall[order], dtype=float)
    p = np.asarray(precision[order], dtype=float)
    unique = np.unique(r)
    p = np.asarray([np.max(p[r == value]) for value in unique])
    p = np.maximum.accumulate(p[::-1])[::-1]
    return unique, p


def precision_at_recall(recall: np.ndarray, precision: np.ndarray, target: float) -> float | None:
    r, p = pr_envelope(recall, precision)
    if target < r.min() or target > r.max():
        return None
    return float(np.interp(target, r, p))


def band_area(recall: np.ndarray, precision: np.ndarray, lo: float, hi: float) -> float:
    r, p = pr_envelope(recall, precision)
    left, right = max(lo, float(r.min())), min(hi, float(r.max()))
    if right <= left:
        return 0.0
    inside = r[(r > left) & (r < right)]
    grid = np.concatenate(([left], inside, [right]))
    return float(np.trapz(np.interp(grid, r, p), grid))


def crossing_rows(curves: dict[str, tuple[np.ndarray, np.ndarray]]) -> list[dict]:
    base_r, base_p = pr_envelope(*curves[METHODS[0][0]])
    rows = []
    for method, _ in METHODS[1:]:
        cand_r, cand_p = pr_envelope(*curves[method])
        lo, hi = max(base_r.min(), cand_r.min()), min(base_r.max(), cand_r.max())
        grid = np.linspace(lo, hi, 2001)
        delta = np.interp(grid, cand_r, cand_p) - np.interp(grid, base_r, base_p)
        crossings = []
        for idx in np.where(np.signbit(delta[:-1]) != np.signbit(delta[1:]))[0]:
            x0, x1, y0, y1 = grid[idx], grid[idx + 1], delta[idx], delta[idx + 1]
            crossings.append(float(x0 if y1 == y0 else x0 - y0 * (x1 - x0) / (y1 - y0)))
        rows.append({
            "method": method,
            "common_recall_min": float(lo),
            "common_recall_max": float(hi),
            "crossing_count": len(crossings),
            "crossing_recalls": ";".join(f"{value:.6f}" for value in crossings),
            "delta_precision_area": float(np.trapz(delta, grid)),
        })
    return rows


def per_image_rows(method: str, eval_dir: Path, ids: list[str], global_threshold: float) -> list[dict]:
    out = []
    for image_id in ids:
        data = np.loadtxt(eval_dir / f"{image_id}_ev1.txt")
        threshold, cnt_r, sum_r, cnt_p, sum_p = data.T
        recall = np.divide(cnt_r, sum_r, out=np.zeros_like(cnt_r), where=sum_r > 0)
        precision = np.divide(cnt_p, sum_p, out=np.ones_like(cnt_p), where=sum_p > 0)
        f = np.divide(2 * recall * precision, recall + precision, out=np.zeros_like(recall), where=(recall + precision) > 0)
        idx = int(np.argmin(np.abs(threshold - global_threshold)))
        out.append({
            "image_id": image_id,
            "method": method,
            "global_ods_threshold": global_threshold,
            "threshold_grid_value": float(threshold[idx]),
            "f_at_global_ods_threshold": float(f[idx]),
            "per_image_best_f": float(np.max(f)),
            "per_image_best_threshold": float(threshold[int(np.argmax(f))]),
            "per_image_ap_envelope_trapezoid": band_area(recall, precision, 0.0, 1.0),
        })
    return out


def density_rows(method: str, pred_dir: Path, ids: list[str], thresholds: np.ndarray) -> list[dict]:
    hist = np.zeros(256, dtype=np.int64)
    total = 0
    for image_id in ids:
        values = np.asarray(Image.open(pred_dir / f"{image_id}.png"), dtype=np.uint8)
        hist += np.bincount(values.ravel(), minlength=256)
        total += values.size
    cumulative = np.cumsum(hist[::-1])[::-1]
    return [{
        "method": method,
        "threshold": float(threshold),
        "serialized_cutoff": int(np.ceil(threshold * 255)),
        "predicted_edge_density": float(cumulative[min(255, int(np.ceil(threshold * 255)))] / total),
    } for threshold in thresholds]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stage21b = json.loads((SOURCE / "summary.json").read_text(encoding="utf-8"))
    if stage21b.get("status") != "completed":
        raise RuntimeError("Stage 21B must be complete before Stage 21C")
    pr_rows = read_csv(SOURCE / "berkeley_standard_pr_curve.csv")
    curves = {}
    fixed_rows = []
    band_rows = []
    for method, _ in METHODS:
        subset = [row for row in pr_rows if row["method"] == method]
        recall = np.asarray([float(row["recall"]) for row in subset])
        precision = np.asarray([float(row["precision"]) for row in subset])
        curves[method] = (recall, precision)
        for target in RECALL_TARGETS:
            value = precision_at_recall(recall, precision, target)
            fixed_rows.append({"method": method, "recall_target": target, "precision_envelope": "" if value is None else value, "supported": value is not None})
        for lo, hi in RECALL_BANDS:
            band_rows.append({"method": method, "recall_band_low": lo, "recall_band_high": hi, "ap_area_envelope_trapezoid": band_area(recall, precision, lo, hi)})

    write_csv(OUT / "precision_at_fixed_recall.csv", fixed_rows)
    write_csv(OUT / "ap_by_recall_band.csv", band_rows)
    write_csv(OUT / "pr_curve_crossings.csv", crossing_rows(curves))

    ids = sorted(path.stem.replace("_ev1", "") for path in (SOURCE / "berkeley_standard" / METHODS[0][0]).glob("*_ev1.txt"))
    standard = {row["method"]: row for row in read_csv(SOURCE / "stage21b_berkeley_standard.csv")}
    image_rows = []
    density = []
    for method, pred_dir in METHODS:
        image_rows.extend(per_image_rows(method, SOURCE / "berkeley_standard" / method, ids, float(standard[method]["ODS_threshold"])))
        density.extend(density_rows(method, pred_dir, ids, np.arange(0.01, 1.0, 0.01)))
    write_csv(OUT / "per_image_pr_ap.csv", image_rows)
    write_csv(OUT / "predicted_edge_density_by_threshold.csv", density)

    base = {row["image_id"]: row for row in image_rows if row["method"] == METHODS[0][0]}
    deltas = []
    for row in image_rows:
        if row["method"] == METHODS[0][0]:
            continue
        ref = base[row["image_id"]]
        deltas.append({
            "image_id": row["image_id"],
            "method": row["method"],
            "delta_f_at_each_methods_global_ods_threshold": float(row["f_at_global_ods_threshold"]) - float(ref["f_at_global_ods_threshold"]),
            "delta_per_image_best_f": float(row["per_image_best_f"]) - float(ref["per_image_best_f"]),
            "delta_per_image_ap_envelope_trapezoid": float(row["per_image_ap_envelope_trapezoid"]) - float(ref["per_image_ap_envelope_trapezoid"]),
        })
    write_csv(OUT / "per_image_deltas_vs_incumbent.csv", deltas)

    shutil.copyfile(SOURCE / "best_method_preview.png", OUT / "best_method_preview.png")
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": "stage20c_dominant_pair_2additive_choquet",
            "export": {"script": "automation/stage21b_frozen_export.py", "args": ["--method", "stage20c_dominant_pair_2additive_choquet", "--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"]},
        }],
    }
    save_json(OUT / "official_eval_manifest.json", manifest)
    summary = {
        "stage": "stage21c_pr_ap_anatomy",
        "status": "completed",
        "architecture_changed": False,
        "detector_or_matcher_rerun": False,
        "protected_split_used": False,
        "primary_protocol": "Berkeley maxDist=0.0075, nthresh=99, thinpb=true, all annotations",
        "berkeley_reference_reproduction_verified": False,
        "methods": [name for name, _ in METHODS],
        "diagnostics": {
            "fixed_recall_targets": RECALL_TARGETS,
            "recall_bands": RECALL_BANDS,
            "per_image_ap_definition": "area under the monotone precision envelope by trapezoidal integration; diagnostic, not official aggregate AP",
            "density_definition": "fraction of serialized map pixels at or above each 8-bit-equivalent threshold",
        },
        "preview": {"file": "best_method_preview.png", "positions": [1, 50, 100], "columns": ["input", "annotation union", "incumbent", "20A", "20B", "20C", "20D"], "reused_byte_for_byte_from_stage21b": True, "documentary_only": True},
        "next_stage_if_complete": "stage21d_ranking_localization_diagnosis",
    }
    save_json(OUT / "summary.json", summary)
    (OUT / "summary.md").write_text(
        "# Stage 21C PR/AP anatomy\n\nThis frozen-artifact diagnostic decomposes the standard Berkeley PR curves, threshold-dependent edge density, and per-image changes without fitting a detector or rerunning a matcher. Per-image AP is explicitly diagnostic and is not substituted for official aggregate AP.\n",
        encoding="utf-8",
    )
    print("STAGE21C_PR_AP_ANATOMY_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
