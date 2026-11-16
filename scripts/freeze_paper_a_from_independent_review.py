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
BIN_POLICY="STRICT_BINARY_0_1_OR_0_255_NATIVE_v1"
BRANCH="experiment/paper-a-conditional-confirmation"
OUT_COMMIT_NOTE="freeze(paper-a): reviewed prospective H1/H2 protocol and N220 cohort"
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
    candidate["cohort"]["target_n_independent_images"]=220
    candidate["cohort"]["dataset_names"]=["BIPED","MultiCue"]
    candidate["measures"]["unit"]="independent_capture_or_scene"
    candidate["cohort"]["selection"]=(
        "Prospective fixed sample: 125 BIPED independent originals and 95 "
        "independent MultiCue captures, one per reviewed scene/prefix, with "
        "hash-ranked deterministic representatives and historic 4113 exclusion. "
        "Each one must have passed the independent exposure and scene audit "
        "before this protocol is committed.")
    candidate["cohort"]["power_analysis"]=(
        "Pre-outcome simulation: 1000 repetitions, homogeneous absolute "
        "rho=0.20, 125 BIPED + 95 MultiCue, joint power about 0.823; "
        "conditional only, not observed post-confirmatory evidence.")
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
    draft=freeze_candidate(protocol)
    desired=jsonify(draft)
    if SOURCE_SNAPSHOT.exists():
        if SOURCE_SNAPSHOT.read_text(encoding="utf-8")!=desired:
            raise RuntimeError("Existing reviewed protocol preview differs from current source")
    else:
        SOURCE_SNAPSHOT.write_text(desired,encoding="utf-8")
    reviewed=SIGNOFF/"REVIEW_220_IMAGES_PENDING.csv"
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
        "approved_executor_source_sha256":sha(EXECUTOR),
        "stage13c_summary_sha256":None,
    }
    stage=ROOT/"results/automation/stage13c_biped_preflight/summary.json"
    if stage.is_file() and not stage.is_symlink() and stage.stat().st_size<2_000_000:
        plan["stage13c_summary_sha256"]=sha(stage)
    if not TEMPLATE.exists():
        TEMPLATE.write_text(jsonify(plan),encoding="utf-8")
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
        "approved_executor_source_sha256":sha(executor)}
    if stage.is_file():
        required["stage13c_summary_sha256"]=sha(stage)
    for key,val in required.items():
        if decision.get(key)!=val:
            raise PermissionError("Signed review hash is stale/different: "+key)
    if decision.get("gt_binary_decoding_contract")!=BIN_POLICY:
        raise PermissionError("No approved, independently verified GT decoder policy")
    if len(sheet)!=220:
        raise PermissionError("Review sheet does not have 220 original captures")
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
    if counts!={"BIPED":125,"MultiCue":95}:
        raise PermissionError("Proposed domain mix changed; re-plan independently before freeze")


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
        "stage13c_summary_sha256":sha(stage) if stage.is_file() else None,
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
        "executor_contract_independently_reviewed":True,
        "gt_binary_decoding_contract":BIN_POLICY,
        "review_notes":decision["review_notes"],
        "review_decision_sha256":sha(SIGNED),
        "review_sheet_sha256":sha(sheet_path),
    }
    with approval_path.open("x",encoding="utf-8") as f:
        f.write(jsonify(record))
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
    if original.exists():
        if original.read_bytes()!=process.stdout:
            raise PermissionError("Original pre-freeze parent snapshot changed")
    else:
        original.write_bytes(process.stdout)
    if (not SOURCE_SNAPSHOT.is_file() or
        SOURCE_SNAPSHOT.read_bytes()!=PROTOCOL.read_bytes()):
        raise PermissionError("Frozen commit differs from originally reviewed protocol")
    decision=json.loads(SIGNED.read_text(encoding="utf-8"))
    sheet_path=SIGNOFF/"REVIEW_220_IMAGES_PENDING.csv"
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
        "approved_executor_source_sha256":sha(EXECUTOR)})
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
                "review_sheet":str(SIGNOFF/"REVIEW_220_IMAGES_PENDING.csv"),
                "freeze_commit_created":False}
    protocol=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol.get("status")=="frozen":
        return resume_freeze_after_interrupted_push()
    if protocol.get("status")!="draft_not_frozen":
        raise PermissionError("Unexpected protocol status; no freeze transition")
    decision=json.loads(SIGNED.read_text(encoding="utf-8"))
    sheet_path=SIGNOFF/"REVIEW_220_IMAGES_PENDING.csv"
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
    if actual!=jsonify(proposal).encode("utf-8"):
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
