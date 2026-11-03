#!/usr/bin/env python3
"""Archive Stage24G-L's verified scientific outputs for git, never raw datasets.

Use --stage only after the complete campaign (or --allow-partial for inspection).
Never commits or pushes automatically.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"results/local_dev/stage24_paper_a_recertification"
OFFICIAL=ROOT/"results/official_eval/stage24_paper_a_recertification"
DEST=ROOT/"results/paper_a_evidence/stage24gl"
FILES=(
    "environment.lock.txt", "environment_manifest.json",
    "preflight.json", "strict_math_contracts.json",
    "campaign_source_fingerprint.json",
    "native_dataset_manifest.json", "descriptor_provenance.csv",
    "campaign_progress.json", "pair_complementarity_all_folds.csv",
    "pair_complementarity_ranked.csv", "geometry_impact_stage24_proxy.csv",
    "individual_descriptors_corrected_fold.csv",
    "individual_descriptors_corrected_per_image.csv",
    "aggregator_landscape_fold.csv", "aggregator_landscape_per_image.csv",
    "inner_cv_trials.csv", "selected_recipes_fold.csv",
    "selected_recipes_per_image.csv", "inner_selected_heldout.csv",
    "inner_selected_heldout_per_image.csv",
    "suppressor_ablation_fold.csv", "suppressor_ablation_per_image.csv",
    "frozen_models.json", "official_eval_manifest.json",
    "literature_aggregator_landscape_fold.csv",
    "literature_aggregator_landscape_per_image.csv",
    "frozen_literature_models.json", "literature_transfer_guard.json",
    "official_bsds_summary.json", "final_claim_guard.json",
    "statistical_tests_exploratory.csv", "claim_status.csv",
    "PAPER_A_METHODS_RESULTS_STATUS.md", "summary.json",
    "descriptor_scale_audit.csv", "trivial_density_baselines_per_image.csv",
    "runtime_end_to_end_per_image.csv", "runtime_end_to_end_manifest.json",
    "aggregator_image_bootstrap_ci.csv",
    "best_single_train_selected_fold.csv", "best_single_train_selected_per_image.csv",
    "logistic_weighted_rank_equivalence_per_image.csv",
    "historical_stage23d_formula_control.csv",
    "calibration_ablation_fold.csv", "calibration_ablation_per_image.csv",
    "membership_score_histograms.csv", "factorial_variance_decomposition.json",
    "complementarity_predictive_test.json", "complementarity_predictive_pairs.csv",
    "friedman_aggregator_image_tests.csv",
    "paper_a_aggregator_group_descriptives.csv",
    "bootstrap_paired_ods_ois_ap.csv", "bootstrap_integrity.json",
    "historical_stage24_bootstrap_guard.json",
    "historical_stage23f_bootstrap_guard.json",
    "historical_stage23f_paired_bootstrap/bootstrap_paired_ods_ois_ap.csv",
    "historical_stage23f_paired_bootstrap/bootstrap_integrity.json",
    "historical_stage24_paired_bootstrap/bootstrap_paired_ods_ois_ap.csv",
    "historical_stage24_paired_bootstrap/bootstrap_integrity.json",
)


def checksum(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def json_write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2),encoding="utf-8")


def csv_write(path,columns,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def safe_copy(source,dest,rows,limit=25_000_000):
    if source.is_symlink():
        raise RuntimeError("Refusing symlink: "+str(source))
    if source.stat().st_size>limit:
        raise RuntimeError("Scientific evidence file exceeds Git archive size limit: "+str(source))
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,dest)
    if checksum(source)!=checksum(dest):
        raise RuntimeError("Archive source checksum mismatch: "+str(source))
    rows.append({
        "source":source.relative_to(ROOT).as_posix(),
        "destination":dest.relative_to(ROOT).as_posix(),
        "bytes":source.stat().st_size,"sha256":checksum(source),
    })


def consolidate_official(rows, allow_partial):
    summary=OFFICIAL/"summary.json"
    if not summary.is_file():
        if not allow_partial:
            raise RuntimeError("Official Berkeley summary missing; run --phase k first")
        return {"status":"pending"}
    official=json.loads(summary.read_text(encoding="utf-8"))
    if official.get("status")!="completed":
        raise RuntimeError("Official Berkeley summary is not complete")
    safe_copy(summary,DEST/"official_bsds"/"summary.json",rows)
    source_rows=[]
    threshold_rows=[]
    counts={}
    for folder in sorted((OFFICIAL/"matlab").glob("*")):
        if not folder.is_dir() or folder.is_symlink():
            continue
        method=folder.name
        paths=sorted(folder.glob("*_ev1.txt"))
        if not paths:
            continue
        counts[method]=len(paths)
        if len(paths)!=100 and not allow_partial:
            raise RuntimeError(f"Expected 100 official images for {method}, got {len(paths)}")
        original=folder/"official_summary.json"
        if original.exists():
            safe_copy(original,DEST/"official_bsds"/"method_summaries"/(method+".json"),rows)
        for src in paths:
            image=src.stem.removesuffix("_ev1")
            data=[]
            for ln in src.read_text(encoding="utf-8").splitlines():
                val=ln.strip().split()
                if not val:continue
                if len(val)!=5:
                    raise RuntimeError(f"Invalid Berkeley numeric source row in {src}")
                data.append(val)
            if len(data)!=99:
                raise RuntimeError(f"Berkeley expected 99 thresholds, got {len(data)} in {src}")
            source_rows.append({
                "method":method,"image_id":image,
                "source":src.relative_to(ROOT).as_posix(),
                "sha256":checksum(src),"threshold_rows":len(data),
            })
            for val in data:
                threshold_rows.append({
                    "method":method,"image_id":image,
                    "threshold":val[0],"cntR":val[1],"sumR":val[2],
                    "cntP":val[3],"sumP":val[4],
                })
    csv_write(DEST/"official_bsds"/"per_image_source_manifest.csv",
              ["method","image_id","source","sha256","threshold_rows"],source_rows)
    csv_write(DEST/"official_bsds"/"per_image_threshold_counts.csv",
              ["method","image_id","threshold","cntR","sumR","cntP","sumP"],threshold_rows)
    expected=len(official.get("methods",{}))
    if expected and len(counts)!=expected and not allow_partial:
        raise RuntimeError(f"Official method count mismatch {len(counts)}/{expected}")
    return {"status":"completed","per_image_files":len(source_rows),
            "threshold_rows":len(threshold_rows),"method_images":counts,
            "reference_reproduction_verified":bool(official.get("evaluator",{}).get("reference_reproduction_verified",False))}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage",action="store_true")
    ap.add_argument("--allow-partial",action="store_true",
                    help="Allow incomplete package for inspection; never stage automatically")
    ap.add_argument("--replace",action="store_true")
    args=ap.parse_args()
    if not (ROOT/".git").exists():
        ap.error("Not a Git checkout of MFI-Edge")
    sm=SOURCE/"summary.json"
    if not sm.is_file():ap.error("Stage24G-L results not found")
    state=json.loads(sm.read_text(encoding="utf-8"))
    complete=state.get("status")=="completed" and state.get("full_cv_folds")==15
    if not complete and not args.allow_partial:
        ap.error("Scientific campaign incomplete. Use --allow-partial for inspection only.")
    if DEST.is_symlink():ap.error("Archive destination must not be a symlink")
    if DEST.exists():
        if not args.replace:ap.error("Archive exists; use --replace after reviewing")
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    rows=[];missing=[]
    for name in FILES:
        path=SOURCE/name
        if path.is_file():
            safe_copy(path,DEST/"campaign"/name,rows)
        else:
            missing.append(name)
    official=consolidate_official(rows,args.allow_partial)
    required={"environment.lock.txt","environment_manifest.json",
              "preflight.json","strict_math_contracts.json",
              "campaign_source_fingerprint.json","native_dataset_manifest.json",
              "pair_complementarity_ranked.csv",
              "individual_descriptors_corrected_per_image.csv",
              "aggregator_landscape_per_image.csv",
              "suppressor_ablation_per_image.csv",
              "inner_cv_trials.csv","frozen_models.json","claim_status.csv",
              "best_single_train_selected_fold.csv",
              "calibration_ablation_per_image.csv",
              "membership_score_histograms.csv",
              "trivial_density_baselines_per_image.csv",
              "factorial_variance_decomposition.json",
              "historical_stage23d_formula_control.csv"}
    absent=sorted(required.intersection(missing))
    if absent and not args.allow_partial:
        raise RuntimeError("Required science files absent: "+", ".join(absent))
    csv_write(DEST/"source_provenance.csv",
              ["source","destination","bytes","sha256"],rows)
    manifest={
        "schema_version":1,"experiment":"stage24_paper_a_recertification",
        "complete":complete,"not_a_new_experiment":True,
        "source_file_count":len(rows),"missing_optional":missing,
        "missing_required":absent,"official":official,
        "literature_status":json.loads((SOURCE/"literature_transfer_guard.json").read_text(encoding="utf-8")) if (SOURCE/"literature_transfer_guard.json").is_file() else {"status":"unknown"},
        "claims_eligible":False,
        "note":"BSDS val is development; independent Berkeley reproduction and protected multi-benchmark still pending.",
    }
    json_write(DEST/"archive_manifest.json",manifest)
    print("Archive:",DEST.relative_to(ROOT),"files:",len(rows),
          "complete:",complete,"official:",official.get("status"))
    if args.stage:
        if args.allow_partial or not complete:
            raise RuntimeError("Refusing to stage incomplete scientific evidence")
        subprocess.run(["git","add","--",DEST.relative_to(ROOT).as_posix()],
                       cwd=ROOT,check=True)
        print("Prepared staging. Check manifest, then commit/push explicitly.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
