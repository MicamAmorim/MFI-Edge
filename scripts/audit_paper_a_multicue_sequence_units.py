#!/usr/bin/env python3
"""Reconstruct 10-frame MultiCue SEQUENCES from H5 filenames and TAR name index.

No TAR reread, extraction, image/GT decoding, F1, evaluation, or model inference.
A capture prefix (e.g., 4108) is NOT a sequence ID: it can contain several
sequences. Each H5 stem is a proposed annotated-last-left-frame anchor.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

ROOT = Path(r"F:\MFI-Edge-Data\MultiCue")
REVISION = "f47b14959e9764c8aa854cb7958d54462c46f8ef"
SHA256 = "8e5fdb2ff7343e4a55f110e9ffe189b2c81689cd326324e34c6c73562191819e"

IMG_RE = re.compile(r"^multicue/images/(\d+)_(left|right)_(\d+)\.png$")
H5_RE = re.compile(r"^multicue/ground-truth/hdf5/(\d+)_left_(\d+)\.h5$")
GT_RE = re.compile(
    r"^multicue/ground-truth/images/(edges|boundaries)/"
    r"(\d+)_left_(\d+)\.(\d+)\.png$"
)
EXPECTED_GT = {"edges": 6, "boundaries": 5}
COLUMNS = [
    "sequence_id", "capture_prefix", "annotated_left_frame", "last_left_image",
    "h5_anchor_path", "left_frame_count", "right_frame_count",
    "boundaries_png_names", "edges_png_names", "other_sequences_same_prefix",
    "independence_review", "layout_issues"
]


def normalized(name: str) -> str:
    value = name.replace("\\", "/")
    if value.startswith("./"):
        value = value[2:]
    p = PurePosixPath(value)
    if not value or value.startswith("/") or re.match(r"^[A-Za-z]:", value) or ".." in p.parts:
        raise ValueError(f"Unsafe TAR member name: {name!r}")
    return p.as_posix()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--directory", type=Path, default=ROOT)
    args = ap.parse_args()
    root = args.directory.expanduser().resolve()
    index = root / "archive_members_inventory.csv"
    summary_path = root / "archive_member_summary.json"
    if not index.is_file() or not summary_path.is_file():
        ap.error("Missing archive member index. Run inventory_paper_a_multicue_archive.py")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (summary.get("status") != "TAR_MEMBER_METADATA_ONLY_NO_EXTRACTION"
        or summary.get("source_revision") != REVISION
        or summary.get("archive_sha256_verified_by_download") != SHA256
        or summary.get("members") != 3207
        or summary.get("files_extracted") != 0
        or summary.get("ground_truth_payload_decoded") is not False
        or Path(summary.get("full_member_csv", "")).resolve() != index):
        ap.error("Archive index provenance/status mismatch, aborting")

    # Index only: no archive/file contents or HDF5/PNG decoders imported.
    images = defaultdict(dict)  # (capture_prefix, side): {frame_int: path}
    annotations = defaultdict(list)  # (prefix, final_frame, task): [path]
    anchors = {}                 # (capture_prefix, last_frame_int): h5 path
    ignored_dirs = 0
    member_names = set()
    recognized_files = set()
    with index.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"index", "path", "kind", "size_bytes", "unsafe_path_flag"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            ap.error("Incorrect TAR index CSV columns")
        for number, record in enumerate(reader, 1):
            if number != int(record["index"]) or record["unsafe_path_flag"]:
                ap.error("Incomplete, out-of-order or unsafe TAR listing")
            name = normalized(record["path"])
            if name in member_names:
                ap.error(f"Duplicated member path: {name}")
            member_names.add(name)
            if record["kind"] == "directory":
                ignored_dirs += 1
                continue
            if record["kind"] != "file":
                ap.error(f"Unsupported TAR member type: {name}")
            a = IMG_RE.fullmatch(name)
            b = H5_RE.fullmatch(name)
            c = GT_RE.fullmatch(name)
            if a:
                prefix, side, frame_str = a.groups()
                key = (prefix, side)
                frame = int(frame_str)
                if frame in images[key]:
                    ap.error(f"Duplicate frame number with different padding: {name}")
                images[key][frame] = name
            elif b:
                prefix, last_str = b.groups()
                key = (prefix, int(last_str))
                if key in anchors:
                    ap.error(f"Duplicated H5 anchor: {name}")
                anchors[key] = name
            elif c:
                task, prefix, frame_str, annotation_number = c.groups()
                annotations[(prefix, int(frame_str), task)].append(name)
            else:
                ap.error(f"Unexpected source member path: {name}")
            recognized_files.add(name)
    if len(member_names) != 3207 or ignored_dirs != 7 or len(recognized_files) != 3200:
        ap.error("TAR name counts inconsistent with verified archive")
    if len(anchors) != 100 or sum(map(len, images.values())) != 2000 or sum(
        map(len, annotations.values())) != 1100:
        ap.error("Anchor/image/annotation counts differ from 100/2000/1100")
    capture_counts = Counter(prefix for prefix, _ in anchors)
    rows = []
    problem_units = []
    all_assigned_images = set()
    all_assigned_gt = set()
    for (prefix, anchor), h5_path in sorted(anchors.items()):
        image_ids = []
        problems = []
        for side in ("left", "right"):
            for frame in range(anchor - 9, anchor + 1):
                name = images[(prefix, side)].get(frame)
                if name is None:
                    problems.append(f"Missing {side} frame {frame} for H5 anchor {anchor}")
                else:
                    image_ids.append(name)
                    if name in all_assigned_images:
                        problems.append(f"Frame shared by two sequences: {name}")
                    all_assigned_images.add(name)
        gt_files = {}
        for task, required in EXPECTED_GT.items():
            matches = sorted(annotations.get((prefix, anchor, task), []))
            gt_files[task] = matches
            if len(matches) != required:
                problems.append(f"{task} GT path count={len(matches)}, expected={required}")
            for name in matches:
                if name in all_assigned_gt:
                    problems.append(f"GT file matched two anchors: {name}")
                all_assigned_gt.add(name)
        last_path = images[(prefix, "left")].get(anchor, "")
        if not last_path:
            problems.append("Final left source image absent")
        sequence_id = f"{prefix}_left_{anchor:04d}"
        siblings = capture_counts[prefix] - 1
        row = {
            "sequence_id": sequence_id,
            "capture_prefix": prefix,
            "annotated_left_frame": anchor,
            "last_left_image": last_path,
            "h5_anchor_path": h5_path,
            "left_frame_count": len([n for n in image_ids if "_left_" in n]),
            "right_frame_count": len([n for n in image_ids if "_right_" in n]),
            "boundaries_png_names": json.dumps(gt_files["boundaries"]),
            "edges_png_names": json.dumps(gt_files["edges"]),
            "other_sequences_same_prefix": siblings,
            "independence_review": (
                "REPEATED_CAPTURE_PREFIX_HOLD" if siblings else
                "PENDING_HISTORY_AND_SCENE_REVIEW"
            ),
            "layout_issues": " | ".join(problems)
        }
        rows.append(row)
        if problems:
            problem_units.append({"sequence_id": sequence_id, "issues": problems})

    raw_image_paths = {x for v in images.values() for x in v.values()}
    raw_gt_paths = {x for v in annotations.values() for x in v}
    orphan_images = sorted(raw_image_paths - all_assigned_images)
    orphan_gt = sorted(raw_gt_paths - all_assigned_gt)
    if orphan_images:
        problem_units.append({"unassigned_images": orphan_images[:15],
                              "n": len(orphan_images)})
    if orphan_gt:
        problem_units.append({"unassigned_gt_names": orphan_gt[:15],
                              "n": len(orphan_gt)})

    csvout = root / "multicue_h5_anchored_sequence_candidates.csv"
    with csvout.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    status = ("H5_ANCHORED_LAYOUT_OK_NOT_CERTIFIED" if not problem_units
              else "H5_ANCHORED_LAYOUT_REVIEW_REQUIRED")
    repeated = {k: v for k, v in sorted(capture_counts.items()) if v > 1}
    report = {
        "status": status,
        "source_revision": REVISION,
        "source_archive_sha256": SHA256,
        "archive_index_members": len(member_names),
        "h5_anchored_sequence_units": len(rows),
        "unique_capture_prefixes": len(capture_counts),
        "repeated_capture_prefixes": repeated,
        "raw_images_accounted": len(all_assigned_images),
        "gt_png_names_accounted": len(all_assigned_gt),
        "expected_raw_images": 2000,
        "expected_gt_png_names": 1100,
        "expected_h5_files": 100,
        "problem_units_count": len(problem_units),
        "problems": problem_units[:25],
        "candidate_csv": str(csvout),
        "max_candidate_capture_groups_before_other_exclusions": len(capture_counts),
        "note": (
            "100 H5-anchored sequences are not automatically 100 independent scenes. "
            "Prefixes 4108 and 4113 may represent shared capture sessions; "
            "conservatively sample at most one sequence per capture prefix "
            "until documented scene independence is established."
        ),
        "no_tar_reread": True,
        "images_or_gt_decoded": False,
        "f1_calculated": False,
        "cohort_frozen": False,
        "gates": [
            "Visually/lineage-audit MultiCue versus UDED 09-MDBD-1C and other sources",
            "Do not treat edges and boundaries GT as equivalent",
            "Set sampling rule, evaluator, and power before any confirmatory GT/F1 access"
        ],
    }
    jsonout = root / "multicue_h5_anchored_sequence_summary.json"
    jsonout.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not problem_units else 2


if __name__ == "__main__":
    raise SystemExit(main())
