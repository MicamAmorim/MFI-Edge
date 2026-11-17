#!/usr/bin/env python3
"""Run actual Paper A inference implementation on SYNTHETIC A219 observations.

This is a statistical-engine test, NOT evaluation of H1/H2 on protected images.
Never reads GT, prediction maps, original image bytes, frozen outcomes,
freeze_approval.json, or sample scores. Never calls the confirmation executor,
run_confirmation, or opens GT. Does not modify the prospective protocol.

Uses the exact existing permutation_test, holm2 and stratified_bootstrap
functions (100000 domain-blocked permutations per H by default).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0,str(HERE))
from analyze_paper_a_confirmed import permutation_test,holm2,stratified_bootstrap

SEED=20261117
DEFAULT=Path(
    r"F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff"
    r"\TESTE_SINTETICO_MOTOR_INFERENCIAL_A219_SEM_GT.json"
)


def source_hash(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def make_synthetic_rows(seed:int=SEED)->list[dict]:
    """219 *fictional* independent captures; no dataset file or image is read."""
    rng=np.random.default_rng(seed)
    population_spearman=.20
    pearson=2*math.sin(math.pi*population_spearman/6)
    rows=[]
    for domain,n in (("BIPED",125),("MultiCue",94)):
        x1=rng.standard_normal(n)
        x2=rng.standard_normal(n)
        e1=rng.standard_normal(n)
        e2=rng.standard_normal(n)
        y1=-pearson*x1+math.sqrt(1-pearson*pearson)*e1
        y2= pearson*x2+math.sqrt(1-pearson*pearson)*e2
        for i in range(n):
            rows.append({
                "dataset":domain,
                "image_id":f"SYNTHETIC_ONLY_{domain}_{i:03d}",
                "X1":float(np.exp(x1[i]/3)),
                "Y1":float(np.tanh(y1[i])*.02),
                "X2":float(np.tanh(x2[i])),
                "Y2":float(np.tanh(y2[i])*.02)
            })
    assert len(rows)==219
    assert len({(r["dataset"],r["image_id"]) for r in rows})==219
    return rows


def exercise(count:int=100000, bootstrap:int=2000, seed:int=SEED)->dict:
    if type(count)!=int or count<1 or count>1000000:
        raise ValueError("Invalid number of permutations")
    if type(bootstrap)!=int or bootstrap<100 or bootstrap>50000:
        raise ValueError("Invalid bootstrap count")
    rows=make_synthetic_rows(seed)
    hypotheses=[]
    for index,name in enumerate(("H1","H2")):
        trial=permutation_test(rows,name,count,20261115+index)
        trial["bootstrap95"]=stratified_bootstrap(
            rows,name,bootstrap,20261115+100+index)
        hypotheses.append(trial)
    pa,pb=holm2(hypotheses[0]["p_one_sided"],
                hypotheses[1]["p_one_sided"])
    for item,p in zip(hypotheses,(pa,pb)):
        item["holm_p_adjusted"]=p
        if not all(k in item for k in ("statistic_within_domain","p_one_sided",
                  "domain_rho","bootstrap95","holm_p_adjusted")):
            raise RuntimeError("Inference engine omitted an expected result")
        if not 0<=p<=1:
            raise RuntimeError("Holm adjusted p invalid")
        if set(item["domain_rho"])!={"BIPED","MultiCue"}:
            raise RuntimeError("Expected both synthetic domains")
    result={
        "schema":"paper_a_A219_synthetic_inference_engine_v1",
        "status":"STATISTICAL_IMPLEMENTATION_DRY_RUN_ONLY_NOT_A_CONFIRMATORY_RESULT",
        "sample":{"BIPED":125,"MultiCue":94,"N":219,
                  "origin":"generated random samples; no real images or GT"},
        "random":{"synthetic_seed":seed,"inference_seed_H1":20261115,
                  "inference_seed_H2":20261116},
        "assumed_abs_Spearman_rho":.20,
        "permutations_per_hypothesis":count,
        "bootstrap_replicates_per_hypothesis":bootstrap,
        "motor_source_sha256":source_hash(HERE/"analyze_paper_a_confirmed.py"),
        "tests":hypotheses,
        "interpretation":"P values and apparent significance refer ONLY to invented "
          "observations and must never be reported as experimental evidence "
          "for H1/H2. The confirmatory execution needs a valid scientific "
          "freeze plus independently signed GT, scene and provenance reviews.",
        "real_GT_images_or_F1_read":False,
        "cohort_confirmatory_outcomes_read":False,
        "freeze_authorized":False,
        "H1_H2_confirmatory_executed":False,
        "independent_review_signed":False,
    }
    return result


def save_without_overwrite(path:Path,result:dict)->None:
    raw=(json.dumps(result,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    if path.exists():
        if path.is_symlink() or path.read_bytes()!=raw:
            raise PermissionError(
                "Different synthetic statistical report already exists; "
                "do not overwrite prior research records")
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--permutations",type=int,default=100000)
    p.add_argument("--bootstrap",type=int,default=2000)
    p.add_argument("--output",type=Path,default=DEFAULT)
    args=p.parse_args()
    obj=exercise(count=args.permutations,bootstrap=args.bootstrap)
    save_without_overwrite(args.output,obj)
    print(json.dumps({
        "status":obj["status"],"output":str(args.output),
        "source_sha256":obj["motor_source_sha256"],
        "N":219,"permutations_per_H":args.permutations,
        "bootstrap_replicates_per_H":args.bootstrap,
        "synthetic_tests":[{"H":it["hypothesis"],
            "rho":it["statistic_within_domain"],
            "p_one_sided":it["p_one_sided"],
            "holm":it["holm_p_adjusted"]} for it in obj["tests"]],
        "real_GT_images_or_F1_read":False,
        "H1_H2_confirmatory_executed":False,
    },ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
