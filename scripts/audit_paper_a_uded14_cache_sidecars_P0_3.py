#!/usr/bin/env python3
"""P0.3: check only descriptor-cache SIDECAR METADATA for UDED-14 H1/H2.

Read-only source/image manifest CSV and JSON, per-artifact metadata JSON and
file stat() only. NEVER opens .npy, images, GT, H5, scores, predictions,
historical models, F1 or model outcomes. It does not fit/evaluate anything.
Cache presence does NOT certify integrity without independent hash checking.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache/local_dev/stage24/descriptors"
MANIFEST = ROOT / "results/paper_a_evidence/stage24gl/campaign/native_dataset_manifest.json"
PROVENANCE = ROOT / "results/paper_a_evidence/stage24gl/campaign/descriptor_provenance.csv"
DEFAULT_OUTPUT = Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_uded14_cache_sidecars_P0_3.json")
DESCRIPTORS = (
    "halfdisc_distribution_contrast",
    "pmi_dependency_deficit",
    "fh_region_boundary",
    "structure_tensor_coherence",
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def is_hash(x):
    return isinstance(x, str) and HEX64.fullmatch(x) is not None


def validate_sidecar(record: dict, image: dict, expected_sha: str) -> tuple[str, str]:
    """Validate metadata only, not the actual cached scientific array bytes."""
    expected_keys = {"schema_version", "identity", "artifact_sha256", "shape", "dtype"}
    if not isinstance(record, dict) or set(record) != expected_keys:
        return "INVALID_SCHEMA", "Unexpected metadata sidecar keys"
    ident = record["identity"]
    required = {
        "schema_version", "dataset", "split", "image_id", "source_sha256",
        "descriptor_id", "parameters", "code_hash", "preprocessing",
        "inference_shape", "native_shape", "dtype", "gt_used",
    }
    if not isinstance(ident, dict) or set(ident) != required:
        return "IDENTITY_SCHEMA_DRIFT", "Unexpected cache identity schema"
    if (record["schema_version"] != 1 or ident["schema_version"] != 1
            or ident["dataset"] != "UDED"
            or ident["split"] != "selection_overlap_clean"
            or ident["image_id"] != image["image_id"]
            or ident["source_sha256"] != image["source_sha256"]
            or ident["gt_used"] is not False
            or ident["preprocessing"] != "downscale_maxside256_then_registered_descriptor_preprocessing_v1"
            or not isinstance(ident["parameters"], dict)
            or not is_hash(ident["code_hash"])):
        return "IDENTITY_DRIFT", "Cache identity does not match UDED development source"
    if (record["dtype"] != "float32" or ident["dtype"] != "float32"
            or record["shape"] != image["inference_shape"]
            or ident["inference_shape"] != image["inference_shape"]
            or ident["native_shape"] != image["native_gt_shape"]
            or not is_hash(record["artifact_sha256"])):
        return "GEOMETRY_OR_FORMAT_DRIFT", "Unexpected shape, dtype or code hash"
    if record["artifact_sha256"] != expected_sha:
        return "MANIFEST_SHA_DISAGREEMENT", "Metadata SHA disagrees with versioned CSV (no NPY bytes read)"
    return "METADATA_MATCH_ONLY", "File content SHA NOT recalculated"


def audit_index(manifest: dict, rows: list[dict], cache_root: Path) -> dict:
    records = manifest.get("records", [])
    originals = {r["image_id"]: r for r in records if r.get("excluded") is False}
    if len(originals) != 14 or any(
        not is_hash(r.get("source_sha256")) for r in originals.values()
    ):
        raise ValueError("UDED-14 original manifest drift")
    if manifest.get("ground_truth") != "native_never_resized":
        raise ValueError("Historic GT geometry metadata changed")
    prior = {}
    for row in rows:
        key = (row["image_id"], row["descriptor_id"])
        if key in prior:
            raise ValueError("Duplicate historical descriptor provenance row")
        prior[key] = row
    if len(rows) != 182:
        raise ValueError("Unexpected historical descriptor CSV length")

    out = []
    for descriptor in DESCRIPTORS:
        folder = cache_root / descriptor
        meta_paths = sorted(folder.glob("*.json")) if folder.is_dir() else []
        if len(meta_paths) > 500:
            raise ValueError("Too many sidecars; refuse ambiguous wide scan")
        known = {}
        invalid = []
        for sidecar in meta_paths:
            if sidecar.is_symlink() or not sidecar.resolve().is_relative_to(cache_root.resolve()):
                invalid.append({"path": str(sidecar), "status": "UNSAFE_SIDECAR"})
                continue
            if not HEX64.fullmatch(sidecar.stem):
                invalid.append({"path": str(sidecar), "status": "UNEXPECTED_FILENAME"})
                continue
            try:
                obj = json.loads(sidecar.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                invalid.append({"path": str(sidecar), "status": "INVALID_JSON"})
                continue
            ident = obj.get("identity") if isinstance(obj, dict) else None
            if not isinstance(ident, dict) or ident.get("descriptor_id") != descriptor:
                invalid.append({"path": str(sidecar), "status": "DESCRIPTOR_ID_MISMATCH"})
                continue
            image_id = ident.get("image_id")
            if image_id not in originals:
                continue  # Other cache identities are not this UDED-14 audit.
            known.setdefault(image_id, []).append((sidecar, obj))
        for image_id, image in sorted(originals.items()):
            prior_entry = prior.get((image_id, descriptor))
            if prior_entry is None or (prior_entry.get("dtype") != "float32"
                 or prior_entry.get("gt_resized") != "False"
                 or prior_entry.get("source") != "stage24_cache"
                 or not is_hash(prior_entry.get("sha256"))):
                raise ValueError("Historical descriptor manifest drift")
            hits = known.get(image_id, [])
            item = {
                "image_id": image_id,
                "descriptor_id": descriptor,
                "sidecar_count": len(hits),
                "cache_npy_path": None,
                "cache_npy_bytes": None,
                "sidecar_status": "NO_MATCHING_SIDECAR",
                "actual_npy_bytes_hashed": False,
                "metadata_sha_matches_manifest": False,
            }
            if len(hits) > 1:
                item["sidecar_status"] = "AMBIGUOUS_MULTIPLE_CACHE_IDENTITIES"
            elif len(hits) == 1:
                sidecar, meta = hits[0]
                status, _ = validate_sidecar(meta, image, prior_entry["sha256"])
                if isinstance(meta.get("identity"), dict) and meta["identity"].get("descriptor_id") != descriptor:
                    status = "WRONG_DESCRIPTOR_ID"
                npy = sidecar.with_suffix(".npy")
                if npy.is_symlink() or not npy.resolve().is_relative_to(cache_root.resolve()):
                    status = "UNSAFE_OR_REDIRECTED_NPY"
                elif not npy.is_file():
                    status = "NPY_MISSING"
                elif npy.stat().st_size <= 128:
                    status = "NPY_TOO_SMALL"
                item.update({
                    "sidecar_status": status,
                    "cache_npy_path": str(npy),
                    "cache_npy_bytes": npy.stat().st_size if npy.is_file() and not npy.is_symlink() else None,
                    "metadata_sha_matches_manifest": status == "METADATA_MATCH_ONLY",
                })
            out.append(item)
        if invalid:
            out.append({"descriptor_id": descriptor,
                        "sidecar_status": "EXTRA_SIDE_CAR_REVIEW",
                        "invalid_entries_count": len(invalid),
                        "invalid_examples": invalid[:4]})
    per = Counter(x["sidecar_status"] for x in out if "image_id" in x)
    total = sum(per.values())
    assert total == 56
    return {
        "status": "P0_3_ALL_CACHE_METADATA_MATCH_ONLY_NOT_CONTENT_VERIFIED"
        if per.get("METADATA_MATCH_ONLY") == 56
        else "P0_3_CACHE_METADATA_REVIEW_REQUIRED",
        "required_UDed14_descriptor_pairs": 56,
        "matching_sidecar_and_npy_metadata": per.get("METADATA_MATCH_ONLY", 0),
        "status_counts": dict(sorted(per.items())),
        "records": out,
        "research_cache_array_payload_bytes_read": 0,
        "cache_npy_sha256_recomputed": False,
        "ground_truth_H5_original_image_F1_read": False,
        "development_training_certified": False,
        "cohort_frozen": False,
        "next_gate": (
            "Scientifically approve development role, then if needed verify "
            "actual cache bytes with explicit read-only hashes against historical "
            "provenance. Never treat sidecar presence as data integrity."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if os.name == "nt" and output.drive.lower() == ROOT.drive.lower():
        parser.error("Output must be on data drive, not project C: drive")
    if output.suffix.lower() != ".json" or not output.parent.is_dir() or output.exists():
        parser.error("Require a NEW JSON in an existing output directory")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    with PROVENANCE.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    report = audit_index(manifest, rows, CACHE)
    tmp = output.with_suffix(".json.part")
    if tmp.exists():
        parser.error("Partial report exists; inspect before retry")
    with tmp.open("x", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
    os.replace(tmp, output)
    print(json.dumps({
        "status": report["status"],
        "required_pairs": report["required_UDed14_descriptor_pairs"],
        "matching_sidecar_and_npy_metadata": report["matching_sidecar_and_npy_metadata"],
        "status_counts": report["status_counts"],
        "research_cache_array_payload_bytes_read": 0,
        "ground_truth_H5_original_image_F1_read": False,
        "output": str(output)
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
