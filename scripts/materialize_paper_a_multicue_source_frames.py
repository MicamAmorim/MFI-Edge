#!/usr/bin/env python3
"""Materialize only 100 original left-view frames for pre-data overlap audit.

The verified MultiCue TAR is scanned once in streaming mode. Only exact
whitelisted multicue/images/*.png members are read via extractfile().
No ground-truth member is extracted or decoded. No HDF5, F1 or inference.
Results are local to F: and remain unapproved for confirmatory testing.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(r"F:\MFI-Edge-Data\MultiCue")
ARCHIVE = "multicue-dataset.tar.bz2"
REVISION = "f47b14959e9764c8aa854cb7958d54462c46f8ef"
EXPECTED_SHA = "8e5fdb2ff7343e4a55f110e9ffe189b2c81689cd326324e34c6c73562191819e"
EXPECTED_SIZE = 3575680805
IMAGE_RE = re.compile(r"^multicue/images/(\d+)_left_(\d+)\.png$")
MAX_FRAME_BYTES = 25 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024


def canonical(name: str) -> str:
    value = name.replace("\\", "/")
    if value.startswith("./"):
        value = value[2:]
    path = PurePosixPath(value)
    if not value or value.startswith("/") or ".." in path.parts or re.match(r"^[A-Za-z]:", value):
        raise ValueError(f"Unsafe TAR member: {name!r}")
    return path.as_posix()


def load_requested(root: Path):
    summary = json.loads((root / "multicue_h5_anchored_sequence_summary.json").read_text(encoding="utf-8"))
    if (summary.get("status") != "H5_ANCHORED_LAYOUT_OK_NOT_CERTIFIED"
            or summary.get("source_revision") != REVISION
            or summary.get("source_archive_sha256") != EXPECTED_SHA
            or summary.get("h5_anchored_sequence_units") != 100
            or summary.get("unique_capture_prefixes") != 96
            or summary.get("problem_units_count") != 0
            or summary.get("images_or_gt_decoded") is not False):
        raise ValueError("Sequence-name inventory not eligible for image-only materialization")
    expected_csv = root / "multicue_h5_anchored_sequence_candidates.csv"
    if Path(summary.get("candidate_csv", "")).resolve() != expected_csv:
        raise ValueError("Sequence candidate CSV does not match sequence report")
    with expected_csv.open(encoding="utf-8-sig", newline="") as stream:
        records = list(csv.DictReader(stream))
    if len(records) != 100:
        raise ValueError("Expected 100 source frames")
    requested = {}
    for row in records:
        name = canonical(row["last_left_image"])
        match = IMAGE_RE.fullmatch(name)
        if not match or int(match.group(2)) != int(row["annotated_left_frame"]):
            raise ValueError(f"Unexpected source frame name or sequence anchor: {name}")
        if row["capture_prefix"] != match.group(1):
            raise ValueError("Capture prefix mismatched annotated frame")
        if row["layout_issues"] or row["left_frame_count"] != "10" or row["right_frame_count"] != "10":
            raise ValueError(f"Invalid sequence layout: {row['sequence_id']}")
        if name in requested:
            raise ValueError(f"Duplicate selected image path: {name}")
        requested[name] = {"sequence_id": row["sequence_id"], "capture_prefix": row["capture_prefix"]}
    return requested


def validate_archive(root: Path):
    archive = root / ARCHIVE
    provenance = json.loads((root / "archive_provenance.json").read_text(encoding="utf-8"))
    if (provenance.get("status") != "ARCHIVE_DOWNLOADED_NOT_EXTRACTED"
            or provenance.get("repository_commit_sha") != REVISION
            or provenance.get("archive_sha256") != EXPECTED_SHA
            or provenance.get("official_lfs_sha256_verified") is not True
            or Path(provenance.get("archive", "")).resolve() != archive
            or provenance.get("archive_bytes") != EXPECTED_SIZE
            or not archive.is_file() or archive.stat().st_size != EXPECTED_SIZE):
        raise ValueError("Unverified or changed archive; stop before extraction")
    summary = json.loads((root / "archive_member_summary.json").read_text(encoding="utf-8"))
    if (summary.get("status") != "TAR_MEMBER_METADATA_ONLY_NO_EXTRACTION"
            or summary.get("source_revision") != REVISION
            or summary.get("archive_sha256_verified_by_download") != EXPECTED_SHA
            or summary.get("members") != 3207
            or summary.get("unsafe_member_examples")):
        raise ValueError("TAR member listing not verified/has unsafe entries")
    return archive


def inventory_sizes(root: Path, requested: set):
    path = root / "archive_members_inventory.csv"
    stats = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = canonical(row["path"])
            if name in requested:
                if row["kind"] != "file" or row["unsafe_path_flag"]:
                    raise ValueError(f"Unsafe source-member entry: {name}")
                size = int(row["size_bytes"])
                if not 0 < size <= MAX_FRAME_BYTES or name in stats:
                    raise ValueError(f"Invalid source frame size or duplicate member: {name}")
                stats[name] = size
    if stats.keys() != requested:
        raise ValueError(f"Missing {len(requested) - len(stats)} requested names in TAR index")
    if sum(stats.values()) > MAX_TOTAL_BYTES:
        raise ValueError("Requested source frames exceed 1 GiB safety cap")
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--directory", type=Path, default=ROOT)
    args = ap.parse_args()
    root = args.directory.expanduser().resolve()
    if not root.is_dir() or (root.drive and root.drive.lower() == Path.home().drive.lower()):
        ap.error("MultiCue must be on a non-system drive, e.g. F:")
    requested = load_requested(root)
    archive = validate_archive(root)
    sizes = inventory_sizes(root, set(requested))
    out = root / "source_frames_only"
    out.mkdir(parents=True, exist_ok=True)
    result_csv = root / "multicue_source_frames_only_manifest.csv"
    result_json = root / "multicue_source_frames_only_summary.json"
    if result_csv.exists() or result_json.exists():
        ap.error("Source-frame manifest already exists; refuse silent overwrite")
    if list(out.iterdir()):
        ap.error("Source-frame directory is not empty; refuse silent overwrite")
    found = {}
    total = 0
    with tarfile.open(archive, mode="r|bz2") as tar:
        for n_header, member in enumerate(tar, 1):
            if n_header % 500 == 0:
                print(
                    f"Inspected {n_header} TAR headers; {len(found)}/100 original frames materialized; no GT extracted",
                    file=sys.stderr, flush=True,
                )
            name = canonical(member.name)
            if name not in requested:
                continue
            if not member.isfile() or member.size != sizes[name] or name in found:
                raise ValueError(f"Unexpected TAR source member: {name}")
            filename = PurePosixPath(name).name
            target = out / filename
            if target.exists():
                raise ValueError(f"Refuse overwrite: {target}")
            part = target.with_suffix(".png.part")
            digest = hashlib.sha256()
            size = 0
            try:
                # Read ONLY the exact whitelisted ORIGINAL image member.
                reader = tar.extractfile(member)
                if reader is None:
                    raise ValueError(f"Cannot read whitelisted original frame: {name}")
                with reader, part.open("xb") as dest:
                    while True:
                        block = reader.read(1024 * 1024)
                        if not block:
                            break
                        size += len(block)
                        total += len(block)
                        if size > MAX_FRAME_BYTES or total > MAX_TOTAL_BYTES:
                            raise ValueError("Original-image extraction safety limit exceeded")
                        digest.update(block)
                        dest.write(block)
                if size != member.size:
                    raise ValueError(f"Incomplete original-image materialization: {name}")
                os.replace(part, target)
            finally:
                if part.exists():
                    part.unlink()
            found[name] = {
                **requested[name],
                "archive_member_path": name,
                "local_original_frame_path": str(target),
                "size_bytes": size,
                "sha256": digest.hexdigest(),
                "overlap_review_status": "PENDING",
            }
    if set(found) != set(requested) or len(found) != 100:
        raise ValueError(f"Only {len(found)}/100 originals found; do NOT use partial extraction")
    columns = ["sequence_id", "capture_prefix", "archive_member_path",
               "local_original_frame_path", "size_bytes", "sha256", "overlap_review_status"]
    with result_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(found[k] for k in sorted(found))
    report = {
        "status": "ORIGINAL_SOURCE_FRAMES_ONLY_OVERLAP_AUDIT_PENDING",
        "archive_commit": REVISION,
        "archive_official_sha256": EXPECTED_SHA,
        "original_left_frames_materialized": len(found),
        "source_frames_total_bytes": total,
        "source_frames_directory": str(out),
        "manifest_csv": str(result_csv),
        "ground_truth_members_extracted": 0,
        "h5_members_extracted": 0,
        "model_or_F1_run": False,
        "cohort_frozen": False,
        "note": "No annotation member payload was extracted or decoded. TAR/BZip2 stream is traversed.",
    }
    result_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
