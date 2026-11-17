#!/usr/bin/env python3
"""Build an unsigned Paper A scenario-A N219 scientific review preview.

Works ONLY with SHA-bound, already-validated pre-outcome CSV/JSON metadata.
Does NOT open original images, ground truths, descriptors, H5, predictions,
F1, or confirmatory outcomes. Does NOT change the active protocol or legacy
freeze executor. Never fills a reviewer PASS or approval; creates only an
explicitly non-active, pre-freeze draft and question sheet for human review.
"""
from __future__ import annotations
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_completion")
SIGNOFF=WORK/"scientific_signoff"
PROTOCOL=ROOT/"docs/paper_a_confirmation/protocol.json"
CANDIDATE=ROOT/"docs/paper_a_confirmation/COORTE_A_N219_PROPOSTA_NAO_CONGELADA.json"
ROSTER=SIGNOFF/"COORTE_A_N219_PARA_REVISAO_NAO_FROZEN.csv"
OLD=SIGNOFF/"REVIEW_220_IMAGES_PENDING.csv"
READINESS=SIGNOFF/"COORTE_A_N219_READINESS_NOT_APPROVED.json"
POWER=SIGNOFF/"PODER_A_N219_SENSIBILIDADE_NAO_APROVADA.json"
P1=SIGNOFF/"P1_LINEAGE_METADATA_CROSSCHECK_NOT_APPROVED.json"
GT_FORMAT=SIGNOFF/"NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json"
GT_DETAIL=SIGNOFF/"GT_PIXEL_ENCODING_DETAIL_PRE_FREEZE_v1.json"
STAGE13C=ROOT/"results/automation/stage13c_biped_preflight/summary.json"
EXE=ROOT/"scripts/execute_paper_a_frozen_cohort.py"
REVIEW_FIELDS=("dataset","image_id","relative_path","image_sha256",
    "independence_review","prior_exposure_review","scene_group","notes",
    "reviewer_independence_decision","reviewer_prior_exposure_decision",
    "evidence_for_both_decisions","reviewer_name","reviewed_utc","historical_attention")
APPROVALS=("training_lineage","capacity_and_thresholds","ground_truth_semantics",
    "independent_scenes_and_exposure","sample_size_and_inference","independent_protocol_review")
PROOFS=("H1.membership","H1.candidate_threshold","H1.control_threshold",
    "H2.membership","H2.candidate_threshold","H2.control_threshold","H2.capacity")

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def read_exact(path:Path,maxlen:int=8_000_000)->bytes:
    if not path.is_file() or path.is_symlink() or not 0<path.stat().st_size<=maxlen:
        raise ValueError("Required audit metadata missing/unsafe: "+str(path))
    return path.read_bytes()


def load_json(path:Path)->dict:
    value=json.loads(read_exact(path).decode("utf-8-sig"))
    if not isinstance(value,dict):raise ValueError("Expected JSON object")
    return value


def load_csv(path:Path)->list[dict]:
    with io.StringIO(read_exact(path).decode("utf-8-sig"),newline="") as stream:
        reader=csv.DictReader(stream)
        fields=tuple(reader.fieldnames or [])
        expected=("dataset","image_id","relative_path","image_sha256",
                  "independence_review","prior_exposure_review","scene_group","notes")
        if fields!=expected:
            raise ValueError("Unsigned N219 CSV unexpected columns")
        return list(reader)


def build(*,protocol:Path=PROTOCOL,candidate:Path=CANDIDATE,
          roster:Path=ROSTER,old:Path=OLD,readiness:Path=READINESS,power:Path=POWER,
          p1_path:Path=P1,stage:Path=STAGE13C,exe:Path=EXE,
          fmt:Path=GT_FORMAT,detail:Path=GT_DETAIL)->dict:
    cfg=load_json(candidate)
    ready=load_json(readiness)
    pw=load_json(power)
    source_protocol=load_json(protocol)
    p1=load_json(p1_path)
    if (cfg.get("counts")!={"BIPED":125,"MultiCue":94,"N":219} or
        ready.get("counts")!={"BIPED":125,"MultiCue":94,"N":219} or
        cfg.get("status")!="PROPOSAL_NOT_FROZEN_NOT_APPROVED" or
        ready.get("status")!="A_N219_ORIGINAL_SHA_VERIFIED_SCIENCE_GATES_OPEN"):
        raise ValueError("Selection A not in the expected unsigned technical state")
    for item in ("scientific_signoff","GT_accessed","freeze_authorized","H1_H2_executed"):
        if ready.get(item) is not False:
            raise PermissionError("Unexpected approved/outcome state: "+item)
    if source_protocol.get("status")!="draft_not_frozen" or source_protocol.get("confirmatory_outcomes_opened") is not False:
        raise PermissionError("Protocol already frozen or outcome state unexpected")
    rows=load_csv(roster)
    if len(rows)!=219 or Counter(r["dataset"] for r in rows)!={"BIPED":125,"MultiCue":94}:
        raise ValueError("Not the exact candidate-A N219 roster")
    if sha(read_exact(old))!=cfg.get("source_cohort_sha256"):
        raise ValueError("Legacy provisional 220-row sheet changed since human review")
    with io.StringIO(read_exact(old).decode("utf-8-sig"),newline="") as stream:
        old_rows=list(csv.DictReader(stream))
    if len(old_rows)!=220 or Counter(r.get("dataset") for r in old_rows)!={"BIPED":125,"MultiCue":95}:
        raise ValueError("Previous reviewed roster size changed")
    old_biped={r["image_id"] for r in old_rows if r["dataset"]=="BIPED"}
    selected_biped={r["image_id"] for r in rows if r["dataset"]=="BIPED"}
    if len(selected_biped & old_biped)!=83 or len(selected_biped-old_biped)!=42:
        raise ValueError("Previously reviewed vs new BIPED candidate partition changed")
    if sha(read_exact(roster))!=ready.get("review_roster_sha256"):
        raise ValueError("N219 roster SHA mismatch")
    idlist={ds:cfg["images"][ds].split(",") for ds in ("BIPED","MultiCue")}
    if [(r["dataset"],r["image_id"]) for r in rows] != [
        (ds,iid) for ds in ("BIPED","MultiCue") for iid in idlist[ds]]:
        raise ValueError("N219 roster order or identity changed")
    if not all(r["independence_review"]=="pending" and
               r["prior_exposure_review"]=="pending" for r in rows):
        raise PermissionError("N219 input silently approved")
    if pw.get("schema")!="paper_a_A_N219_power_sensitivity_no_protected_outcomes_v1" or pw.get("status")!="SYNTHETIC_PLANNING_ONLY_NOT_SCIENTIFICALLY_APPROVED":
        raise ValueError("Unexpected power-sensitivity source")
    if pw.get("source_metadata_sha256")!={"readiness_sha256":sha(read_exact(readiness)),
                                         "roster_sha256":sha(read_exact(roster))}:
        raise ValueError("Power assumptions are not bound to the exact current N219 inputs")
    if (pw.get("scientific_power_approval") is not False or
        pw.get("freeze_authorized") is not False or
        pw.get("GT_opened") is not False or
        pw.get("H1_H2_executed") is not False):
        raise PermissionError("Power report may not authorize freeze")
    effects={float(x["assumed_abs_population_Spearman_rho"]):x for x in pw.get("effects",[])}
    if set(effects)!={.15,.20,.25} or int(pw.get("replicates_per_effect",0))<1000:
        raise ValueError("Required power sensitivity scenarios missing")
    if pw.get("assumptions",{}).get("true_image_independence_presumed_not_verified") is not True:
        raise ValueError("Missing conditional-dependence limitation")
    if p1.get("all_seven_training_digests_match") is not True or len(p1.get("P1_seven_proofs",[]))!=7:
        raise PermissionError("Seven fitted development lineage records missing")
    if any(cfg.get(field) is not False for field in (
        "historical_exposure_approved","GT_semantics_approved",
        "independent_scene_approval","power_for_new_domain_mix_approved",
        "freeze_authorized","outcomes_access_authorized")):
        raise PermissionError("N219 source proposal has unexpected authorization")
    if not exe.is_file() or exe.is_symlink():
        raise FileNotFoundError("Confirmatory executor source missing")
    # Metadata evidence hashes are recorded but never treated as proof of semantic approval.
    evidence={}
    for label,path in (("P1",p1_path),("Stage13c",stage),
                       ("GT_format",fmt),("GT_detail",detail),("executor",exe)):
        if path.is_file() and not path.is_symlink():
            evidence[label]={"sha256":sha(read_exact(path,maxlen=4_000_000)),"available":True}
        else:
            evidence[label]={"sha256":None,"available":False}
    # This is a derived review DRAFT, not active protocol and not a freeze preview
    # recognized by the legacy N220 freeze command.
    draft=json.loads(json.dumps(source_protocol))
    draft["cohort"]["target_n_independent_images"]=219
    draft["cohort"]["dataset_names"]=["BIPED","MultiCue"]
    draft["cohort"]["selection"]=(
        "UNSIGNED PROSPECTIVE CANDIDATE A: 125 BIPED + 94 MultiCue; "
        "219 original source SHA256s verified in the independent source audit. "
        "42 alternative BIPED images introduced. Visual scene-group and "
        "historical-exposure independence remain independently unapproved. "
        "Do not open confirmatory outcomes.")
    draft["cohort"]["power_analysis"]=(
        "PREOUTCOME MODEL SENSITIVITY ONLY: Gaussian-copula Monte Carlo; "
        "10000 replicates each, within-domain Spearman weighted by n_d-1; "
        "one-sided normal-approximation p values, two-test Holm; "
        f"joint rejection rate at assumed |rho| 0.20 is "
        f"{effects[.20]['candidate_A']['joint_rejection_rate']:.4f}, "
        f"95% MC interval {effects[.20]['candidate_A']['mc_95pct_interval']}; "
        "not 100000-permutation exact planning; true scene independence assumed. "
        "Effect justification and power sufficiency require review.")
    draft["inference"]["test"]=(
        "PROPOSED (NOT FROZEN): domain-blocked one-sided midrank Spearman, "
        "weighted by n_d-1; 100000 Y permutations within each domain; "
        "two primary H1/H2 Holm familywise alpha=0.05.")
    draft["inference"]["ties"]=(
        "PROPOSED: midranks within each domain; undefined/constant rank maps "
        "fail closed; no outcome-dependent replacement.")
    draft["inference"]["multiplicity"]="Two-test Holm familywise stepdown"
    draft["measures"]["unit"]="proposed independent original scene/capture, never GT annotator"
    draft["measures"]["ground_truth_contract_proposal"]={
        "BIPED":"one original binary edge-map GT per image (scientific semantics not yet independently attested)",
        "MultiCue":"six edges GT masks per original capture, averaged at capture level, not six independent observations",
        "encoding_proposed_not_approved":"BIPED_UINT8_0_254_255_MULTICUE_UINT16_0_65535_NATIVE_v2",
        "empty_or_invalid_masks":"fail closed; handle only under prospectively approved missingness rules",
        "validation":"REQUIRES documented independent review of GT semantics and the six-annotator aggregation",
    }
    draft["status"]="draft_not_frozen"
    draft["freeze_commit"]=None
    draft["confirmatory_outcomes_opened"]=False
    draft["pre_freeze_revision_disclaimer"]=(
        "SCIENTIFIC REVIEW PREVIEW ONLY; not active protocol, no row signoffs "
        "or authority for first confirmatory access. Legacy freeze code N220 "
        "must be adapted and tested only after independent review.")
    review=[]
    for row in rows:
        review.append({
            **row,
            "reviewer_independence_decision":"PENDING",
            "reviewer_prior_exposure_decision":"PENDING",
            "evidence_for_both_decisions":"",
            "reviewer_name":"",
            "reviewed_utc":"",
            "historical_attention":(
                "NEW_BIPED_ALTERNATIVE_HISTORY_AND_SCENE_CHECK_REQUIRED"
                if row["dataset"]=="BIPED" and row["image_id"] not in old_biped
                else "HISTORY_AND_SCENE_CHECK_REQUIRED"),
        })
    # Every row is a pending human decision, not a machine-issued PASS.
    for item in review:
        if item["dataset"]!="BIPED":
            item["historical_attention"]="MULTICUE_EXPOSURE_AND_SCENE_CHECK_REQUIRED"
        elif item["image_id"] in set(cfg["quarantine_BIPED_ids"].split(",")):
            raise PermissionError("A quarantined original was silently selected")
    tmp=io.StringIO(newline="")
    writer=csv.DictWriter(tmp,fieldnames=REVIEW_FIELDS,lineterminator="\n")
    writer.writeheader()
    writer.writerows(review)
    sheet_bytes=tmp.getvalue().encode("utf-8")
    template={
        "schema_version":1,"approved_for_first_confirmatory_outcome_access":False,
        "reviewed_by":None,"approved_utc":None,
        "review_notes":None,
        "scientific_approvals":{name:False for name in APPROVALS},
        "P1_seven_lineage_reviews":{name:False for name in PROOFS},
        "reviewed_draft_protocol_sha256":sha(read_exact(protocol)),
        "reviewed_candidate_A_source_sha256":sha(read_exact(candidate)),
        "reviewed_A219_science_preview_sha256":None,
        "reviewed_cohort_sheet_sha256":sha(sheet_bytes),
        "power_report_sha256":sha(read_exact(power)),
        "P1_lineage_evidence":None,"stage13c_exposure_evidence":None,
        "cohort_independence_evidence":None,
        "ground_truth_encoding_evidence":None,
        "statistics_and_missingness_evidence":None,
        "gt_binary_decoding_contract":None,
        "evidence_paths_and_hashes":evidence,
        "review_template_only":True,"cannot_unlock_legacy_N220_freeze":True,
    }
    blockers=[
        "219 individual scene/exposure decisions remain unreviewed; never infer PASS from distinct SHA",
        "Historical Stage13c and Stage23/24 exposure must be independently evaluated, especially 42 new BIPED",
        "All seven P1 lineages need documented independent attestations (not just matching training hashes)",
        "GT v2 decoding semantics and MultiCue six-annotator policy need documentary review",
        "The |rho|=0.20 planning assumption and sensitivity to |rho|=0.15 need statistical signoff",
        "The current freeze script hardcodes 220 rows, 125+95 and REVIEW_220_IMAGES_PENDING.csv",
        "No reviewer has authored an approved scientific signoff for N219; H1/H2 must remain locked",
    ]
    return {
        "draft_protocol":draft,
        "review_sheet_bytes":sheet_bytes,
        "template":template,
        "assessment":{
            "schema":"paper_a_A219_scientific_gates_pre_freeze_v1",
            "status":"PREVIEW_ONLY_HUMAN_REVIEW_REQUIRED",
            "counts":{"BIPED":125,"MultiCue":94,"N":219},
            "power_result_at_assumed_abs_rho_020":effects[.20]["candidate_A"],
            "power_at_015":effects[.15]["candidate_A"],
            "power_at_025":effects[.25]["candidate_A"],
            "origin_sha256":{"active_protocol":sha(read_exact(protocol)),
                             "candidate_A_roster":sha(read_exact(roster)),
                             "power_sensitivity":sha(read_exact(power))},
            "evidence":evidence,"blockers":blockers,
            "frozen":False,"GT_opened":False,"confirmatory_H1_H2_executed":False,
            "scientific_signoff":False,
        }
    }


def write_immutable(out:Path,raw:bytes)->None:
    if out.exists():
        if out.is_symlink() or out.read_bytes()!=raw:
            raise RuntimeError("Previously reviewed preview differs; refuse overwrite: "+str(out))
    else:
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_bytes(raw)


def jsonbytes(obj:dict)->bytes:
    return (json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode("utf-8")


def main()->int:
    data=build()
    root=SIGNOFF/"CANDIDATE_A_N219_SCIENCE_REVIEW_NOT_ACTIVE"
    draftpath=root/"PROTOCOLO_N219_PARA_REVISAO_NAO_ATIVO.json"
    sheetpath=root/"REVIEW_A_N219_ALL_PENDING.csv"
    templatepath=root/"FINAL_INDEPENDENT_REVIEW_A219.template_NOT_APPROVED.json"
    statuspath=root/"SCIENTIFIC_GATES_A219_PENDING.json"
    template=data["template"]
    preview_bytes=jsonbytes(data["draft_protocol"])
    template["reviewed_A219_science_preview_sha256"]=sha(preview_bytes)
    write_immutable(draftpath,preview_bytes)
    write_immutable(sheetpath,data["review_sheet_bytes"])
    write_immutable(templatepath,jsonbytes(template))
    write_immutable(statuspath,jsonbytes(data["assessment"]))
    print(json.dumps({
        "status":"N219_SCIENCE_REVIEW_PREVIEW_READY_NO_APPROVAL",
        "protocol_preview":str(draftpath),
        "review_sheet":str(sheetpath),
        "unsigned_signoff_template":str(templatepath),
        "blockers_report":str(statuspath),
        "source_power_sha256":template["power_report_sha256"],
        "N":219,
        "science_approved":False,"freeze_authorized":False,
        "GT_opened":False,"H1_H2_executed":False
    },ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
