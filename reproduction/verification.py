"""Paper A verification from immutable published numeric evidence.

This is a numerical replay, not raw image/GT regeneration. Uses original
published inference library without changing its algorithms.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
import numpy as np

from .context import CONFIRMATION,Context,digest
from .execution import ReproductionError
from src.paper_a_three_domain_inference import (
    partition_primary_secondary, aggregate_domain_rho,
    permutation_test,stratified_bootstrap,holm2,
)

FLOAT_KEYS=("X1","Y1","X2","Y2")
def _read_csv(path:Path) -> list[dict]:
    with path.open(newline="",encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))

def evaluate_confirmatory_evidence(ctx:Context) -> dict:
    """Compare reconstructed rho, means and optionally 100k permutations against paper."""
    cohort_path=CONFIRMATION/"cohort.csv"
    outcomes_path=CONFIRMATION/"PAIRED_OUTCOMES.csv"
    report_path=CONFIRMATION/"EXECUTION_RESULTS.json"
    for p in (cohort_path,outcomes_path,report_path):
        if not p.is_file():
            raise ReproductionError("Missing frozen published evidence: "+str(p))
    published=json.loads(report_path.read_text(encoding="utf-8"))
    if digest(outcomes_path)!=published["outcomes_sha256"]:
        raise ReproductionError("Frozen outcomes SHA256 differs from published result")
    cohort=_read_csv(cohort_path)
    rows=_read_csv(outcomes_path)
    for row in rows:
        try:
            for field in FLOAT_KEYS:
                row[field]=float(row[field])
                if not np.isfinite(row[field]):
                    raise ValueError(field)
        except (KeyError,ValueError) as exc:
            raise ReproductionError("Invalid/nonfinite confirmation outcome") from exc
    primary,secondary=partition_primary_secondary(rows,cohort)
    if (len(primary),len(secondary),len(rows))!=(
        published["N_primary"],published["N_secondary_BIPED"],published["N_total"]
    ):
        raise ReproductionError("Confirmation units differ from frozen report")
    results=[]
    for index,original in enumerate(published["analyses"]):
        hypothesis="H1" if index==0 else "H2"
        if original["hypothesis"]!=hypothesis:
            raise ReproductionError("Published hypothesis sequence changed")
        x,y=FLOAT_KEYS[index*2:index*2+2]
        measured,per_domain=aggregate_domain_rho(primary,x,y)
        mean_delta=float(np.mean([r[y] for r in primary]))
        if abs(measured-original["statistic_within_domain"])>1e-10:
            raise ReproductionError(hypothesis+" rho does not match the published value")
        if abs(mean_delta-original["mean_paired_F1_difference"])>1e-10:
            raise ReproductionError(hypothesis+" mean delta F1 does not match")
        if any(abs(per_domain[d]["rho"]-original["domain_rho"][d]["rho"])>1e-10 for d in per_domain):
            raise ReproductionError(hypothesis+" per-domain rho differs")
        row={
          "hypothesis":hypothesis,
          "rho_recomputed":measured,
          "mean_delta_F1_recomputed":mean_delta,
          "published_holm_p_NOT_RECOMPUTED_UNLESS_DEEP":original["holm_p_adjusted"],
          "bootstrap95_published":original["bootstrap95"],
          "domain_rho_recomputed":per_domain,
          "numerical_check":"PASS",
        }
        results.append(row)
    if ctx.deep:
        permutations=[]
        for index,row in enumerate(results):
            hypothesis=row["hypothesis"]
            full=permutation_test(primary,hypothesis,100000,20261115+index)
            orig=published["analyses"][index]
            if full["extreme_permutations"]!=orig["extreme_permutations"]:
                raise ReproductionError(hypothesis+" fixed-seed permutation count differs")
            if abs(full["p_one_sided"]-orig["p_one_sided"])>1e-12:
                raise ReproductionError(hypothesis+" fixed-seed permutation p differs")
            ci=stratified_bootstrap(primary,hypothesis,2000,20261215+index)
            for field in ("ci95_lower","ci95_upper"):
                if abs(ci[field]-orig["bootstrap95"][field])>1e-10:
                    raise ReproductionError(hypothesis+" bootstrap interval differs")
            row["permutations_100000_recomputed"]="PASS"
            row["bootstrap_2000_recomputed"]="PASS"
            permutations.append(full["p_one_sided"])
        adjusted=holm2(*permutations)
        for index,row in enumerate(results):
            original=published["analyses"][index]
            if abs(adjusted[index]-original["holm_p_adjusted"])>1e-12:
                raise ReproductionError("Holm adjustment differs")
            row["holm_p_recomputed"]=adjusted[index]
    return {
       "status":"NUMERIC_ARCHIVE_REPRODUCED" if ctx.deep else "DESCRIPTIVE_NUMBERS_VERIFIED",
       "n_primary":len(primary),"n_secondary":len(secondary),
       "n_total":len(rows),
       "outcomes_sha256":published["outcomes_sha256"],
       "hypotheses":results,
       "scope":"Archived paired X/Y and reference values only; no new image-level inference",
    }
