#!/usr/bin/env python3
"""Audit MultiCue scene/frame/annotation PATHS from an existing TAR index.

NO download, TAR re-read, extraction, image decoding, annotation decoding, F1
or model inference. The CSV stores names and sizes obtained by the earlier
verified streaming TAR inventory.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

EXPECTED_REVISION = "f47b14959e9764c8aa854cb7958d54462c46f8ef"
EXPECTED_HASH = "8e5fdb2ff7343e4a55f110e9ffe189b2c81689cd326324e34c6c73562191819e"
EXPECTED_MEMBERS = 3207
DEFAULT_ROOT = Path(r"F:\MFI-Edge-Data\MultiCue")
IMAGE_RE = re.compile(r"^multicue/images/(?P<scene>\d+)_(?P<side>left|right)_(?P<frame>\d+)\.png$", re.I)
GT_RE = re.compile(
    r"^multicue/ground-truth/images/(?P<task>[^/]+)/"
    r"(?P<scene>\d+)_(?P<side>left|right)_(?P<frame>\d+)"
    r"(?:\.(?P<suffix_index>\d+))?\.png$", re.I
)
NONPAYLOAD_FIELDS = {"index", "path", "kind", "size_bytes", "suffix",
                     "annotation_name_hint_only", "unsafe_path_flag"}


def normalize_path(value: str) -> str:
    name = value.replace("\\", "/")
    if name.startswith("./"):
        name = name[2:]
    path = PurePosixPath(name)
    if (not name or name.startswith("/") or ".." in path.parts
            or re.match(r"^[a-zA-Z]:", name)):
        raise ValueError("Unsafe member name in index")
    return path.as_posix()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--directory", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()
    directory = args.directory.expanduser().resolve()
    index = directory / "archive_members_inventory.csv"
    summary_file = directory / "archive_member_summary.json"
    if not index.is_file() or not summary_file.is_file():
        ap.error("Missing TAR index or summary. Run inventory_paper_a_multicue_archive.py first.")
    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    if (summary.get("status") != "TAR_MEMBER_METADATA_ONLY_NO_EXTRACTION"
            or summary.get("source_revision") != EXPECTED_REVISION
            or summary.get("archive_sha256_verified_by_download") != EXPECTED_HASH):
        ap.error("Source revision/hash/status mismatch; refuse to analyze unverified index")
    if summary.get("members") != EXPECTED_MEMBERS:
        ap.error("Unexpected TAR member count")
    if summary.get("files_extracted") != 0 or summary.get("ground_truth_payload_decoded"):
        ap.error("Expected strictly no-extraction inventory")
    if Path(summary.get("full_member_csv", "")).resolve() != index:
        ap.error("Index path not the one named by verified summary")

    image_frames = defaultdict(lambda: defaultdict(set))
    gt_paths = defaultdict(lambda: defaultdict(list))
    gt_unparsed = []
    h5_paths = []
    path_prefixes = Counter()
    all_members = set()
    counters = Counter()
    with index.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not NONPAYLOAD_FIELDS.issubset(reader.fieldnames):
            ap.error("Unexpected CSV format")
        for expected_index, row in enumerate(reader, start=1):
            if int(row["index"]) != expected_index:
                ap.error("Out-of-order or incomplete member index")
            if row["unsafe_path_flag"]:
                ap.error("Unsafe member path flagged in inventory")
            name = normalize_path(row["path"])
            if name in all_members:
                ap.error(f"Repeated path in TAR index: {name}")
            all_members.add(name)
            kind, suffix = row["kind"], row["suffix"].lower()
            counters[kind] += 1
            if kind == "file":
                path_prefixes[str(PurePosixPath(name).parent)] += 1
            raw = IMAGE_RE.fullmatch(name)
            annotation = GT_RE.fullmatch(name)
            if raw:
                if kind != "file":
                    ap.error("Image path has non-file TAR type")
                scene, side, frame = raw.group("scene", "side", "frame")
                image_frames[scene][side.lower()].add(frame)
            elif annotation:
                if kind != "file":
                    ap.error("GT path has non-file TAR type")
                task, scene, side, frame, suffix_index = annotation.group(
                    "task", "scene", "side", "frame", "suffix_index")
                gt_paths[scene][task.lower()].append({
                    "path": name, "side": side.lower(), "frame": frame,
                    "suffix_index": suffix_index,
                })
            elif kind == "file" and name.startswith("multicue/ground-truth/"):
                if suffix == ".h5":
                    h5_paths.append(name)
                else:
                    gt_unparsed.append(name)
            elif kind == "file" and name.startswith("multicue/images/"):
                gt_unparsed.append(name)

    if len(all_members) != EXPECTED_MEMBERS:
        ap.error(f"Expected {EXPECTED_MEMBERS} rows, saw {len(all_members)}")
    scenes = sorted(set(image_frames) | set(gt_paths))
    all_tasks = sorted({task for tasks in gt_paths.values() for task in tasks})
    problems = []
    units = []
    counts_task = Counter()
    for scene in scenes:
        left = image_frames[scene].get("left", set())
        right = image_frames[scene].get("right", set())
        if not left:
            problems.append(f"Scene {scene}: no left images")
            continue
        # Numeric frame IDs, preserving zero padding from archive.
        last = max(left, key=lambda s: int(s))
        last_image = f"multicue/images/{scene}_left_{last}.png"
        task_match = {}
        task_other_frame = {}
        task_paths = {}
        for task in all_tasks:
            items = gt_paths[scene].get(task, [])
            exact = [item for item in items
                     if item["side"] == "left" and item["frame"] == last]
            mismatched = [item for item in items
                          if item["side"] != "left" or item["frame"] != last]
            task_match[task] = len(exact)
            task_other_frame[task] = len(mismatched)
            task_paths[task] = [entry["path"] for entry in exact]
            counts_task[task] += len(items)
        scene_problems = []
        if len(left) != 10:
            scene_problems.append(f"left_count={len(left)}, expected=10")
        if len(right) != 10:
            scene_problems.append(f"right_count={len(right)}, expected=10")
        if len(left) != len(right):
            scene_problems.append("left/right frame count imbalance")
        if any(v == 0 for v in task_match.values()):
            scene_problems.append("missing matched GT name for one or more tasks")
        if any(v for v in task_other_frame.values()):
            scene_problems.append("some GT paths do not name last left frame")
        if scene_problems:
            problems.append(f"Scene {scene}: {', '.join(scene_problems)}")
        units.append({
            "scene_id": scene,
            "last_left_frame": last,
            "last_left_image_path": last_image,
            "left_image_count": len(left),
            "right_image_count": len(right),
            "gt_name_matches_by_task": json.dumps(task_match, sort_keys=True),
            "gt_name_other_frames": json.dumps(task_other_frame, sort_keys=True),
            "matching_gt_name_paths": json.dumps(task_paths, sort_keys=True),
            "review_status": ("REVIEW_ANOMALY" if scene_problems
                              else "PENDING_INDEPENDENCE_AND_PROTOCOL_FREEZE"),
        })

    outcsv = directory / "multicue_scene_name_candidates.csv"
    with outcsv.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "scene_id", "last_left_frame", "last_left_image_path",
            "left_image_count", "right_image_count", "gt_name_matches_by_task",
            "gt_name_other_frames", "matching_gt_name_paths", "review_status"])
        writer.writeheader()
        writer.writerows(units)
    report = {
        "status": "SCENE_NAME_LAYOUT_ONLY_NOT_CERTIFIED",
        "source_revision": EXPECTED_REVISION,
        "source_archive_sha256": EXPECTED_HASH,
        "archive_members_from_index": len(all_members),
        "kinds": dict(counters),
        "scene_ids_from_names": len(scenes),
        "scene_units_with_left_images": len(units),
        "task_directories_found": all_tasks,
        "task_annotation_png_counts": dict(counts_task),
        "h5_file_count": len(h5_paths),
        "h5_path_examples": h5_paths[:10],
        "unparsed_gt_or_image_paths_count": len(gt_unparsed),
        "unparsed_examples": gt_unparsed[:12],
        "common_file_directories": dict(path_prefixes.most_common(15)),
        "scene_problems_count": len(problems),
        "scene_problems_first": problems[:30],
        "candidate_scene_csv": str(outcsv),
        "cohort_frozen": False,
        "image_or_gt_decoded": False,
        "f1_calculated": False,
        "prohibitions": [
            "Do not interpret filename suffix indices as confirmed annotator identities",
            "Do not assume GT boundaries and edges are interchangeable",
            "Do not treat scenes as independent until sequence/cross-domain audit",
            "No GT payload or H5 content was opened",
            "No selective extraction performed; no F1 or model inference run",
        ],
    }
    out = directory / "multicue_scene_name_summary.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
