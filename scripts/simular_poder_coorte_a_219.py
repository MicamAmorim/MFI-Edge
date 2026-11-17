#!/usr/bin/env python3
"""Paper A prospective POWER SENSITIVITY: N=125+94, no outcomes/GT/F1.

Synthetic Gaussian-copula paired associations with signed Spearman effects
H1=-rho, H2=+rho. Each replicate computes within-domain Spearman correlations,
weights n_d-1, approximates its one-sided H0 p-values with a normal null,
and applies Holm to both primary hypotheses. H1/H2 simulated independent;
same random draws are reused to compare 125+94 and 125+95.

THIS IS *NOT* the final 100,000-permutation confirmatory test. It does not
attest scientific adequacy, open protected data, update a cohort, or freeze.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

WORK=Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_completion")
SIGNOFF=WORK/"scientific_signoff"
READINESS=SIGNOFF/"COORTE_A_N219_READINESS_NOT_APPROVED.json"
COHORT=SIGNOFF/"COORTE_A_N219_PARA_REVISAO_NAO_FROZEN.csv"
OUTPUT=SIGNOFF/"PODER_A_N219_SENSIBILIDADE_NAO_APROVADA.json"
SEED=20261117
ALPHA=.05
EFFECTS=(.15,.20,.25)


def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()


def read_inputs(*, readiness:Path=READINESS, cohort:Path=COHORT)->dict:
    if not readiness.is_file() or readiness.is_symlink() or not cohort.is_file() or cohort.is_symlink():
        raise ValueError("Scenario A metadata missing/unsafe")
    if readiness.stat().st_size>1_000_000 or cohort.stat().st_size>2_000_000:
        raise ValueError("Unexpected review metadata size")
    status=json.loads(readiness.read_text(encoding="utf-8"))
    if (status.get("schema")!="paper_a_A_219_metadata_readiness_v1" or
        status.get("status")!="A_N219_ORIGINAL_SHA_VERIFIED_SCIENCE_GATES_OPEN" or
        status.get("counts")!={"BIPED":125,"MultiCue":94,"N":219} or
        status.get("GT_accessed") is not False or
        status.get("scientific_signoff") is not False or
        status.get("freeze_authorized") is not False or
        status.get("roster_sha256")!="78cc7c4b36e0fc6faf9996c3dd760cbc8b97f21cfe23c18e26d4f31f7e8ae1d2"):
        raise ValueError("Cannot analyze unverified or approved cohort")
    if sha(cohort)!=status.get("review_roster_sha256"):
        raise ValueError("Scenario A cohort CSV SHA differs from validated inventory")
    with cohort.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=219 or not all(r.get("independence_review")=="pending" and
                                 r.get("prior_exposure_review")=="pending" for r in rows):
        raise ValueError("Review CSV contains unexpected scientific decisions")
    from collections import Counter
    if Counter(r["dataset"] for r in rows)!={"BIPED":125,"MultiCue":94}:
        raise ValueError("Scenario A changed its domain counts")
    return {"readiness_sha256":sha(readiness),"roster_sha256":sha(cohort)}


def rho_pearson_from_spearman(abs_rho:float)->float:
    """Exact bivariate-normal correlation producing expected Spearman rho."""
    if not 0<abs_rho<1:
        raise ValueError("Invalid anticipated absolute Spearman effect")
    return 2*math.sin(math.pi*abs_rho/6)


def correlation_of_ranks(x:np.ndarray,y:np.ndarray)->np.ndarray:
    """No ties: Gaussian draws are continuous; rank midranks coincide."""
    if x.shape!=y.shape or x.ndim!=3:
        raise ValueError("Expected (replicate,hypothesis,observation) arrays")
    n=x.shape[-1]
    if n<4:raise ValueError("Too few images per domain")
    rx=np.argsort(np.argsort(x,axis=-1),axis=-1).astype(np.float64)
    ry=np.argsort(np.argsort(y,axis=-1),axis=-1).astype(np.float64)
    mid=(n-1)/2
    rx-=mid;ry-=mid
    return (rx*ry).sum(axis=-1)/(n*(n*n-1)/12)


def pvalues_from_weighted_rho(rho_sum:np.ndarray, counts:tuple[int,int])->np.ndarray:
    # Var(weighted_sum)=sum((n_d-1)^2/(n_d-1)) = sum(n_d-1).
    # H1 predeclared negative, H2 predeclared positive.
    z=rho_sum/math.sqrt(sum(n-1 for n in counts))
    directed=z*np.array([-1.0,1.0])
    # Normal asymptotic p rather than costly within-domain permutations.
    return np.vectorize(lambda v:0.5*math.erfc(v/math.sqrt(2)),otypes=[float])(directed)


def both_holm(p:np.ndarray)->np.ndarray:
    """For exactly two p-values: p_(1)<=.025 and p_(2)<=.05."""
    return (p.min(axis=1)<=ALPHA/2)&(p.max(axis=1)<=ALPHA)


def wilson_binomial(x:int,n:int,z:float=1.959963984540054)->tuple[float,float]:
    phat=x/n
    den=1+z*z/n
    center=(phat+z*z/(2*n))/den
    half=z*math.sqrt(phat*(1-phat)/n+z*z/(4*n*n))/den
    return max(0,center-half),min(1,center+half)


def simulate(replicates:int=10000,seed:int=SEED,
             abs_rho:float=.20,batch:int=250)->dict:
    if type(replicates)!=int or replicates<100 or replicates>200_000:
        raise ValueError("Planning simulation requires 100 to 200000 replicates")
    rp=rho_pearson_from_spearman(abs_rho)
    rng=np.random.default_rng(seed)
    passed_A=passed_old=0
    for start in range(0,replicates,batch):
        k=min(batch,replicates-start)
        # Common draws shared by both composition scenarios.
        weighted_B=None
        raw_M=None
        for dataset,n in (("BIPED",125),("MultiCue",95)):
            x=rng.standard_normal((k,2,n))
            e=rng.standard_normal((k,2,n))
            signs=np.array([-1.0,+1.0])[None,:,None]
            y=signs*rp*x+math.sqrt(1-rp*rp)*e
            if dataset=="BIPED":
                weighted_B=(n-1)*correlation_of_ranks(x,y)
            else:
                raw_M=(x,y)
        old=weighted_B+94*correlation_of_ranks(*raw_M)
        A=weighted_B+93*correlation_of_ranks(raw_M[0][:,:,:94],raw_M[1][:,:,:94])
        passed_A+=int(both_holm(pvalues_from_weighted_rho(A,(125,94))).sum())
        passed_old+=int(both_holm(pvalues_from_weighted_rho(old,(125,95))).sum())
    def entry(success:int,nB:int,nM:int)->dict:
        ci=wilson_binomial(success,replicates)
        return {"BIPED":nB,"MultiCue":nM,"N":nB+nM,
                "joint_rejection_rate":round(success/replicates,5),
                "mc_95pct_interval":[round(ci[0],5),round(ci[1],5)],
                "successes":success}
    return {"assumed_abs_population_Spearman_rho":abs_rho,
            "candidate_A":entry(passed_A,125,94),
            "former_legacy_mix_comparison_only":entry(passed_old,125,95),
            "common_random_numbers":True,
            "difference_A_minus_legacy":round((passed_A-passed_old)/replicates,5)}


def generate(*,replicates:int=10000,seed:int=SEED,
             output:Path=OUTPUT,readiness:Path=READINESS,cohort:Path=COHORT)->dict:
    inputs=read_inputs(readiness=readiness,cohort=cohort)
    cases=[simulate(replicates=replicates,seed=seed+i*1000,abs_rho=rho)
           for i,rho in enumerate(EFFECTS)]
    result={
        "schema":"paper_a_A_N219_power_sensitivity_no_protected_outcomes_v1",
        "status":"SYNTHETIC_PLANNING_ONLY_NOT_SCIENTIFICALLY_APPROVED",
        "source_metadata_sha256":inputs,
        "replicates_per_effect":replicates,
        "planning_seeds":[seed+i*1000 for i in range(len(EFFECTS))],
        "assumptions":{
            "population_model":"independent H1/H2 bivariate Gaussian copula within each domain",
            "domain_effects":"homogeneous Spearman rho H1=-r and H2=+r",
            "statistic":"within-domain Spearman, weights n_d-1",
            "null_p_approximation":"one-sided asymptotic normal, not 100000 permutation",
            "multiplicity":"two hypotheses Holm familywise alpha=0.05",
            "true_image_independence_presumed_not_verified":True,
            "binomial_intervals":"Wilson 95% for Monte Carlo sampling uncertainty",
            "confirmation_outcomes_accessed":False
        },
        "effects":cases,
        "interpretation":"Prospective sensitivity only, NOT an exact confirmatory-permutation power determination. Scientific reviewer must approve design, sample adequacy and handling of scene dependence.",
        "scientific_power_approval":False,
        "freeze_authorized":False,
        "GT_opened":False,
        "H1_H2_executed":False
    }
    raw=(json.dumps(result,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    if output.exists():
        if output.is_symlink() or output.read_bytes()!=raw:
            raise RuntimeError("Power report exists with different inputs/seed; preserve prior run")
    else:
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(raw)
    return {"path":str(output),"sha256":sha(output),"results":cases,
            "GT_opened":False,"freeze_authorized":False}


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--replicates",type=int,default=10000)
    args=p.parse_args()
    print(json.dumps(generate(replicates=args.replicates),indent=2,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
