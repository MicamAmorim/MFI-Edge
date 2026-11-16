#!/usr/bin/env python3
"""Investigate visual false-positive SIFT/RANSAC alerts from cached source features.

Uses ONLY prior image-only .npz SIFT descriptors and JSON manifests from F:.
No re-extraction, no image decoding, no GT/H5/F1, no operator evaluation.
Computes stricter mutual BF/Lowe matches and geometry diagnostics on 25
pre-existing flagged pairs. Results are diagnostics, never automatic exclusions.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import cv2
import numpy as np

from audit_paper_a_multicue_all_uded_geometry import ALGORITHM
from audit_paper_a_multicue_image_overlap import MULTICUE

COLUMNS = [
    "uded_id", "multicue_id", "capture_prefix",
    "previous_flann_matches", "previous_flann_inliers",
    "mutual_bf_matches", "mutual_ransac_inliers", "mutual_inlier_fraction",
    "source_inlier_x_span", "source_inlier_y_span",
    "target_inlier_x_span", "target_inlier_y_span",
    "homography_condition_number", "mutual_homography_valid",
    "visual_decision_prior",
]


def load_feature(cache: Path, sha: str, expected_cv: str):
    path = cache / f"sift_{sha}.npz"
    if not path.is_file():
        raise ValueError(f"Missing cached image-only SIFT features: {path}")
    with np.load(path, allow_pickle=False) as a:
        if (str(a["sha"].item()) != sha
                or str(a["algorithm"].item()) != ALGORITHM
                or str(a["opencv"].item()) != expected_cv):
            raise ValueError(f"Image-only cache provenance mismatch: {path}")
        xy = np.asarray(a["coords"], np.float32)
        desc = np.asarray(a["desc"], np.float32)
    if xy.ndim != 2 or xy.shape[1] != 2 or desc.ndim != 2 or desc.shape[1] != 128 or len(xy) != len(desc):
        raise ValueError(f"Invalid cached descriptor shapes: {path}")
    return xy, np.ascontiguousarray(desc)


def span_fraction(all_xy: np.ndarray, inlier_xy: np.ndarray):
    if len(all_xy) < 2 or len(inlier_xy) < 2:
        return (0.0, 0.0)
    full = np.ptp(all_xy, axis=0)
    selected = np.ptp(inlier_xy, axis=0)
    return tuple(round(float(v), 5) for v in selected / np.maximum(full, 1))


def mutual_match(xy1, d1, xy2, d2):
    """Cross-validated Lowe ratio test with unique correspondences."""
    empty = {
        "mutual_bf_matches": 0, "mutual_ransac_inliers": 0,
        "mutual_inlier_fraction": 0.0,
        "source_inlier_x_span": 0.0, "source_inlier_y_span": 0.0,
        "target_inlier_x_span": 0.0, "target_inlier_y_span": 0.0,
        "homography_condition_number": None, "mutual_homography_valid": False,
    }
    if len(d1) < 4 or len(d2) < 4:
        return empty
    matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    forward = matcher.knnMatch(d1, d2, k=2)
    reverse = matcher.knnMatch(d2, d1, k=2)
    ratio = 0.70
    valid_forward = {
        pair[0].queryIdx: pair[0].trainIdx
        for pair in forward if len(pair) == 2
        and pair[0].distance < ratio * pair[1].distance
    }
    valid_reverse = {
        pair[0].queryIdx: pair[0].trainIdx
        for pair in reverse if len(pair) == 2
        and pair[0].distance < ratio * pair[1].distance
    }
    paired = sorted(
        (a, b) for a, b in valid_forward.items()
        if valid_reverse.get(b) == a
    )
    result = {**empty, "mutual_bf_matches": len(paired)}
    if len(paired) < 4:
        return result
    src = np.asarray([xy1[a] for a, _ in paired], np.float32).reshape(-1, 1, 2)
    dst = np.asarray([xy2[b] for _, b in paired], np.float32).reshape(-1, 1, 2)
    cv2.setRNGSeed(20261115)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 4.0,
                                 maxIters=3000, confidence=0.995)
    valid = bool(H is not None and np.isfinite(H).all()
                 and np.linalg.matrix_rank(H) == 3)
    if not valid:
        return result
    inlier_mask = mask.ravel().astype(bool)
    inliers = int(inlier_mask.sum())
    source_spread = span_fraction(xy1, src.reshape(-1, 2)[inlier_mask])
    target_spread = span_fraction(xy2, dst.reshape(-1, 2)[inlier_mask])
    condition = float(np.linalg.cond(H))
    result.update({
        "mutual_ransac_inliers": inliers,
        "mutual_inlier_fraction": round(inliers / len(paired), 5),
        "source_inlier_x_span": source_spread[0],
        "source_inlier_y_span": source_spread[1],
        "target_inlier_x_span": target_spread[0],
        "target_inlier_y_span": target_spread[1],
        "homography_condition_number": round(condition, 4) if math.isfinite(condition) else None,
        "mutual_homography_valid": True,
    })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--multicue-root", type=Path, default=MULTICUE)
    args = parser.parse_args()
    root = args.multicue_root.expanduser().resolve()
    if root.drive and root.drive.lower() == Path.home().drive.lower():
        parser.error("Do not write audit results to the nearly full system drive")
    summary = json.loads((root / "multicue_all_uded_geometric_overlap_summary.json").read_text(encoding="utf-8"))
    flags = summary.get("flags", [])
    if (summary.get("status") != "ALL_UDED_GEOMETRY_SCREEN_REVIEW_ONLY"
            or summary.get("gt_h5_model_f1_opened") is not False
            or summary.get("image_only_pairs") != 2700
            or len(flags) != 25
            or summary.get("algorithm") != ALGORITHM
            or summary.get("opencv") != cv2.__version__):
        parser.error("Incompatible earlier image-only audit")
    manifest = root / "multicue_source_frames_only_manifest.csv"
    with manifest.open(encoding="utf-8-sig", newline="") as f:
        index = {r["sequence_id"]: r for r in csv.DictReader(f)}
    if len(index) != 100:
        parser.error("Original-only MultiCue manifest incomplete")
    ref_dir = root / "predata_sift_cache" / "reference_checkpoints"
    references = {}
    for path in ref_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("algorithm") != ALGORITHM or data.get("gt_h5_f1_accessed") is not False:
            parser.error(f"Unexpected original-image checkpoint: {path}")
        key = data["reference_id"]
        if key in references:
            parser.error("Duplicate UDED reference checkpoint")
        references[key] = data
    if len(references) != 27:
        parser.error("Expected 27 cached original UDED references")
    cache = root / "predata_sift_cache"
    visual = {}
    # Decision table is an authored repository record, not a model output.
    decisions = Path(__file__).resolve().parents[1] / "docs/paper_a_confirmation/multicue_visual_25_decisions.csv"
    with decisions.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            key = (r["uded_original_id"], r["multicue_sequence_id"])
            if key in visual:
                parser.error("Duplicate visually reviewed pair")
            visual[key] = r["visual_decision"]
    if len(visual) != 25:
        parser.error("Expected 25 reviewed pairs")
    rows = []
    for i, old in enumerate(flags, 1):
        a, b = old["uded_original_id"], old["multicue_sequence_id"]
        key = (a, b)
        if key not in visual or a not in references or b not in index:
            parser.error("Flag source missing from reviewed tables")
        axy, ad = load_feature(cache, references[a]["reference_sha256"], cv2.__version__)
        bxy, bd = load_feature(cache, index[b]["sha256"], cv2.__version__)
        metrics = mutual_match(axy, ad, bxy, bd)
        rows.append({
            "uded_id": a, "multicue_id": b,
            "capture_prefix": old["capture_prefix"],
            "previous_flann_matches": old["ratio_matches"],
            "previous_flann_inliers": old["ransac_inliers"],
            **metrics, "visual_decision_prior": visual[key],
        })
        if i % 5 == 0:
            print(f"Diagnosed {i}/25 SIFT alerts from caches; no source decoding, GT or F1", flush=True)
    controls = [r for r in rows if r["visual_decision_prior"] == "SAME_SCENE_CONFIRMED"]
    if len(controls) != 1 or controls[0]["multicue_id"] != "4113_left_0082":
        parser.error("Known positive image-only control absent")
    csvpath = root / "multicue_sift_mutual_validation_diagnostics.csv"
    with csvpath.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "status": "GEOMETRY_FALSE_POSITIVE_DIAGNOSTIC_ONLY",
        "prior_report": str(root / "multicue_all_uded_geometric_overlap_summary.json"),
        "cached_pairs_checked": len(rows),
        "confirmed_same_visible_frame_pair_count": len(controls),
        "visually_different_pair_count": sum(r["visual_decision_prior"] == "DIFFERENT_SCENE" for r in rows),
        "reference_positive_control": controls[0],
        "top_by_mutual_inliers": sorted(rows, key=lambda x: -x["mutual_ransac_inliers"])[:12],
        "csv": str(csvpath),
        "no_images_redecoded": True,
        "no_GT_H5_F1_opened": True,
        "no_cohort_exclusions_or_promotions": True,
        "warning": "Diagnostic geometry is not a new learned or validated scene-similarity classifier. Record any algorithmic fixes before dataset freeze.",
    }
    result = root / "multicue_sift_mutual_validation_diagnostics.json"
    result.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
