from __future__ import annotations

"""Stage 21B: rescore five frozen map sets under three distinct protocols."""

from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import shutil
import subprocess

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/local_dev/stage21b_three_protocol_retrospective_benchmark"
OFFICIAL = ROOT / "evaluation/bsds_official"
METHODS = [
    ("incumbent_compact_positive_choquet", ROOT / "automation/runtime/official_eval_cache/incumbent/val/e4fa09acaf61ec23"),
    ("stage20a_full_shortlist_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20a_full_shortlist_2additive_choquet/stage20a_full_shortlist_2additive_choquet/val"),
    ("stage20b_interaction_core_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20b_interaction_core_2additive_choquet/stage20b_interaction_core_2additive_choquet/val"),
    ("stage20c_dominant_pair_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20c_dominant_pair_2additive_choquet/stage20c_dominant_pair_2additive_choquet/val"),
    ("stage20d_incumbent_bank_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20d_incumbent_bank_2additive_choquet/stage20d_incumbent_bank_2additive_choquet/val"),
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def official_module():
    path = OFFICIAL / "run_official_bsds.py"
    spec = importlib.util.spec_from_file_location("stage21b_official", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def extract_boundaries(gt: dict) -> list[np.ndarray]:
    arr = gt["groundTruth"][0]
    out = []
    for item in arr:
        try:
            boundary = np.asarray(item[0][0][1], dtype=bool)
            if boundary.ndim == 2: out.append(boundary)
        except Exception:
            pass
    return out


def preview(image_dir: Path, gt_dir: Path, ids: list[str]) -> None:
    positions = [0, 49, 99]
    fig, axes = plt.subplots(3, 7, figsize=(18, 8), constrained_layout=True)
    titles = ["input", "annotation union", "incumbent", "20A", "20B", "20C", "20D"]
    for row, pos in enumerate(positions):
        iid = ids[pos]
        image = np.asarray(Image.open(image_dir / f"{iid}.jpg").convert("RGB"))
        boundaries = extract_boundaries(loadmat(gt_dir / f"{iid}.mat"))
        if not boundaries:
            raise RuntimeError(f"could not parse annotations for preview image {iid}")
        union = np.any(np.stack(boundaries), axis=0).astype(np.uint8) * 255
        panels = [image, union] + [np.asarray(Image.open(path / f"{iid}.png")) for _, path in METHODS]
        for col, panel in enumerate(panels):
            axes[row, col].imshow(panel, cmap=None if col == 0 else "gray", vmin=None if col == 0 else 0, vmax=None if col == 0 else 255)
            axes[row, col].axis("off")
            if row == 0: axes[row, col].set_title(titles[col])
            if col == 0: axes[row, col].set_ylabel(f"pos {pos+1}: {iid}")
    fig.savefig(OUT / "best_method_preview.png", dpi=150)
    plt.close(fig)


def flatten_berkeley(track: str, results: dict[str, dict]) -> list[dict]:
    keys = ["ODS", "ODS_precision", "ODS_recall", "ODS_threshold", "OIS", "OIS_precision", "OIS_recall", "AP"]
    return [{"track": track, "method": name, **{key: value[key] for key in keys}} for name, value in results.items()]


def collect_pr(track_dir: Path, track: str) -> list[dict]:
    rows = []
    for name, _ in METHODS:
        path = track_dir / name / "eval_bdry_thr.txt"
        for line in path.read_text(encoding="utf-8").splitlines():
            fields = line.split()
            if len(fields) >= 4:
                rows.append({"track": track, "method": name, "threshold": fields[0], "recall": fields[1], "precision": fields[2], "f_measure": fields[3]})
    return rows


def write_manifest() -> None:
    methods = []
    for name, _ in METHODS[1:]:
        methods.append({"name": name, "export": {"script": "automation/stage21b_frozen_export.py", "args": ["--method", name, "--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"]}})
    save_json(OUT / "official_eval_manifest.json", {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": methods})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    certification = load_json(ROOT / "results/automation/stage21a_protocol_certification/protocol_certification.json")
    if not certification["stage21a_stop_rule_satisfied"]:
        raise RuntimeError("Stage 21A stop rule is not satisfied")
    write_manifest()
    mod = official_module()
    standard_cfg = load_json(OFFICIAL / "config.json")
    loose_cfg = load_json(OFFICIAL / "config_berkeley_0p025.json")
    bsds_root, benchmark_dir = mod._ensure_benchmark_sources(standard_cfg, "val")
    image_dir = bsds_root / "BSDS500/data/images/val"
    gt_dir = bsds_root / "BSDS500/data/groundTruth/val"
    ids = sorted(path.stem for path in image_dir.glob("*.jpg"))
    if len(ids) != 100: raise RuntimeError("expected exactly 100 BSDS validation images")

    hashes = {}
    for name, pred_dir in METHODS:
        maps = sorted(pred_dir.glob("*.png"))
        if [p.stem for p in maps] != ids: raise RuntimeError(f"frozen manifest mismatch: {name}")
        hashes[name] = {p.name: sha256(p) for p in maps}
    save_json(OUT / "frozen_map_hashes.json", hashes)
    preview(image_dir, gt_dir, ids)

    matlab = mod._matlab_executable(standard_cfg)
    track_results = {}
    for track, cfg in [("berkeley_standard", standard_cfg), ("berkeley_maxdist_0p025_sensitivity", loose_cfg)]:
        results = {}
        base = OUT / track
        for name, pred_dir in METHODS:
            results[name] = mod._evaluate_one(matlab, benchmark_dir=benchmark_dir, image_dir=image_dir, gt_dir=gt_dir, pred_dir=pred_dir, out_dir=base / name, cfg=cfg)
        track_results[track] = results
        write_csv(OUT / ("stage21b_berkeley_standard.csv" if track == "berkeley_standard" else "stage21b_berkeley_0p025_sensitivity.csv"), flatten_berkeley(track, results))
        write_csv(OUT / f"{track}_pr_curve.csv", collect_pr(base, track))

    runtime_dir = ROOT / "results/automation/stage21a_protocol_certification/kitt_runtime"
    kitt_dir = OFFICIAL / "vendor/KITT/boundaryImageComparison"
    ej_spec = OUT / "estrada_jepson_spec.json"
    save_json(ej_spec, {"methods": [{"name": name, "pred_dir": str(path.resolve()).replace("\\", "/")} for name, path in METHODS]})
    ej_json = OUT / "estrada_jepson_grid.json"
    quote = lambda p: str(Path(p).resolve()).replace("\\", "/").replace("'", "''")
    expression = f"addpath('{quote(OFFICIAL / 'matlab')}');stage21b_estrada_jepson_eval('{quote(ej_spec)}','{quote(runtime_dir)}','{quote(kitt_dir)}','{quote(gt_dir)}','{quote(ej_json)}');"
    run = subprocess.run([str(matlab), "-batch", expression], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=24*60*60)
    if run.returncode != 0: raise RuntimeError(f"Estrada-Jepson evaluation failed: {run.stdout}\n{run.stderr}")
    ej_rows = load_json(ej_json)
    write_csv(OUT / "estrada_jepson_pr_curve.csv", ej_rows)
    fuzzy = []
    for name, _ in METHODS:
        subset = [row for row in ej_rows if row["method"] == name]
        fixed = min(subset, key=lambda row: abs(float(row["threshold"]) - 0.5))
        best = max(subset, key=lambda row: (float(row["f_measure"]), -float(row["threshold"])))
        fuzzy.append({"method": name, "fixed_threshold": 0.5, "fixed_precision": fixed["precision"], "fixed_recall": fixed["recall"], "fixed_f_measure": fixed["f_measure"], "best_threshold": best["threshold"], "best_precision": best["precision"], "best_recall": best["recall"], "best_f_measure": best["f_measure"], "comparison_eligibility": "BSDS500 validation; best-public-KITT fidelity; not numerically equivalent to protected-test fuzzy-paper rows; non-promotional"})
    write_csv(OUT / "stage21b_estrada_jepson_0p025_fuzzy_comparison.csv", fuzzy)

    deltas = []
    for name, _ in METHODS:
        primary, loose = track_results["berkeley_standard"][name], track_results["berkeley_maxdist_0p025_sensitivity"][name]
        deltas.append({"method": name, "delta_ODS_loose_minus_primary": loose["ODS"]-primary["ODS"], "delta_OIS_loose_minus_primary": loose["OIS"]-primary["OIS"], "delta_AP_loose_minus_primary": loose["AP"]-primary["AP"], "protocol_warning": "tolerance sensitivity only; not promotion evidence and not Estrada-Jepson"})
    write_csv(OUT / "stage21b_cross_protocol_deltas.csv", deltas)
    summary = {"stage": "stage21b_three_protocol_retrospective_benchmark", "status": "completed", "architecture_changed": False, "detector_fitted": False, "protected_split_used": False, "methods": [name for name, _ in METHODS], "berkeley_reference_reproduction_verified": False, "berkeley_rng_caveat": certification["berkeley_standard"]["exact_blocker"], "estrada_jepson_fidelity": certification["estrada_jepson_0p025"]["fidelity"], "tracks": track_results, "estrada_jepson": fuzzy, "cross_protocol_deltas": deltas, "preview": {"file": "best_method_preview.png", "positions": [1, 50, 100], "columns": ["input", "annotation union", "incumbent", "20A", "20B", "20C", "20D"], "documentary_only": True}, "next_stage_if_complete": "stage21c_pr_ap_anatomy"}
    save_json(OUT / "summary.json", summary)
    (OUT / "summary.md").write_text("# Stage 21B three-protocol retrospective\n\nThe five frozen map sets were rescored without refitting. Berkeley 0.0075 is the primary diagnostic track; Berkeley 0.025 is tolerance sensitivity; Estrada--Jepson 0.025 is a separate best-public-KITT-fidelity fuzzy-literature track. Metrics are not averaged or interchanged, neither 0.025 track can promote a model, and Berkeley reference reproduction remains unverified because the shipped fixture RNG state is unavailable.\n", encoding="utf-8")
    print("STAGE21B_THREE_PROTOCOL_RETROSPECTIVE_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
