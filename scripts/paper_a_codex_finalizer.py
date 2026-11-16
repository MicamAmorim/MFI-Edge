#!/usr/bin/env python3
"""ONE-command Paper A controller with bounded Codex review cycles.

Does not turn an LLM review into independent scientific authorization. Runs
existing fail-closed freeze/GT/F1/H1/H2 pipeline first; then (if still blocked)
does ONE cached format-only GT inspection on excluded samples and up to TWO
read-only Codex audit iterations. This agent cannot mutate models, commits,
cohort, GT, approvals, or frozen state.
"""
from __future__ import annotations

from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1]
WORK=Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_completion")
REVIEWS=WORK/"codex_final_audit"
PIPELINE=ROOT/"scripts/continuar_paper_a.py"
FORMAT_CHECK=ROOT/"scripts/paper_a_nonconfirmatory_gt_format.py"
DASH=WORK/"FINAL_ONE_COMMAND_REPORT.json"
PIPE_STATUS=WORK/"ONE_COMMAND_STATUS.json"
MAX_AUDIT_ROUNDS=2
CODEX_TIMEOUT_SECONDS=1800
TECHNICAL_GATES={"PREFREEZE_SCIENTIFIC_GATES_OPEN",
                 "FROZEN_ANALYSIS_REQUIRES_INDEPENDENT_REVIEW"}


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path:Path)->dict:
    if not path.is_file() or path.is_symlink() or path.stat().st_size>3_000_000:
        return {}
    try:
        v=json.loads(path.read_text(encoding="utf-8"))
        return v if isinstance(v,dict) else {}
    except (ValueError,OSError):
        return {}


def capture(label:str,argv:list[str],timeout:int)->dict:
    REVIEWS.mkdir(parents=True,exist_ok=True)
    log=REVIEWS/(label+".log")
    print("[ONE SHOT]",label,flush=True)
    try:
        with log.open("wb") as out:
            p=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,
                             timeout=timeout,check=False)
        result={"exit_code":p.returncode,"log_path":str(log)}
    except subprocess.TimeoutExpired:
        result={"exit_code":124,"log_path":str(log),"timeout":True}
    except OSError as error:
        result={"exit_code":127,"log_path":str(log),
                "launch_error":str(error)}
    return result


def available_codex()->str|None:
    return shutil.which("codex") or shutil.which("codex.cmd") or shutil.which("codex.exe")


def prompt_round(round_no:int, state:dict, gt_report:dict, prior:str)->str:
    status=state.get("status","UNKNOWN")
    errors=state.get("blockers",[])
    initial = (
        "You are auditing the Paper A scientific reproducibility workflow for "
        "the MFI-Edge repository. This is a READ-ONLY evidence/technical audit. "
        "You must not change ANY files, run protected GT, inspect images or "
        "masks belonging to the 125 BIPED train + 95 MultiCue confirmatory "
        "cohort, run F1 on confirmatory data, auto-approve any review, or "
        "fabricate statistical results. You cannot act as an independent "
        "human scientific signatory. No git commits, pushes or code changes. "
        "Read-only repository inspection and synthetic tests are allowed.\n\n"
        f"Current system status: {status}\n"
        f"Current scientific blockers: {json.dumps(errors,ensure_ascii=False)}\n"
        f"Nonconfirmatory GT *format* sample report summary: "
        f"{json.dumps(gt_report,ensure_ascii=False)[:2200]}\n"
        "Grounded records (metadata only):\n"
        r"F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff"
        "\n"
        "Repo files: docs/paper_a_confirmation/AUDITORIA_INDEPENDENTE_ZIP_20261116.md, "
        "scripts/paper_a_freeze_guard.py, scripts/freeze_paper_a_from_independent_review.py, "
        "scripts/execute_paper_a_frozen_cohort.py, "
        "scripts/analyze_paper_a_confirmed.py.\n\n"
        "The BIPED Stage13c preflight opened train GT for *dimensions only* "
        "as described in code; never assert no GT ever accessed.\n"
    )
    if round_no==1:
        task=(
            "TASK A: independently assess pre-freeze audit readiness from "
            "metadata/lineage and identify concrete EXTERNAL evidence that "
            "would justify 220 scene-independence decisions, all seven P1 "
            "no-overlap attestations and the GT-format decoding policy. "
            "List what is proven and what is unproven, with file paths and "
            "line/field references. Do not mark PASS for any candidate. "
            "Find any blockers that can be resolved without GT and without "
            "modifying scientific assumptions. Write a concise report in "
            "Brazilian Portuguese, with a clear NO-GO/GO recommendation.\n"
        )
    else:
        task=(
            "TASK B: examine possible CODE/TEST errors in the one-command "
            "workflow and confirmatory frozen evaluator, including script "
            "imports, source pins, dataset field mapping, duplicate identity, "
            "write atomicity, hash/approval recovery, inference, scientific "
            "GT format and state transitions. Use synthetic-only existing "
            "unit tests if possible. Identify REAL defects with exact code "
            "location and minimal safe repair suggestions. READ-ONLY: do "
            "not implement any fix or modify metadata. Propose a prioritized "
            "plan for unresolved scientific/human issues.\n"
        )
    prior=prior[-12000:]
    return initial+task+("\nPrevious Codex audit excerpt:\n"+prior if prior else "")


def codex_audits(state:dict, gt_report:dict)->dict:
    exe=available_codex()
    if not exe:
        return {"status":"CODEX_NOT_FOUND_CONTROLLER_STILL_SAFE",
                "rounds":0,"note":"Install/authenticate Codex CLI to use its read-only iterative audit."}
    output=[]
    previous=""
    for idx in range(1,MAX_AUDIT_ROUNDS+1):
        final=REVIEWS/f"codex_round_{idx}_final.md"
        command=[exe,"exec","--sandbox","read-only",
                 "-C",str(ROOT),"-o",str(final),
                 prompt_round(idx,state,gt_report,previous)]
        run=capture(f"codex_round_{idx}",command,CODEX_TIMEOUT_SECONDS)
        entry={"round":idx,**run,"report":str(final) if final.is_file() else None}
        output.append(entry)
        if run["exit_code"] or not final.is_file():
            return {"status":"CODEX_AUDIT_PARTIAL_REQUIRES_CLI_CHECK",
                    "rounds":len(output),"details":output,
                    "scientific_approval_granted":False}
        previous=final.read_text(encoding="utf-8",errors="replace")[-12000:]
        print(f"[CODEX] read-only audit round {idx} finished",flush=True)
    return {"status":"CODEX_TWO_READ_ONLY_AUDITS_COMPLETED",
            "rounds":len(output),"details":output,
            "scientific_approval_granted":False}


def run()->int:
    WORK.mkdir(parents=True,exist_ok=True)
    REVIEWS.mkdir(parents=True,exist_ok=True)
    print("[PAPER A] One-command stage: guarded science & technical verification",flush=True)
    # Existing core runs synthetic tests, frozen guard, real F1 and
    # inferential H1/H2 if independently authorized.
    ctrl=capture("existing_guarded_pipeline",
                 [sys.executable,"-u",str(PIPELINE)], 172800)
    state=load_json(PIPE_STATUS)
    status=state.get("status","TECHNICAL_ERROR_NOT_CONFIRMATION")
    format_task={"status":"SKIPPED"}
    fmt={}
    codex={"status":"NOT_RUN"}
    if ctrl["exit_code"]==0 and status=="PREFREEZE_SCIENTIFIC_GATES_OPEN":
        # This may scan a 3.5GB archive ONCE. Only the excluded MultiCue
        # capture and BIPED test masks are inspected. Never read protected GT.
        format_task=capture("excluded_GT_format_only",
                            [sys.executable,str(FORMAT_CHECK)],172800)
        fmt=load_json(WORK/"scientific_signoff/NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json")
        if format_task["exit_code"]:
            fmt={"status":"NONCONFIRMATORY_FORMAT_CHECK_FAILED",
                 "diagnostic_log":format_task["log_path"]}
        print("[PAPER A] Bounded Codex review, no self-signoff",flush=True)
        codex=codex_audits(state,fmt)
    elif ctrl["exit_code"]!=0:
        # Technical failure only: Codex can diagnose but may not overwrite
        # scientific code or forge a freeze.
        codex=codex_audits(
            {"status":"TECHNICAL_ERROR_NOT_CONFIRMATION",
             "blockers":[load_json(WORK/"ONE_COMMAND_ERROR.json").get("error"),
                         "See: "+ctrl["log_path"]]}, {})
    report={
        "status":status if ctrl["exit_code"]==0 else "TECHNICAL_ERROR_NOT_CONFIRMATION",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "branch":"experiment/paper-a-conditional-confirmation",
        "pipeline":ctrl,
        "stage_status_file":str(PIPE_STATUS),
        "codex":codex,
        "excluded_sample_GT_format":format_task,
        "excluded_sample_report":str(WORK/"scientific_signoff/NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json"),
        "protected_GT_not_opened_before_valid_freeze":True,
        "independent_review_not_generated_by_codex":True,
        "hypotheses_not_declared_confirmed_without_real_outcomes":True,
        "blockers":state.get("blockers",[]) if ctrl["exit_code"]==0 else
            [load_json(WORK/"ONE_COMMAND_ERROR.json").get("error","unknown")],
        "next_actions_file":str(WORK/"NEXT_ACTIONS.md"),
        "review_sheet":str(WORK/"scientific_signoff/REVIEW_220_IMAGES_PENDING.csv"),
        "independent_decision_template":str(WORK/"scientific_signoff/FINAL_INDEPENDENT_REVIEW.template.json"),
    }
    DASH.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "code":ctrl["exit_code"],
        "reviewer_signoff_required":status=="PREFREEZE_SCIENTIFIC_GATES_OPEN",
        "codex_status":codex["status"],
        "review_report":str(DASH),
        "next_actions":report["next_actions_file"],
        "message":"Only independently reviewed freeze can authorize real H1/H2 outcomes."
    },indent=2,ensure_ascii=False),flush=True)
    return 0 if ctrl["exit_code"]==0 else 2


if __name__=="__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        WORK.mkdir(parents=True,exist_ok=True)
        (WORK/"PAPER_A_CODEX_ORCHESTRATOR_ERROR.json").write_text(json.dumps(
            {"status":"ORCHESTRATOR_TECHNICAL_ERROR","error":str(exc),
             "trace":traceback.format_exc()[-4000:]},indent=2),
             encoding="utf-8")
        print("[ERROR] Orchestrator failed without scientific approval:",exc,flush=True)
        raise SystemExit(2)
