#!/usr/bin/env python3
"""One resumable Paper A command. No protected GT before signed freeze.

Runs available predata audits/checks once, reuses development and MultiCue
evidence, then invokes the existing fail-closed finish_paper_a controller.
Never reruns descriptor maps, dev fit, image matching or dataset downloads.
"""
from __future__ import annotations
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
# Windows direct-script launches put scripts/, not the repository root, on
# sys.path. Native packages (src.*) require the repository root explicitly.
# Also works under python -I and does not modify the user's environment.
for module_root in (ROOT, ROOT / "scripts"):
    module_path = str(module_root)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)
WORK = Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_completion")
MULTICUE = Path(r"F:\MFI-Edge-Data\MultiCue")
DATA = ROOT / "results/local_dev/paper_a_confirmation_inventory"
INV = DATA / "biped_candidates_P1_20261116.csv"
AUDIT = DATA / "predata_audit/candidate_review.csv"
DEDUP = DATA / "predata_audit/biped_train_after_visual_dedup_candidates.csv"
DEDUP_META = DATA / "predata_audit/visual_dedup_summary.json"
DECISIONS = ROOT / "docs/paper_a_confirmation/visual_duplicate_decisions.csv"
TESTS = (
    "test_paper_a_prefreeze_map_adapter.py",
    "test_paper_a_multicue_gt_task_names.py",
    "test_paper_a_paired_f1_contract.py",
    "test_paper_a_freeze_guard.py",
    "test_analyze_paper_a_confirmed.py",
    "test_finish_paper_a.py",
    "test_continuar_paper_a.py",
    "test_execute_paper_a_frozen_cohort.py",
    "test_revisar_paper_a_pre_freeze.py",
    "test_export_paper_a_review_bundle.py",
    "test_prepare_paper_a_final_signoff.py",
    "test_freeze_paper_a_from_independent_review.py",
    "test_paper_a_codex_finalizer.py",
    "test_paper_a_nonconfirmatory_gt_format.py",
)


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def run(label: str, arguments: list[str], timeout: int = 1800) -> None:
    log = WORK / "one_command_logs" / (label + ".log")
    log.parent.mkdir(parents=True, exist_ok=True)
    print("[RUN]", label, flush=True)
    with log.open("w", encoding="utf-8", errors="replace") as f:
        p = subprocess.run(arguments, cwd=ROOT, stdout=f,
                           stderr=subprocess.STDOUT, timeout=timeout, check=False)
    if p.returncode:
        raise RuntimeError(label + " failed (exit " + str(p.returncode) +
                           "). See " + str(log))
    print("[OK]", label, flush=True)


def checkout() -> str:
    for args, expectation in [
        (["branch", "--show-current"], "experiment/paper-a-conditional-confirmation"),
    ]:
        p = subprocess.run(["git", *args], cwd=ROOT, check=True,
                           capture_output=True, text=True, timeout=60)
        if p.stdout.strip() != expectation:
            raise RuntimeError("Wrong Git branch: " + p.stdout.strip())
    state = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           cwd=ROOT, check=True, capture_output=True,
                           text=True, timeout=60).stdout.strip()
    if state:
        raise RuntimeError("Tracked files modified, no automatic overwrite: " + state)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                          capture_output=True, text=True, timeout=60).stdout.strip()


def validate_biped() -> dict:
    original, reviewed = csv_rows(INV), csv_rows(DEDUP)
    meta = json.loads(DEDUP_META.read_text(encoding="utf-8"))
    a = {r["image_id"]: r["sha256"].lower() for r in original}
    b = {r["image_id"]: r["sha256"].lower() for r in reviewed}
    if (len(original) != 200 or len(a) != 200 or len(reviewed) != 198
            or len(b) != 198 or set(a) - set(b) != {"RGB_172", "RGB_222"}
            or any(a.get(k) != sha for k, sha in b.items())
            or meta.get("remaining_not_certified") != 198
            or meta.get("audit_csv_sha256") != hash_file(AUDIT)
            or meta.get("decision_csv_sha256") != hash_file(DECISIONS)
            or meta.get("excluded_for_sampling") != ["RGB_172", "RGB_222"]
            or any(r["confirmatory_eligibility"] !=
                   "PENDING_HISTORICAL_AND_SCENE_LINEAGE_AUDIT"
                   for r in reviewed)):
        raise RuntimeError("Historical BIPED 198-image dedup changed; stop")
    return {"status": "198_CANDIDATES_NOT_CERTIFIED",
            "reused_csv_sha256": hash_file(DEDUP)}


def biped_once() -> dict:
    root = ROOT / "datasets/BIPEDv2/edges/imgs/train/rgbr/real"
    if not INV.exists():
        run("biped_inventory", [
            sys.executable, str(ROOT / "scripts/inventory_paper_a_confirmation_images.py"),
            "--dataset", "BIPEDv2_train=" + str(root), "--out", str(INV)])
    if not AUDIT.exists():
        run("biped_audit", [
            sys.executable, str(ROOT / "scripts/audit_paper_a_confirmation_predata.py"),
            "--inventory", str(INV)], timeout=2400)
    if not DEDUP.exists() and not DEDUP_META.exists():
        run("biped_dedup", [
            sys.executable, str(ROOT / "scripts/apply_paper_a_visual_dedup.py"),
            "--audit", str(AUDIT)])
    result = validate_biped()
    print("[REUSE] 198 BIPED candidates, no GT", flush=True)
    return result


def multicue_metadata() -> dict:
    from check_paper_a_multicue_gt_task_names import validate_inventory
    result = validate_inventory(MULTICUE)
    if (result.get("status") != "TASK_GT_NAME_LAYOUT_VERIFIED_CONTENT_UNOPENED_NOT_FROZEN"
            or result.get("sequence_count") != 100
            or result.get("capture_prefix_count") != 96
            or result.get("provisional_max_other_prefixes") != 95
            or result.get("annotation_file_names_by_task") !=
               {"edges": 600, "boundaries": 500}):
        raise RuntimeError("MultiCue index not coherent with prior audit")
    print("[REUSE] 100 sequences, 95 provisional capture groups, no GT", flush=True)
    return {"status": "95_GROUPS_NOT_CERTIFIED",
            "archive_sha256": result["archive_sha256"]}


def p1_metadata() -> dict:
    from src.paper_a_h1h2_inference_core import validate_fitted_recipe
    path = ROOT / "docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json"
    recipe = json.loads(path.read_text(encoding="utf-8"))
    validate_fitted_recipe(recipe)
    return {"status": "DEVELOPMENT_RECIPE_VALIDATED_NOT_ATTESTED",
            "recipe_sha256": hash_file(path)}


def propose_review_cohort() -> dict:
    """Deterministic 125+95 DRAFT; never copies to a frozen manifest."""
    p = WORK / "COHORT_PROPOSAL_220_NOT_CERTIFIED.csv"
    if p.exists():
        rows = csv_rows(p)
        if (len(rows) != 220 or
                any(r["independence_review"] != "pending" or
                    r["prior_exposure_review"] != "pending" for r in rows)):
            raise RuntimeError("Existing proposal was changed; do not silently replace it")
        return {"status": "DRAFT_REUSED_NOT_CERTIFIED", "file": str(p)}
    biped = csv_rows(DEDUP)
    source = csv_rows(MULTICUE / "multicue_source_frames_only_manifest.csv")
    index = csv_rows(MULTICUE / "multicue_h5_anchored_sequence_candidates.csv")
    seq = {r["sequence_id"]: r for r in index}
    if len(biped) != 198 or len(source) != 100 or len(seq) != 100:
        raise ValueError("Source manifests incomplete: no draft selection")
    fields = ("dataset", "image_id", "relative_path", "image_sha256",
              "independence_review", "prior_exposure_review", "scene_group", "notes")
    rows = []
    for r in sorted(biped, key=lambda x: (x["sha256"], x["image_id"]))[:125]:
        rows.append({
            "dataset": "BIPED", "image_id": r["image_id"],
            "relative_path": r["relative_path"], "image_sha256": r["sha256"],
            "independence_review": "pending", "prior_exposure_review": "pending",
            "scene_group": r["image_id"],
            "notes": "DRAFT: scene group provisional, prior exposure not certified"})
    groups = {}
    for r in source:
        key = r["sequence_id"]
        if key not in seq or r["capture_prefix"] != seq[key]["capture_prefix"]:
            raise ValueError("MultiCue source/sequence manifest mismatch")
        if r["capture_prefix"] == "4113":
            continue
        groups.setdefault(r["capture_prefix"], []).append(r)
    if len(groups) != 95:
        raise ValueError("Expected 95 MultiCue provisional capture prefixes")
    for prefix, group in sorted(groups.items()):
        chosen = sorted(group, key=lambda x: (x["sha256"], x["sequence_id"]))[0]
        filename = Path(chosen["local_original_frame_path"]).name
        if filename != Path(seq[chosen["sequence_id"]]["last_left_image"]).name:
            raise ValueError("MultiCue original image filename mismatch")
        rows.append({
            "dataset": "MultiCue", "image_id": chosen["sequence_id"],
            "relative_path": filename, "image_sha256": chosen["sha256"],
            "independence_review": "pending", "prior_exposure_review": "pending",
            "scene_group": prefix,
            "notes": "DRAFT: one per capture prefix, scene lineage pending"})
    if len(rows) != 220:
        raise RuntimeError("Expected 220 draft rows")
    with p.open("x", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return {"status": "DRAFT_CREATED_NOT_CERTIFIED", "file": str(p),
            "BIPED": 125, "MultiCue": 95, "sha256": hash_file(p)}


def find_old_audit() -> bool:
    from finish_paper_a import audit_exists
    return audit_exists(checkout()) is not None


def one_shot() -> dict:
    WORK.mkdir(exist_ok=True, parents=True)
    info = {"schema": "paper_a_one_command_v1",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": checkout(), "steps": {},
            "GT_read_during_prefreeze": False,
            "scientific_freeze_autoapproved": False,
            "old_detector_maps_recomputed": False}
    for name, action in [
        ("biped", biped_once),
        ("multicue", multicue_metadata),
        ("P1", p1_metadata),
    ]:
        info["steps"][name] = action()
    # Pre-freeze proposals must never be rewritten or required after a
    # legitimately signed freeze. Otherwise the single-command executor
    # could never reach its authorized post-freeze confirmation path.
    protocol_status = json.loads(
        (ROOT / "docs/paper_a_confirmation/protocol.json").read_text(encoding="utf-8")
    ).get("status")
    if protocol_status == "draft_not_frozen":
        info["steps"]["cohort_proposal"] = propose_review_cohort()
        from revisar_paper_a_pre_freeze import create_dossier
        info["steps"]["scientific_review"] = create_dossier()
        from prepare_paper_a_final_signoff import run as prepare_review
        info["steps"]["signoff_readiness"] = prepare_review()
        from freeze_paper_a_from_independent_review import prepare as freeze_preview
        info["steps"]["frozen_protocol_preview"] = freeze_preview()
    else:
        info["steps"]["cohort_proposal"] = {
            "status": "SKIPPED_AFTER_DRAFT_NO_FROZEN_ARTIFACT_CHANGES"}
        info["steps"]["scientific_review"] = {
            "status": "SKIPPED_AFTER_DRAFT_FREEZE_GUARD_STILL_REQUIRED"}
    for file in TESTS:
        # The prefreeze reviewer-dossier unit test intentionally asserts a
        # draft N=150 protocol; do not make a legitimate frozen confirmation
        # fail merely because that development-only test is no longer relevant.
        if protocol_status == "frozen" and file == "test_revisar_paper_a_pre_freeze.py":
            info["steps"]["draft_dossier_test"] = {"status": "SKIPPED_AFTER_FREEZE"}
            continue
        run("test_" + file.replace(".py", ""), [
            sys.executable, str(ROOT / "tests" / file)], timeout=600)
    run("real_Stage23_synthetic_preflight", [
        sys.executable, str(ROOT / "scripts/preflight_paper_a_prefreeze_map_adapter.py"),
        "--real-stage23"], timeout=1200)
    info["steps"]["synthetic_tests"] = {"status": "ALL_PASSED"}
    if protocol_status == "draft_not_frozen":
        from freeze_paper_a_from_independent_review import attempt_freeze
        try:
            result_freeze = attempt_freeze()
        except PermissionError as denied:
            result_freeze = {
                "status": "SIGNED_REVIEW_NOT_AUTHORIZED_YET",
                "reason": str(denied), "freeze_commit_created": False,
            }
        info["steps"]["scientific_freeze_transition"] = result_freeze
        protocol_status = json.loads(
            (ROOT / "docs/paper_a_confirmation/protocol.json").read_text(encoding="utf-8")
        ).get("status")
    elif protocol_status == "frozen" and not (WORK / "freeze_approval.json").exists():
        # Recover a committed, independently reviewed freeze if the previous
        # run was interrupted after Git commit/before its safe approval output.
        from freeze_paper_a_from_independent_review import resume_freeze_after_interrupted_push
        try:
            info["steps"]["scientific_freeze_transition"] = resume_freeze_after_interrupted_push()
        except PermissionError as denied:
            info["steps"]["scientific_freeze_transition"] = {
                "status": "FROZEN_UNPUBLISHED_OR_REVIEW_NOT_RECOVERABLE",
                "reason": str(denied),
            }
    # The *real* image->F1 executor is only allowed when the separately signed
    # scientific freeze passes and its exact source hash/policy were approved.
    # Before that condition: do not inspect GT, TAR, or protected outcomes.
    protocol = json.loads((ROOT / "docs/paper_a_confirmation/protocol.json")
                          .read_text(encoding="utf-8"))
    if protocol.get("status") == "frozen":
        from paper_a_freeze_guard import validate_files
        frozen = (WORK / "frozen_H1_H2_recipe.json",
                  WORK / "frozen_cohort_manifest.csv",
                  WORK / "freeze_approval.json")
        if all(p.is_file() for p in frozen):
            gate = validate_files(
                ROOT / "docs/paper_a_confirmation/protocol.json", *frozen)
            if not gate["blockers"]:
                approval = json.loads(frozen[2].read_text(encoding="utf-8"))
                from execute_paper_a_frozen_cohort import BIN_POLICY, digest
                executor = ROOT / "scripts/execute_paper_a_frozen_cohort.py"
                if (approval.get("approved_executor_source_sha256") == digest(executor)
                    and approval.get("executor_contract_independently_reviewed") is True
                    and approval.get("gt_binary_decoding_contract") == BIN_POLICY):
                    outcomes = WORK / "certified_outcomes.csv"
                    provenance = WORK / "certified_outcomes_provenance.json"
                    if not outcomes.exists() and not provenance.exists():
                        run("frozen_image_to_xy_executor",
                            [sys.executable, str(executor)], timeout=172800)
                        info["steps"]["certified_evaluator"] = {
                            "status": "EXECUTED_AFTER_INDEPENDENT_SOURCE_AND_GT_REVIEW"}
                else:
                    info["steps"]["certified_evaluator"] = {
                        "status": "AWAITING_INDEPENDENT_EXECUTOR_AND_GT_DECODING_REVIEW"}
    # The existing central controller already signs nothing, verifies freeze
    # before outcomes, and knows how to run Holm + 100000 permutations.
    # Reuse a prior validated SHA audit; if absent it creates one safely.
    options = ["--skip-baseline-zip"]
    if find_old_audit():
        options.append("--no-reaudit")
    run("finish_paper_a_gated", [
        sys.executable, str(ROOT / "scripts/finish_paper_a.py"), *options],
        timeout=14400)
    old = json.loads((WORK / "LAST_STATUS.json").read_text(encoding="utf-8"))
    info["status"] = old.get("status", "UNSPECIFIED")
    info["freeze_certified"] = old.get("freeze_certified", False)
    info["blockers"] = old.get("blockers", [])
    info["steps"]["existing_completion"] = {
        "status": info["status"],
        "source_status_file": str(WORK / "LAST_STATUS.json")}
    if info["status"] == "PREFREEZE_SCIENTIFIC_GATES_OPEN":
        info["blockers"].append(
            "Reviewer must complete scientific_signoff/REVIEW_220_IMAGES_PENDING.csv "
            "and FINAL_INDEPENDENT_REVIEW.json with genuine evidence before freeze.")
    # Keep a single human-readable record after the gated controller overwrote it.
    freeze_state=info["steps"].get("scientific_freeze_transition")
    if freeze_state and freeze_state.get("status") not in (
            "SIGNED_FREEZE_COMMITTED_AND_GUARD_VALIDATED",):
        note=WORK/"NEXT_ACTIONS.md"
        with note.open("a",encoding="utf-8") as f:
            f.write("\n## Reviewed freeze / single-command continuation\n"
                    "Review sheet: scientific_signoff/REVIEW_220_IMAGES_PENDING.csv\n"
                    "Template: scientific_signoff/FINAL_INDEPENDENT_REVIEW.template.json\n"
                    "Reviewer decision (external): scientific_signoff/FINAL_INDEPENDENT_REVIEW.json\n"
                    "Last freeze transition: "+str(freeze_state.get("status"))+"\n"
                    "No independent scientific PASS was generated by the software.\n")

    # Preserve existing NEXT_ACTIONS.md from the scientific controller.
    (WORK / "ONE_COMMAND_STATUS.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    # Assemble a single review artifact using ONLY whitelisted metadata
    # and documentation; do not bundle raw images, protected GT, cache maps.
    if protocol_status == "draft_not_frozen":
        from export_paper_a_review_bundle import assemble
        info["steps"]["review_bundle"] = assemble()
        (WORK / "ONE_COMMAND_STATUS.json").write_text(
            json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return info


def main() -> int:
    try:
        result = one_shot()
    except Exception as exc:
        WORK.mkdir(parents=True, exist_ok=True)
        report = {"status": "TECHNICAL_ERROR_NOT_CONFIRMATION",
                  "error": str(exc),
                  "traceback": traceback.format_exc()[-2500:],
                  "no_protected_GT_access_authorized": True}
        (WORK / "ONE_COMMAND_ERROR.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
        return 2
    print(json.dumps({
        "status": result["status"],
        "blockers": result["blockers"],
        "NEXT_ACTIONS": str(WORK / "NEXT_ACTIONS.md"),
        "ONE_COMMAND_STATUS": str(WORK / "ONE_COMMAND_STATUS.json"),
        "SCIENTIFIC_REVIEW_SHEET": str(WORK / "scientific_signoff/REVIEW_220_IMAGES_PENDING.csv")
            if result.get("steps",{}).get("signoff_readiness") else None,
        "REVIEW_ZIP": result.get("steps",{}).get("review_bundle",{}).get("path"),
        "FREEZE_REVIEW_TEMPLATE": str(WORK / "scientific_signoff/FINAL_INDEPENDENT_REVIEW.template.json"),
        "FREEZE_TRANSITION": result.get("steps",{}).get("scientific_freeze_transition",{}).get("status"),
        "message": "The remaining scientific signoff is independent; no self-approval was issued.",
    }, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
