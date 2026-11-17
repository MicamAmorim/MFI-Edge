#!/usr/bin/env python3
"""Metadata-only, fail-closed independent review binding for Paper A N219.

This module never opens images, GT, H5, maps or outcomes, never approves a
review row or signs a decision, and never modifies any input or protocol.
"""
from __future__ import annotations
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SIGNOFF=Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff")
CANDIDATE=ROOT/"docs/paper_a_confirmation/COORTE_A_N219_PROPOSTA_NAO_CONGELADA.json"
ROSTER=SIGNOFF/"COORTE_A_N219_PARA_REVISAO_NAO_FROZEN.csv"
READINESS=SIGNOFF/"COORTE_A_N219_READINESS_NOT_APPROVED.json"
POWER=SIGNOFF/"PODER_A_N219_SENSIBILIDADE_NAO_APROVADA.json"
PREVIEW=SIGNOFF/"CANDIDATE_A_N219_SCIENCE_REVIEW_NOT_ACTIVE/PROTOCOLO_N219_PARA_REVISAO_NAO_ATIVO.json"
ORIGINAL_REVIEW=SIGNOFF/"REVIEW_220_IMAGES_PENDING.csv"
EXPECTED={"BIPED":125,"MultiCue":94}
MATCH_FIELDS=("dataset","image_id","relative_path","image_sha256")
SCENE_PLACEHOLDERS=("NOT_INDEPENDENTLY_ATTESTED_","UNVERIFIED_SCENE_",
                    "NOT_REVIEWED","PENDING_","UNVERIFIED_")


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()


def safe(path:Path,max_bytes:int=8_000_000)->Path:
    if (not path.is_file() or path.is_symlink() or
        not 0 < path.stat().st_size <= max_bytes):
        raise PermissionError("Missing/unsafe candidate-A metadata: "+str(path))
    return path


def read_json(path:Path)->dict:
    obj=json.loads(safe(path).read_text(encoding="utf-8-sig"))
    if not isinstance(obj,dict):raise ValueError("Malformed candidate-A JSON")
    return obj


def read_rows(path:Path)->list[dict]:
    with safe(path).open(newline="",encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def validate_sources(*, candidate:Path=CANDIDATE, roster:Path=ROSTER,
                     readiness:Path=READINESS, power:Path=POWER,
                     preview:Path=PREVIEW, old:Path=ORIGINAL_REVIEW)->dict:
    """Bind the original 219 list, preview and synthetic-power evidence."""
    cfg=read_json(candidate);ready=read_json(readiness);study=read_json(power)
    version=read_json(preview)
    if (cfg.get("schema")!="paper_a_candidate_A_219_pre_freeze_v1" or
        cfg.get("status")!="PROPOSAL_NOT_FROZEN_NOT_APPROVED" or
        cfg.get("counts")!={"BIPED":125,"MultiCue":94,"N":219} or
        ready.get("counts")!=cfg["counts"] or
        ready.get("status")!="A_N219_ORIGINAL_SHA_VERIFIED_SCIENCE_GATES_OPEN" or
        ready.get("review_roster_sha256")!=sha(safe(roster)) or
        cfg.get("source_cohort_sha256")!=sha(safe(old))):
        raise PermissionError("Candidate-A IDs or source SHA disagree with audited N219")
    if any(cfg.get(k) is not False for k in (
        "historical_exposure_approved","GT_semantics_approved",
        "independent_scene_approval","power_for_new_domain_mix_approved",
        "freeze_authorized","outcomes_access_authorized")):
        raise PermissionError("Candidate-A source has fabricated prior scientific approval")
    if any(ready.get(k) is not False for k in (
        "scientific_signoff","freeze_authorized","GT_accessed","H1_H2_executed")):
        raise PermissionError("Source A219 audit unexpectedly claims approval/outcomes")
    if (version.get("status")!="draft_not_frozen" or
        version.get("cohort",{}).get("target_n_independent_images")!=219 or
        version.get("confirmatory_outcomes_opened") is not False or
        version.get("freeze_commit") is not None):
        raise PermissionError("Preliminary A219 protocol is not an unsigned draft")
    if (study.get("schema")!="paper_a_A_N219_power_sensitivity_no_protected_outcomes_v1" or
        study.get("status")!="SYNTHETIC_PLANNING_ONLY_NOT_SCIENTIFICALLY_APPROVED" or
        study.get("source_metadata_sha256")!={"readiness_sha256":sha(readiness),
                                               "roster_sha256":sha(roster)} or
        study.get("replicates_per_effect")!=10000):
        raise PermissionError("Power sensitivity does not match exact A219 sources")
    if any(study.get(k) is not False for k in (
        "scientific_power_approval","freeze_authorized","GT_opened","H1_H2_executed")):
        raise PermissionError("Power sensitivity may not authorize freeze")
    by_rho={float(x["assumed_abs_population_Spearman_rho"]):x
            for x in study.get("effects",[])}
    if set(by_rho)!={.15,.20,.25}:
        raise PermissionError("Prospective power-sensitivity effects absent")
    if (study.get("assumptions",{}).get("true_image_independence_presumed_not_verified")
        is not True):
        raise PermissionError("Power simulation incorrectly states verified independence")
    sample=read_rows(roster)
    if len(sample)!=219 or Counter(x.get("dataset") for x in sample)!=EXPECTED:
        raise PermissionError("Wrong candidate-A domain mix")
    expected_order=[(ds,id) for ds in ("BIPED","MultiCue")
                    for id in cfg.get("images",{}).get(ds,"").split(",")]
    if [(x["dataset"],x["image_id"]) for x in sample]!=expected_order:
        raise PermissionError("Source roster differs from selected A219 IDs")
    if any(x.get("independence_review")!="pending" or
           x.get("prior_exposure_review")!="pending" for x in sample):
        raise PermissionError("Automatic scene/exposure PASS found in source roster")
    quarantine=set(cfg.get("quarantine_BIPED_ids","").split(","))
    if len(quarantine)!=16 or quarantine.intersection(cfg["images"]["BIPED"].split(",")):
        raise PermissionError("16 disputed BIPED scenes were not quarantined")
    if "4586_left_0080" in cfg["images"]["MultiCue"].split(","):
        raise PermissionError("Repeated MultiCue frame reintroduced")
    return {"baseline_rows":sample,"candidate_A_sha256":sha(candidate),
            "roster_A_sha256":sha(roster),"readiness_sha256":sha(readiness),
            "power_A_sha256":sha(power),
            "N219_preliminary_protocol_sha256":sha(preview),
            "not_a_scientific_signoff":True}


def validate_reviewed_rows(reviewed:list[dict], base:list[dict],
                           *, require_groups:bool=False)->None:
    """Allow evidence/scene-group editing, NEVER image membership or hidden PASS."""
    if len(reviewed)!=219 or len(base)!=219:
        raise PermissionError("Signed N219 sheet must have exactly 219 original rows")
    groups=set();ids=set();hashes=set()
    for idx,(row,source) in enumerate(zip(reviewed,base)):
        if any(row.get(key)!=source.get(key) for key in MATCH_FIELDS):
            raise PermissionError("Reviewed image ID/path/SHA differs at A219 row "+str(idx))
        if row.get("independence_review")!="pending" or row.get("prior_exposure_review")!="pending":
            raise PermissionError("Original review status is not pending: "+str(idx))
        id=(row["dataset"],row["image_id"])
        if id in ids or row["image_sha256"] in hashes:
            raise PermissionError("Repeated image ID or hash in reviewed N219 sheet")
        ids.add(id);hashes.add(row["image_sha256"])
        group=str(row.get("scene_group") or "").strip()
        if require_groups:
            if not group or group.startswith(SCENE_PLACEHOLDERS):
                raise PermissionError("Unresolved automatic scene group at row "+str(idx))
            key=(row["dataset"],group)
            if key in groups:
                raise PermissionError("Repeated independent scene among selected rows")
            groups.add(key)
