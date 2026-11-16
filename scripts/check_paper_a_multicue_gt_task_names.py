#!/usr/bin/env python3
"""Metadata-only MultiCue task/annotator-path contract check, before freeze.

Reads ONLY existing CSV/JSON from the verified TAR name inventory and the
predata exclusion-decision CSV. Never reads TAR, H5, original PNG, GT PNG,
scores, descriptors or F1. Counts GT FILE NAMES, not actual annotator content.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

# Self-contained scientific provenance pin.  This name-only validator must
# work even on partial Windows checkouts lacking the earlier sequence-audit
# script; it validates the source revision/SHA against existing JSON.
# Do not import other audit scripts or silently read the TAR/GT.
ROOT = Path(r"F:\MFI-Edge-Data\MultiCue")
REVISION = "f47b14959e9764c8aa854cb7958d54462c46f8ef"
SHA256 = "8e5fdb2ff7343e4a55f110e9ffe189b2c81689cd326324e34c6c73562191819e"

TASK_COUNTS = {"edges": 6, "boundaries": 5}
GT_PATTERN = re.compile(
    r"^multicue/ground-truth/images/(edges|boundaries)/"
    r"(\d+)_left_(\d+)\.(\d+)\.png$"
)
IMAGE_PATTERN = re.compile(r"^multicue/images/(\d+)_left_(\d+)\.png$")
H5_PATTERN = re.compile(r"^multicue/ground-truth/hdf5/(\d+)_left_(\d+)\.h5$")


def check_unit(row: dict) -> dict:
    prefix = row["capture_prefix"]
    seq = row["sequence_id"]
    anchor = int(row["annotated_left_frame"])
    if seq != f"{prefix}_left_{anchor:04d}":
        raise ValueError(f"Sequence ID/anchor mismatch: {seq}")
    original = IMAGE_PATTERN.fullmatch(row["last_left_image"])
    h5 = H5_PATTERN.fullmatch(row["h5_anchor_path"])
    if (original is None or h5 is None
            or original.group(1) != prefix or h5.group(1) != prefix
            or int(original.group(2)) != anchor
            or int(h5.group(2)) != anchor):
        raise ValueError(f"Original/H5 anchor mismatch: {seq}")
    if row["layout_issues"].strip():
        raise ValueError(f"Pre-existing layout issue: {seq}")
    if int(row["left_frame_count"]) != 10 or int(row["right_frame_count"]) != 10:
        raise ValueError(f"Incomplete left/right raw sequence: {seq}")

    by_task = {}
    all_paths = set()
    for task, count in TASK_COUNTS.items():
        paths = json.loads(row[f"{task}_png_names"])
        if not isinstance(paths, list) or len(paths) != count:
            raise ValueError(f"Wrong {task} GT file-name count: {seq}")
        indices = []
        for name in paths:
            if not isinstance(name, str) or name in all_paths:
                raise ValueError(f"Duplicate/invalid GT path: {seq}")
            all_paths.add(name)
            m = GT_PATTERN.fullmatch(name)
            if (m is None or m.group(1) != task
                    or m.group(2) != prefix or int(m.group(3)) != anchor):
                raise ValueError(f"GT path is for another task/frame: {seq}: {name}")
            indices.append(int(m.group(4)))
        if len(set(indices)) != count:
            raise ValueError(f"Duplicate {task} suffix index: {seq}")
        by_task[task] = {
            "file_names": count,
            "suffix_indices": sorted(indices),
            "suffixes_are_NOT_proof_of_annotator_identity": True,
        }
    return {"sequence_id": seq, "capture_prefix": prefix,
            "annotated_frame": anchor, "tasks": by_task,
            "all_gt_paths": sorted(all_paths)}


def validate_inventory(root: Path) -> dict:
    summary_path = root / "multicue_h5_anchored_sequence_summary.json"
    csv_path = root / "multicue_h5_anchored_sequence_candidates.csv"
    if not summary_path.is_file() or not csv_path.is_file():
        raise ValueError("Missing existing index-only MultiCue sequence inventory")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (summary.get("status") != "H5_ANCHORED_LAYOUT_OK_NOT_CERTIFIED"
            or summary.get("source_revision") != REVISION
            or summary.get("source_archive_sha256") != SHA256
            or summary.get("h5_anchored_sequence_units") != 100
            or summary.get("unique_capture_prefixes") != 96
            or summary.get("gt_png_names_accounted") != 1100
            or summary.get("problem_units_count") != 0
            or summary.get("no_tar_reread") is not True
            or summary.get("images_or_gt_decoded") is not False
            or summary.get("cohort_frozen") is not False
            or Path(summary.get("candidate_csv", "")).resolve() != csv_path.resolve()):
        raise ValueError("Archive/sequence inventory provenance changed")
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 100:
        raise ValueError("Expected 100 H5-anchored sequences")
    units = [check_unit(r) for r in rows]
    if len({u["sequence_id"] for u in units}) != len(units):
        raise ValueError("Repeated sequence IDs")
    prefixes = Counter(u["capture_prefix"] for u in units)
    if len(prefixes) != 96 or {k: v for k, v in prefixes.items() if v > 1} != {
            k: int(v) for k, v in summary["repeated_capture_prefixes"].items()}:
        raise ValueError("Capture grouping mismatch")

    all_gt = [p for u in units for p in u["all_gt_paths"]]
    if len(all_gt) != 1100 or len(set(all_gt)) != 1100:
        raise ValueError("Duplicate/incorrect total GT paths")
    hold = [u for u in units if u["capture_prefix"] == "4113"]
    if len(hold) != 2 or "4113_left_0082" not in {
            u["sequence_id"] for u in hold}:
        raise ValueError("Known historical UDED/MultiCue overlap absent")
    return {
        "status": "TASK_GT_NAME_LAYOUT_VERIFIED_CONTENT_UNOPENED_NOT_FROZEN",
        "source_revision": REVISION,
        "archive_sha256": SHA256,
        "sequence_count": len(units),
        "capture_prefix_count": len(prefixes),
        "repeated_capture_prefixes": {
            k: v for k, v in sorted(prefixes.items()) if v > 1
        },
        "annotated_last_left_frame_per_sequence": True,
        "annotation_file_names_by_task": {
            "edges": sum(u["tasks"]["edges"]["file_names"] for u in units),
            "boundaries": sum(u["tasks"]["boundaries"]["file_names"] for u in units)
        },
        "annotation_file_names_per_sequence": TASK_COUNTS,
        "historically_exposed_prefix_held": "4113",
        "provisional_max_other_prefixes": len(prefixes) - 1,
        "no_actual_GT_content_or_annotator_identity_verified": True,
        "no_TAR_H5_PNG_or_F1_read": True,
        "protocol_frozen": False,
        "evaluation_policy_proposal": {
            "primary_task": "edges",
            "BIPED_anotation_count_expected": 1,
            "MultiCue_anotation_count_expected": 6,
            "per_image_outcome": (
                "mean over separately evaluated annotator-specific F1 "
                "candidate minus mean over annotator-specific F1 control"
            ),
            "must_freeze_policy_and_validate_actual_GT_format_before_F1": True
        },
        "caveat": (
            "Filename suffixes only prove distinct names; annotation content, "
            "annotator identity and GT equivalence are not examined here."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if root.drive and root.drive.lower() == Path.home().drive.lower():
        parser.error("Do not write project reports to nearly full C:")
    report = validate_inventory(root)
    output = root / "multicue_annotation_task_name_contract_predata.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
