#!/usr/bin/env python3
"""Paper A one-command REVIEWED freeze transition. Never self-approve.

Prepares a byte-exact prospective protocol preview and an approval *template*.
Once a genuinely independently reviewed row sheet and signed external decision
exist, the SAME command creates the freeze commit and approves exact local
hashes, then the existing guarded executor can run. No confirmatory GT/XY/F1
is read by this module. No 'pass' or signoff is manufactured.
"""
from __future__ import annotations
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
WORK=Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_completion")
SIGNOFF=WORK/"scientific_signoff"
PROTOCOL=ROOT/"docs/paper_a_confirmation/protocol.json"
P1=ROOT/"docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json"
EXECUTOR=ROOT/"scripts/execute_paper_a_frozen_cohort.py"
from paper_a_freeze_guard import GT_POLICY_V2 as BIN_POLICY
import paper_a_a219_freeze_policy as a219
BRANCH="experiment/paper-a-conditional-confirmation"
OUT_COMMIT_NOTE="freeze(paper-a): independently reviewed prospective H1/H2 protocol and N219 cohort"
PROOFS=("H1.membership","H1.candidate_threshold","H1.control_threshold",
        "H2.membership","H2.candidate_threshold","H2.control_threshold","H2.capacity")
APPROVALS=("training_lineage","capacity_and_thresholds","ground_truth_semantics",
           "independent_scenes_and_exposure","sample_size_and_inference",
           "independent_protocol_review")
ROWS=("dataset","image_id","relative_path","image_sha256",
      "independence_review","prior_exposure_review","scene_group","notes")
REVIEW_FIELDS=ROWS+("reviewer_independence_decision",
                "reviewer_prior_exposure_decision","evidence_for_both_decisions",
                "reviewer_name","reviewed_utc","historical_attention")
SOURCE_SNAPSHOT=SIGNOFF/"FROZEN_PROTOCOL_BYTES_TO_REVIEW_NOT_ACTIVE.json"
TEMPLATE=SIGNOFF/"FINAL_INDEPENDENT_REVIEW.template.json"
SIGNED=SIGNOFF/"FINAL_INDEPENDENT_REVIEW.json"
A_DIR=SIGNOFF/"CANDIDATE_A_N219_SCIENCE_REVIEW_NOT_ACTIVE"
REVIEW_SHEET=A_DIR/"REVIEW_A_N219_ALL_PENDING.csv"
CANDIDATE_A=ROOT/"docs/paper_a_confirmation/COORTE_A_N219_PROPOSTA_NAO_CONGELADA.json"
ROSTER_A=SIGNOFF/"COORTE_A_N219_PARA_REVISAO_NAO_FROZEN.csv"
READINESS_A=SIGNOFF/"COORTE_A_N219_READINESS_NOT_APPROVED.json"
POWER_A=SIGNOFF/"PODER_A_N219_SENSIBILIDADE_NAO_APROVADA.json"
SCIENTIFIC_PREVIEW_A=A_DIR/"PROTOCOLO_N219_PARA_REVISAO_NAO_ATIVO.json"
A_COUNTS={"BIPED":125,"MultiCue":94}
GT_FORMAT_EVIDENCE=SIGNOFF/"NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json"
GT_DETAIL_EVIDENCE=SIGNOFF/"GT_PIXEL_ENCODING_DETAIL_PRE_FREEZE_v1.json"


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()


def csvrows(path: Path) -> list[dict]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size>8_000_000:
        raise ValueError("Missing/unsafe review CSV: "+str(path))
    with path.open(newline="",encoding="utf-8-sig") as f:
        dr=csv.DictReader(f)
        if tuple(dr.fieldnames or ())!=REVIEW_FIELDS:
            raise ValueError("Review sheet columns unexpectedly changed")
        return list(dr)


def jsonify(obj: dict) -> str:
    return json.dumps(obj,indent=2,ensure_ascii=False)+"\n"


def freeze_candidate(protocol: dict) -> dict:
    if protocol.get("status")!="draft_not_frozen":
        raise ValueError("Freeze candidate requires a draft")
    from revisar_paper_a_pre_freeze import proposed_protocol
    candidate=proposed_protocol(protocol)
    candidate.pop("pre_freeze_revision_disclaimer",None)
    candidate["status"]="frozen"
    candidate["confirmatory_outcomes_opened"]=False
    candidate["freeze_commit"]=None
    candidate["cohort"]["target_n_independent_images"]=219
    candidate["cohort"]["dataset_names"]=["BIPED","MultiCue"]
    candidate["measures"]["unit"]="independent_capture_or_scene"
    candidate["cohort"]["selection"]=(
        "Prospective candidate A: 125 BIPED and 94 MultiCue originals. "
        "Identities fixed by 219 source SHA256s, 42 BIPED replacements, "
        "16 disputed BIPED scenes quarantined, 4113 excluded. "
        "Each one must have passed the independent exposure and scene audit "
        "before this protocol is committed.")
    candidate["cohort"]["power_analysis"]=(
        "Pre-outcome 10000-replicate Gaussian copula planning simulation, homogeneous "
        "rho=0.20, 125 BIPED + 94 MultiCue, planning joint power about 0.815; "
        "asymptotic normal rather than exact permutation p; conditionally assumed independent scenes. Not confirmed outcomes.")
    contract=candidate["measures"].pop("ground_truth_contract_proposal")
    contract["encoding"]=BIN_POLICY
    contract["validation"]=(
        "Independent GT-semantics and binary-decoding evidence is required "
        "in the external reviewed freeze decision; no automatic decoding "
        "or late threshold fitting.")
    candidate["measures"]["ground_truth_contract"]=contract
    candidate["inference"]["test"]=(
        "Primary domain-blocked one-sided Spearman midranks, "
        "weighted mean of within-domain rho with weights n_d-1; "
        "100000 Y permutations restricted to each domain.")
    candidate["inference"]["ties"]=(
        "Midranks within domain, permute Y within each domain; constant ranks "
        "fail closed and require scientific escalation, no post-outcome exclusions.")
    candidate["inference"]["multiplicity"]=(
        "Holm step-down adjustment for the two preregistered primary hypotheses")
    return candidate


def verified_nonconfirmatory_gt_v2_evidence(
        fmt: Path = GT_FORMAT_EVIDENCE,
        detail: Path = GT_DETAIL_EVIDENCE) -> dict[str, str]:
    """Metadata-only validation. Does NOT certify foreground semantics.

    This only prevents approving a decoder that contradicts the exact
    previously recorded out-of-cohort masks. Real scientific signoff is
    still a separately required external decision.
    """
    for path in (fmt, detail):
        if (not path.is_file() or path.is_symlink() or
                path.stat().st_size > 1_000_000):
            raise PermissionError("Nonconfirmatory GT metadata unavailable/unsafe: "+str(path))
    original=json.loads(fmt.read_text(encoding="utf-8"))
    observed=json.loads(detail.read_text(encoding="utf-8"))
    if (original.get("schema_version") != 1 or
            original.get("status") != "GT_FORMAT_SAMPLE_OBSERVED_NOT_INDEPENDENTLY_CERTIFIED" or
            original.get("only_nonconfirmatory_GT_opened") is not True or
            original.get("protected_confirmatory_GT_opened") is not False or
            original.get("confirmation_F1_computed") is not False or
            original.get("scientific_GT_semantics_approval") is not False or
            original.get("sample_counts") != {"BIPED":3,"MultiCue":12} or
            observed.get("schema_version") != 1 or
            observed.get("source_report_sha256") != sha(fmt) or
            observed.get("status") != "NONCONFIRMATORY_GT_PIXEL_ENCODING_DETAIL_NOT_CERTIFIED" or
            observed.get("confirmatory_GT_accessed") is not False or
            observed.get("F1_computed") is not False or
            observed.get("excluded_capture_only") is not True or
            observed.get("no_threshold_selected") is not True or
            observed.get("requires_independent_encoding_review") is not True or
            observed.get("sample_counts") != {"BIPED_test":3,"MultiCue_excluded_4113":12}):
        raise PermissionError("Nonconfirmatory GT evidence is incomplete or mismatched")
    for label, old_key, new_key, dtype, allowed in (
            ("BIPED","BIPED_samples","BIPED_test","uint8",{0,254,255}),
            ("MultiCue","MultiCue_samples","MultiCue_excluded_4113","uint16",{0,65535})):
        earlier=original.get(old_key)
        later=observed.get(new_key)
        if not isinstance(earlier,list) or not isinstance(later,list) or len(earlier)!=len(later):
            raise PermissionError("Nonconfirmatory sample count changed: "+label)
        known={r.get("source_file"):r for r in earlier}
        if len(known)!=len(earlier):
            raise PermissionError("Duplicate earlier GT sample names")
        union=set()
        for entry in later:
            name=entry.get("source_file")
            previous=known.get(name)
            values=entry.get("all_values_if_at_most_32")
            if (not isinstance(name,str) or previous is None or
                    entry.get("sha256") != previous.get("file_sha256") or
                    entry.get("dtype") != dtype or
                    entry.get("shape") != previous.get("shape") or
                    not isinstance(values,list) or
                    not values or not set(values).issubset(allowed) or
                    entry.get("scientific_decoding_approved") is not False):
                raise PermissionError("GT detailed encoding record drift: "+label)
            if label=="BIPED":
                if ("/edges/edge_maps/test/rgbr/" not in
                    name.replace("\\","/").lower()):
                    raise PermissionError("BIPED reference is not from test split")
            elif not re.fullmatch(
                    r"multicue/ground-truth/images/edges/4113_left_\d+\.\d+\.png",
                    name.removeprefix("./")):
                raise PermissionError("MultiCue reference not in excluded 4113")
            union.update(values)
        if union!=allowed:
            raise PermissionError("Observed GT sample code set differs: "+label)
    return {"nonconfirmatory_gt_format_sha256":sha(fmt),
            "nonconfirmatory_gt_detail_sha256":sha(detail)}


def git(*args: str) -> str:
    p=subprocess.run(["git",*args],cwd=ROOT,capture_output=True,
                     text=True,check=False,timeout=80)
    if p.returncode:
        raise RuntimeError("git "+ " ".join(args) +" failed: "+p.stderr[-400:])
    return p.stdout.strip()


def prepare() -> dict:
    SIGNOFF.mkdir(parents=True,exist_ok=True)
    if not PROTOCOL.is_file() or not EXECUTOR.is_file() or not P1.is_file():
        raise ValueError("Missing protocol/P1/executor")
    protocol=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol.get("status")!="draft_not_frozen":
        return {"status":"VERSIONED_PROTOCOL_ALREADY_NON_DRAFT",
                "external_approval_not_issued":True}
    metadata=a219.validate_sources()
    a219.validate_reviewed_rows(csvrows(REVIEW_SHEET),metadata["baseline_rows"])
    draft=freeze_candidate(protocol)
    desired=jsonify(draft)
    desired_bytes=desired.encode("utf-8")
    if SOURCE_SNAPSHOT.exists() and SOURCE_SNAPSHOT.read_bytes()!=desired_bytes:
        if SIGNED.exists():
            raise PermissionError("Signed decision exists: cannot alter reviewed protocol preview")
        previous=SOURCE_SNAPSHOT.read_bytes()
        backup=SOURCE_SNAPSHOT.with_name(
            SOURCE_SNAPSHOT.stem+"_SUPERSEDED_"+hashlib.sha256(previous).hexdigest()[:12]+".json")
        if backup.exists() and backup.read_bytes()!=previous:
            raise RuntimeError("Existing superseded protocol preview differs")
        if not backup.exists():
            backup.write_bytes(previous)
        SOURCE_SNAPSHOT.write_bytes(desired_bytes)
    elif not SOURCE_SNAPSHOT.exists():
        SOURCE_SNAPSHOT.write_bytes(desired_bytes)
    reviewed=REVIEW_SHEET
    original_sha=sha(PROTOCOL)
    candidate_sha=sha(SOURCE_SNAPSHOT)
    plan={
        "schema_version":1,
        "approved_for_first_confirmatory_outcome_access":False,
        "reviewed_by":None,"approved_utc":None,
        "review_notes":None,
        "scientific_approvals":{key:False for key in APPROVALS},
        "P1_seven_lineage_reviews":{key:False for key in PROOFS},
        "P1_lineage_evidence":None,
        "cohort_independence_evidence":None,
        "stage13c_exposure_evidence":None,
        "ground_truth_encoding_evidence":None,
        "statistics_and_missingness_evidence":None,
        "gt_binary_decoding_contract":None,
        "reviewed_draft_protocol_sha256":original_sha,
        "reviewed_frozen_protocol_preview_sha256":candidate_sha,
        "reviewed_cohort_sheet_sha256":sha(reviewed) if reviewed.is_file() else None,
        "reviewed_P1_recipe_sha256":sha(P1),
        "reviewed_candidate_A_sha256":metadata["candidate_A_sha256"],
        "reviewed_A219_roster_sha256":metadata["roster_A_sha256"],
        "reviewed_A219_power_report_sha256":metadata["power_A_sha256"],
        "reviewed_N219_preliminary_protocol_sha256":metadata["N219_preliminary_protocol_sha256"],
        "approved_executor_source_sha256":sha(EXECUTOR),
        "approved_runtime_sources_sha256":__import__(
            "paper_a_freeze_guard",fromlist=["runtime_source_hashes"]
        ).runtime_source_hashes(ROOT),
        "stage13c_summary_sha256":None,
        "nonconfirmatory_gt_format_sha256":sha(GT_FORMAT_EVIDENCE) if GT_FORMAT_EVIDENCE.is_file() else None,
        "nonconfirmatory_gt_detail_sha256":sha(GT_DETAIL_EVIDENCE) if GT_DETAIL_EVIDENCE.is_file() else None,
    }
    stage=ROOT/"results/automation/stage13c_biped_preflight/summary.json"
    if stage.is_file() and not stage.is_symlink() and stage.stat().st_size<2_000_000:
        plan["stage13c_summary_sha256"]=sha(stage)
    if not TEMPLATE.exists():
        TEMPLATE.write_bytes(jsonify(plan).encode("utf-8"))
    elif not SIGNED.exists():
        # The reviewer has not signed: preserve the old template as evidence
        # of the previous revision and provide a current hash-bound template.
        template_old=json.loads(TEMPLATE.read_text(encoding="utf-8"))
        if any(template_old.get(k)!=plan[k] for k in (
                "reviewed_draft_protocol_sha256",
                "reviewed_frozen_protocol_preview_sha256",
                "reviewed_cohort_sheet_sha256",
                "reviewed_P1_recipe_sha256",
                "reviewed_candidate_A_sha256",
                "reviewed_A219_roster_sha256",
                "reviewed_A219_power_report_sha256",
                "reviewed_N219_preliminary_protocol_sha256",
                "approved_executor_source_sha256",
                "approved_runtime_sources_sha256",
                "nonconfirmatory_gt_format_sha256",
                "nonconfirmatory_gt_detail_sha256")):
            backup=TEMPLATE.with_name(TEMPLATE.stem+"_SUPERSEDED_"+
                hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()[:12]+".json")
            if not backup.exists():
                backup.write_bytes(TEMPLATE.read_bytes())
            TEMPLATE.write_bytes(jsonify(plan).encode("utf-8"))
    output=SIGNOFF/"FREEZE_READINESS_PREVIEW.json"
    info={
        "status":"REVIEWED_FREEZE_READY_ONLY_WHEN_SIGNED_AND_EVIDENCED",
        "review_template":str(TEMPLATE),
        "expected_signoff_file":str(SIGNED),
        "review_sheet":str(reviewed),
        "reviewed_protocol_candidate":str(SOURCE_SNAPSHOT),
        "protocol_sha256":candidate_sha,
        "technical_evaluator_sha256":sha(EXECUTOR),
        "stage13c_summary_present":plan["stage13c_summary_sha256"] is not None,
        "scientific_signoff_issued":False,
        "next_step":"Independent reviewer must fully adjudicate rows AND sign explicit final decision; no automatic PASS",
    }
    output.write_text(jsonify(info),encoding="utf-8")
    return info


def iso_utc(value) -> bool:
    if not isinstance(value,str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z",value):
        return False
    try:
        datetime.fromisoformat(value[:-1]+"+00:00")
        return True
    except ValueError:
        return False


def validate_signed_decision(decision: dict, sheet: list[dict],
                             source_protocol: Path, preview: Path,
                             source_recipe: Path, executor: Path,
                             sheet_path: Path, stage: Path) -> None:
    # The decision is AUTHORED OUTSIDE this script and must bind the exact
    # reviewed bytes. A username is accountability, not a crypto signature.
    if decision.get("schema_version")!=1 or decision.get(
            "approved_for_first_confirmatory_outcome_access") is not True:
        raise PermissionError("No independent prospective release authorization")
    reviewer=decision.get("reviewed_by")
    if not isinstance(reviewer,str) or len(reviewer.strip())<5:
        raise PermissionError("Named accountable independent reviewer required")
    if not iso_utc(decision.get("approved_utc")):
        raise PermissionError("Reviewer UTC timestamp missing/invalid")
    if not isinstance(decision.get("review_notes"),str) or len(decision["review_notes"].strip())<60:
        raise PermissionError("Substantive, auditable reviewer report required")
    for key in APPROVALS:
        if decision.get("scientific_approvals",{}).get(key) is not True:
            raise PermissionError("Scientific approval missing: "+key)
    for key in PROOFS:
        if decision.get("P1_seven_lineage_reviews",{}).get(key) is not True:
            raise PermissionError("P1 lineage proof NOT independently approved: "+key)
    for key in ("P1_lineage_evidence","cohort_independence_evidence",
                "stage13c_exposure_evidence","ground_truth_encoding_evidence",
                "statistics_and_missingness_evidence"):
        item=decision.get(key)
        if not isinstance(item,str) or len(item.strip())<60:
            raise PermissionError("Missing independently reviewed evidence: "+key)
    required={
        "reviewed_draft_protocol_sha256":sha(source_protocol),
        "reviewed_frozen_protocol_preview_sha256":sha(preview),
        "reviewed_cohort_sheet_sha256":sha(sheet_path),
        "reviewed_P1_recipe_sha256":sha(source_recipe),
        "reviewed_candidate_A_sha256":a219.validate_sources()["candidate_A_sha256"],
        "reviewed_A219_roster_sha256":a219.validate_sources()["roster_A_sha256"],
        "reviewed_A219_power_report_sha256":a219.validate_sources()["power_A_sha256"],
        "reviewed_N219_preliminary_protocol_sha256":a219.validate_sources()["N219_preliminary_protocol_sha256"],
        "approved_executor_source_sha256":sha(executor),
        "approved_runtime_sources_sha256":__import__(
            "paper_a_freeze_guard",fromlist=["runtime_source_hashes"]
        ).runtime_source_hashes(ROOT)}
    if stage.is_file():
        required["stage13c_summary_sha256"]=sha(stage)
    for key,val in required.items():
        if decision.get(key)!=val:
            raise PermissionError("Signed review hash is stale/different: "+key)
    if decision.get("gt_binary_decoding_contract")!=BIN_POLICY:
        raise PermissionError("No approved, independently verified v2 GT decoder policy")
    verified=verified_nonconfirmatory_gt_v2_evidence()
    for name,actual in verified.items():
        if decision.get(name)!=actual:
            raise PermissionError("Independently reviewed GT evidence SHA is stale: "+name)
    # The matching metadata does not grant approval; the independently
    # authored scientific_approvals.ground_truth_semantics and full reviewer
    # evidence are separate mandatory checks above.
    if len(sheet)!=219:
        raise PermissionError("Review sheet does not have 219 original captures")
    counts={"BIPED":0,"MultiCue":0}
    ids,groups,hashes=set(),set(),set()
    for i,row in enumerate(sheet):
        if row.get("independence_review")!="pending" or row.get("prior_exposure_review")!="pending":
            raise PermissionError("Original proposal was modified at row "+str(i))
        if row.get("reviewer_independence_decision")!="PASS" or row.get("reviewer_prior_exposure_decision")!="PASS":
            raise PermissionError("Independent review remains PENDING at row "+str(i))
        if (not row.get("reviewer_name") or
            not iso_utc(row.get("reviewed_utc")) or
            len(row.get("evidence_for_both_decisions","").strip())<35):
            raise PermissionError("Scene evidence/reviewer missing at row "+str(i))
        ds=row.get("dataset")
        if ds not in counts:
            raise PermissionError("Invalid domain")
        counts[ds]+=1
        key=(ds,row.get("image_id"))
        grp=(ds,row.get("scene_group"))
        hashval=row.get("image_sha256")
        if (key in ids or grp in groups or hashval in hashes):
            raise PermissionError("Duplicate capture/scene/hash")
        ids.add(key);groups.add(grp);hashes.add(hashval)
        if row.get("scene_group")=="4113" and ds=="MultiCue":
            raise PermissionError("Previously exposed MultiCue group 4113 forbidden")
    if counts!=A_COUNTS:
        raise PermissionError("Proposed A219 mix changed; re-plan independently before freeze")
    evidence=a219.validate_sources()
    a219.validate_reviewed_rows(sheet,evidence["baseline_rows"],require_groups=True)


def version_freeze_evidence(recipe: Path, cohort: Path,
                            decision: dict, sheet_path: Path) -> list[str]:
    """Git-version protocol-linked recipe and minimal public cohort without PII.

    All detailed reviewer evidence stays on F:. Commit only dataset identifiers,
    independent scene identifiers, hash checksums and frozen fitted parameters.
    """
    docs=ROOT/"docs/paper_a_confirmation"
    rec=docs/"FROZEN_H1_H2_RECIPE_P1.json"
    selections=docs/"FROZEN_COHORT_IDS_PUBLIC.csv"
    manifest=docs/"FROZEN_FREEZE_INPUTS_MANIFEST.json"
    if any(p.exists() for p in (rec,selections,manifest)):
        raise PermissionError("Existing versioned freeze metadata must not be overwritten")
    rec.write_bytes(recipe.read_bytes())
    with cohort.open(newline="",encoding="utf-8-sig") as original, \
            selections.open("x",newline="",encoding="utf-8") as out:
        reader=csv.DictReader(original)
        writer=csv.DictWriter(out,fieldnames=ROWS)
        writer.writeheader()
        for row in reader:
            public={k:row[k] for k in ROWS}
            public["notes"]="Independent adjudication stored privately; bound by freeze manifest hashes."
            writer.writerow(public)
    stage=ROOT/"results/automation/stage13c_biped_preflight/summary.json"
    record={
        "status":"REVIEWED_PRE_GT_CONFIRMATORY_LOCK",
        "schema_version":1,
        "protocol_sha256":sha(SOURCE_SNAPSHOT),
        "local_frozen_recipe_sha256":sha(recipe),
        "public_frozen_recipe_sha256":sha(rec),
        "local_frozen_cohort_sha256":sha(cohort),
        "public_frozen_cohort_sha256":sha(selections),
        "external_signed_decision_sha256":sha(SIGNED),
        "external_review_sheet_sha256":sha(sheet_path),
        "executor_source_sha256":sha(EXECUTOR),
        "approved_runtime_sources_sha256":__import__(
            "paper_a_freeze_guard",fromlist=["runtime_source_hashes"]
        ).runtime_source_hashes(ROOT),
        "stage13c_summary_sha256":sha(stage) if stage.is_file() else None,
        **{k:decision[k] for k in ("nonconfirmatory_gt_format_sha256", "nonconfirmatory_gt_detail_sha256")},
        "reviewed_utc":decision["approved_utc"],
        "no_GT_opened_by_freeze_step":True,
        "explanation":"SHA-bound independent review; full reviewer notes retained privately on F:, not pushed to Git",
    }
    manifest.write_text(jsonify(record),encoding="utf-8")
    return [str(p.relative_to(ROOT)).replace("\\","/") for p in
            (rec,selections,manifest)]


def materialize_protocol_and_cohort(decision: dict, sheet: list[dict],
                                    protocol_preview: Path, recipe_source: Path,
                                    work: Path) -> tuple[Path,Path]:
    # Generate reviewed artifacts, NEVER modify the human-completed review sheet.
    # Verify historical fitted-source SHA and all seven independently approved
    # provenance claims BEFORE writing or publishing any frozen files.
    from paper_a_freeze_guard import validate_fitted_recipe as validate_historical
    proposed=json.loads(protocol_preview.read_text(encoding="utf-8"))
    probe=json.loads(recipe_source.read_text(encoding="utf-8"))
    for item in probe["hypotheses"]:
        proofs=(item["membership"]["fit_provenance"],
                item["candidate"]["threshold_fit_provenance"],
                item["control"]["threshold_fit_provenance"])
        for record in proofs:
            record["no_confirmatory_overlap_attested"]=True
        if item["id"]=="H2":
            item["candidate"]["capacity_fit_provenance"]["no_confirmatory_overlap_attested"]=True
    proof_blockers=validate_historical(probe,proposed,ROOT)
    if proof_blockers:
        raise PermissionError("Review input cannot be frozen: "+"; ".join(proof_blockers))
    cohort=work/"frozen_cohort_manifest.csv"
    recipe=work/"frozen_H1_H2_recipe.json"
    if cohort.exists() or recipe.exists():
        raise RuntimeError("Frozen artifacts already present; refuse implicit overwrite")
    with cohort.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=ROWS)
        writer.writeheader()
        for row in sheet:
            writer.writerow({
                **{k:row[k] for k in ROWS},
                "independence_review":"pass",
                "prior_exposure_review":"pass",
                "notes": (row["notes"]+"; reviewer="+row["reviewer_name"]+
                          "; evidence="+row["evidence_for_both_decisions"])[:3000],
            })
    fitted=json.loads(recipe_source.read_text(encoding="utf-8"))
    for h in fitted["hypotheses"]:
        proofs=[h["membership"]["fit_provenance"],
                h["candidate"]["threshold_fit_provenance"],
                h["control"]["threshold_fit_provenance"]]
        if h["id"]=="H2":
            proofs.append(h["candidate"]["capacity_fit_provenance"])
        for proof in proofs:
            proof["no_confirmatory_overlap_attested"]=True
    fitted["status"]="FITTED_DEVELOPMENT_GT_LINEAGE_INDEPENDENTLY_REVIEWED"
    recipe.write_text(jsonify(fitted),encoding="utf-8")
    return recipe,cohort


def issue_approval_after_remote_freeze(decision: dict, sheet_path: Path,
                                       recipe: Path, cohort: Path,
                                       commit: str) -> dict:
    """Bind the preapproved reviewer decision to final exact hashes post-push."""
    approval_path=WORK/"freeze_approval.json"
    if approval_path.exists():
        raise PermissionError("Existing freeze_approval.json must be reviewed, not overwritten")
    record={
        "schema_version":1,
        "approved_for_first_confirmatory_outcome_access":True,
        "reviewed_by":decision["reviewed_by"],
        "approved_utc":decision["approved_utc"],
        "freeze_commit":commit,
        "protocol_sha256":sha(PROTOCOL),
        "cohort_sha256":sha(cohort),
        "recipe_sha256":sha(recipe),
        "scientific_approvals":{k:True for k in APPROVALS},
        "approved_executor_source_sha256":sha(EXECUTOR),
        "approved_runtime_sources_sha256":decision["approved_runtime_sources_sha256"],
        "executor_contract_independently_reviewed":True,
        "gt_binary_decoding_contract":BIN_POLICY,
        **{k:decision[k] for k in ("nonconfirmatory_gt_format_sha256", "nonconfirmatory_gt_detail_sha256")},
        "review_notes":decision["review_notes"],
        "review_decision_sha256":sha(SIGNED),
        "review_sheet_sha256":sha(sheet_path),
    }
    # Do not expose a partially written approval after a crash. If a prior
    # run was interrupted while staging, resume only identical reviewed bytes.
    import os
    staged=approval_path.with_suffix(".json.part")
    approved_bytes=jsonify(record).encode("utf-8")
    if staged.exists():
        if staged.is_symlink() or staged.read_bytes()!=approved_bytes:
            raise PermissionError("Unrecoverable partial freeze approval; requires manual review")
    else:
        with staged.open("xb") as out:
            out.write(approved_bytes)
    os.replace(staged,approval_path)
    from paper_a_freeze_guard import validate_files
    gate=validate_files(PROTOCOL,recipe,cohort,approval_path)
    if gate["blockers"]:
        raise RuntimeError("Scientific freeze guard rejected signed commit: "+
                           "; ".join(gate["blockers"]))
    return {
        "status":"SIGNED_FREEZE_COMMITTED_AND_GUARD_VALIDATED",
        "freeze_commit":commit,
        "freeze_certified":True,
        "review_decision_sha256":sha(SIGNED),
        "protected_GT_opened_by_this_module":False,
    }


def resume_freeze_after_interrupted_push() -> dict:
    """Resume a fully REVIEWED local Git freeze, never self-authorize."""
    if not SIGNED.is_file():
        return {"status":"FROZEN_PROTOCOL_MISSING_SIGNED_REVIEW",
                "freeze_commit_created":False}
    if (WORK/"freeze_approval.json").exists():
        return {"status":"FROZEN_APPROVAL_PRESENT_DEFER_TO_GUARD"}
    current=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if current.get("status")!="frozen":
        raise ValueError("Recovery requires frozen versioned protocol")
    commit=git("rev-parse","HEAD")
    if (git("branch","--show-current")!=BRANCH or
        git("log","-1","--format=%s")!=OUT_COMMIT_NOTE or
        git("status","--porcelain","--untracked-files=no")):
        raise PermissionError("Cannot recover freeze: commit/branch/worktree unexpected")
    process=subprocess.run(
        ["git","show","HEAD^:docs/paper_a_confirmation/protocol.json"],
        cwd=ROOT,capture_output=True,check=False,timeout=60)
    if process.returncode or len(process.stdout)>4_000_000:
        raise RuntimeError("Cannot recover frozen protocol's original reviewed parent")
    original=SIGNOFF/"PRE_FREEZE_PROTOCOL_FROM_REVIEWED_PARENT.json"
    if not original.is_file() or original.is_symlink():
        raise PermissionError("Missing exact pre-freeze reviewed working tree backup")
    if original.read_bytes().replace(b"\r\n",b"\n") != (
            process.stdout.replace(b"\r\n",b"\n")):
        raise PermissionError("Pre-freeze backup contradicts committed Git parent")
    if (not SOURCE_SNAPSHOT.is_file() or
        SOURCE_SNAPSHOT.read_bytes()!=PROTOCOL.read_bytes()):
        raise PermissionError("Frozen commit differs from originally reviewed protocol")
    decision=json.loads(SIGNED.read_text(encoding="utf-8"))
    sheet_path=REVIEW_SHEET
    sheet=csvrows(sheet_path)
    stage=ROOT/"results/automation/stage13c_biped_preflight/summary.json"
    validate_signed_decision(decision,sheet,original,SOURCE_SNAPSHOT,
                             P1,EXECUTOR,sheet_path,stage)
    recipe=WORK/"frozen_H1_H2_recipe.json"
    cohort=WORK/"frozen_cohort_manifest.csv"
    if not recipe.is_file() or not cohort.is_file():
        raise PermissionError("Cannot recover incomplete freeze inputs")
    checked=json.loads(recipe.read_text(encoding="utf-8"))
    source=json.loads(P1.read_text(encoding="utf-8"))
    for a,b in zip(checked["hypotheses"],source["hypotheses"]):
        for key in ("membership","candidate","control"):
            if a[key].get("threshold")!=b[key].get("threshold"):
                raise PermissionError("Recovery found modified fitted threshold")
        for p in (a["membership"]["fit_provenance"],
                  a["candidate"]["threshold_fit_provenance"],
                  a["control"]["threshold_fit_provenance"],
                  *((a["candidate"]["capacity_fit_provenance"],)
                    if a["id"]=="H2" else ())):
            if p.get("no_confirmatory_overlap_attested") is not True:
                raise PermissionError("Recovery found unattested P1 source")
    if len(sheet)!=len(csvrows_for_frozen(cohort)):
        raise PermissionError("Recovery cohort rows changed")
    # Verify the versioned source and hashes again; a partially committed
    # freeze must not be marked approved if its public evidence is missing.
    from paper_a_freeze_guard import verify_versioned_freeze_inputs
    manifest_blockers=verify_versioned_freeze_inputs(
        ROOT, PROTOCOL, recipe, cohort, {"review_decision_sha256":sha(SIGNED),
        "review_sheet_sha256":sha(sheet_path),
        "approved_executor_source_sha256":sha(EXECUTOR),
        "approved_runtime_sources_sha256":decision["approved_runtime_sources_sha256"]})
    if manifest_blockers:
        raise PermissionError("Review evidence changed during recovery: "+"; ".join(manifest_blockers))
    git("push","origin",BRANCH)
    return issue_approval_after_remote_freeze(decision,sheet_path,recipe,cohort,commit)


def csvrows_for_frozen(cohort_path: Path) -> list[dict]:
    with cohort_path.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames or ())!=ROWS:
            raise ValueError("Unexpected frozen cohort schema")
        return list(reader)


def attempt_freeze() -> dict:
    """Use a reviewer-supplied signed decision, never create it."""
    prep=prepare()
    if not SIGNED.is_file():
        return {"status":"AWAITING_INDEPENDENT_SCIENTIFIC_SIGNOFF",
                "review_template":str(TEMPLATE),
                "review_sheet":str(REVIEW_SHEET),
                "freeze_commit_created":False}
    protocol=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol.get("status")=="frozen":
        return resume_freeze_after_interrupted_push()
    if protocol.get("status")!="draft_not_frozen":
        raise PermissionError("Unexpected protocol status; no freeze transition")
    decision=json.loads(SIGNED.read_text(encoding="utf-8"))
    sheet_path=REVIEW_SHEET
    sheet=csvrows(sheet_path)
    stage=ROOT/"results/automation/stage13c_biped_preflight/summary.json"
    validate_signed_decision(decision,sheet,PROTOCOL,SOURCE_SNAPSHOT,
                             P1,EXECUTOR,sheet_path,stage)
    if git("branch","--show-current")!=BRANCH or git(
            "status","--porcelain","--untracked-files=no"):
        raise PermissionError("Repo branch wrong or tracked working tree modified")
    # Fail closed on any source drift. The preview bytes are precisely what
    # the reviewer approved; no post-signoff protocol field edits.
    actual=SOURCE_SNAPSHOT.read_bytes()
    proposal=freeze_candidate(protocol)
    # Existing Windows CRLF previews were already SHA-bound to reviews.
    # Compare their text semantics without changing their reviewed bytes.
    if actual.replace(b"\r\n",b"\n")!=jsonify(proposal).encode("utf-8"):
        raise PermissionError("Reviewed protocol preview no longer matches source draft")
    # Authentication/push permission must be available BEFORE changing protocol.
    git("push","--dry-run","origin",BRANCH)
    # Exact reviewed recipe source must still pass structural audit before freeze.
    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0,str(ROOT))
    from src.paper_a_h1h2_inference_core import validate_fitted_recipe
    validate_fitted_recipe(json.loads(P1.read_text(encoding="utf-8")))
    recipe,cohort=materialize_protocol_and_cohort(
        decision,sheet,SOURCE_SNAPSHOT,P1,WORK)
    # Save exact PRE-FREEZE reviewed bytes before any write. Git may normalize
    # the parent blob to LF, while the reviewed working tree used CRLF.
    parent_backup=SIGNOFF/"PRE_FREEZE_PROTOCOL_FROM_REVIEWED_PARENT.json"
    original_bytes=PROTOCOL.read_bytes()
    if parent_backup.exists():
        if parent_backup.read_bytes()!=original_bytes:
            raise PermissionError("Pre-freeze source backup does not match reviewed draft")
    else:
        with parent_backup.open("xb") as stream:
            stream.write(original_bytes)
    # Version the recipe, a redacted cohort ID list and a SHA-only review
    # manifest alongside the separately reviewed prospective protocol.
    versioned=version_freeze_evidence(recipe,cohort,decision,sheet_path)
    PROTOCOL.write_bytes(actual)
    git("add","--","docs/paper_a_confirmation/protocol.json",*versioned)
    git("commit","-m",OUT_COMMIT_NOTE)
    commit=git("rev-parse","HEAD")
    # The freeze is not published until an explicit push succeeds. Never
    # generate an authorization to open protected outcomes before push.
    git("push","origin",BRANCH)
    # Bind the reviewer-signed decision to exact frozen hashes after remote push.
    return issue_approval_after_remote_freeze(decision,sheet_path,recipe,cohort,commit)
