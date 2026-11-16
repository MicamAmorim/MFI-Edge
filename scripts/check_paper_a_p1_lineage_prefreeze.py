#!/usr/bin/env python3
"""Paper A: bounded metadata-only P1 training lineage versus draft cohort.

Read only three explicitly named small source/recipe/cohort metadata files.
NEVER open source images, GT, caches, H5, F1, TAR, exploratory metrics,
model outputs or confirmation results. No scientific signoff or auto-freeze.
"""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(r"F:\MFI-Edge-Data\MultiCue")
WORK = DATA / "paper_a_completion"
P1 = ROOT / "docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json"
UD14 = ROOT / "results/paper_a_evidence/stage24gl/campaign/native_dataset_manifest.json"
DRAFT = WORK / "COHORT_PROPOSAL_220_NOT_CERTIFIED.csv"
OUTPUT = WORK / "scientific_signoff/P1_LINEAGE_METADATA_CROSSCHECK_NOT_APPROVED.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SCHEMA = "paper_a_p1_metadata_crosscheck_v1"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def safe_read(path: Path, *, size_limit: int = 8_000_000) -> bytes:
    if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size < size_limit:
        raise ValueError("Missing/unsafe required metadata file: " + str(path))
    return path.read_bytes()


def validate_and_compare(manifest: dict, recipe: dict,
                         cohort: list[dict]) -> dict:
    records = manifest.get("records")
    if (not isinstance(records, list) or
            manifest.get("ground_truth") != "native_never_resized"):
        raise ValueError("Unrecognized UDED source manifest")
    training = [r for r in records if isinstance(r, dict) and r.get("excluded") is False]
    pairs = []
    for item in training:
        iid, sha = item.get("image_id"), item.get("source_sha256")
        if not isinstance(iid, str) or not iid or not isinstance(sha, str) or not HEX64.fullmatch(sha):
            raise ValueError("Invalid UDED training identity/hash")
        pairs.append((iid, sha))
    if len(pairs) != 14 or len(set(pairs)) != 14 or len(set(k for k,v in pairs)) != 14:
        raise ValueError("Expected exactly 14 distinct UDED development originals")
    # Match scripts/fit_paper_a_development_uded14.py::training_ids_hash
    # This hashes sorted [image ID, original source image SHA256] pairs.
    training_digest = digest(json.dumps(sorted(pairs), separators=(",",":"),
                                        ensure_ascii=False).encode("utf-8"))
    if recipe.get("schema") != "paper_a_h1h2_recipe_P1_fitted_development":
        raise ValueError("Not the expected P1 development fitted recipe")
    hyps = {h.get("id"):h for h in recipe.get("hypotheses",[]) if isinstance(h,dict)}
    if set(hyps) != {"H1","H2"} or len(recipe.get("hypotheses",[])) != 2:
        raise ValueError("Incorrect P1 hypothesis identities")
    claims = []
    for hid in ("H1","H2"):
        h=hyps[hid]
        proofs=[
            ("membership",h.get("membership",{}).get("fit_provenance")),
            ("candidate_threshold",h.get("candidate",{}).get("threshold_fit_provenance")),
            ("control_threshold",h.get("control",{}).get("threshold_fit_provenance"))
        ]
        if hid=="H2":
            proofs.append(("capacity",h.get("candidate",{}).get("capacity_fit_provenance")))
        for label,proof in proofs:
            if not isinstance(proof,dict):
                raise ValueError("Missing P1 provenance dict for "+hid+":"+label)
            claims.append({
                "hypothesis":hid,"fitted_part":label,
                "training_ids_sha256":proof.get("training_ids_sha256"),
                "fitting_commit":proof.get("fitting_commit"),
                "parameter_export_sha256":proof.get("parameter_export_sha256"),
                "training_hash_matches_recomputed":proof.get("training_ids_sha256")==training_digest,
                "no_confirmatory_overlap_attested":proof.get("no_confirmatory_overlap_attested")
            })
    if len(claims)!=7:
        raise ValueError("Unexpected P1 claim count")
    fitting_commit=recipe.get("source_commit")
    source_consistent=(isinstance(fitting_commit,str) and len(fitting_commit)==40
                       and all(x["fitting_commit"]==fitting_commit for x in claims)
                       and len({x["parameter_export_sha256"] for x in claims})==1
                       and all(isinstance(x["parameter_export_sha256"],str)
                               and HEX64.fullmatch(x["parameter_export_sha256"])
                               for x in claims))
    if not isinstance(cohort,list) or len(cohort)!=220:
        raise ValueError("Expected 220 draft rows")
    required={"dataset","image_id","image_sha256","scene_group",
              "independence_review","prior_exposure_review"}
    seen_ids=set(); seen_scenes=set(); counted=Counter(); exact_hash=[]; exact_id=[]
    training_hashes={sha for _,sha in pairs}
    training_ids={iid for iid,_ in pairs}
    for row in cohort:
        if not required.issubset(row):
            raise ValueError("Draft cohort missing source fields")
        domain,iid,sha,scene = (row[x] for x in ("dataset","image_id","image_sha256","scene_group"))
        if domain not in ("BIPED","MultiCue") or not iid or not scene or not HEX64.fullmatch(sha.lower()):
            raise ValueError("Invalid draft cohort entry")
        if (row["independence_review"]!="pending" or
                row["prior_exposure_review"]!="pending"):
            raise ValueError("Draft cohort contains unexpected approval")
        if (domain,iid) in seen_ids or (domain,scene) in seen_scenes:
            raise ValueError("Duplicate ID/scene in draft cohort")
        seen_ids.add((domain,iid)); seen_scenes.add((domain,scene))
        counted[domain]+=1
        if sha.lower() in training_hashes:
            exact_hash.append({"dataset":domain,"image_id":iid,"sha256":sha.lower()})
        if iid in training_ids:
            exact_id.append({"dataset":domain,"image_id":iid})
        if domain=="MultiCue" and scene=="4113":
            raise ValueError("Excluded MultiCue capture 4113 is in draft cohort")
    if counted!={"BIPED":125,"MultiCue":95}:
        raise ValueError("Unexpected provisional domain count")
    return {
        "training_images":len(pairs),
        "training_ids_hash_recomputed":training_digest,
        "P1_seven_proofs":claims,
        "all_seven_training_digests_match":all(c["training_hash_matches_recomputed"] for c in claims),
        "all_seven_provenance_fields_internally_consistent":bool(source_consistent),
        "draft_cohort_n":len(cohort),
        "draft_cohort_domain_counts":dict(counted),
        "cross_domain_exact_source_image_sha256_matches":exact_hash,
        "cross_domain_exact_image_id_matches":exact_id,
        "all_seven_externally_attested":all(c["no_confirmatory_overlap_attested"] is True for c in claims),
        "scope_limitations": [
            "Exact original-source SHA comparison only; no dHash, perceptual near-duplicate, sequence or scene-independence certification.",
            "Cannot prove historical absence of outcome exposure from file paths or source manifests.",
            "Does not compare annotations/GT across datasets or inspect image pixels.",
            "Metadata equality is evidence for reviewer assessment, not an automatic scientific signoff.",
        ]
    }


def generate(p1: Path = P1, uded: Path = UD14,
             draft: Path = DRAFT, output: Path = OUTPUT) -> dict:
    original = {"recipe":safe_read(p1),"uded_manifest":safe_read(uded),"cohort":safe_read(draft)}
    recipe=json.loads(original["recipe"].decode("utf-8-sig"))
    manifest=json.loads(original["uded_manifest"].decode("utf-8-sig"))
    cohort=list(csv.DictReader(io.StringIO(original["cohort"].decode("utf-8-sig"))))
    check=validate_and_compare(manifest,recipe,cohort)
    status=("P1_TRAINING_DIGEST_MATCH_NO_EXACT_IMAGE_SHA_COLLISION_NOT_APPROVED"
            if check["all_seven_training_digests_match"] and
               check["all_seven_provenance_fields_internally_consistent"] and
               not check["cross_domain_exact_source_image_sha256_matches"] and
               not check["cross_domain_exact_image_id_matches"]
            else "P1_TRAINING_PROVENANCE_METADATA_REVIEW_REQUIRED")
    report={
        "schema":SCHEMA,"status":status,
        "input_sha256":{k:digest(v) for k,v in original.items()},
        **check,
        "protected_confirmatory_GT_H5_F1_opened":False,
        "training_or_descriptor_maps_recomputed":False,
        "scientific_approval_issued":False,
        "frozen":False,
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        existing=json.loads(safe_read(output))
        if existing != report:
            raise RuntimeError("Existing evidence differs; refuse overwrite")
    else:
        tmp=output.with_suffix(".json.part")
        if tmp.exists():
            raise RuntimeError("Partial output exists; do not overwrite")
        with tmp.open("x",encoding="utf-8") as f:
            json.dump(report,f,ensure_ascii=False,indent=2)
        tmp.replace(output)
    return {"status":status,"report":str(output),
            "report_sha256":digest(output.read_bytes()),
            "training_sha_matches":check["all_seven_training_digests_match"],
            "exact_source_image_matches":len(check["cross_domain_exact_source_image_sha256_matches"]),
            "scientific_approval_issued":False}


if __name__=="__main__":
    print(json.dumps(generate(),ensure_ascii=False,indent=2))
