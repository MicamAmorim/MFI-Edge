from __future__ import annotations

"""Stage 22B: frozen-map retrospective through the certified thesis pipeline."""

import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.visual_report import write_panel_grid

OUT = ROOT / "results/local_dev/stage22b_thesis_legacy_retrospective_benchmark"
CERT = ROOT / "results/automation/stage22a_thesis_legacy_protocol_certification/summary.json"
LEGACY = ROOT / "evaluation/legacy_thesis"
KITT = ROOT / "vendor/kitt_stage22a/generalImageProcessing"
MATCHER = ROOT / "results/automation/stage21a_protocol_certification/kitt_runtime/estradaJepsonMatching.m"
STAGE21B_KITT = ROOT / "results/local_dev/stage21b_three_protocol_retrospective_benchmark/stage21b_estrada_jepson_0p025_fuzzy_comparison.csv"
METHODS = [
    ("incumbent_compact_positive_choquet", ROOT / "automation/runtime/official_eval_cache/incumbent/val/e4fa09acaf61ec23"),
    ("stage20c_dominant_pair_2additive_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage20c_dominant_pair_2additive_choquet/stage20c_dominant_pair_2additive_choquet/val"),
    ("stage21h_consensus_pairwise_choquet", ROOT / "automation/runtime/official_eval_cache/experiments/stage21h_consensus_pairwise_choquet_retry2/stage21h_consensus_pairwise_choquet/val"),
]
BOOTSTRAP_SEED = 20261028
BOOTSTRAP_REPLICATES = 1000
PREVIEW_POSITIONS = (0, 49, 99)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def official_module():
    path = ROOT / "evaluation/bsds_official/run_official_bsds.py"
    spec = importlib.util.spec_from_file_location("stage22b_official", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def matlab_quote(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def write_matlab_harness(runtime: Path) -> Path:
    harness = runtime / "stage22b_legacy_eval.m"
    harness.write_text(r'''function stage22b_legacy_eval(specJson,vendorDir,kittDir,matcherDir,gtDir,outDir)
addpath(vendorDir); addpath(fullfile(vendorDir,'external')); addpath(kittDir); addpath(matcherDir);
S=jsondecode(fileread(specJson));
for m=1:numel(S.methods)
    method=char(S.methods(m).name); predDir=char(S.methods(m).pred_dir);
    methodOut=fullfile(outDir,'per_image',method); mapOut=fullfile(outDir,'legacy_binary_maps',method);
    if ~exist(methodOut,'dir'), mkdir(methodOut); end
    if ~exist(mapOut,'dir'), mkdir(mapOut); end
    for i=1:numel(S.image_ids)
        imageId=char(S.image_ids{i}); csvPath=fullfile(methodOut,[imageId '.csv']); mapPath=fullfile(mapOut,[imageId '.png']);
        csvDone=false; mapDone=false;
        if exist(csvPath,'file'), d=dir(csvPath); csvDone=d.bytes>0; end
        if exist(mapPath,'file'), d=dir(mapPath); mapDone=d.bytes>0; end
        if csvDone && mapDone, continue; end
        score=double(imread(fullfile(predDir,[imageId '.png'])))/255;
        [~,boundary]=getBoundaries(score,inf); boundary=boundary>0;
        G=load(fullfile(gtDir,[imageId '.mat'])); n=numel(G.groundTruth); gt=cell(1,n);
        for g=1:n, gt{g}=struct('Boundaries',logical(G.groundTruth{g}.Boundaries)); end
        vals=ComparisonResiduals('ejBCM-F',boundary,gt,0.025);
        T=table(repmat(string(imageId),n,1),repmat(string(method),n,1),(1:n)',vals(:,1),vals(:,2),vals(:,3),...
            'VariableNames',{'image_id','method','gt_index','precision','recall','f0_5'});
        tmp=[csvPath '.tmp.csv']; writetable(T,tmp); movefile(tmp,csvPath,'f'); imwrite(uint8(boundary)*255,mapPath);
        fprintf('STAGE22B_LEGACY %s %03d/%03d %s\n',method,i,numel(S.image_ids),imageId);
    end
end
end
''', encoding="utf-8")
    return harness


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    n = len(values)
    draws = rng.integers(0, n, size=(BOOTSTRAP_REPLICATES, n))
    means = values[draws].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def aggregate(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    by_method_image: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        by_method_image.setdefault((row["method"], row["image_id"]), []).append(row)
    per_image = []
    for (method, image_id), values in sorted(by_method_image.items()):
        f = np.array([float(v["f0_5"]) for v in values])
        best = int(np.argmax(f))
        per_image.append({"method": method, "image_id": image_id, "n_gt": len(values),
                          "best_gt_index": int(values[best]["gt_index"]), "best_f0_5": float(f[best]),
                          "mean_gt_f0_5": float(f.mean()), "median_gt_f0_5": float(np.median(f))})
    summaries, best_gt_rows = [], []
    for method, _ in METHODS:
        image_rows = [r for r in per_image if r["method"] == method]
        all_rows = [r for r in rows if r["method"] == method]
        best = np.array([r["best_f0_5"] for r in image_rows], dtype=float)
        per_image_mean = np.array([r["mean_gt_f0_5"] for r in image_rows], dtype=float)
        all_f = np.array([float(r["f0_5"]) for r in all_rows], dtype=float)
        rng = np.random.default_rng(BOOTSTRAP_SEED)
        ci_lo, ci_hi = bootstrap_ci(best, rng)
        summaries.append({
            "method": method, "n_images": len(image_rows), "n_image_gt_pairs": len(all_rows),
            "best_f0_5_mean": float(best.mean()), "best_f0_5_median": float(np.median(best)),
            "best_f0_5_q25": float(np.quantile(best, .25)), "best_f0_5_q75": float(np.quantile(best, .75)),
            "best_f0_5_mean_bootstrap_ci_low": ci_lo, "best_f0_5_mean_bootstrap_ci_high": ci_hi,
            "all_per_gt_f0_5_mean": float(all_f.mean()), "all_per_gt_f0_5_median": float(np.median(all_f)),
            "per_image_mean_gt_f0_5_mean": float(per_image_mean.mean()),
            "per_image_mean_gt_f0_5_median": float(np.median(per_image_mean)),
            "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "promotional": False,
        })
        indices = sorted(set(int(r["best_gt_index"]) for r in image_rows))
        for index in indices:
            best_gt_rows.append({"method": method, "gt_index": index,
                                 "best_match_image_count": sum(int(r["best_gt_index"]) == index for r in image_rows),
                                 "note": "GT index is image-local; distribution is descriptive"})
    return summaries, per_image, best_gt_rows


def preview(image_dir: Path, gt_dir: Path, ids: list[str]) -> None:
    rows = []
    for pos in PREVIEW_POSITIONS:
        iid = ids[pos]
        image = np.asarray(Image.open(image_dir / f"{iid}.jpg").convert("RGB"))
        boundaries = extract_boundaries(loadmat(gt_dir / f"{iid}.mat"))
        union = np.any(np.stack(boundaries), axis=0)
        incumbent = np.asarray(Image.open(METHODS[0][1] / f"{iid}.png"))
        candidate = np.asarray(Image.open(METHODS[1][1] / f"{iid}.png"))
        stage21h = np.asarray(Image.open(METHODS[2][1] / f"{iid}.png"))
        incumbent_binary = np.asarray(Image.open(OUT / "legacy_binary_maps" / METHODS[0][0] / f"{iid}.png"))
        candidate_binary = np.asarray(Image.open(OUT / "legacy_binary_maps" / METHODS[1][0] / f"{iid}.png"))
        stage21h_binary = np.asarray(Image.open(OUT / "legacy_binary_maps" / METHODS[2][0] / f"{iid}.png"))
        rows.append([image, union, incumbent, incumbent_binary, candidate, candidate_binary, stage21h, stage21h_binary])
    write_panel_grid(OUT / "best_method_preview.png", rows, panel_height=180, panel_width=180)


def write_manifest() -> None:
    save_json(OUT / "official_eval_manifest.json", {
        "schema_version": 1, "split": "val", "include_incumbent": True,
        "methods": [{"name": name, "export": {"script": "automation/stage22b_frozen_export.py",
                    "args": ["--method", name, "--image-dir", "{image_dir}",
                             "--output-dir", "{output_dir}", "--split", "{split}"]}}
                    for name, _ in METHODS[1:]],
        "stage22_note": "Unchanged frozen-map attachment only; Stage 22B is comparison-only and cannot promote a detector.",
    })


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    write_manifest()
    cert = load_json(CERT)
    if not (cert.get("source_hashes_ok") and cert.get("ejBCM_microcases_pass") and cert.get("getBoundaries_smoke_pass")):
        raise RuntimeError("Stage 22A certification gate is not satisfied")
    mod = official_module()
    cfg = load_json(ROOT / "evaluation/bsds_official/config.json")
    bsds_root, _ = mod._ensure_benchmark_sources(cfg, "val")
    image_dir = bsds_root / "BSDS500/data/images/val"
    gt_dir = bsds_root / "BSDS500/data/groundTruth/val"
    ids = sorted(p.stem for p in image_dir.glob("*.jpg"))
    if len(ids) != 100:
        raise RuntimeError("expected exactly 100 BSDS500-validation images")
    frozen_hashes = {}
    for name, path in METHODS:
        maps = sorted(path.glob("*.png"))
        if [p.stem for p in maps] != ids:
            raise RuntimeError(f"frozen-map manifest mismatch for {name}")
        frozen_hashes[name] = {p.name: sha256(p) for p in maps}
    save_json(OUT / "frozen_map_hashes.json", frozen_hashes)

    runtime = OUT / "matlab_runtime"
    runtime.mkdir(exist_ok=True)
    shutil.copyfile(MATCHER, runtime / "estradaJepsonMatching.m")
    write_matlab_harness(runtime)
    spec = {"image_ids": ids, "methods": [{"name": n, "pred_dir": p.resolve().as_posix()} for n, p in METHODS]}
    save_json(OUT / "matlab_spec.json", spec)
    matlab = mod._matlab_executable(cfg)
    expr = (f"addpath('{matlab_quote(runtime)}');stage22b_legacy_eval('{matlab_quote(OUT / 'matlab_spec.json')}',"
            f"'{matlab_quote(LEGACY)}','{matlab_quote(KITT)}','{matlab_quote(runtime)}',"
            f"'{matlab_quote(gt_dir)}','{matlab_quote(OUT)}');")
    run = subprocess.run([str(matlab), "-batch", expr], cwd=ROOT, text=True, capture_output=True,
                         encoding="utf-8", errors="replace", timeout=5 * 60 * 60)
    (OUT / "matlab_stdout.log").write_text(run.stdout, encoding="utf-8")
    (OUT / "matlab_stderr.log").write_text(run.stderr, encoding="utf-8")
    if run.returncode != 0:
        raise RuntimeError(f"legacy MATLAB evaluation failed with return code {run.returncode}")

    rows = []
    for method, _ in METHODS:
        for iid in ids:
            path = OUT / "per_image" / method / f"{iid}.csv"
            if not path.exists() or path.stat().st_size == 0:
                raise RuntimeError(f"missing checkpoint {path}")
            with path.open(newline="", encoding="utf-8") as handle:
                rows.extend(dict(row) for row in csv.DictReader(handle))
    summaries, per_image, best_gt = aggregate(rows)
    write_csv(OUT / "per_image_per_gt_metrics.csv", rows)
    write_csv(OUT / "per_image_best_and_mean.csv", per_image)
    write_csv(OUT / "legacy_summary.csv", summaries)
    write_csv(OUT / "best_gt_distribution.csv", best_gt)

    with STAGE21B_KITT.open(newline="", encoding="utf-8") as handle:
        kitt = [row for row in csv.DictReader(handle) if row["method"] in {name for name, _ in METHODS}]
    for row in kitt:
        row["separate_protocol_warning"] = "Certified aggregate KITT threshold track; not thesis getBoundaries/per-GT best-match metric"
    write_csv(OUT / "separate_stage21b_kitt_reference.csv", kitt)
    preview(image_dir, gt_dir, ids)

    save_json(OUT / "summary.json", {
        "stage": "stage22b_thesis_legacy_retrospective_benchmark", "status": "completed",
        "scientific_experiment_index": "2/5", "architecture_changed": False, "detector_fitted": False,
        "promotion_allowed": False, "protected_split_used": False, "split": "BSDS500 validation (development)",
        "methods": [name for name, _ in METHODS], "stage21h_included": True,
        "stage21h_inclusion_note": "Included only as the program-authorized labeled rejected diagnostic comparator; its exact retry-2 validation cache contained all 100 frozen maps.",
        "legacy_contract": cert["legacy_contract"], "legacy_results": summaries,
        "separate_kitt_reference_file": "separate_stage21b_kitt_reference.csv",
        "protocol_warning": "Thesis legacy, aggregate KITT 0.025, Berkeley 0.025, and standard Berkeley 0.0075 are distinct. Stage 22B cannot promote or tune a detector.",
        "preview": {"file": "best_method_preview.png", "positions": [1, 50, 100],
                    "columns": ["input", "annotation_union", "incumbent_continuous", "incumbent_legacy_binary",
                                "stage20c_continuous", "stage20c_legacy_binary",
                                "stage21h_continuous", "stage21h_legacy_binary"], "documentary_only": True},
        "official_attachment": "Unchanged frozen incumbent and Stage-20C maps; non-promotional documentary attachment.",
        "next_stage_if_complete": "stage22c_inter_image_score_calibration_diagnosis",
    })
    (OUT / "summary.md").write_text(
        "# Stage 22B thesis-legacy retrospective\n\nFrozen maps only. The thesis getBoundaries -> per-annotation ejBCM-F path is reported separately from the aggregate KITT and Berkeley protocols. All metrics are descriptive and non-promotional.\n",
        encoding="utf-8")
    print("STAGE22B_THESIS_LEGACY_RETROSPECTIVE_COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
