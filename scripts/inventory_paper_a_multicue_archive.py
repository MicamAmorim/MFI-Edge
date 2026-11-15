#!/usr/bin/env python3
"""Metadata-only TAR inventory of a verified, pinned MultiCue archive.

Reads TAR headers/member names/types/sizes in a streaming pass. It never
extracts archive members, opens individual image/GT payloads, or computes F1.
The bzip2 stream is necessarily decompressed internally to reach later headers.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import tarfile
from collections import Counter, deque
from pathlib import Path, PurePosixPath

ARCHIVE_NAME = "multicue-dataset.tar.bz2"
EXPECTED_REVISION = "f47b14959e9764c8aa854cb7958d54462c46f8ef"
EXPECTED_SHA = "8e5fdb2ff7343e4a55f110e9ffe189b2c81689cd326324e34c6c73562191819e"
EXPECTED_SIZE = 3575680805
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".ppm"}
ANNOTATION_PATTERN = re.compile(r"(?i)(?:annot|ground.?truth|[/_]gt[/_.]|boundar|edge.?map|label|contour)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_provenance(archive: Path, provenance: Path, rehash: bool) -> dict:
    if not archive.is_file() or not provenance.is_file():
        raise ValueError("Missing verified archive or archive_provenance.json")
    record = json.loads(provenance.read_text(encoding="utf-8"))
    if record.get("status") != "ARCHIVE_DOWNLOADED_NOT_EXTRACTED":
        raise ValueError("Archive provenance is not marked as verified download")
    if record.get("repository_commit_sha") != EXPECTED_REVISION:
        raise ValueError("Unexpected dataset revision in provenance")
    if record.get("archive_sha256", "").lower() != EXPECTED_SHA:
        raise ValueError("Unexpected archive SHA256 in provenance")
    if record.get("official_lfs_sha256", "").lower() != EXPECTED_SHA:
        raise ValueError("Unexpected official LFS digest in provenance")
    if record.get("official_lfs_sha256_verified") is not True:
        raise ValueError("Archive was not verified against official LFS SHA256")
    if Path(record.get("archive", "")).resolve() != archive:
        raise ValueError("Provenance file points to a different archive")
    if archive.stat().st_size != EXPECTED_SIZE or record.get("archive_bytes") != EXPECTED_SIZE:
        raise ValueError("Unexpected archive size; possible truncation/change")
    if rehash and sha256(archive) != EXPECTED_SHA:
        raise ValueError("Recomputed SHA256 does not match official digest")
    return record


def unsafe_path(name: str, is_link: bool) -> str:
    # This is an inventory, never an extractor. Mark unsafe tar paths for
    # any future selective materialization, including Windows-like paths.
    normalized = name.replace("\\", "/")
    if not normalized or normalized.startswith("/"):
        return "absolute_or_empty"
    if re.match(r"^[A-Za-z]:", normalized):
        return "windows_drive_path"
    if ".." in PurePosixPath(normalized).parts:
        return "path_traversal"
    if is_link:
        return "link_member"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, default=Path(
        r"F:\MFI-Edge-Data\MultiCue\multicue-dataset.tar.bz2"))
    ap.add_argument("--output-dir", type=Path, default=None,
                    help="Defaults to the archive's directory on F:")
    ap.add_argument("--rehash", action="store_true",
                    help="Recompute whole 3.58GB SHA before listing; previous LFS check already exists")
    args = ap.parse_args()
    archive = args.archive.expanduser().resolve()
    output = (args.output_dir or archive.parent).expanduser().resolve()
    if output != archive.parent:
        ap.error("For provenance and disk safety, outputs must remain next to archive on F:")
    provenance = archive.parent / "archive_provenance.json"
    verified = validate_provenance(archive, provenance, args.rehash)
    if archive.parent.drive and archive.parent.drive.lower() == Path.home().drive.lower():
        ap.error("Refusing to write an inventory on the near-full system drive")
    if not output.is_dir():
        ap.error("Destination directory does not exist")
    csvpath = output / "archive_members_inventory.csv"
    resultpath = output / "archive_member_summary.json"
    filetypes = Counter()
    extensions = Counter()
    prefixes = Counter()
    unsafe = []
    examples_first, examples_image, examples_annotation = [], [], []
    tail = deque(maxlen=16)
    members_count = 0
    regular_bytes = 0
    with csvpath.open("w", encoding="utf-8", newline="") as dest:
        writer = csv.writer(dest)
        writer.writerow(["index", "path", "kind", "size_bytes", "suffix",
                         "annotation_name_hint_only", "unsafe_path_flag"])
        with tarfile.open(archive, mode="r|bz2") as tar:
            for member in tar:
                members_count += 1
                kind = ("file" if member.isfile() else "directory" if member.isdir()
                        else "symlink" if member.issym() else "hardlink"
                        if member.islnk() else "other")
                hint = bool(ANNOTATION_PATTERN.search(member.name))
                flagged = unsafe_path(member.name, member.issym() or member.islnk())
                suffix = PurePosixPath(member.name.replace("\\", "/")).suffix.lower()
                prefix = "/".join(PurePosixPath(
                    member.name.replace("\\", "/")).parts[:2])
                writer.writerow([members_count, member.name, kind, member.size,
                                 suffix, str(hint).lower(), flagged])
                filetypes[kind] += 1
                if member.isfile():
                    regular_bytes += member.size
                    extensions[suffix or "(none)"] += 1
                prefixes[prefix] += 1
                info = {"name": member.name, "kind": kind, "size_bytes": member.size}
                if len(examples_first) < 20:
                    examples_first.append(info)
                if suffix in IMAGE_EXTENSIONS and len(examples_image) < 20:
                    examples_image.append(info)
                if hint and len(examples_annotation) < 30:
                    examples_annotation.append(info)
                if flagged and len(unsafe) < 30:
                    unsafe.append({"path": member.name, "reason": flagged})
                tail.append(info)
                if members_count % 1000 == 0:
                    print(f"Scanned {members_count} TAR headers; no files extracted",
                          flush=True, file=sys.stderr)
    report = {
        "status": "TAR_MEMBER_METADATA_ONLY_NO_EXTRACTION",
        "archive": str(archive),
        "source_revision": verified["repository_commit_sha"],
        "archive_sha256_verified_by_download": EXPECTED_SHA,
        "archive_sha256_recomputed_this_run": args.rehash,
        "members": members_count,
        "member_kinds": dict(filetypes),
        "sum_uncompressed_regular_file_bytes": regular_bytes,
        "extension_counts": dict(extensions.most_common(35)),
        "common_first_two_path_components": dict(prefixes.most_common(35)),
        "unsafe_member_examples": unsafe,
        "first_members": examples_first,
        "image_path_examples": examples_image,
        "annotation_name_hint_examples": examples_annotation,
        "last_members": list(tail),
        "full_member_csv": str(csvpath),
        "ground_truth_payload_decoded": False,
        "files_extracted": 0,
        "model_or_F1_executed": False,
        "caveats": [
            "TAR/BZip2 compression stream is read and decompressed internally to reach later headers",
            "Name-based annotation hints do not verify content, labeling task or match to scenes",
            "Archive listing does not certify independence or legitimate sample units",
            "This tool will not open annotation payloads; do not extract until scene/protocol review",
        ],
    }
    resultpath.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
