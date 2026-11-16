#!/usr/bin/env python3
"""Run Paper A's frozen analysis once per certified input signature.

This wrapper NEVER reads or analyses an outcome before validate_files approves
a signed prospective freeze. The cached analysis is only reused after verifying
the SAME input hashes, evaluator SHA, analyzer SHA, report hashes and provenance.
Never changes approvals or scientific decisions.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

from paper_a_freeze_guard import validate_files, sha256
from analyze_paper_a_confirmed import verify_outcome_provenance, run_confirmation

ROOT=Path(__file__).resolve().parents[1]
EXECUTOR=ROOT/"scripts/execute_paper_a_frozen_cohort.py"
ANALYZER=ROOT/"scripts/analyze_paper_a_confirmed.py"


def request_fingerprint(approval_file: Path, protocol: Path, recipe: Path,
                        cohort: Path, outcome: Path, provenance: Path) -> tuple[str,dict]:
    # Under no circumstances read protected outcome bytes before independent
    # freeze signature validation.
    gate=validate_files(protocol,recipe,cohort,approval_file)
    if gate["blockers"]:
        raise PermissionError("Protected confirmatory outcome remains locked: "+"; ".join(gate["blockers"]))
    approval=json.loads(approval_file.read_text(encoding="utf-8"))
    if (not approval.get("executor_contract_independently_reviewed") or
        not isinstance(approval.get("approved_executor_source_sha256"),str)):
        raise PermissionError("Independent evaluator review missing")
    expected=approval["approved_executor_source_sha256"]
    if (not EXECUTOR.is_file() or sha256(EXECUTOR)!=expected):
        raise PermissionError("Executor source SHA differs from independently reviewed source")
    provenance_record=verify_outcome_provenance(provenance,outcome,gate,approval)
    if (provenance_record.get("evaluator_source_sha256")!=expected or
        provenance_record.get("reviewed_by")!=approval.get("reviewed_by")):
        raise PermissionError("Outcome executor provenance contradicts independent freeze review")
    fields={
        "protocol_sha256":sha256(protocol),
        "recipe_sha256":sha256(recipe),
        "cohort_sha256":sha256(cohort),
        "approval_sha256":sha256(approval_file),
        "outcome_sha256":sha256(outcome),
        "provenance_sha256":sha256(provenance),
        "analyzer_sha256":sha256(ANALYZER),
        "executor_sha256":sha256(EXECUTOR),
        "bootstrap_replicates":2000,
    }
    signature=hashlib.sha256(json.dumps(fields,sort_keys=True).encode("utf-8")).hexdigest()
    return signature,gate


def run_once(protocol:Path,recipe:Path,cohort:Path,approval:Path,
             outcomes:Path,provenance:Path,output_dir:Path):
    signature, gate=request_fingerprint(approval,protocol,recipe,cohort,outcomes,provenance)
    cache=output_dir/("CONFIRMED_ANALYSIS_CACHE_"+signature+".json")
    if cache.exists():
        item=json.loads(cache.read_text(encoding="utf-8"))
        folder=Path(item["folder"]).resolve()
        if not folder.is_relative_to(output_dir.resolve()) or not folder.is_dir():
            raise RuntimeError("Cached analysis folder outside approved output directory")
        json_file=folder/"results.json"
        md_file=folder/"results.md"
        if (item.get("signature")!=signature or not json_file.is_file()
            or not md_file.is_file() or sha256(json_file)!=item.get("results_json_sha256")
            or sha256(md_file)!=item.get("results_md_sha256")):
            raise RuntimeError("Certified analysis cache has been altered")
        prior=json.loads(json_file.read_text(encoding="utf-8"))
        if (prior.get("freeze_commit")!=gate["freeze_commit"] or
            prior.get("status")!="FROZEN_H1_H2_ANALYSIS_COMPLETED_NOT_INDEPENDENTLY_REVIEWED" or
            prior.get("input_sha256",{}).get("outcome_sha256")!=sha256(outcomes)):
            raise RuntimeError("Previously recorded analysis is not equivalent")
        print("[REUSE] Verified signed confirmatory statistical output:",folder,flush=True)
        return prior,folder
    print("[RUN] 100000 domain-blocked permutations/Holm once for approved frozen cohort",flush=True)
    result,folder=run_confirmation(protocol,recipe,cohort,approval,outcomes,provenance,output_dir)
    content={
        "schema_version":1,
        "signature":signature,
        "folder":str(folder.resolve()),
        "results_json_sha256":sha256(folder/"results.json"),
        "results_md_sha256":sha256(folder/"results.md"),
        "freeze_commit":gate["freeze_commit"],
        "p_values_from_frozen_outcomes":True,
        "independent_numerical_review_pending":True,
    }
    tmp=cache.with_suffix(".pending")
    with tmp.open("x",encoding="utf-8") as f:
        json.dump(content,f,ensure_ascii=False,indent=2)
    os.replace(tmp,cache)
    return result,folder
