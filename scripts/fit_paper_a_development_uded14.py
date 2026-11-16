#!/usr/bin/env python3
"""H1/H2 development-only calibration using verified UDED-14 caches.

This code READS UDED-14 DEVELOPMENT GT ONLY when the explicit CLI flag
--authorize-uded-development-gt is present. It NEVER opens BIPED/MultiCue GT,
never recomputes descriptor maps, never uses validation/confirmatory outcomes
to select parameters, never modifies Stage24 artifacts or protocol.json.
It exports UNATTESTED fitted recipes requiring independent cohort review.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_paper_a_uded14_cache_sidecars_P0_3 import (
    CACHE, MANIFEST, PROVENANCE, audit_index)
from paper_a_freeze_guard import sha256
from prepare_paper_a_h1h2_recipe_P0_1 import (
    code_provenance, new_draft, validate as validate_recipe)
from src.stage24_integrity import load_float_artifact,resize_score_to_native
from src.stage24_residual import fit_membership, apply_membership
from src.stage24_recertification_ops import (
    fit_aggregator,apply_aggregator,choose_threshold)

PROTOCOL=ROOT/"docs/paper_a_confirmation/protocol.json"
OUT=Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_completion")
DESCRIPTORS=(
    "halfdisc_distribution_contrast",
    "pmi_dependency_deficit",
    "fh_region_boundary",
    "structure_tensor_coherence",
)


def git_head():
    p=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,
                     text=True,check=False,timeout=30)
    if p.returncode or len(p.stdout.strip())!=40:
        raise RuntimeError("Git HEAD not available")
    return p.stdout.strip()


def training_ids_hash(items:list[dict]) -> str:
    records=sorted((x["id"],x["source_sha256"]) for x in items)
    body=json.dumps(records,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(body).hexdigest()


def metadata_cache_lookup(items:list[dict]) -> tuple[dict,dict]:
    historic=json.loads(MANIFEST.read_text(encoding="utf-8"))
    with PROVENANCE.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    index=audit_index(historic,rows,CACHE)
    if index["status"]!="P0_3_ALL_CACHE_METADATA_MATCH_ONLY_NOT_CONTENT_VERIFIED":
        raise RuntimeError("UDED development cache not fully verified by P0.3")
    historic_by_id={r["image_id"]:r for r in historic["records"] if r["excluded"] is False}
    by_id={x["id"]:x for x in items}
    if len(by_id)!=len(historic_by_id) or set(by_id)!=set(historic_by_id):
        raise RuntimeError("Development GT original-image cohort drift")
    for iid,item in by_id.items():
        ref=historic_by_id[iid]
        if (item["source_sha256"]!=ref["source_sha256"] or
            list(item["gt"].shape)!=ref["native_gt_shape"]):
            raise RuntimeError("Development original/GT native geometry drift")
    pairs={(r["image_id"],r["descriptor_id"]):r
           for r in index["records"] if "image_id" in r}
    if len(pairs)!=56:
        raise RuntimeError("Expected exactly 56 unique P0.3 cache entries")
    return pairs,historic_by_id


def read_verified_maps(items,pairs):
    """Loaded arrays are DEVELOPMENT ONLY, with sidecar/NPY SHA verified."""
    maps={name:[] for name in DESCRIPTORS}
    artifact_sha=[]
    for item in items:
        for descriptor in DESCRIPTORS:
            rec=pairs[(item["id"],descriptor)]
            path=Path(rec["cache_npy_path"])
            if not path.is_file() or path.is_symlink():
                raise RuntimeError("Missing verified UDED cache: "+str(path))
            arr=load_float_artifact(path)
            registered=resize_score_to_native(arr,item["gt"].shape)
            if registered.shape!=item["gt"].shape:
                raise RuntimeError("GT-native registration failed")
            maps[descriptor].append(registered)
            artifact_sha.append({"id":item["id"],"descriptor":descriptor,
                                 "sha256":sha256(path)})
    return maps,artifact_sha


def fit_dev_models(items, maps, protocol, commit):
    gts=[x["gt"] for x in items]
    indices=list(range(len(items)))
    recipe=new_draft(protocol,code_provenance(ROOT),commit)
    method=recipe["fixed_method_choices"]
    if method["thinning"]!="nms_image" or method["calibration"]!="legacy_sigmoid":
        raise RuntimeError("Cannot silently change H1/H2 scientific method")
    export={"schema":"paper_a_uded14_development_fit_export_v1",
            "status":"TRAINED_ON_HISTORICALLY_EXPLORATORY_DEVELOPMENT_NOT_ATTESTED",
            "source_commit":commit,
            "development_dataset":"UDED14_exploratory_development_only",
            "training_ids_sha256":training_ids_hash(items),
            "models":{},
            "no_BIPED_or_MultiCue_GT_opened":True,
            "training_GT_UDED14_opened_with_explicit_permission":True,
            "historical_discovery_reused_for_parameter_training":True}
    for r in recipe["hypotheses"]:
        group=r["group"]
        cue_sets=[maps[d] for d in group]
        mem=fit_membership(cue_sets,gts,indices)
        memberships=[
            apply_membership([cue_sets[d][i] for d in range(len(group))],mem)
            for i in indices
        ]
        r["membership"]["midpoint"]=list(map(float,mem.midpoint))
        r["membership"]["scale"]=list(map(float,mem.scale))
        results={}
        for role in ("candidate","control"):
            kind=r[role]["family"]
            fitted=fit_aggregator(kind,memberships,gts,indices,seed=20261115)
            scores=[apply_aggregator(m,fitted) for m in memberships]
            threshold,train_counts=choose_threshold(
                scores,gts,[v["img"] for v in items],
                mode="nms_image",count=21)
            r[role]["threshold"]=float(threshold)
            if kind=="choquet_generalized_150":
                r[role]["capacity"]=list(map(float,fitted["capacity"]))
                r[role]["mobius"]=list(map(float,fitted["mobius"]))
            results[role]={"family":kind,"threshold":float(threshold),
                           "aggregator_state":fitted}
        export["models"][r["id"]]={
            "group":group,
            "membership":{"midpoint":r["membership"]["midpoint"],
                          "scale":r["membership"]["scale"]},
            "operators":results,
        }
    return recipe,export


def fill_fit_proofs_unattested(recipe,export_sha,commit,train_ids):
    proof={
        "development_dataset_id":"UDED14_exploratory_development_only",
        "split_role":"development_train",
        "training_ids_sha256":train_ids,
        "fitting_commit":commit,
        "parameter_export_sha256":export_sha,
        "no_confirmatory_overlap_attested":None,
    }
    for r in recipe["hypotheses"]:
        r["membership"]["fit_provenance"]=dict(proof)
        for role in ("candidate","control"):
            r[role]["threshold_fit_provenance"]=dict(proof)
        if r["id"]=="H2":
            r["candidate"]["capacity_fit_provenance"]=dict(proof)
    return recipe


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--authorize-uded-development-gt",action="store_true",
                    help="Explicit permission to open 14 UDED DEVELOPMENT GT masks")
    ap.add_argument("--uded-root",type=Path)
    ap.add_argument("--output-dir",type=Path,default=OUT)
    args=ap.parse_args()
    if not args.authorize_uded_development_gt:
        ap.error("Refusing GT access without --authorize-uded-development-gt")
    protocol=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol.get("status")!="draft_not_frozen" or protocol.get("confirmatory_outcomes_opened") is not False:
        ap.error("Development fitting allowed only before outcome access/freeze")
    from benchmark_uded import DEFAULT_UDED
    from run_stage24_residual_campaign import load_uded_native
    root=args.uded_root or Path(DEFAULT_UDED)
    if "UDED" not in str(root).upper() or any(
            x in str(root).lower() for x in ("multicue","bipedv2","test/bsds500")):
        ap.error("Only the original UDED development root is allowed")
    items,loaded=load_uded_native(root)
    if len(items)!=14:
        raise RuntimeError("Expected exactly 14 UDED original images")
    pairs,manifest=metadata_cache_lookup(items)
    maps,artifacts=read_verified_maps(items,pairs)
    commit=git_head()
    recipe,export=fit_dev_models(items,maps,protocol,commit)
    export["source_GT_sha256"]={k:v["gt_sha256"] for k,v in manifest.items()}
    export["descriptor_cache_sha256"]=artifacts
    args.output_dir.mkdir(parents=True,exist_ok=True)
    name=datetime.now(timezone.utc).strftime("devfit_%Y%m%dT%H%M%S_%fZ")
    ex_path=args.output_dir/(name+"_parameters.json")
    ex_path.write_text(json.dumps(export,indent=2,ensure_ascii=False),encoding="utf-8")
    recipe=fill_fit_proofs_unattested(
        recipe,sha256(ex_path),commit,training_ids_hash(items))
    recipe_path=args.output_dir/(name+"_recipe_UNATTESTED.json")
    recipe_path.write_text(json.dumps(recipe,indent=2,ensure_ascii=False),encoding="utf-8")
    check=validate_recipe(recipe,protocol,code_provenance(ROOT),commit)
    print(json.dumps({
        "status":"DEVELOPMENT_PARAMETERS_FITTED_NOT_INDEPENDENTLY_ATTESTED",
        "development_images":14,
        "required_maps_reused":56,
        "export":str(ex_path),
        "recipe":str(recipe_path),
        "remaining_P0_1_provenance_gates":check["pending"],
        "no_confirmatory_GT_F1_opened":True,
        "protocol_frozen":False,
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
