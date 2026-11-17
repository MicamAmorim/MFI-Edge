#!/usr/bin/env python3
"""Validate chosen A N219 as UNSIGNED prospective original-only review roster.
Never reads GT/H5/F1/descriptor maps; never signs, freezes, trains, or changes protocol.
"""
from __future__ import annotations
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
WORK=Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_completion")
SIGNOFF=WORK/"scientific_signoff"
CFG=ROOT/"docs/paper_a_confirmation/COORTE_A_N219_PROPOSTA_NAO_CONGELADA.json"
INV=ROOT/"results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv"
OLD=SIGNOFF/"REVIEW_220_IMAGES_PENDING.csv"
P1=SIGNOFF/"P1_LINEAGE_METADATA_CROSSCHECK_NOT_APPROVED.json"
PROTO=ROOT/"docs/paper_a_confirmation/protocol.json"
BIPED=ROOT/"datasets/BIPEDv2/edges/imgs/train/rgbr/real"
MULTICUE=Path(r"F:\MFI-Edge-Data\MultiCue\source_frames_only")
SHA=re.compile(r"^[a-f0-9]{64}$")
IMAGE=re.compile(r"^[A-Za-z0-9_-]+\.(?:jpg|jpeg|png|bmp)$",re.I)
COLUMNS=("dataset","image_id","relative_path","image_sha256",
         "independence_review","prior_exposure_review","scene_group","notes")


def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()


def read(path:Path)->bytes:
    if not path.is_file() or path.is_symlink() or not 0<path.stat().st_size<8_000_000:
        raise ValueError("Required metadata missing/unsafe: "+str(path))
    return path.read_bytes()


def load_csv(path:Path)->list[dict]:
    with io.StringIO(read(path).decode("utf-8-sig"),newline="") as f:
        return list(csv.DictReader(f))


def audit(config:Path=CFG,inventory:Path=INV,selected_old:Path=OLD,
          p1_path:Path=P1,protocol:Path=PROTO,
          biped_base:Path=BIPED,multicue_base:Path=MULTICUE,
          *,check_original_bytes:bool=True)->tuple[dict,list[dict]]:
    proposal=json.loads(read(config).decode("utf-8"))
    if proposal.get("schema")!="paper_a_candidate_A_219_pre_freeze_v1" or proposal.get("status")!="PROPOSAL_NOT_FROZEN_NOT_APPROVED":
        raise ValueError("Invalid candidate A schema or approval status")
    if proposal.get("counts")!={"BIPED":125,"MultiCue":94,"N":219}:
        raise ValueError("Candidate A counts changed")
    for label in ("historical_exposure_approved","GT_semantics_approved",
                  "independent_scene_approval","power_for_new_domain_mix_approved",
                  "freeze_authorized","outcomes_access_authorized"):
        if proposal.get(label) is not False:raise ValueError("Unauthorized flag: "+label)
    ids={ds:proposal["images"][ds].split(",") for ds in ("BIPED","MultiCue")}
    if any(len(set(ids[ds]))!=n for ds,n in (("BIPED",125),("MultiCue",94))):
        raise ValueError("Duplicate or missing original IDs")
    quarantine=set(proposal["quarantine_BIPED_ids"].split(","))
    if len(quarantine)!=16 or quarantine.intersection(ids["BIPED"]):
        raise ValueError("16 quarantined BIPED images cannot enter cohort A")
    if ("4586_left_0080" in ids["MultiCue"] or
        "4582_left_0020" not in ids["MultiCue"]):
        raise ValueError("MultiCue repeated pair exclusion changed")
    if digest(selected_old)!=proposal["source_cohort_sha256"]:
        raise ValueError("Original 220-row review sheet SHA drift")
    old=load_csv(selected_old)
    inv=load_csv(inventory)
    if (len(old)!=220 or Counter(r["dataset"] for r in old)!={"BIPED":125,"MultiCue":95} or
        len(inv)!=198 or any(r["dataset"]!="BIPEDv2_train" for r in inv)):
        raise ValueError("Prior cohort or BIPED candidates changed")
    old_by={(r["dataset"],r["image_id"]):r for r in old}
    inv_by={r["image_id"]:r for r in inv}
    if len(inv_by)!=198 or not set(ids["BIPED"]).issubset(inv_by):
        raise ValueError("Unrecognized BIPED candidate")
    rows=[]
    for ds in ("BIPED","MultiCue"):
        for name in ids[ds]:
            previous=old_by.get((ds,name))
            src=inv_by[name] if ds=="BIPED" else previous
            if src is None:raise ValueError("Unknown MultiCue original: "+name)
            sha=(src["sha256"] if ds=="BIPED" else src["image_sha256"]).lower()
            rel=src["relative_path"]
            if not SHA.fullmatch(sha) or not IMAGE.fullmatch(rel) or Path(rel).stem!=name:
                raise ValueError("Image ID, original filename or SHA malformed: "+name)
            if previous and (sha!=previous["image_sha256"].lower() or rel!=previous["relative_path"]):
                raise ValueError("Original selected image changed: "+name)
            base=biped_base if ds=="BIPED" else multicue_base
            image=base/rel
            if (not image.is_file() or image.is_symlink() or
                not image.resolve().is_relative_to(base.resolve()) or
                not 0<image.stat().st_size<50_000_000):
                raise FileNotFoundError("Original image missing/unsafe: "+str(image))
            if check_original_bytes and digest(image)!=sha:
                raise ValueError("Original SHA mismatch: "+name)
            rows.append({"dataset":ds,"image_id":name,"relative_path":rel,
                         "image_sha256":sha,"independence_review":"pending",
                         "prior_exposure_review":"pending",
                         "scene_group":"NOT_INDEPENDENTLY_ATTESTED_"+name,
                         "notes":"A_N219_REVIEW_ONLY__NOT_FROZEN"})
    lines=sorted("%s|%s|%s\n"%(r["dataset"],r["image_id"],r["image_sha256"]) for r in rows)
    manifest=hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    if manifest!=proposal["roster_sha256_sorted_dataset_id_source_sha"]:
        raise ValueError("Roster IDs/hashes differ from selected A proposal")
    retained=sum(("BIPED",x) in old_by for x in ids["BIPED"])
    if retained!=83 or 125-retained!=42:raise ValueError("Original and alternative mix changed")
    p1=json.loads(read(p1_path).decode("utf-8"))
    p1meta=(p1.get("all_seven_training_digests_match") is True and
            p1.get("all_seven_provenance_fields_internally_consistent") is True and
            len(p1.get("P1_seven_proofs",[]))==7)
    protocol_data=json.loads(read(protocol).decode("utf-8"))
    if protocol_data.get("status")!="draft_not_frozen":
        raise ValueError("Protocol no longer draft; do not run pre-freeze proposal audit")
    return ({
        "schema":"paper_a_A_219_metadata_readiness_v1",
        "status":"A_N219_ORIGINAL_SHA_VERIFIED_SCIENCE_GATES_OPEN",
        "counts":{"BIPED":125,"MultiCue":94,"N":219},
        "original_bytes_hashed":bool(check_original_bytes),
        "roster_sha256":manifest,"proposal_source_sha256":digest(config),
        "initial_cohort_source_sha256":digest(selected_old),
        "retained_BIPED":retained,"replacement_BIPED":42,
        "P1_lineage_metadata_consistent":p1meta,
        "existing_protocol_target_n":protocol_data.get("cohort",{}).get("target_n_independent_images"),
        "required_new_target_n":219,
        "scientific_signoff":False,"GT_accessed":False,
        "freeze_authorized":False,"H1_H2_executed":False,
        "blockers":[
            "History/exposure audit must cover 42 new BIPED alternatives and all 219 originals",
            "Scene independence requires adjudication beyond original-only SHA checks",
            "Seven P1 provenance and GT v2 semantics need external science review",
            "Recalculate joint H1/H2 power for the new 125 BIPED + 94 MultiCue composition",
            "Existing freeze code/preview and guard still assume N220 and 125+95: amend and test first",
            "Revised protocol, reviewer sheet, SHA bindings and real independent signoff must precede GT/F1 access"
        ]
    },rows)


def write_unchanged(path:Path,data:bytes)->None:
    if path.exists():
        if path.is_symlink() or path.read_bytes()!=data:
            raise RuntimeError("Previous review differs; do not overwrite: "+str(path))
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)


def main()->int:
    status,rows=audit()
    buffer=io.StringIO(newline="")
    writer=csv.DictWriter(buffer,fieldnames=COLUMNS,lineterminator="\n")
    writer.writeheader();writer.writerows(rows)
    cohort=SIGNOFF/"COORTE_A_N219_PARA_REVISAO_NAO_FROZEN.csv"
    content=buffer.getvalue().encode("utf-8")
    write_unchanged(cohort,content)
    status["review_roster_csv"]=str(cohort)
    status["review_roster_sha256"]=hashlib.sha256(content).hexdigest()
    report=SIGNOFF/"COORTE_A_N219_READINESS_NOT_APPROVED.json"
    write_unchanged(report,(json.dumps(status,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    status["readiness_report"]=str(report)
    print(json.dumps(status,ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
