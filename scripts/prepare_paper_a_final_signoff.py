#!/usr/bin/env python3
"""Create ONE review-ready Paper A science signoff packet without opening GT.

Reads only existing input CSV/JSON and the specifically named legacy Stage13c
technical summary. No image or ground truth is loaded; no annotations, TAR,
HDF5, F1, Stage24 caches, training or fitting are inspected. It never issues
review PASS, a frozen protocol, a freeze approval or an outcome.
"""
from __future__ import annotations
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DATA = Path(r"F:\MFI-Edge-Data\MultiCue")
WORK = DATA / "paper_a_completion"
REVIEW = WORK / "scientific_signoff"
PROPOSAL = WORK / "COHORT_PROPOSAL_220_NOT_CERTIFIED.csv"
BIPED = ROOT / "results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv"
MULTICUE = DATA / "multicue_h5_anchored_sequence_candidates.csv"
P1 = ROOT / "docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json"
STAGE13C_SUMMARY = ROOT / "results/automation/stage13c_biped_preflight/summary.json"
EXECUTOR = ROOT / "scripts/execute_paper_a_frozen_cohort.py"
EXPECTED_FIELDS = ("dataset","image_id","relative_path","image_sha256",
                   "independence_review","prior_exposure_review","scene_group","notes")
REVIEW_FIELDS = EXPECTED_FIELDS + ("reviewer_independence_decision",
              "reviewer_prior_exposure_decision","evidence_for_both_decisions",
              "reviewer_name","reviewed_utc","historical_attention")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for x in iter(lambda: stream.read(1024*1024), b""):
            h.update(x)
    return h.hexdigest()


def rows(path: Path) -> list[dict]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 8_000_000:
        raise ValueError("Missing/unsafe existing metadata CSV: " + str(path))
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("Metadata CSV missing fields: " + str(path))
        return list(reader)


def existing_json(path: Path) -> dict | None:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 2_000_000:
        return None
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    return obj if isinstance(obj, dict) else None


def stage13c_metadata() -> dict:
    # This specifically named summary was produced by an existing
    # geometry/size preflight. Never open any referenced GT or image.
    if not STAGE13C_SUMMARY.is_file():
        return {
            "status": "EXECUTION_EVIDENCE_NOT_FOUND",
            "path_expected": str(STAGE13C_SUMMARY),
            "execution_verified": False,
            "independence_attested": False,
            "next_action": "Reviewer must inspect original operational summary/logs",
        }
    raw = existing_json(STAGE13C_SUMMARY)
    if raw is None:
        return {
            "status": "EXECUTION_SUMMARY_UNREADABLE",
            "path_expected": str(STAGE13C_SUMMARY),
            "independence_attested": False,
        }
    return {
        "status": "TECHNICAL_LOG_PRESENT_NEEDS_INDEPENDENT_ADJUDICATION",
        "path": str(STAGE13C_SUMMARY),
        "sha256": sha(STAGE13C_SUMMARY),
        "original_report_status": str(raw.get("status", "NOT_STATED"))[:120],
        "original_report_keys": sorted(raw.keys())[:40],
        "execution_verified": False,
        "independence_attested": False,
        "caveat": "Log existence is not proof of no train-GT exposure or use for optimization",
    }


def build_review_rows(cohort: list[dict], biped: list[dict],
                      multicue: list[dict]) -> list[dict]:
    if len(cohort) != 220:
        raise ValueError("Expected 220 draft originals; no scientific sample-size change")
    if any(set(EXPECTED_FIELDS) != set(r) for r in cohort):
        raise ValueError("Unexpected cohort schema")
    if any(r["independence_review"] != "pending" or
           r["prior_exposure_review"] != "pending" for r in cohort):
        raise ValueError("Provisional cohort has been silently marked approved")
    base_b = {r["image_id"]: r for r in biped}
    base_m = {r["sequence_id"]: r for r in multicue}
    count = {"BIPED": 0, "MultiCue": 0}
    seen, groups = set(), set()
    result = []
    for r in cohort:
        ds, iid = r["dataset"], r["image_id"]
        if ds not in count:
            raise ValueError("Unexpected cohort domain")
        count[ds] += 1
        if (ds,iid) in seen or (ds,r["scene_group"]) in groups:
            raise ValueError("Repeated image or independent group in proposal")
        seen.add((ds,iid)); groups.add((ds,r["scene_group"]))
        if ds == "BIPED":
            original = base_b.get(iid)
            if original is None or original["sha256"].lower() != r["image_sha256"].lower():
                raise ValueError("BIPED source provenance mismatch: " + iid)
            if r["relative_path"] != original["relative_path"]:
                raise ValueError("BIPED original path mismatch: " + iid)
            attention = "BIPED_HISTORICAL_TRAIN_GT_AND_SCENE_REVIEW"
            if iid == "RGB_221":
                attention += "; DUPLICATE_PAIR_REPRESENTATIVE_RGB_222"
            if original.get("near_image_flags"):
                attention += "; NEAR_IMAGE_FLAGS_PRESENT"
        else:
            source = base_m.get(iid)
            if source is None or source["capture_prefix"] != r["scene_group"] or r["scene_group"] == "4113":
                raise ValueError("MultiCue capture history mismatch: " + iid)
            if r["relative_path"] != Path(source["last_left_image"]).name:
                raise ValueError("MultiCue original source path mismatch")
            attention = "MULTICUE_HISTORY_AND_FRAME_SEQUENCE_INDEPENDENCE_PENDING"
            if r["scene_group"] == "4108":
                attention += "; REPEATED_PREFIX_FOUR_SEQUENCES_HOLD"
        result.append({
            **r,
            "reviewer_independence_decision": "PENDING",
            "reviewer_prior_exposure_decision": "PENDING",
            "evidence_for_both_decisions": "",
            "reviewer_name": "",
            "reviewed_utc": "",
            "historical_attention": attention,
        })
    if count != {"BIPED":125, "MultiCue":95}:
        raise ValueError("Expected proposed 125+95 composition")
    return result


def run(root: Path = ROOT, data: Path = DATA, work: Path = WORK) -> dict:
    # Root/data/work are provided for synthetic unit tests and source safety.
    protocol = existing_json(root / "docs/paper_a_confirmation/protocol.json")
    if protocol is None or protocol.get("status") != "draft_not_frozen":
        raise ValueError("Review-kit preparer is prefreeze only; cannot alter signed artifacts")
    cohort_path = work / "COHORT_PROPOSAL_220_NOT_CERTIFIED.csv"
    recipe_path = root / "docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json"
    evaluator = root / "scripts/execute_paper_a_frozen_cohort.py"
    cohort = rows(cohort_path)
    originals = rows(root / "results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv")
    seq = rows(data / "multicue_h5_anchored_sequence_candidates.csv")
    recipe = existing_json(recipe_path)
    if recipe is None:
        raise ValueError("P1 development recipe missing")
    from src.paper_a_h1h2_inference_core import validate_fitted_recipe
    validate_fitted_recipe(recipe)
    samples = build_review_rows(cohort, originals, seq)
    path = work / "scientific_signoff"
    path.mkdir(parents=True, exist_ok=True)
    sheet = path / "REVIEW_220_IMAGES_PENDING.csv"
    if not sheet.exists():
        with sheet.open("x", newline="", encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=REVIEW_FIELDS)
            writer.writeheader();writer.writerows(samples)
    else:
        current = rows(sheet)
        if len(current)!=220 or any(
                any(a.get(field)!=b.get(field) for field in EXPECTED_FIELDS)
                for a,b in zip(current,samples)):
            raise RuntimeError("Previously edited review sheet changed sample ID/hash/order; refuse overwrite")
    seven=[]
    for h in recipe["hypotheses"]:
        proofs = [("membership",h["membership"].get("fit_provenance")),
                  ("candidate_threshold",h["candidate"].get("threshold_fit_provenance")),
                  ("control_threshold",h["control"].get("threshold_fit_provenance"))]
        if h["id"]=="H2":
            proofs.append(("capacity",h["candidate"].get("capacity_fit_provenance")))
        for label, proof in proofs:
            seven.append({"hypothesis":h["id"],"fitted_part":label,
                          "no_confirmatory_overlap_attested":(proof or {}).get(
                              "no_confirmatory_overlap_attested"),
                          "source_training_ids_sha256":(proof or {}).get(
                              "training_ids_sha256")})
    if len(seven)!=7:
        raise ValueError("Unexpected number of P1 provenance claims")
    stage = root/"results/automation/stage13c_biped_preflight/summary.json"
    stage_info = ({"status": "EXECUTION_EVIDENCE_NOT_FOUND", "expected_path": str(stage),
                   "science_approval": False} if not stage.exists() else {
                   "status": "TECHNICAL_SUMMARY_PRESENT_REVIEW_REQUIRED",
                   "file_sha256": sha(stage),
                   "file_path": str(stage),
                   "science_approval": False})
    readme = path / "REVIEWER_DECISION_REQUIRED.md"
    readme.write_text(
        "# Paper A — independent signoff required before protected GT/F1\n\n"
        "This package contains metadata only. It MUST NOT be used to approve itself.\n\n"
        "1. Independently inspect Stage13c execution log and historical use of BIPED train GT.\n"
        "2. Review each row in REVIEW_220_IMAGES_PENDING.csv; document exposure, scene"
        " independence, evidence and accountable reviewer. PENDING is NOT PASS.\n"
        "3. Verify all seven UDED-14 P1 parameter provenance claims, including"
        " historical scene/capture overlap with the candidate cohort.\n"
        "4. Validate real BIPED and MultiCue edges GT encoding using documentation"
        " or non-confirmatory sample; the strict binary decoder is only a proposal.\n"
        "5. Review 125+95, effect-size assumptions, blocked Spearman/Holm,"
        " constant maps, empty masks and policy for missing data.\n"
        "6. AFTER genuine signoff, create frozen_cohort_manifest.csv,"
        " frozen_H1_H2_recipe.json, a separate versioned protocol freeze commit"
        " and freeze_approval.json with true reviewed evidence and SHA256.\n"
        "7. Run the SAME concluir_paper_a.ps1; it will validate the freeze and"
        " automatically execute paired F1 and H1/H2 only when permitted.\n\n"
        "Never edit the canonical candidate proposal or mark reviews PASSED without evidence.\n",
        encoding="utf-8")
    report = {
        "status":"REVIEW_PACKET_READY_SCIENTIFIC_SIGNOFF_PENDING",
        "n_candidates":220,"BIPED":125,"MultiCue":95,
        "requires_evidence_per_capture":True,
        "provisional_CORES_not_approved":True,
        "stage13c":stage_info,
        "P1_provenance_claims":seven,
        "P1_lineage_fully_attested":all(x["no_confirmatory_overlap_attested"] is True for x in seven),
        "technical_GT_executor_source_sha256":sha(evaluator) if evaluator.is_file() else None,
        "executor_independently_approved":False,
        "actual_GT_decoding_certified":False,
        "protocol_status":protocol.get("status"),
        "protocol_n":protocol["cohort"]["target_n_independent_images"],
        "proposed_n":220,
        "human_scientific_approval_issued":False,
        "review_sheet":str(sheet),
        "stage13c_metadata_only":True,
        "protected_GT_opened":False,
        "generated_utc":datetime.now(timezone.utc).isoformat(),
    }
    (path/"SIGNOFF_READINESS_NOT_APPROVAL.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    return {"status":report["status"],"sheet":str(sheet),"status_json":str(
        path/"SIGNOFF_READINESS_NOT_APPROVAL.json"),"stage13c":stage_info["status"],
        "science_approval":False}


if __name__=="__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
