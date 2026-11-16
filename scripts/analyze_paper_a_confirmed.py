#!/usr/bin/env python3
"""Paper A domain-blocked H1/H2 inference after signed prospective freeze.

Critically: validates the frozen protocol, independent cohort, full H1/H2
recipe, signed human review and externally-certified results provenance BEFORE
opening any CSV containing image-level X/Y/F1. This script does NOT extract
maps, decode image GT, choose thresholds or train models. It analyzes only
final, previously produced paired observations from a certified executor.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

from paper_a_freeze_guard import (
    ROOT, SHA, GIT_SHA, sha256, ancestor, validate_files,
    COLUMNS as COHORT_COLUMNS,
)

OUTCOME_COLUMNS = ("dataset","image_id","scene_group","image_sha256",
                   "X1","Y1","X2","Y2")


def rho(x: np.ndarray, y: np.ndarray) -> float:
    """Tied-midrank Spearman; reject undefined constant vectors."""
    xr = rankdata(np.asarray(x, dtype=float), method="average")
    yr = rankdata(np.asarray(y, dtype=float), method="average")
    xr = xr - xr.mean()
    yr = yr - yr.mean()
    nx, ny = np.linalg.norm(xr), np.linalg.norm(yr)
    if nx == 0 or ny == 0:
        raise ValueError("Undefined Spearman: constant/tied feature or outcome")
    return float(xr @ yr / (nx * ny))


def aggregate_domain_rho(rows: list[dict], x_key: str, y_key: str) -> tuple[float,dict]:
    groups = {}
    for row in rows:
        groups.setdefault(row["dataset"], []).append(row)
    values, weights, detail = [], [], {}
    for domain in sorted(groups):
        records = groups[domain]
        if len(records) < 3:
            raise ValueError("Too few independent captures per domain")
        r = rho(np.asarray([v[x_key] for v in records]),
                np.asarray([v[y_key] for v in records]))
        detail[domain] = {"n":len(records),"rho":r}
        values.append(r)
        weights.append(len(records)-1)
    if len(groups) != 2:
        raise ValueError("Expected exactly two independent domains")
    return float(np.average(values, weights=weights)), detail


def permutation_test(rows: list[dict], hypothesis: str, count: int,
                     seed: int) -> dict:
    if count < 1:
        raise ValueError("Permutation count must be positive")
    x_key = "X1" if hypothesis == "H1" else "X2"
    y_key = "Y1" if hypothesis == "H1" else "Y2"
    sign = -1 if hypothesis == "H1" else 1
    observed, details = aggregate_domain_rho(rows, x_key, y_key)
    groups = {}
    for row in rows:
        groups.setdefault(row["dataset"], []).append(row)
    prepared = []
    denom = 0
    for domain in sorted(groups):
        group = groups[domain]
        xr = rankdata([v[x_key] for v in group], method="average")
        yr = rankdata([v[y_key] for v in group], method="average")
        xr = xr - xr.mean()
        yr = yr - yr.mean()
        nx,ny = np.linalg.norm(xr),np.linalg.norm(yr)
        if nx == 0 or ny == 0:
            raise ValueError("Constant variable in block")
        weight = len(group)-1
        denom += weight
        prepared.append((xr/nx,yr/ny,weight))
    rng = np.random.default_rng(seed)
    extreme = 0
    for _ in range(count):
        draw = sum(weight * float(x @ y[rng.permutation(len(y))])
                   for x,y,weight in prepared)/denom
        if sign * draw >= sign * observed - 1e-15:
            extreme += 1
    return {
        "hypothesis": hypothesis, "statistic_within_domain": observed,
        "domain_rho": details,
        "direction": "negative" if sign < 0 else "positive",
        "permutations": count,
        "extreme_permutations": extreme,
        "p_one_sided": (1+extreme)/(1+count),
        "mean_paired_F1_difference": float(np.mean([v[y_key] for v in rows])),
        "fraction_positive_difference": float(np.mean([v[y_key] > 0 for v in rows])),
    }


def stratified_bootstrap(rows: list[dict], hypothesis: str,
                         replicates: int, seed: int) -> dict:
    x_key = "X1" if hypothesis == "H1" else "X2"
    y_key = "Y1" if hypothesis == "H1" else "Y2"
    groups={}
    for row in rows:
        groups.setdefault(row["dataset"], []).append(row)
    rng = np.random.default_rng(seed)
    valid=[]
    bad=0
    for _ in range(replicates):
        sample=[]
        for domain in sorted(groups):
            g=groups[domain]
            sample.extend(g[j] for j in rng.integers(len(g),size=len(g)))
        try:
            estimate,_=aggregate_domain_rho(sample,x_key,y_key)
            valid.append(estimate)
        except ValueError:
            bad+=1
    if len(valid) < int(replicates * 0.95):
        raise ValueError("Too many undefined stratified bootstrap replicates")
    low,high=np.quantile(valid,[0.025,0.975])
    return {"ci95_lower":float(low),"ci95_upper":float(high),
            "valid_bootstrap_replicates":len(valid),
            "rejected_bootstrap_replicates":bad}


def holm2(a: float,b: float) -> tuple[float,float]:
    """Holm step-down for exactly two tests, adjusted p in original order."""
    if not (0<=a<=1 and 0<=b<=1):
        raise ValueError("Invalid p values")
    if a<=b:
        q1=min(1,2*a)
        return q1,max(q1,b)
    q2=min(1,2*b)
    return max(a,q2),q2


def check_outcomes(rows: list[dict], cohort: list[dict]) -> list[dict]:
    """Validate 1:1 original/capture correspondence without inspecting GT."""
    expected = {(r["dataset"],r["image_id"]):r for r in cohort}
    if len(expected)!=len(cohort) or len(rows)!=len(cohort):
        raise ValueError("Output count does not match frozen independent images")
    unique=set()
    out=[]
    for row in rows:
        if set(row)!=set(OUTCOME_COLUMNS):
            raise ValueError("Unexpected outcome CSV schema")
        key=(row["dataset"],row["image_id"])
        if key in unique or key not in expected:
            raise ValueError("Duplicate/unregistered outcome image")
        unique.add(key)
        ref=expected[key]
        if (row["scene_group"]!=ref["scene_group"] or
                row["image_sha256"].lower()!=ref["image_sha256"].lower()):
            raise ValueError("Frozen image/capture identity mismatch")
        numbers={}
        for k in ("X1","Y1","X2","Y2"):
            try:
                value=float(row[k])
            except (TypeError,ValueError) as exc:
                raise ValueError("Nonnumeric outcome") from exc
            if not np.isfinite(value):
                raise ValueError("Nonfinite outcome")
            numbers[k]=value
        if not (numbers["X1"]>=0 and -1<=numbers["X2"]<=1
                and all(-1<=numbers[k]<=1 for k in ("Y1","Y2"))):
            raise ValueError("Outcome/feature range inconsistent with contract")
        out.append({**row,**numbers})
    if unique!=set(expected):
        raise ValueError("Missing frozen image/capture outcomes")
    return out


def verify_outcome_provenance(path: Path, outcomes: Path, freeze: dict,
                              approval: dict | None = None) -> dict:
    if not path.is_file() or path.is_symlink() or path.stat().st_size>200000:
        raise ValueError("Missing/unsafe signed executor provenance")
    rec=json.loads(path.read_text(encoding="utf-8"))
    required={"schema_version":1,
              "outcomes_csv_sha256":sha256(outcomes),
              "freeze_commit":freeze["freeze_commit"],
              "protocol_frozen_before_first_GT_access":True,
              "no_parameter_tuning_or_threshold_fitting_on_confirmatory_GT":True,
              "paired_evaluator_contract_independently_certified":True,
              "complete_per_capture_output":True}
    if any(rec.get(k)!=v for k,v in required.items()):
        raise ValueError("Uncertified evaluator output or outcomes SHA mismatch")
    if not isinstance(approval, dict) or approval.get(
            "executor_contract_independently_reviewed") is not True:
        raise PermissionError("Independent executor approval required for EVERY analysis entrypoint")
    approved=approval.get("approved_executor_source_sha256")
    if not isinstance(approved,str) or not SHA.fullmatch(approved):
        raise ValueError("Approved evaluator SHA256 invalid")
    if (not isinstance(rec.get("evaluator_source_sha256"),str)
            or not SHA.fullmatch(rec["evaluator_source_sha256"])
            or rec["evaluator_source_sha256"]!=approved):
        raise ValueError("Executor provenance SHA256 does not match signed approval")
    executor=ROOT/"scripts/execute_paper_a_frozen_cohort.py"
    if not executor.is_file() or sha256(executor)!=approved:
        raise ValueError("Executed evaluator source differs from independently approved source")
    if rec.get("reviewed_by")!=approval.get("reviewed_by"):
        raise ValueError("Executor provenance and independent reviewer mismatch")
    commit=rec.get("source_commit")
    if not isinstance(commit,str) or not GIT_SHA.fullmatch(commit) or not ancestor(ROOT,commit):
        raise ValueError("Executor source commit is not a verified ancestor")
    if rec.get("gt_decoding_policy")!=approval.get("gt_binary_decoding_contract"):
        raise ValueError("Unapproved GT decoding policy in provenance")
    return rec


def run_confirmation(protocol_path:Path,recipe_path:Path,cohort_path:Path,
                     approval_path:Path, outcomes_path:Path, provenance_path:Path,
                     output_dir:Path, *, bootstrap_replicates:int=2000):
    # ORDER MATTERS: frozen lock is checked without reading outcomes/F1.
    gate=validate_files(protocol_path,recipe_path,cohort_path,approval_path)
    if gate["blockers"]:
        raise RuntimeError("Outcomes remain locked: "+ "; ".join(gate["blockers"]))
    approval=json.loads(approval_path.read_text(encoding="utf-8"))
    verify_outcome_provenance(provenance_path,outcomes_path,gate,approval)
    with cohort_path.open(encoding="utf-8-sig",newline="") as handle:
        cohort=list(csv.DictReader(handle))
    with outcomes_path.open(encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle)
        if tuple(reader.fieldnames or ())!=OUTCOME_COLUMNS:
            raise ValueError("Wrong measured-outcome file layout")
        rows=check_outcomes(list(reader),cohort)
    protocol=json.loads(protocol_path.read_text(encoding="utf-8"))
    count=protocol["inference"]["permutations"]
    seed=protocol["inference"]["permutation_seed"]
    if count != 100000:
        raise ValueError("Confirmed inference requires locked 100000 permutations")
    analyses=[
        permutation_test(rows,tag,count,seed+j)
        for j,tag in enumerate(("H1","H2"))
    ]
    qa,qb=holm2(analyses[0]["p_one_sided"],analyses[1]["p_one_sided"])
    for j,(item,adjusted) in enumerate(zip(analyses,(qa,qb))):
        item["holm_p_adjusted"]=adjusted
        item["bootstrap95"]=stratified_bootstrap(rows,item["hypothesis"],
                                                 bootstrap_replicates,seed+100+j)
        item["confirmed"]=(adjusted<0.05 and
            item["statistic_within_domain"] * (-1 if j==0 else 1) > 0)
    result={
        "status":"FROZEN_H1_H2_ANALYSIS_COMPLETED_NOT_INDEPENDENTLY_REVIEWED",
        "freeze_commit":gate["freeze_commit"],
        "input_sha256":{**gate["frozen_input_sha256"],
                         "outcome_sha256":sha256(outcomes_path)},
        "n_independent_capture_units":len(rows),
        "analyses":analyses,
        "GT_payload_opened_by_this_script":False,
        "precalculated_confirmatory_XY_read_after_freeze":True,
        "statement":"Direction and Holm decisions are reported even if negative.",
    }
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    folder=output_dir / ("confirmed_analysis_"+stamp)
    folder.mkdir(parents=True,exist_ok=False)
    (folder/"results.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),
                                         encoding="utf-8")
    report=[
        "# Paper A — frozen confirmatory inferential results",
        "",
        "**Status:** automatically calculated from reviewed frozen inputs; independent reviewer sign-off of the numerical report remains required.",
        "",
        "Frozen commit: "+str(gate["freeze_commit"]),
        "Independent capture units: "+str(len(rows)),
        "",
        "| Hypothesis | Weighted within-domain rho | one-sided p | Holm-adjusted p | 95% bootstrap interval | Primary decision |",
        "|---|---:|---:|---:|---|---|",
    ]
    for r in analyses:
        ci=r["bootstrap95"]
        report.append("| {} | {:.6f} | {:.6g} | {:.6g} | [{:.4f}, {:.4f}] | {} |".format(
            r["hypothesis"],r["statistic_within_domain"],r["p_one_sided"],
            r["holm_p_adjusted"],ci["ci95_lower"],ci["ci95_upper"],
            "SIGNED HYPOTHESIS CONFIRMED" if r["confirmed"] else "NOT CONFIRMED"))
    report += ["","These results are from a custom native-geometry evaluator, not official Berkeley ODS/OIS/AP.",""]
    (folder/"results.md").write_text("\n".join(report),encoding="utf-8")
    return result,folder


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol",type=Path,required=True)
    parser.add_argument("--recipe",type=Path,required=True)
    parser.add_argument("--cohort",type=Path,required=True)
    parser.add_argument("--approval",type=Path,required=True)
    parser.add_argument("--outcomes",type=Path,required=True)
    parser.add_argument("--provenance",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    result,folder=run_confirmation(args.protocol,args.recipe,args.cohort,
        args.approval,args.outcomes,args.provenance,args.output_dir)
    print(json.dumps({"status":result["status"],"report":str(folder),
                      "decisions":{x["hypothesis"]:x["confirmed"] for x in result["analyses"]}},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
