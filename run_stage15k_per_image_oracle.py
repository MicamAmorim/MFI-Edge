from __future__ import annotations

"""Stage 15k frozen-output per-image oracle and complementarity diagnosis."""

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
from scipy.io import loadmat
from skimage.io import imread

from src.bsds import _extract_boundaries


EXPERIMENT_ID = "stage15k_per_image_oracle_matrix"
OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
POSITIONS = (0, 49, 99)
TIE_TOLERANCE = 1e-12


@dataclass(frozen=True)
class MethodSpec:
    name: str
    label: str
    official_experiment: str
    official_method: str
    prediction_dir: str


METHODS = (
    MethodSpec(
        "incumbent_mfi",
        "MFI incumbent",
        "stage15i_qfrd_exact_reproduction",
        "incumbent_compact_positive_choquet",
        "__INCUMBENT_CACHE__",
    ),
    MethodSpec(
        "sed",
        "Exact SED",
        "stage15b_sed_exact_reproduction_retry1",
        "stage15b_exact_author_sed",
        "results/local_dev/stage15b_sed_exact_reproduction/predictions",
    ),
    MethodSpec(
        "edpf",
        "Exact EDPF",
        "stage15d_edpf_exact_reproduction",
        "stage15d_exact_author_edpf",
        "results/local_dev/stage15d_edpf_exact_reproduction/predictions",
    ),
    MethodSpec(
        "co",
        "Exact CO",
        "stage15e_co_sco_exact_reproduction",
        "stage15e_exact_author_co",
        "results/local_dev/stage15e_co_sco_exact_reproduction/predictions/co",
    ),
    MethodSpec(
        "sco",
        "Exact SCO",
        "stage15e_co_sco_exact_reproduction",
        "stage15e_exact_author_sco",
        "results/local_dev/stage15e_co_sco_exact_reproduction/predictions/sco",
    ),
    MethodSpec(
        "compass",
        "Exact Compass",
        "stage15f_compass_exact_reproduction_retry1",
        "stage15f_exact_author_compass",
        "results/local_dev/stage15f_compass_exact_reproduction/predictions/compass",
    ),
    MethodSpec(
        "qfrd",
        "Exact QFrD",
        "stage15i_qfrd_exact_reproduction",
        "stage15i_exact_author_qfrd",
        "results/local_dev/stage15i_qfrd_exact_reproduction/predictions",
    ),
)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator > 0 else 0.0


def _metrics(row: np.ndarray) -> dict[str, float]:
    threshold, cnt_r, sum_r, cnt_p, sum_p = (float(value) for value in row)
    recall = _safe_ratio(cnt_r, sum_r)
    precision = _safe_ratio(cnt_p, sum_p)
    f1 = _safe_ratio(2.0 * precision * recall, precision + recall)
    return {
        "threshold": threshold,
        "cnt_r": cnt_r,
        "sum_r": sum_r,
        "cnt_p": cnt_p,
        "sum_p": sum_p,
        "recall": recall,
        "precision": precision,
        "f1": f1,
    }


def _aggregate(rows: list[dict[str, float]]) -> dict[str, float]:
    cnt_r = sum(row["cnt_r"] for row in rows)
    sum_r = sum(row["sum_r"] for row in rows)
    cnt_p = sum(row["cnt_p"] for row in rows)
    sum_p = sum(row["sum_p"] for row in rows)
    recall = _safe_ratio(cnt_r, sum_r)
    precision = _safe_ratio(cnt_p, sum_p)
    return {
        "cnt_r": cnt_r,
        "sum_r": sum_r,
        "cnt_p": cnt_p,
        "sum_p": sum_p,
        "recall": recall,
        "precision": precision,
        "f1": _safe_ratio(2.0 * precision * recall, precision + recall),
    }


def _official_paths(spec: MethodSpec) -> tuple[Path, Path]:
    base = ROOT / "results" / "official_eval" / spec.official_experiment
    return base / "summary.json", base / "matlab" / spec.official_method


def _prediction_dirs(incumbent_fingerprint: str) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for spec in METHODS:
        if spec.prediction_dir == "__INCUMBENT_CACHE__":
            path = (
                ROOT
                / "automation"
                / "runtime"
                / "official_eval_cache"
                / "incumbent"
                / "val"
                / incumbent_fingerprint
            )
        else:
            path = ROOT / spec.prediction_dir
        result[spec.name] = path
    return result


def _preview(
    image_dir: Path,
    gt_dir: Path,
    prediction_dirs: dict[str, Path],
    image_ids: list[str],
) -> dict[str, object]:
    selected_ids = [image_ids[index] for index in POSITIONS]
    titles = ["Input", "Mean GT"] + [spec.label for spec in METHODS]
    fig, axes = plt.subplots(3, len(titles), figsize=(20, 7.5), squeeze=False)
    for row_index, image_id in enumerate(selected_ids):
        image_path = image_dir / f"{image_id}.jpg"
        boundaries = _extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))
        agreement = np.mean(np.stack(boundaries), axis=0)
        panels: list[np.ndarray] = [imread(image_path), agreement]
        panels.extend(
            np.asarray(Image.open(prediction_dirs[spec.name] / f"{image_id}.png")) / 255.0
            for spec in METHODS
        )
        for column, (panel, title) in enumerate(zip(panels, titles)):
            axis = axes[row_index, column]
            axis.imshow(
                panel,
                cmap=None if column == 0 else "gray",
                vmin=None if column == 0 else 0,
                vmax=None if column == 0 else 1,
            )
            if row_index == 0:
                axis.set_title(title, fontsize=8)
            if column == 0:
                axis.set_ylabel(image_id, fontsize=8)
            axis.set_xticks([])
            axis.set_yticks([])
    fig.suptitle(
        "Stage 15k frozen BSDS500-val outputs; sorted positions 1, 50, 100; qualitative only",
        fontsize=11,
    )
    fig.tight_layout()
    path = OUT / "best_method_preview.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "selection": "sorted BSDS500-validation positions 1, 50, and 100",
        "image_ids": selected_ids,
        "panel_order": ["input", "mean annotator boundary (display only)"]
        + [spec.label for spec in METHODS],
        "optimization_use": "none; documentary comparison of already-frozen outputs",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    config = _read_json(ROOT / "evaluation" / "bsds_official" / "config.json")
    bsds_root = ROOT / str(config["sources"]["bsds500"]["vendor_dir"])
    image_dir = bsds_root / "BSDS500" / "data" / "images" / "val"
    gt_dir = bsds_root / "BSDS500" / "data" / "groundTruth" / "val"

    qfrd_summary = _read_json(
        ROOT / "results" / "official_eval" / "stage15i_qfrd_exact_reproduction" / "summary.json"
    )
    incumbent_fingerprint = str(
        qfrd_summary["export"]["incumbent_compact_positive_choquet"]["fingerprint"]
    )
    prediction_dirs = _prediction_dirs(incumbent_fingerprint)

    official_metadata: dict[str, dict[str, object]] = {}
    raw_tables: dict[str, dict[str, np.ndarray]] = {}
    expected_ids: list[str] | None = None
    for spec in METHODS:
        summary_path, ev_dir = _official_paths(spec)
        summary = _read_json(summary_path)
        method_summary = summary["methods"][spec.official_method]
        if summary.get("status") != "completed" or summary.get("split") != "val":
            raise RuntimeError(f"incomplete or non-validation official source for {spec.name}")
        if int(method_summary["n_images"]) != 100:
            raise RuntimeError(f"expected 100 evaluated images for {spec.name}")
        official_metadata[spec.name] = {
            "source_experiment": spec.official_experiment,
            "source_method": spec.official_method,
            "reported_ods": float(method_summary["ODS"]),
            "reported_ois": float(method_summary["OIS"]),
            "reported_ap": float(method_summary["AP"]),
            "reported_ods_threshold": float(method_summary["ODS_threshold"]),
        }
        files = sorted(ev_dir.glob("*_ev1.txt"), key=lambda path: path.stem.removesuffix("_ev1"))
        ids = [path.stem.removesuffix("_ev1") for path in files]
        if len(ids) != 100:
            raise RuntimeError(f"expected 100 per-image tables for {spec.name}, found {len(ids)}")
        if expected_ids is None:
            expected_ids = ids
        elif ids != expected_ids:
            raise RuntimeError(f"per-image identity/order mismatch for {spec.name}")
        tables: dict[str, np.ndarray] = {}
        for image_id, path in zip(ids, files):
            table = np.loadtxt(path, dtype=np.float64)
            table = np.atleast_2d(table)
            if table.shape != (99, 5) or not np.isfinite(table).all():
                raise RuntimeError(f"invalid official per-image table: {path}")
            tables[image_id] = table
        raw_tables[spec.name] = tables
        map_dir = prediction_dirs[spec.name]
        if sorted(path.stem for path in map_dir.glob("*.png")) != expected_ids:
            raise RuntimeError(f"frozen prediction set mismatch for {spec.name}: {map_dir}")

    assert expected_ids is not None
    metric_rows: list[dict[str, object]] = []
    metric_lookup: dict[tuple[str, str, str], dict[str, float]] = {}
    for spec in METHODS:
        target_threshold = float(official_metadata[spec.name]["reported_ods_threshold"])
        for image_id in expected_ids:
            table = raw_tables[spec.name][image_id]
            all_metrics = [_metrics(row) for row in table]
            ods_index = int(np.argmin(np.abs(table[:, 0] - target_threshold)))
            ois_index = int(np.argmax([row["f1"] for row in all_metrics]))
            ods = all_metrics[ods_index]
            ois = all_metrics[ois_index]
            metric_lookup[(image_id, spec.name, "ods_raw_nearest")] = ods
            metric_lookup[(image_id, spec.name, "ois_raw")] = ois
            metric_rows.append(
                {
                    "image_id": image_id,
                    "method": spec.name,
                    "official_ods_threshold": target_threshold,
                    "raw_ods_threshold": ods["threshold"],
                    "ods_precision": ods["precision"],
                    "ods_recall": ods["recall"],
                    "ods_f1": ods["f1"],
                    "ods_cnt_r": int(ods["cnt_r"]),
                    "ods_sum_r": int(ods["sum_r"]),
                    "ods_cnt_p": int(ods["cnt_p"]),
                    "ods_sum_p": int(ods["sum_p"]),
                    "raw_ois_threshold": ois["threshold"],
                    "ois_precision": ois["precision"],
                    "ois_recall": ois["recall"],
                    "ois_f1": ois["f1"],
                    "ois_cnt_r": int(ois["cnt_r"]),
                    "ois_sum_r": int(ois["sum_r"]),
                    "ois_cnt_p": int(ois["cnt_p"]),
                    "ois_sum_p": int(ois["sum_p"]),
                }
            )

    per_image_path = OUT / "per_image_metrics.csv"
    with per_image_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metric_rows[0]))
        writer.writeheader()
        writer.writerows(metric_rows)

    pairwise_rows: list[dict[str, object]] = []
    for mode in ("ods_raw_nearest", "ois_raw"):
        for method_a, method_b in combinations((spec.name for spec in METHODS), 2):
            deltas = np.asarray(
                [
                    metric_lookup[(image_id, method_a, mode)]["f1"]
                    - metric_lookup[(image_id, method_b, mode)]["f1"]
                    for image_id in expected_ids
                ],
                dtype=np.float64,
            )
            pairwise_rows.append(
                {
                    "mode": mode,
                    "method_a": method_a,
                    "method_b": method_b,
                    "wins_a": int(np.sum(deltas > TIE_TOLERANCE)),
                    "wins_b": int(np.sum(deltas < -TIE_TOLERANCE)),
                    "ties": int(np.sum(np.abs(deltas) <= TIE_TOLERANCE)),
                    "mean_f1_delta_a_minus_b": float(np.mean(deltas)),
                    "median_f1_delta_a_minus_b": float(np.median(deltas)),
                }
            )
    pairwise_path = OUT / "pairwise_win_loss.csv"
    with pairwise_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pairwise_rows[0]))
        writer.writeheader()
        writer.writerows(pairwise_rows)

    ranking_rows: list[dict[str, object]] = []
    for mode in ("ods_raw_nearest", "ois_raw"):
        for spec in METHODS:
            rows = [metric_lookup[(image_id, spec.name, mode)] for image_id in expected_ids]
            aggregate = _aggregate(rows)
            ranking_rows.append(
                {
                    "mode": mode,
                    "method": spec.name,
                    "aggregate_precision": aggregate["precision"],
                    "aggregate_recall": aggregate["recall"],
                    "aggregate_f1": aggregate["f1"],
                    "mean_per_image_f1": float(np.mean([row["f1"] for row in rows])),
                    "median_per_image_f1": float(np.median([row["f1"] for row in rows])),
                }
            )
    ranking_path = OUT / "method_ranking.csv"
    with ranking_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ranking_rows[0]))
        writer.writeheader()
        writer.writerows(ranking_rows)

    oracle_rows: list[dict[str, object]] = []
    oracle_summary: dict[str, object] = {}
    for mode in ("ods_raw_nearest", "ois_raw"):
        selected_rows: list[dict[str, float]] = []
        winner_counts = {spec.name: 0 for spec in METHODS}
        for image_id in expected_ids:
            choices = [metric_lookup[(image_id, spec.name, mode)] for spec in METHODS]
            winner_index = int(np.argmax([row["f1"] for row in choices]))
            winner = METHODS[winner_index].name
            selected = choices[winner_index]
            winner_counts[winner] += 1
            selected_rows.append(selected)
            oracle_rows.append(
                {
                    "mode": mode,
                    "image_id": image_id,
                    "selected_method": winner,
                    "selected_threshold": selected["threshold"],
                    "selected_precision": selected["precision"],
                    "selected_recall": selected["recall"],
                    "selected_f1": selected["f1"],
                }
            )
        aggregate = _aggregate(selected_rows)
        single_rows = [row for row in ranking_rows if row["mode"] == mode]
        best_single = max(single_rows, key=lambda row: float(row["aggregate_f1"]))
        oracle_summary[mode] = {
            "aggregate": aggregate,
            "winner_counts": winner_counts,
            "best_single_method_by_aggregate_f1": best_single["method"],
            "best_single_aggregate_f1": best_single["aggregate_f1"],
            "oracle_gain_over_best_single": aggregate["f1"] - float(best_single["aggregate_f1"]),
        }
    oracle_path = OUT / "oracle_complementarity.csv"
    with oracle_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(oracle_rows[0]))
        writer.writeheader()
        writer.writerows(oracle_rows)

    preview = _preview(image_dir, gt_dir, prediction_dirs, expected_ids)
    summary = {
        "stage": "15k-per-image-oracle-matrix",
        "role": "frozen_output_complementarity_diagnosis",
        "architecture_changed": False,
        "protected_split_used": False,
        "dataset": {
            "name": "BSDS500",
            "split": "validation",
            "role": "development diagnosis over already-frozen reproduction outputs",
            "n_images": len(expected_ids),
        },
        "methods": [spec.name for spec in METHODS],
        "official_sources": official_metadata,
        "threshold_semantics": {
            "ods_raw_nearest": "nearest of each method's 99 raw thresholds to that method's previously reported ODS threshold; lower raw index wins an exact distance tie",
            "ois_raw": "per-image best raw threshold from the pre-existing 99-threshold table; ground-truth oracle diagnostic only",
        },
        "oracle": oracle_summary,
        "stage15a_caveat": "all count tables come from the unmodified Windows matcher, which remains stochastic and reference-uncertified; no matcher or detector is rerun here",
        "decision_guard": "oracle selections use validation ground truth and are descriptive upper bounds only; they may motivate later preregistered diagnostics but cannot be deployed, reported as ODS/OIS, or directly tune an MFI architecture before Stage 15o",
        "official_eval_manifest_omission": "justified: Stage 15k creates no detector map and invokes no evaluator; it analyzes frozen maps and existing official per-image count tables only",
        "preview": preview,
        "artifacts": {
            "per_image_metrics": per_image_path.relative_to(ROOT).as_posix(),
            "pairwise_win_loss": pairwise_path.relative_to(ROOT).as_posix(),
            "method_ranking": ranking_path.relative_to(ROOT).as_posix(),
            "oracle_complementarity": oracle_path.relative_to(ROOT).as_posix(),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15K_PER_IMAGE_ORACLE_MATRIX_COMPLETE")
    print(OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
