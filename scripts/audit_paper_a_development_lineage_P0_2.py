#!/usr/bin/env python3
"""P0.2 — existing development lineage/descriptor metadata audit for H1/H2.

Reads only the already versioned stage24gl UDED **metadata manifests**,
protocol.json and the P0.1 draft schema/source hashes. Never imports
scientific code, decodes images/GT/H5/maps or accesses prediction/F1 outputs.
No new fitting, selection, training or experiment is performed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = "results/paper_a_evidence/stage24gl/campaign/native_dataset_manifest.json"
DESCRIPTOR_MANIFEST = "results/paper_a_evidence/stage24gl/campaign/descriptor_provenance.csv"
PROTOCOL = "docs/paper_a_confirmation/protocol.json"
DEFAULT_DRAFT = Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_H1_H2_recipe_P0_1_DRAFT.json")
DEFAULT_OUT = Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_development_lineage_P0_2.json")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_DESCRIPTORS = (
    "halfdisc_distribution_contrast",
    "pmi_dependency_deficit",
    "fh_region_boundary",
    "structure_tensor_coherence",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_metadata(manifest: dict, rows: list[dict],
                    discovery_ids: set[str]) -> dict:
    """Fail closed on a changed metadata contract; do not use GT hash values."""
    if manifest.get("ground_truth") != "native_never_resized":
        raise ValueError("Historic original-GT geometry contract drift")
    if manifest.get("inference") != "maxside256_score_registered_to_native":
        raise ValueError("Historic inference geometry contract drift")
    records = manifest.get("records")
    if not isinstance(records, list) or len(records) != 15:
        raise ValueError("Expected 15 original Stage24 UDED manifest entries")
    active = [r for r in records if r.get("excluded") is False]
    excluded = [r for r in records if r.get("excluded") is True]
    if len(active) != 14 or len(excluded) != 1:
        raise ValueError("Expected 14 development images and 1 protected exclusion")
    ids = [r["image_id"] for r in active]
    if len(set(ids)) != 14 or set(ids) != discovery_ids:
        raise ValueError("Metadata image identities disagree with preregistration")
    if excluded[0]["image_id"] != "03-35028":
        raise ValueError("Unexpected previously protected image")
    for r in active:
        if r.get("gt_resized") is not False:
            raise ValueError("Source metadata reports changed GT geometry")
        if not HEX64.fullmatch(str(r.get("source_sha256", ""))):
            raise ValueError("Missing historic original image SHA")
        if r.get("bytes_read") is not True:
            raise ValueError("Historic manifest lacks source-read provenance")
        # Never use r['gt_sha256'] in downstream decisions/output.
    expected_fields = ("image_id", "descriptor_id", "source",
                       "sha256", "gt_resized", "dtype")
    if len(rows) != 182 or not all(set(r) == set(expected_fields) for r in rows):
        raise ValueError("Unexpected descriptor provenance schema/row count")
    by_key = {}
    for row in rows:
        key = (row["image_id"], row["descriptor_id"])
        if key in by_key or row["image_id"] not in discovery_ids:
            raise ValueError("Duplicate or historically unapproved descriptor record")
        if (row["source"] != "stage24_cache"
                or row["gt_resized"] != "False"
                or row["dtype"] != "float32"
                or not HEX64.fullmatch(row["sha256"])):
            raise ValueError("Descriptor float provenance contract drift")
        by_key[key] = row
    missing = sorted((img, descriptor) for img in ids
                     for descriptor in EXPECTED_DESCRIPTORS
                     if (img, descriptor) not in by_key)
    if missing:
        raise ValueError("H1/H2 descriptor metadata missing for originals: " + repr(missing))
    counts = Counter(r["descriptor_id"] for r in rows)
    if len(counts) != 13 or any(n != 14 for n in counts.values()):
        raise ValueError("Expected 13 descriptor kinds on 14 originals")
    return {
        "historic_development_source": "Stage24GL_UDED_14_previously_exploratory",
        "development_image_count": len(ids),
        "ids_match_discovery_set": True,
        "excluded_protected_image": excluded[0]["image_id"],
        "historical_descriptor_kinds": len(counts),
        "descriptor_metadata_rows": len(rows),
        "H1_H2_required_descriptor_types": list(EXPECTED_DESCRIPTORS),
        "H1_H2_required_descriptor_metadata_rows": len(ids) * len(EXPECTED_DESCRIPTORS),
        "all_required_descriptor_metadata_present": True,
        "all_metadata_dtypes_float32": True,
        "stored_descriptor_binary_payloads_NOT_revalidated": True,
        "any_GT_payload_loaded": False,
        "historical_GT_checksum_metadata_not_redistributed": True,
        "overlap_with_exploratory_discovery_count": len(ids),
        "known_cross_source_collision": {
            "historic_uded_id": "09-MDBD-1C",
            "multicue_sequence_id": "4113_left_0082",
            "whole_multicue_capture_prefix_held": "4113",
        },
        "source_ids": sorted(ids),
        "warning": (
            "The 14 UDED images were also used to discover H1/H2. This "
            "can at most be a DEVELOPMENT training pool with documented "
            "overlap/exposure policy, NEVER an independent confirmatory cohort."
        ),
    }


def verify_draft(draft: dict, root: Path, protocol: dict) -> dict:
    if draft.get("schema") != "paper_a_h1h2_recipe_P0_1":
        raise ValueError("Unexpected P0.1 recipe schema")
    if draft.get("status") != "DRAFT_VALUES_UNVERIFIED_NOT_FROZEN":
        raise ValueError("P0.1 status was changed; abort")
    if draft.get("protocol_frozen") is not False:
        raise ValueError("Premature recipe freeze")
    if draft.get("no_scientific_artifacts_or_outcomes_read") is not True:
        raise ValueError("P0.1 safe-source contract missing")
    for relative, expected in draft.get("source_sha256", {}).items():
        path = root / relative
        if (not path.is_file() or path.is_symlink()
                or not path.resolve().is_relative_to(root.resolve())
                or sha256(path) != expected):
            raise ValueError("P0.1 referenced source changed since draft: " + relative)
    sources = draft.get("source_sha256", {})
    if len(sources) < 9 or "src/stage24_recertification_ops.py" not in sources:
        raise ValueError("Incomplete original P0.1 source checksums")
    ids = [item.get("id") for item in draft.get("hypotheses", [])]
    if ids != ["H1", "H2"]:
        raise ValueError("P0.1 hypothesis identities changed")
    for r in draft["hypotheses"]:
        target = next((p for p in protocol["hypotheses"]
                       if p["id"] == r["id"]), None)
        if target is None or r.get("group") != target["group"]:
            raise ValueError("P0.1 descriptor groups changed")
        if r["membership"]["midpoint"] is not None or r["membership"]["scale"] is not None:
            raise ValueError("P0.1 draft unexpectedly contains filled membership")
        for role in ("candidate", "control"):
            if r[role]["threshold"] is not None:
                raise ValueError("P0.1 draft unexpectedly has threshold")
        if r["id"] == "H2" and (r["candidate"]["capacity"] is not None
                              or r["candidate"]["mobius"] is not None):
            raise ValueError("P0.1 draft unexpectedly has Choquet coefficients")
    return {
        "draft_source_commit": draft.get("source_commit"),
        "source_checksums_still_match_current_branch": True,
        "draft_has_no_fitted_parameters": True,
    }


def audit(root: Path, draft_path: Path) -> dict:
    root = root.resolve()
    protocol = json.loads((root / PROTOCOL).read_text(encoding="utf-8"))
    if protocol.get("status") != "draft_not_frozen":
        raise ValueError("P0.2 strictly before protocol freeze")
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    check = verify_draft(draft, root, protocol)
    manifest_file, descriptor_file = root / SOURCE_MANIFEST, root / DESCRIPTOR_MANIFEST
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    with descriptor_file.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    metadata = source_metadata(
        manifest, rows, set(protocol["exploratory_source"]["discovery_images"])
    )
    return {
        "status": "P0_2_DEVELOPMENT_METADATA_AUDITED_TRAINING_NOT_CERTIFIED",
        "safe_metadata_sources_sha256": {
            SOURCE_MANIFEST: sha256(manifest_file),
            DESCRIPTOR_MANIFEST: sha256(descriptor_file),
        },
        "draft_recipe_sha256": sha256(draft_path),
        "draft_check": check,
        "development_metadata": metadata,
        "training_fit_approved": False,
        "source_lineage_and_development_role_need_scientific_signoff": True,
        "next_actions": [
            "Determine which existing H1/H2-compatible membership/capacity/threshold exports already exist, without using historical F1 ranking",
            "If no recipe exists, approve a bounded train-only parameter fit on an explicitly designated DEVELOPMENT cohort",
            "Reuse verified source float caches when possible and never regenerate 14x4 maps without technical necessity",
            "Require a content-addressed F1-free fit-output artifact with training image IDs and function/code SHA",
            "Import fixed values into a NEW P0.1 recipe version only after audit; no automatic population of unknown parameters",
            "Keep MultiCue and BIPED confirmatory GT/H5 closed until a separate frozen protocol commit",
        ],
        "GT_H5_maps_F1_contents_opened": False,
        "historical_models_or_results_opened": False,
        "new_training_or_processing_done": False,
        "cohort_frozen": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, default=DEFAULT_DRAFT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    draft = args.draft.expanduser().resolve()
    if not draft.is_file():
        parser.error("Existing P0.1 draft missing; do NOT regenerate if already present")
    if os.name == "nt" and output.drive.lower() == ROOT.drive.lower():
        parser.error("Output must be written to data drive, not C:")
    if output.suffix.lower() != ".json" or not output.parent.is_dir() or output.exists():
        parser.error("Output must be a NEW JSON in an existing directory")
    report = audit(ROOT, draft)
    temporary = output.with_suffix(".json.part")
    if temporary.exists():
        parser.error("Previous partial audit exists; inspect manually")
    with temporary.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    os.replace(temporary, output)
    print(json.dumps({
        "status": report["status"],
        "draft_check": report["draft_check"],
        "development_metadata": report["development_metadata"],
        "training_fit_approved": False,
        "GT_H5_maps_F1_contents_opened": False,
        "report": str(output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
