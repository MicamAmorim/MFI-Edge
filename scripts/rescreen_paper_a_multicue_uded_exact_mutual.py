#!/usr/bin/env python3
"""Re-screen ALL 27 x 100 historical UDED/MultiCue pairs with exact mutual BF.

Pre-data image-lineage QA only. Uses existing SHA-bound SIFT descriptor caches,
not original images, GT, HDF5, predictions, F1 or model inference.

The 25 image-only pairs already computed with EXACT reciprocal BF/Lowe are
reused. Remaining pairs use the exact same mutual_match() implementation;
per-UDED checkpoints on F: are atomically written every 10 pairs, permitting
safe resumption without repeating completed work. No cohort approvals/exclusions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

import cv2

from audit_paper_a_multicue_image_overlap import MULTICUE
from audit_paper_a_multicue_all_uded_geometry import ALGORITHM
from diagnose_paper_a_multicue_sift_false_positives import load_feature, mutual_match

POLICY = "EXACT_BF_Lowe070_BIDIRECTIONAL_MUTUAL_RANSAC4_v1"
REFERENCE_POSITIVE = ("09-MDBD-1C", "4113_left_0082")
METRICS = [
    "mutual_bf_matches", "mutual_ransac_inliers",
    "mutual_inlier_fraction", "source_inlier_x_span",
    "source_inlier_y_span", "target_inlier_x_span", "target_inlier_y_span",
    "homography_condition_number", "mutual_homography_valid",
]
CSV_COLUMNS = [
    "uded_id", "multicue_id", "capture_prefix", *METRICS,
    "screen_flag", "source_of_matching_result",
]


def read_csv(path, mandatory):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not set(mandatory).issubset(reader.fieldnames):
            raise ValueError("Missing required CSV columns: " + str(path))
        return list(reader)


def manifest_digest(rows, id_key, sha_key):
    raw = "\n".join(sorted(r[id_key] + "|" + r[sha_key] for r in rows))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def screen_flag(metrics):
    """Broad visual-review triggers, NOT duplicate certification."""
    count = int(metrics["mutual_ransac_inliers"])
    mutual = int(metrics["mutual_bf_matches"])
    share = float(metrics["mutual_inlier_fraction"])
    if metrics["mutual_homography_valid"] and count >= 12 and mutual >= 15 and share >= 0.55:
        return "REVIEW_STRONG"
    if metrics["mutual_homography_valid"] and count >= 6 and mutual >= 8 and share >= 0.50:
        return "REVIEW_WEAK"
    return "NO_MATCHING_FLAG"


def atomic_json(path, obj):
    temporary = path.with_suffix(".json.part")
    if temporary.exists():
        temporary.unlink()  # stale temporary file from an interrupted write only
    try:
        with temporary.open("x", encoding="utf-8") as dest:
            json.dump(obj, dest, ensure_ascii=False, indent=2)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def provenance(root: Path):
    report = json.loads((root / "multicue_all_uded_geometric_overlap_summary.json")
                        .read_text(encoding="utf-8"))
    diag = json.loads((root / "multicue_sift_mutual_validation_diagnostics.json")
                      .read_text(encoding="utf-8"))
    if (report.get("status") != "ALL_UDED_GEOMETRY_SCREEN_REVIEW_ONLY"
            or report.get("image_only_pairs") != 2700
            or report.get("algorithm") != ALGORITHM
            or report.get("opencv") != cv2.__version__
            or report.get("gt_h5_model_f1_opened") is not False
            or diag.get("status") != "GEOMETRY_FALSE_POSITIVE_DIAGNOSTIC_ONLY"
            or diag.get("cached_pairs_checked") != 25
            or diag.get("no_images_redecoded") is not True
            or diag.get("no_GT_H5_F1_opened") is not True):
        raise ValueError("Previous cache-only lineage audits incompatible")

    target_manifest = read_csv(
        root / "multicue_source_frames_only_manifest.csv",
        {"sequence_id", "capture_prefix", "sha256"}
    )
    if len(target_manifest) != 100 or len(
            {r["sequence_id"] for r in target_manifest}) != 100:
        raise ValueError("Target manifest must contain 100 unique source frames")
    target_manifest.sort(key=lambda r: r["sequence_id"])

    references = []
    cp_folder = root / "predata_sift_cache" / "reference_checkpoints"
    for cp in cp_folder.glob("*.json"):
        data = json.loads(cp.read_text(encoding="utf-8"))
        if (data.get("algorithm") != ALGORITHM
                or data.get("opencv") != cv2.__version__
                or data.get("gt_h5_f1_accessed") is not False
                or len(data.get("pairs", [])) != 100):
            raise ValueError("Unrecognized cached UDED source reference: " + str(cp))
        references.append({
            "id": data["reference_id"],
            "sha256": data["reference_sha256"],
        })
    references.sort(key=lambda r: r["id"])
    if len(references) != 27 or len({r["id"] for r in references}) != 27:
        raise ValueError("Expected 27 historical UDED reference caches")

    prior_csv = read_csv(
        root / "multicue_sift_mutual_validation_diagnostics.csv",
        {"uded_id", "multicue_id", "capture_prefix", *METRICS}
    )
    if len(prior_csv) != 25:
        raise ValueError("Expected 25 prior exact mutual BF results")
    prior_map = {}
    target_names = {r["sequence_id"] for r in target_manifest}
    ref_names = {r["id"] for r in references}
    for row in prior_csv:
        key = (row["uded_id"], row["multicue_id"])
        if key in prior_map or key[0] not in ref_names or key[1] not in target_names:
            raise ValueError("Duplicate/unknown prior mutual-BF pair")
        prior_map[key] = row
    if REFERENCE_POSITIVE not in prior_map or int(
            prior_map[REFERENCE_POSITIVE]["mutual_ransac_inliers"]) < 2000:
        raise ValueError("Known exposed image not recovered in prior BF control")

    return references, target_manifest, prior_map


def check_resume(data, reference, digest, expected_names):
    if (data.get("status") != "PARTIAL_EXACT_MUTUAL_BF_IMAGE_ONLY"
            or data.get("policy") != POLICY
            or data.get("sift_cache_algorithm") != ALGORITHM
            or data.get("opencv") != cv2.__version__
            or data.get("reference_id") != reference["id"]
            or data.get("reference_sha256") != reference["sha256"]
            or data.get("target_manifest_digest") != digest
            or data.get("gt_h5_f1_accessed") is not False):
        raise ValueError("Checkpoint provenance mismatch; stop before resuming")
    rows = data.get("pairs")
    if not isinstance(rows, list):
        raise ValueError("Checkpoint pairs must be a list")
    keys = [x.get("multicue_id") for x in rows]
    if len(set(keys)) != len(keys) or not set(keys).issubset(expected_names):
        raise ValueError("Unexpected/duplicate checkpoint source frame")
    if any(x.get("uded_id") != reference["id"] for x in rows):
        raise ValueError("Checkpoint UDED reference mismatch")
    return {r["multicue_id"]: r for r in rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--multicue-root", type=Path, default=MULTICUE)
    parser.add_argument("--reference-limit", type=int, default=27,
                        help="1..27 for safe incremental run; default all 27")
    args = parser.parse_args()
    if not 1 <= args.reference_limit <= 27:
        parser.error("Reference limit must be 1..27")
    root = args.multicue_root.expanduser().resolve()
    if root.drive and root.drive.lower() == Path.home().drive.lower():
        parser.error("Refuse to write cache/report to the near-full system disk")
    references, targets, already_done = provenance(root)
    cache = root / "predata_sift_cache"
    checkpoint_folder = root / "predata_exact_mutual_rescreen"
    checkpoint_folder.mkdir(exist_ok=True)
    targets_digest = manifest_digest(targets, "sequence_id", "sha256")
    target_names = {x["sequence_id"] for x in targets}
    cv2.setNumThreads(4)

    target_features = {
        row["sequence_id"]: load_feature(cache, row["sha256"], cv2.__version__)
        for row in targets
    }
    print("Validated 100 SHA-bound original-image SIFT caches; no images opened",
          flush=True)

    new_pairs, reused_25, resumed_pairs = 0, 0, 0
    all_results = []
    for i, ref in enumerate(references[:args.reference_limit], 1):
        path = checkpoint_folder / ("ref_" + ref["sha256"] + ".json")
        checkpoint = {
            "status": "PARTIAL_EXACT_MUTUAL_BF_IMAGE_ONLY",
            "policy": POLICY,
            "sift_cache_algorithm": ALGORITHM,
            "opencv": cv2.__version__,
            "reference_id": ref["id"], "reference_sha256": ref["sha256"],
            "target_manifest_digest": targets_digest,
            "gt_h5_f1_accessed": False,
            "pairs": [],
        }
        if path.exists():
            stored = json.loads(path.read_text(encoding="utf-8"))
            old_rows = check_resume(stored, ref, targets_digest, target_names)
            checkpoint["pairs"] = list(old_rows.values())
            resumed_pairs += len(old_rows)
        else:
            old_rows = {}
        reference_features = None
        for j, target in enumerate(targets, 1):
            key = (ref["id"], target["sequence_id"])
            if target["sequence_id"] in old_rows:
                continue
            if key in already_done:
                previous = already_done[key]
                metrics = {
                    k: (previous[k] == "True" if k == "mutual_homography_valid"
                        else float(previous[k]) if k == "mutual_inlier_fraction"
                        or k.endswith("_span")
                        or k == "homography_condition_number" and previous[k] != ""
                        else int(previous[k]) if k in ("mutual_bf_matches", "mutual_ransac_inliers")
                        else None)
                    for k in METRICS
                }
                if previous["homography_condition_number"] == "":
                    metrics["homography_condition_number"] = None
                reused_25 += 1
                origin = "PRIOR_25_BF_CACHE"
            else:
                if reference_features is None:
                    reference_features = load_feature(cache, ref["sha256"], cv2.__version__)
                x1, d1 = reference_features
                x2, d2 = target_features[target["sequence_id"]]
                metrics = mutual_match(x1, d1, x2, d2)
                new_pairs += 1
                origin = "EXACT_MUTUAL_BF_NEW"
            result = {
                "uded_id": ref["id"], "multicue_id": target["sequence_id"],
                "capture_prefix": target["capture_prefix"],
                **metrics, "screen_flag": screen_flag(metrics),
                "source_of_matching_result": origin
            }
            checkpoint["pairs"].append(result)
            if j % 10 == 0 or j == len(targets):
                atomic_json(path, checkpoint)
                print(f"UDED {i}/{args.reference_limit}: {ref['id']} "
                      f"{len(checkpoint['pairs'])}/100 pairs saved", flush=True)
        if len(checkpoint["pairs"]) != 100:
            atomic_json(path, checkpoint)
        if len(checkpoint["pairs"]) != 100:
            raise ValueError("Reference is incomplete, no full-report promotion")
        all_results.extend(checkpoint["pairs"])
        print(f"Reference {i}/{args.reference_limit} complete: {ref['id']}", flush=True)

    positive = next((x for x in all_results if
                     (x["uded_id"], x["multicue_id"]) == REFERENCE_POSITIVE), None)
    complete = len(all_results) == 2700 and args.reference_limit == 27
    if complete and (positive is None or int(positive["mutual_ransac_inliers"]) < 2000):
        raise ValueError("Known prior-exposure control not confirmed; no negative conclusion")
    # The provenance() gate validates the previously established positive
    # control even during --reference-limit partial runs. Only a complete
    # re-screen may claim the control was reproduced in its own 2700-pair set.
    if len({(r["uded_id"], r["multicue_id"]) for r in all_results}) != len(all_results):
        raise ValueError("Duplicate comparison in resumed report")

    all_results.sort(key=lambda r: (r["uded_id"], r["multicue_id"]))
    csvout = root / ("multicue_all_uded_exact_mutual_pairs.csv" if complete
                     else "multicue_all_uded_exact_mutual_PARTIAL_pairs.csv")
    with csvout.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(all_results)
    flags = [r for r in all_results if r["screen_flag"] != "NO_MATCHING_FLAG"]
    output = {
        "status": ("ALL_UDED_EXACT_MUTUAL_SCREEN_REVIEW_ONLY"
                   if complete else "PARTIAL_EXACT_MUTUAL_SCREEN_NO_CONCLUSION"),
        "source": "27 historical UDED originals x 100 MultiCue final-left originals",
        "matching_policy": POLICY, "opencv": cv2.__version__,
        "comparison_count": len(all_results),
        "expected_comparisons": 2700,
        "completed_reference_count": args.reference_limit,
        "new_pairs_computed_this_run": new_pairs,
        "previously_diagnosed_pairs_reused": reused_25,
        "checkpointed_pairs_reused": resumed_pairs,
        "known_exposure_control": positive,
        "review_flags": sorted(flags, key=lambda r: (
            -r["mutual_ransac_inliers"], -r["mutual_bf_matches"]))[:100],
        "review_flag_count": len(flags),
        "distinct_multicue_prefixes_flagged": sorted(
            {r["capture_prefix"] for r in flags}),
        "pairs_csv": str(csvout),
        "checkpoint_dir": str(checkpoint_folder),
        "image_GT_H5_F1_opened": False,
        "automatic_exclusions": 0, "cohort_frozen": False,
        "caveats": [
            "Pre-data image-only overlap triage, not H1/H2 confirmation",
            "Mutual BF+Lowe may miss severe viewpoint changes and other video frames",
            "Even full 2700-pair negative result cannot certify historical independence",
            "Flags need manual inspection before any sampling/exclusion decision",
            "All decisions must be documented before protocol freeze",
        ]
    }
    jsonout = root / ("multicue_all_uded_exact_mutual_summary.json" if complete
                      else "multicue_all_uded_exact_mutual_PARTIAL_summary.json")
    atomic_json(jsonout, output)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
