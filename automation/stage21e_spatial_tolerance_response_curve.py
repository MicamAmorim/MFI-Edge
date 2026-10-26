from __future__ import annotations

"""Stage 21E: frozen-map Berkeley spatial-tolerance response curves."""

from pathlib import Path
import csv
import importlib.util
import json
import shutil


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/local_dev/stage21e_spatial_tolerance_response_curve"
SOURCE = ROOT / "results/local_dev/stage21b_three_protocol_retrospective_benchmark"
OFFICIAL = ROOT / "evaluation/bsds_official"
METHODS = [
    ("incumbent_compact_positive_choquet", ROOT / "automation/runtime/official_eval_cache/incumbent/val/e4fa09acaf61ec23"),
    ("stage20a_full_shortlist_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20a_full_shortlist_2additive_choquet/stage20a_full_shortlist_2additive_choquet/val"),
    ("stage20b_interaction_core_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20b_interaction_core_2additive_choquet/stage20b_interaction_core_2additive_choquet/val"),
    ("stage20c_dominant_pair_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20c_dominant_pair_2additive_choquet/stage20c_dominant_pair_2additive_choquet/val"),
    ("stage20d_incumbent_bank_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20d_incumbent_bank_2additive_choquet/stage20d_incumbent_bank_2additive_choquet/val"),
]
DISTANCES = (0.00375, 0.0075, 0.015, 0.025)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


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


def official_module():
    path = OFFICIAL / "run_official_bsds.py"
    spec = importlib.util.spec_from_file_location("stage21e_official", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate_resumable(mod, matlab: Path, *, benchmark_dir: Path, image_dir: Path,
                       gt_dir: Path, pred_dir: Path, out_dir: Path,
                       max_dist: float) -> dict:
    summary_path = out_dir / "official_summary.json"
    if summary_path.exists():
        return load_json(summary_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = sorted(path.stem for path in image_dir.glob("*.jpg"))
    quote = mod._matlab_quote
    expr = (
        f"addpath('{quote(mod.MATLAB_WRAPPER_DIR)}');evaluate_bsds_official("
        f"'{quote(benchmark_dir)}','{quote(image_dir)}','{quote(gt_dir)}',"
        f"'{quote(pred_dir)}','{quote(out_dir)}',99,{max_dist:.12g},1"
    )
    missing = [iid for iid in ids if not (out_dir / f"{iid}_ev1.txt").exists()
               or (out_dir / f"{iid}_ev1.txt").stat().st_size == 0]
    while missing:
        before = len(missing)
        run = mod._run([str(matlab), "-batch", expr + ",'evaluate');"],
                       timeout=4 * 60 * 60, check=False)
        missing = [iid for iid in ids if not (out_dir / f"{iid}_ev1.txt").exists()
                   or (out_dir / f"{iid}_ev1.txt").stat().st_size == 0]
        if len(missing) >= before:
            raise RuntimeError(
                f"resumable matching made no progress at {max_dist}: "
                f"missing={missing[:10]} returncode={run.returncode}\n"
                f"{run.stdout}\n{run.stderr}"
            )
    mod._run([str(matlab), "-batch", expr + ",'collect');"], timeout=4 * 60 * 60)
    if not summary_path.exists():
        raise RuntimeError(f"collection did not create {summary_path}")
    return load_json(summary_path)


def metric_row(method: str, distance: float, result: dict, source: str) -> dict:
    return {
        "method": method,
        "max_dist_fraction": distance,
        "ODS": result["ODS"],
        "ODS_precision": result["ODS_precision"],
        "ODS_recall": result["ODS_recall"],
        "ODS_threshold": result["ODS_threshold"],
        "OIS": result["OIS"],
        "AP": result["AP"],
        "source": source,
    }


def source_table(path: Path) -> dict[str, dict]:
    return {row["method"]: row for row in read_csv(path)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stage21d = load_json(ROOT / "results/local_dev/stage21d_ranking_localization_diagnosis/summary.json")
    if stage21d.get("status") != "completed":
        raise RuntimeError("Stage 21D must be complete before Stage 21E")

    standard = source_table(SOURCE / "stage21b_berkeley_standard.csv")
    loose = source_table(SOURCE / "stage21b_berkeley_0p025_sensitivity.csv")
    mod = official_module()
    cfg = load_json(OFFICIAL / "config.json")
    bsds_root, benchmark_dir = mod._ensure_benchmark_sources(cfg, "val")
    image_dir = bsds_root / "BSDS500/data/images/val"
    gt_dir = bsds_root / "BSDS500/data/groundTruth/val"
    ids = sorted(path.stem for path in image_dir.glob("*.jpg"))
    if len(ids) != 100:
        raise RuntimeError("expected exactly 100 BSDS validation images")
    for name, pred_dir in METHODS:
        if sorted(path.stem for path in pred_dir.glob("*.png")) != ids:
            raise RuntimeError(f"frozen map manifest mismatch for {name}")

    save_json(OUT / "official_eval_manifest.json", {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": "stage20c_dominant_pair_2additive_choquet",
            "export": {
                "script": "automation/stage21b_frozen_export.py",
                "args": ["--method", "stage20c_dominant_pair_2additive_choquet", "--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"],
            },
        }],
    })
    shutil.copyfile(SOURCE / "best_method_preview.png", OUT / "best_method_preview.png")

    matlab = mod._matlab_executable(cfg)
    rows: list[dict] = []
    pr_rows: list[dict] = []
    for name, pred_dir in METHODS:
        for distance in DISTANCES:
            if distance == 0.0075:
                result = standard[name]
                source = "reused_stage21b_standard_without_rematching"
            elif distance == 0.025:
                result = loose[name]
                source = "reused_stage21b_0p025_without_rematching"
            else:
                track_dir = OUT / f"berkeley_maxdist_{str(distance).replace('.', 'p')}" / name
                result = evaluate_resumable(
                    mod, matlab, benchmark_dir=benchmark_dir, image_dir=image_dir,
                    gt_dir=gt_dir, pred_dir=pred_dir, out_dir=track_dir,
                    max_dist=distance,
                )
                source = "new_resumable_berkeley_match"
                for line in (track_dir / "eval_bdry_thr.txt").read_text(encoding="utf-8").splitlines():
                    fields = line.split()
                    if len(fields) >= 4:
                        pr_rows.append({
                            "method": name, "max_dist_fraction": distance,
                            "threshold": fields[0], "recall": fields[1],
                            "precision": fields[2], "f_measure": fields[3],
                        })
            rows.append(metric_row(name, distance, result, source))

    write_csv(OUT / "spatial_tolerance_metrics.csv", rows)
    write_csv(OUT / "spatial_tolerance_pr_curves_new_tracks.csv", pr_rows)
    deltas = []
    for name, _ in METHODS:
        base = next(row for row in rows if row["method"] == name and row["max_dist_fraction"] == 0.0075)
        for row in rows:
            if row["method"] == name:
                deltas.append({
                    "method": name,
                    "max_dist_fraction": row["max_dist_fraction"],
                    "delta_ODS_vs_0p0075": float(row["ODS"]) - float(base["ODS"]),
                    "delta_OIS_vs_0p0075": float(row["OIS"]) - float(base["OIS"]),
                    "delta_AP_vs_0p0075": float(row["AP"]) - float(base["AP"]),
                    "interpretation": "spatial-tolerance sensitivity only; 0.0075 remains primary",
                })
    write_csv(OUT / "spatial_tolerance_deltas.csv", deltas)
    summary = {
        "stage": "stage21e_spatial_tolerance_response_curve",
        "status": "completed",
        "architecture_changed": False,
        "detector_fitted_or_maps_regenerated": False,
        "protected_split_used": False,
        "methods": [name for name, _ in METHODS],
        "max_dist_fractions": list(DISTANCES),
        "primary_max_dist_fraction": 0.0075,
        "berkeley_reference_reproduction_verified": False,
        "matcher_caveat": "Pinned Windows correspondPixels is clock-seeded and reference-unverified; Stage-21B rows are reused exactly while new tolerance rows come from resumable fresh matching.",
        "interpretation_contract": "Sensitivity diagnosis only; loose tolerances cannot promote or rescue a method and are not Estrada--Jepson.",
        "preview": {
            "file": "best_method_preview.png", "positions": [1, 50, 100],
            "columns": ["input", "annotation union", "incumbent", "20A", "20B", "20C", "20D"],
            "reused_byte_for_byte_from_stage21b": True, "documentary_only": True,
        },
        "next_stage_if_complete": "stage21f_context_localizer_nms_decomposition",
    }
    save_json(OUT / "summary.json", summary)
    (OUT / "summary.md").write_text(
        "# Stage 21E spatial-tolerance response curve\n\n"
        "The five exact frozen map sets were evaluated at four Berkeley matching distances. "
        "Only 0.0075 is primary; all other rows are non-promotional sensitivity diagnostics, "
        "not Estrada--Jepson metrics. Reference reproduction remains unverified.\n",
        encoding="utf-8",
    )
    print("STAGE21E_SPATIAL_TOLERANCE_RESPONSE_CURVE_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
