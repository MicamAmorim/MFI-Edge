#!/usr/bin/env python3
"""Paper A fail-closed frozen-confirmation authorization gate.

The gate never opens GT/H5/predictions or result/F1 rows. It checks the
versioned protocol, an explicitly reviewed external sign-off, a fixed
cohort CSV and approved H1/H2 recipe before downstream outcome processing.
This module does NOT issue its own scientific approval or freeze a protocol.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/paper_a_confirmation/protocol.json"
SHA = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
COLUMNS = ("dataset", "image_id", "relative_path", "image_sha256",
           "independence_review", "prior_exposure_review", "scene_group", "notes")
REQUIRED_APPROVALS = (
    "training_lineage",
    "capacity_and_thresholds",
    "ground_truth_semantics",
    "independent_scenes_and_exposure",
    "sample_size_and_inference",
    "independent_protocol_review",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ancestor(repo: Path, pinned: str) -> bool:
    if not GIT_SHA.fullmatch(pinned):
        return False
    p = subprocess.run(
        ["git", "merge-base", "--is-ancestor", pinned, "HEAD"],
        cwd=repo, capture_output=True, check=False, timeout=30)
    return p.returncode == 0


def check_freeze(protocol: dict, recipe: dict, approval: dict,
                 cohort_rows: list[dict], actual_hashes: dict,
                 ancestor_check) -> list[str]:
    """Pure contract inspection. Does not read outcome files."""
    problems = []
    if protocol.get("status") != "frozen":
        problems.append("Protocol still draft_not_frozen")
    if protocol.get("confirmatory_outcomes_opened") is not False:
        problems.append("Protocol does not attest first protected outcome access")
    if protocol.get("cohort", {}).get("no_GT_until_lock") is not True:
        problems.append("Protected GT lock is missing")
    hypotheses = protocol.get("hypotheses", [])
    if [(x.get("id"), x.get("candidate"), x.get("control"))
            for x in hypotheses] != [
                ("H1", "maximum", "equal_mean"),
                ("H2", "choquet_generalized_150", "equal_mean")]:
        problems.append("Scientific hypothesis/operator identities changed")
    if protocol.get("inference", {}).get("multiplicity", "").lower().find("holm") < 0:
        problems.append("Holm multiplicity not specified")
    if protocol.get("inference", {}).get("permutations") != 100000:
        problems.append("Expected 100000 preregistered permutations")
    inference = protocol.get("inference", {})
    if inference.get("alpha_familywise") != 0.05:
        problems.append("Confirmatory implementation requires familywise alpha=0.05")
    if inference.get("directional_alternative") != {
            "H1": "rho<0", "H2": "rho>0"}:
        problems.append("Preregistered directional alternatives disagree with H1/H2 implementation")
    if inference.get("permutation_seed") != 20261115:
        problems.append("Confirmatory RNG seed differs from implemented frozen protocol")
    test_contract = str(inference.get("test", "")).lower()
    if not all(s in test_contract for s in ("spearman", "domain", "permutation")):
        problems.append("Blocked within-domain Spearman contract missing")
    if approval.get("schema_version") != 1:
        problems.append("Missing frozen-authorization schema_version=1")
    if approval.get("approved_for_first_confirmatory_outcome_access") is not True:
        problems.append("No explicit first-confirmatory-outcome permission")
    if not isinstance(approval.get("reviewed_by"), str) or not approval["reviewed_by"].strip():
        problems.append("Missing accountable reviewer")
    if not isinstance(approval.get("approved_utc"), str) or not approval["approved_utc"].endswith("Z"):
        problems.append("Missing UTC approval time")
    pinned = approval.get("freeze_commit", "")
    if not isinstance(pinned, str) or not GIT_SHA.fullmatch(pinned) or not ancestor_check(pinned):
        problems.append("Frozen commit absent or not verified Git ancestor")
    claimed_protocol = protocol.get("freeze_commit")
    if claimed_protocol not in (None, pinned):
        problems.append("Protocol and reviewed freeze commit disagree")
    for name in ("protocol_sha256", "cohort_sha256", "recipe_sha256"):
        if not SHA.fullmatch(str(approval.get(name, ""))) or approval.get(name) != actual_hashes.get(name):
            problems.append("Frozen input SHA mismatch: " + name)
    gates = approval.get("scientific_approvals")
    if not isinstance(gates, dict):
        problems.append("Missing independent scientific sign-off table")
    else:
        for item in REQUIRED_APPROVALS:
            if gates.get(item) is not True:
                problems.append("Scientific sign-off missing: " + item)
    if not isinstance(approval.get("review_notes"), str) or len(approval["review_notes"].strip()) < 30:
        problems.append("Review notes must document scientific basis")
    if recipe.get("schema") != "paper_a_h1h2_recipe_P1_fitted_development":
        problems.append("Frozen input requires a truthful fitted-development P1 recipe")
    if (recipe.get("development_GT_and_cached_maps_read") is not True or
            recipe.get("no_scientific_artifacts_or_outcomes_read") is not False):
        problems.append("Fitted recipe must explicitly disclose development GT/map access")
    if [r.get("id") for r in recipe.get("hypotheses", [])] != ["H1", "H2"]:
        problems.append("Unrecognized recipe hypotheses")
    for item in recipe.get("hypotheses", []):
        group = item.get("group", [])
        mem = item.get("membership", {})
        if not (isinstance(mem.get("midpoint"), list) and
                isinstance(mem.get("scale"), list) and
                len(mem["midpoint"]) == len(mem["scale"]) == len(group) and
                all(isinstance(x, (int, float)) and x > 0 for x in mem["scale"])):
            problems.append("Unfitted membership for " + str(item.get("id")))
        for role in ("candidate", "control"):
            if not isinstance(item.get(role, {}).get("threshold"), (int, float)):
                problems.append("Missing pre-fitted " + role + " threshold: " + str(item.get("id")))
        if item.get("id") == "H2":
            if not (isinstance(item.get("candidate", {}).get("capacity"), list)
                    and len(item["candidate"]["capacity"]) == 8
                    and isinstance(item.get("candidate", {}).get("mobius"), list)
                    and len(item["candidate"]["mobius"]) == 6):
                problems.append("H2 trained capacity/Mobius absent")
    if len(cohort_rows) == 0:
        problems.append("No frozen independent image/capture manifest rows")
    expected_domains = protocol.get("cohort", {}).get("dataset_names")
    expected_count = protocol.get("cohort", {}).get("target_n_independent_images")
    if not isinstance(expected_domains, list) or len(expected_domains) != 2:
        problems.append("Frozen dataset_names must list exactly two domains")
        expected_domains = []
    if type(expected_count) is not int or expected_count < 1 or len(cohort_rows) != expected_count:
        problems.append("Frozen cohort size disagrees with protocol")
    counts = Counter()
    ids, hashes, scene_groups = set(), set(), set()
    for row in cohort_rows:
        if set(row) != set(COLUMNS):
            problems.append("Cohort CSV unexpected columns")
            break
        ds, iid, group, img_sha = (
            row["dataset"], row["image_id"], row["scene_group"],
            row["image_sha256"].lower())
        counts[ds] += 1
        key = (ds, iid)
        if key in ids:
            problems.append("Duplicate original image identity")
        ids.add(key)
        if not SHA.fullmatch(img_sha) or img_sha in hashes:
            problems.append("Invalid or duplicate original source SHA256")
        hashes.add(img_sha)
        if (not group or (ds, group) in scene_groups):
            problems.append("Duplicate or absent independent scene/capture ID")
        scene_groups.add((ds, group))
        if row["independence_review"].lower() != "pass" or row["prior_exposure_review"].lower() != "pass":
            problems.append("Unreviewed exposure or non-independent capture")
        if iid in protocol.get("exploratory_source", {}).get("discovery_images", []):
            problems.append("Exploratory UDED image present in confirmatory cohort")
        if ds not in expected_domains or not row["relative_path"]:
            problems.append("Unknown domain or missing original source path")
    if set(counts) != set(expected_domains):
        problems.append("Domain counts disagree with frozen domain list")
    if counts and min(counts.values()) < protocol.get("cohort", {}).get("min_n_per_domain", 60):
        problems.append("Insufficient samples within one domain")
    return sorted(set(problems))


def source_sha256_at_pinned_commit(
        repo: Path, pinned: str,
        expected_hashes: dict[str, str] | None = None) -> dict[str, str]:
    """Verify historical P1 bytes under the exact LF or Windows CRLF encoding.

    Does not rewrite any source, provenance or science decision. A historical
    working-tree checksum is admissible only if it matches the committed blob
    byte-for-byte or the deterministic LF->CRLF checkout transformation.
    """
    from prepare_paper_a_h1h2_recipe_P0_1 import CODE_FILES, PROTOCOL
    if not ancestor(repo, pinned):
        raise ValueError("P1 source revision is not a verified ancestor")
    observed = {}
    for relative in (PROTOCOL, *CODE_FILES):
        proc = subprocess.run(
            ["git", "show", f"{pinned}:{relative}"], cwd=repo,
            capture_output=True, check=False, timeout=40)
        if proc.returncode or len(proc.stdout) > 4_000_000:
            raise ValueError("Historical P1 code file unavailable: " + relative)
        blob=proc.stdout
        canonical=hashlib.sha256(blob).hexdigest()
        if expected_hashes is None:
            observed[relative]=canonical
        else:
            expected=expected_hashes.get(relative)
            # Exact Git checkout conversion; do not accept arbitrary whitespace,
            # reordered lines, code edits or normalized scientific parameters.
            windows=blob.replace(b"\r\n",b"\n").replace(b"\n",b"\r\n")
            candidates={canonical,hashlib.sha256(windows).hexdigest()}
            if (not isinstance(expected,str) or not SHA.fullmatch(expected)
                    or expected not in candidates):
                raise ValueError("Historical fitted-source SHA not equivalent to Git blob: "+relative)
            observed[relative]=expected
    return observed


def validate_fitted_recipe(recipe: dict, protocol: dict,
                          repository: Path) -> list[str]:
    """Apply full P0.1 fitted-parameter checks: monotone capacity, source
    SHA, per-parameter lineage, no-confirmatory-overlap attestation, etc.

    The original P0.1 source validation is reused directly, but without
    requiring protocol.status==draft_not_frozen: frozen protocol is the
    expected status for *outcome* authorization.
    """
    from prepare_paper_a_h1h2_recipe_P0_1 import (
        validate as recipe_validate)
    blockers=[]
    pinned=recipe.get("source_commit")
    if not isinstance(pinned,str) or not ancestor(repository,pinned):
        return ["Recipe source commit is not a verified Git ancestor"]
    if (recipe.get("schema")!="paper_a_h1h2_recipe_P1_fitted_development"
            or recipe.get("development_GT_and_cached_maps_read") is not True
            or recipe.get("no_scientific_artifacts_or_outcomes_read") is not False):
        return ["Fitted P1 recipe must truthfully record development-GT access"]
    # P0.1 originally described a metadata-only draft. A P1 recipe has
    # ACTUALLY read permitted development GT; create a transient compatibility
    # shape to reuse its rigorous monotonicity/provenance checks.
    shadow=dict(recipe)
    shadow.pop("development_GT_and_cached_maps_read",None)
    shadow["schema"]="paper_a_h1h2_recipe_P0_1"
    shadow["status"]="DRAFT_VALUES_UNVERIFIED_NOT_FROZEN"
    shadow["no_scientific_artifacts_or_outcomes_read"]=True
    try:
        result=recipe_validate(shadow,protocol,source_sha256_at_pinned_commit(repository,pinned,
                recipe.get("source_sha256")),pinned)
    except (ValueError,KeyError,TypeError) as error:
        return ["P1 fitted parameters/provenance invalid: "+str(error)]
    if result.get("pending_count")!=0:
        blockers.append("P0.1 H1/H2 fitted values/proofs incomplete: "
                        +str(result.get("pending_count")))
    # All supervised-fitting commits must also precede the freeze.
    for h in recipe.get("hypotheses",[]):
        proofs=[h.get("membership",{}).get("fit_provenance",{}),
                h.get("candidate",{}).get("threshold_fit_provenance",{}),
                h.get("control",{}).get("threshold_fit_provenance",{})]
        if h.get("id")=="H2":
            proofs.append(h.get("candidate",{}).get("capacity_fit_provenance",{}))
        for proof in proofs:
            if not isinstance(proof,dict) or not ancestor(
                    repository,str(proof.get("fitting_commit",""))):
                blockers.append("Fitting commit not verified in Git ancestry")
    return sorted(set(blockers))


def verify_versioned_freeze_inputs(repo: Path, protocol: Path,
                                   recipe: Path, cohort: Path,
                                   approval: dict) -> list[str]:
    """Cross-check local signed frozen inputs against Git committed SHA manifest.

    This reads no images, GT, F1 or analysis outcomes and never generates
    signoffs. Full reviewer notes are private, public files have no notes/PII.
    """
    folder=repo/"docs/paper_a_confirmation"
    manifest=folder/"FROZEN_FREEZE_INPUTS_MANIFEST.json"
    recipe_public=folder/"FROZEN_H1_H2_RECIPE_P1.json"
    cohort_public=folder/"FROZEN_COHORT_IDS_PUBLIC.csv"
    expected=[manifest,recipe_public,cohort_public]
    if any(not p.is_file() or p.is_symlink() or p.stat().st_size>4_000_000
           for p in expected):
        return ["Missing/unsafe Git-versioned frozen evidence bundle"]
    try:
        data=json.loads(manifest.read_text(encoding="utf-8"))
    except (ValueError,UnicodeError,OSError):
        return ["Malformed versioned freeze manifest"]
    checks={
        "status":"REVIEWED_PRE_GT_CONFIRMATORY_LOCK",
        "schema_version":1,
        "protocol_sha256":sha256(protocol),
        "local_frozen_recipe_sha256":sha256(recipe),
        "public_frozen_recipe_sha256":sha256(recipe_public),
        "local_frozen_cohort_sha256":sha256(cohort),
        "public_frozen_cohort_sha256":sha256(cohort_public),
        "external_signed_decision_sha256":approval.get("review_decision_sha256"),
        "external_review_sheet_sha256":approval.get("review_sheet_sha256"),
        "executor_source_sha256":approval.get("approved_executor_source_sha256"),
    }
    problems=[]
    for key,value in checks.items():
        if not value or data.get(key)!=value:
            problems.append("Versioned freeze evidence mismatch: "+key)
    if data.get("no_GT_opened_by_freeze_step") is not True:
        problems.append("Freeze provenance does not attest outcome lock")
    return problems


def validate_files(protocol_path: Path, recipe_path: Path,
                   cohort_path: Path, approval_path: Path,
                   repo: Path = ROOT) -> dict:
    """Read only signed metadata/recipe, not experimental outcomes or GT."""
    files = (protocol_path, recipe_path, cohort_path, approval_path)
    for path in files:
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing/unsafe required frozen-input file: " + str(path))
        if path.stat().st_size > 4_000_000:
            raise ValueError("Unexpectedly large manifest/approval file")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    with cohort_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError("Unexpected frozen cohort CSV columns")
        rows = list(reader)
    digest = {
        "protocol_sha256": sha256(protocol_path),
        "recipe_sha256": sha256(recipe_path),
        "cohort_sha256": sha256(cohort_path),
    }
    blockers = check_freeze(protocol, recipe, approval, rows, digest,
                            lambda commit: ancestor(repo, commit))
    blockers.extend(validate_fitted_recipe(recipe, protocol, repo))
    if protocol.get("status")=="frozen":
        blockers.extend(verify_versioned_freeze_inputs(
            repo,protocol_path,recipe_path,cohort_path,approval))
    blockers = sorted(set(blockers))
    return {
        "status": "FROZEN_OUTCOME_ACCESS_APPROVED" if not blockers else "FROZEN_ACCESS_BLOCKED",
        "blockers": blockers,
        "frozen_cohort_count": len(rows),
        "frozen_input_sha256": digest,
        "freeze_commit": approval.get("freeze_commit"),
        "GT_H5_F1_opened": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = validate_files(args.protocol, args.recipe, args.cohort, args.approval)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not result["blockers"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
