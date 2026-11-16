#!/usr/bin/env python3
"""Paper A one-command checkpointed completion orchestrator.

SAFE BY DEFAULT. Never makes protocol frozen, approves a scientific cohort,
fits H1/H2 parameters, or opens protected GT/H5/F1 before an independently
signed freeze. Runs existing verified prefreeze audit only if no suitable
recent copy is available, packages methods evidence, and lists exact blockers.

After all preregistered gates have been independently approved, the SAME
command can analyze certified image-level X/Y output and assemble a review-
ready manuscript supplement plus a source/checksum bundle. The scientifically
certified image-to-GT evaluator is NOT implemented by this orchestrator:
it must produce signed outcomes following an independently audited contract.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(r"F:\MFI-Edge-Data\MultiCue")
WORK = DATA / "paper_a_completion"
AUDITS = DATA / "paper_a_prefreeze_combined_audit"
PROTOCOL = ROOT / "docs/paper_a_confirmation/protocol.json"
DRAFT = DATA / "paper_a_H1_H2_recipe_P0_1_DRAFT.json"
SCHEMA = "paper_a_completion_v1"
GATES = (
    "development_parameter_lineage",
    "H2_capacity_and_all_four_thresholds",
    "dataset_and_GT_semantics",
    "independent_scene_and_prior_exposure_audit",
    "N_and_domain_blocked_inference",
    "signed_frozen_commit_before_first_GT",
    "certified_independent_outcome_evaluator",
)
AGENT_TASKS = ROOT / "docs/paper_a_confirmation/PAPER_A_COMPLETION_TASKS.md"


def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")


def file_sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1<<20),b""):
            h.update(c)
    return h.hexdigest()


def run(argv, timeout=1800, log_path=None):
    if log_path:
        log_path.parent.mkdir(parents=True,exist_ok=True)
        with log_path.open("wb") as f:
            p=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,
                             timeout=timeout,check=False)
        return p.returncode
    return subprocess.run(argv,cwd=ROOT,timeout=timeout,check=False).returncode


def git(*args):
    p=subprocess.run(["git",*args],cwd=ROOT,capture_output=True,
                     text=True,check=False,timeout=50)
    if p.returncode:
        raise RuntimeError("Git command failed: "+" ".join(args))
    return p.stdout.strip()


def git_safety():
    branch=git("branch","--show-current")
    if branch!="experiment/paper-a-conditional-confirmation":
        raise RuntimeError("Use Paper A scientific-confirmation branch")
    tracked=git("status","--porcelain","--untracked-files=no")
    if tracked:
        raise RuntimeError("Tracked Git modifications are present; controller will not overwrite")
    return git("rev-parse","HEAD")


def good_audit(report: dict) -> bool:
    return (report.get("status") ==
                "TECHNICAL_AUDITS_OK_SCIENTIFIC_GATES_STILL_OPEN"
            and report.get("failures")==[]
            and report.get("phases",{}).get("P0_4_cache_SHA256",{}).get("matched")==56
            and report.get("GT_H5_F1_or_confirmatory_data_opened") is False
            and report.get("new_training_or_descriptor_reprocessing") is False)


def audit_exists(repository_head: str):
    if not AUDITS.is_dir():
        return None
    for p in sorted(AUDITS.glob("prefreeze_*.json"),reverse=True)[:30]:
        if p.is_symlink() or p.stat().st_size>1_500_000:
            continue
        try:
            report=json.loads(p.read_text(encoding="utf-8"))
        except (ValueError,UnicodeError,OSError):
            continue
        if not good_audit(report):
            continue
        source=report.get("git_commit")
        if not isinstance(source,str) or len(source)!=40:
            continue
        ancestor=subprocess.run(
            ["git","merge-base","--is-ancestor",source,repository_head],
            cwd=ROOT,capture_output=True,check=False,timeout=45)
        if ancestor.returncode:
            continue
        changed=subprocess.run(
            ["git","diff","--name-only",source,repository_head,"--",
             "src/","run_stage24_paper_a_recertification.py"],
            cwd=ROOT,capture_output=True,text=True,check=False,timeout=45)
        if changed.returncode or changed.stdout.strip():
            continue
        return {"path":str(p),"sha256":file_sha256(p),
                "status":"REUSED_VERIFIED_56_56_WITH_UNCHANGED_SCIENTIFIC_CODE",
                "observed_sha256_matches":56}
    return None


def ensure_audit(head: str, folder: Path):
    existing=audit_exists(head)
    if existing:
        print("[1/5] Reusing prior 56/56 technical audit; no cache recomputation",flush=True)
        return existing
    print("[1/5] Running technical prefreeze audit (read-only 56 cache hashes)",flush=True)
    log=folder/"technical_audit.log"
    rc=run([sys.executable,"-u",str(ROOT/"scripts/run_paper_a_prefreeze_one_shot.py")],
           timeout=4500,log_path=log)
    verified=audit_exists(head)
    if rc!=0 or not verified:
        return {"status":"TECHNICAL_AUDIT_FAILED",
                "exit_code":rc,"log":str(log)}
    return verified


def count_recipe_missing(draft: dict) -> list[str]:
    if not isinstance(draft,dict) or draft.get("schema")!="paper_a_h1h2_recipe_P0_1":
        return ["H1/H2 recipe missing or unrecognized"]
    pending=[]
    for h in draft.get("hypotheses",[]):
        hid=h.get("id","?")
        membership=h.get("membership",{})
        for key in ("midpoint","scale"):
            if membership.get(key) is None:
                pending.append(hid+".membership."+key)
        for key in ("candidate","control"):
            op=h.get(key,{})
            if op.get("threshold") is None:
                pending.append(hid+"."+key+".threshold")
            proof=op.get("threshold_fit_provenance",{})
            if not isinstance(proof,dict) or any(v is None for v in proof.values()):
                pending.append(hid+"."+key+".threshold_fit_provenance")
        p=membership.get("fit_provenance",{})
        if not isinstance(p,dict) or any(v is None for v in p.values()):
            pending.append(hid+".membership.fit_provenance")
        if hid=="H2":
            can=h.get("candidate",{})
            if can.get("capacity") is None or can.get("mobius") is None:
                pending.append("H2.choquet.capacity_and_mobius")
            p=can.get("capacity_fit_provenance",{})
            if not isinstance(p,dict) or any(v is None for v in p.values()):
                pending.append("H2.capacity_fit_provenance")
    if len(draft.get("hypotheses",[]))!=2:
        pending.append("Two fixed H1/H2 hypothesis records")
    return pending


def approval_template():
    """A NON-authorizing template. Never auto-generates true approvals."""
    return {
        "schema_version":1,
        "approved_for_first_confirmatory_outcome_access":False,
        "reviewed_by":None,"approved_utc":None,"freeze_commit":None,
        "protocol_sha256":None,"cohort_sha256":None,"recipe_sha256":None,
        "scientific_approvals": {
            "training_lineage":False,
            "capacity_and_thresholds":False,
            "ground_truth_semantics":False,
            "independent_scenes_and_exposure":False,
            "sample_size_and_inference":False,
            "independent_protocol_review":False,
        },
        "review_notes":"NOT APPROVED; reviewer must document every scientific gate.",
    }


def safe_write_template(path:Path,obj:dict):
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("x",encoding="utf-8") as f:
            json.dump(obj,f,indent=2,ensure_ascii=False)


def make_repro_baseline(folder: Path) -> dict:
    print("[4/5] Creating separate technical reproducibility snapshot",flush=True)
    log=folder/"package.log"
    outdir=DATA/"paper_a_publication"
    rc=run([sys.executable,str(ROOT/"scripts/package_paper_a_repro.py"),
            "--outdir",str(outdir)],timeout=300,log_path=log)
    if rc:
        return {"status":"PACKAGE_FAILED","log":str(log),"exit_code":rc}
    files=sorted(outdir.glob("PaperA_repro_preconfirmatory_*.zip"))
    if not files:
        return {"status":"PACKAGE_MISSING","log":str(log)}
    latest=max(files,key=lambda x:x.stat().st_mtime)
    return {"status":"PACKAGED","path":str(latest),
            "zip_sha256":file_sha256(latest),"bytes":latest.stat().st_size}


def write_gate_status(folder: Path, state: dict):
    folder.mkdir(parents=True,exist_ok=True)
    output=folder/("state_"+stamp()+".json")
    output.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
    (WORK/"LAST_STATUS.json").write_text(
        json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Paper A — completion pipeline status",
           "","**Outcome:** "+state["status"],"",
           "Source Git commit: "+str(state["source_commit"]), "",
           "## Verified technical evidence",
           "","- UDED cache hash audit: "+state["technical_audit"]["status"],
           "- No confirmed H1/H2 outcome was inferred by the prefreeze phase.",
           "",
           "## Required scientific gates (fail closed)",""]
    lines.extend("- "+line for line in state["blockers"])
    lines+=["","## Paths",
            "","- Status JSON: "+str(output),
            "- Baseline ZIP: "+str(state.get("reproducibility",{}).get("path")),
            "- Manuscript source: docs/paper_a_confirmation/PAPER_A_MANUSCRIPT_DRAFT.md",
            "","The program never auto-approves GT/F1 access; use explicit freeze review.",
            ""]
    (WORK/"NEXT_ACTIONS.md").write_text("\n".join(lines),encoding="utf-8")


def package_confirmatory(folder:Path,analysis_folder:Path,state:dict):
    """Curated research supplement, explicitly pending independent review."""
    draft=ROOT/"docs/paper_a_confirmation/PAPER_A_MANUSCRIPT_DRAFT.md"
    supplement=analysis_folder/"results.md"
    combined=analysis_folder/"PAPER_A_COMPLETE_REVIEW_DRAFT.md"
    combined.write_text(
        draft.read_text(encoding="utf-8")+
        "\n\n---\n\n# Confirmatory results supplement (independent audit pending)\n\n"+
        supplement.read_text(encoding="utf-8"),encoding="utf-8")
    included=[draft,combined,supplement,analysis_folder/"results.json",
              WORK/"NEXT_ACTIONS.md"]
    names=["manuscript/source_draft.md","manuscript/review_draft_with_results.md",
           "analysis/results.md","analysis/results.json",
           "status/NEXT_ACTIONS.md"]
    index={"status":"FROZEN_ANALYSIS_COMPLETED_EXTERNAL_REVIEW_REQUIRED",
           "source_commit":state["source_commit"],
           "files":[{"path":name,"sha256":file_sha256(path),"bytes":path.stat().st_size}
                    for path,name in zip(included,names)]}
    zipped=analysis_folder/"PaperA_frozen_analysis_review_bundle.zip"
    with zipfile.ZipFile(zipped,"x",compression=zipfile.ZIP_DEFLATED) as f:
        for path,name in zip(included,names):
            f.write(path,arcname=name)
        f.writestr("MANIFEST.json",json.dumps(index,indent=2))
    with zipfile.ZipFile(zipped) as f:
        for row in index["files"]:
            if hashlib.sha256(f.read(row["path"])).hexdigest()!=row["sha256"]:
                raise RuntimeError("Analysis ZIP SHA256 mismatch")
    return {"status":index["status"],"zip":str(zipped),
            "sha256":file_sha256(zipped)}


def run_pipeline(base:Path=WORK, *, no_reaudit:bool=False,
                 skip_baseline_zip:bool=False,
                 authorize_uded_development_gt:bool=False) -> dict:
    base.mkdir(parents=True,exist_ok=True)
    folder=base/("run_"+stamp())
    folder.mkdir(parents=False,exist_ok=False)
    print("[START] Paper A gated completion pipeline",flush=True)
    head=git_safety()
    protocol=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    audit=audit_exists(head) if no_reaudit else ensure_audit(head,folder)
    if audit is None:
        audit={"status":"NO_RECENT_VALID_AUDIT"}
    dev_fit={"status":"NOT_REQUESTED"}
    if authorize_uded_development_gt:
        if audit["status"]!="REUSED_VERIFIED_56_56_WITH_UNCHANGED_SCIENTIFIC_CODE":
            dev_fit={"status":"REFUSED_WITHOUT_CURRENT_TECHNICAL_AUDIT"}
        else:
            print("[DEV FIT] Reading only explicitly authorized UDED-14 DEVELOPMENT GT",flush=True)
            log=folder/"development_fit.log"
            rc=run([sys.executable,
                    str(ROOT/"scripts/fit_paper_a_development_uded14.py"),
                    "--authorize-uded-development-gt",
                    "--output-dir",str(base)],
                   timeout=21600,log_path=log)
            dev_fit={"status":"FITTED_UNATTESTED" if rc==0 else "DEVELOPMENT_FIT_FAILED",
                     "log":str(log),"exit_code":rc,
                     "requires_independent_overlap_attestation":True}
    draft=json.loads(DRAFT.read_text(encoding="utf-8")) if DRAFT.is_file() else {}
    missing=count_recipe_missing(draft)
    safe_write_template(base/"freeze_approval.template.json",approval_template())
    frozen_recipe=base/"frozen_H1_H2_recipe.json"
    cohort=base/"frozen_cohort_manifest.csv"
    approval=base/"freeze_approval.json"
    outcomes=base/"certified_outcomes.csv"
    outcome_prov=base/"certified_outcomes_provenance.json"
    blockers=[]
    if audit["status"] not in ("REUSED_VERIFIED_56_56_WITH_UNCHANGED_SCIENTIFIC_CODE",):
        blockers.append("Technical SHA audit not currently verified")
    if missing and protocol.get("status") != "frozen":
        blockers.append("P0.1 H1/H2 training recipe missing: "+", ".join(missing))
    if dev_fit["status"]=="DEVELOPMENT_FIT_FAILED":
        blockers.append("Explicit development fitting failed; review development_fit.log")
    if dev_fit["status"]=="FITTED_UNATTESTED":
        blockers.append("Development-fit exports produced but independent training/overlap attestation still required")
    if protocol.get("status")!="frozen":
        blockers.append("Protocol draft_not_frozen; scientific freeze review required")
    if not frozen_recipe.is_file():
        blockers.append("Missing independently certified frozen_H1_H2_recipe.json")
    if not cohort.is_file():
        blockers.append("Missing scene-level reviewed frozen_cohort_manifest.csv")
    if not approval.is_file():
        blockers.append("Missing signed freeze_approval.json; see NON-APPROVING template")
    print("[2/5] Checking science gates; no protected outcomes accessed",flush=True)
    gate=None
    if not any(b.startswith("Missing") or b.startswith("Protocol") for b in blockers):
        from paper_a_freeze_guard import validate_files
        gate=validate_files(PROTOCOL,frozen_recipe,cohort,approval)
        blockers.extend(gate["blockers"])
    if gate and not gate["blockers"]:
        if not outcomes.is_file():
            blockers.append(
                "No certified_outcomes.csv from an independently audited "
                "frozen image/GT evaluator (the evaluator must be implemented "
                "and independently certified, not substituted with synthetic output)")
        if not outcome_prov.is_file():
            blockers.append("Missing certified_outcomes_provenance.json")
    elif outcomes.is_file():
        print("[SAFETY] Existing results files NOT opened: freeze gate failed",
              flush=True)
    state={
        "schema":SCHEMA,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "source_commit":head,
        "status":"PREFREEZE_SCIENTIFIC_GATES_OPEN",
        "technical_audit":audit,
        "recipe_structural_pending":missing,
        "protocol_status":protocol.get("status"),
        "development_fit":dev_fit,
        "freeze_certified":bool(gate and not gate["blockers"]),
        "blockers":sorted(set(blockers)),
        "protected_GT_H5_F1_opened_by_prefreeze":False,
        "automatic_freeze_performed":False,
    }
    if gate and not gate["blockers"] and outcomes.is_file() and outcome_prov.is_file():
        print("[3/5] Signed freeze validated; analyzing certified image outcomes",
              flush=True)
        from analyze_paper_a_confirmed import run_confirmation
        result,path=run_confirmation(PROTOCOL,frozen_recipe,cohort,approval,
                                     outcomes,outcome_prov,base)
        state["analysis"]={"status":result["status"],"path":str(path),
                          "primary_decisions":{a["hypothesis"]:a["confirmed"]
                                               for a in result["analyses"]}}
        state["status"]="FROZEN_ANALYSIS_REQUIRES_INDEPENDENT_REVIEW"
        state["blockers"]=["Independent review of final numerical report and article required"]
    else:
        print("[3/5] Outcome access BLOCKED until all signed gates pass",flush=True)
    if not skip_baseline_zip:
        state["reproducibility"]=make_repro_baseline(folder)
    else:
        state["reproducibility"]={"status":"SKIPPED_BY_USER"}
    if state["reproducibility"]["status"] not in ("PACKAGED","SKIPPED_BY_USER"):
        state["status"]="TECHNICAL_ERROR_BLOCKED"
        state["blockers"].append("Reproducibility baseline packaging failed")
    if state["development_fit"]["status"]=="DEVELOPMENT_FIT_FAILED":
        state["status"]="TECHNICAL_ERROR_BLOCKED"
    write_gate_status(folder,state)
    if state.get("analysis"):
        state["confirmatory_package"]=package_confirmatory(folder,Path(state["analysis"]["path"]),state)
        write_gate_status(folder,state)
    print("[5/5] Final status:",state["status"],flush=True)
    print("[STATUS]",str(base/"LAST_STATUS.json"),flush=True)
    print("[NEXT]",str(base/"NEXT_ACTIONS.md"),flush=True)
    return state


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace",type=Path,default=WORK)
    p.add_argument("--no-reaudit",action="store_true",
                   help="Use previous verified SHA record only; do not read map bytes")
    p.add_argument("--skip-baseline-zip",action="store_true")
    p.add_argument("--authorize-uded-development-gt",action="store_true",
                   help="Explicitly fit on the 14 known UDED DEVELOPMENT GT masks")
    args=p.parse_args()
    if os.name=="nt":
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        except Exception as exc:
            print("[WARN] Could not disable Windows idle sleep:",exc,flush=True)
    try:
        result=run_pipeline(args.workspace,no_reaudit=args.no_reaudit,
                            skip_baseline_zip=args.skip_baseline_zip,
                            authorize_uded_development_gt=args.authorize_uded_development_gt)
        # A gate being open is an expected, reportable result, not an execution crash.
        return 0 if (result["technical_audit"]["status"]==
                     "REUSED_VERIFIED_56_56_WITH_UNCHANGED_SCIENTIFIC_CODE"
                     and result["status"]!="TECHNICAL_ERROR_BLOCKED") else 2
    except Exception as exc:
        print("[FAIL CLOSED]",type(exc).__name__+":",str(exc),flush=True)
        return 2
    finally:
        if os.name=="nt":
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)


if __name__=="__main__":
    raise SystemExit(main())
