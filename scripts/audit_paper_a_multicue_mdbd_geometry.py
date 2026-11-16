#!/usr/bin/env python3
"""Image-only local-feature overlap audit of UDED 09-MDBD-1C vs MultiCue.

Reads original RGB images only (never GT, H5, predictions, F1). Existing
image-only MultiCue manifest and SHA256 are revalidated. SIFT+RANSAC
supplies candidates for review; automated output does not certify lineage.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np

from audit_paper_a_multicue_image_overlap import MULTICUE, UDED_ROOT, prepare_targets

REFERENCE = UDED_ROOT / "09-MDBD-1C.png"
COLS = ["sequence_id", "capture_prefix", "sift_keypoints_uded",
        "sift_keypoints_multicue", "ratio_matches", "ransac_inliers",
        "inlier_fraction", "homography_valid", "review_status"]


def load_grayscale(path: Path, max_edge: int = 1280):
    raw = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if raw is None or not 8 <= raw.shape[0] <= 10000 or not 8 <= raw.shape[1] <= 10000:
        raise ValueError(f"Invalid source image (not GT): {path}")
    h, w = raw.shape[:2]
    if max(h, w) > max_edge:
        scale = max_edge / max(h, w)
        raw = cv2.resize(raw, (round(w * scale), round(h * scale)),
                         interpolation=cv2.INTER_AREA)
    return raw


def match_pair(a: np.ndarray, b: np.ndarray, sift=None, reference_features=None):
    if sift is None:
        sift = cv2.SIFT_create(nfeatures=3500)
    points_a, desc_a = (reference_features if reference_features is not None
                        else sift.detectAndCompute(a, None))
    points_b, desc_b = sift.detectAndCompute(b, None)
    n1, n2 = len(points_a), len(points_b)
    if desc_a is None or desc_b is None or n1 < 4 or n2 < 4:
        return (n1, n2, 0, 0, 0.0, False)
    matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    pairings = matcher.knnMatch(desc_a, desc_b, k=2)
    good = [pair[0] for pair in pairings if len(pair) == 2
            and pair[0].distance < 0.77 * pair[1].distance]
    if len(good) < 4:
        return (n1, n2, len(good), 0, 0.0, False)
    a_points = np.float32([points_a[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    b_points = np.float32([points_b[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(a_points, b_points, cv2.RANSAC, 4.0,
                                 maxIters=3000, confidence=0.995)
    inliers = int(mask.sum()) if H is not None and mask is not None else 0
    valid = H is not None and bool(np.isfinite(H).all()) and abs(float(np.linalg.det(H))) > 1e-8
    return (n1, n2, len(good), inliers, round(inliers / len(good), 5), valid)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--multicue-root", type=Path, default=MULTICUE)
    ap.add_argument("--reference", type=Path, default=REFERENCE)
    args = ap.parse_args()
    root = args.multicue_root.expanduser().resolve()
    reference = args.reference.expanduser().resolve()
    if reference != REFERENCE.resolve():
        ap.error("Only the historical original UDED 09-MDBD-1C is allowed as reference")
    if not hasattr(cv2, "SIFT_create"):
        ap.error("This OpenCV lacks SIFT; use an isolated venv with opencv-python")
    targets = prepare_targets(root)
    ref = load_grayscale(reference)
    sift = cv2.SIFT_create(nfeatures=3500)
    reference_features = sift.detectAndCompute(ref, None)
    rows = []
    for i, target in enumerate(targets, 1):
        image = load_grayscale(target["path"])
        n1, n2, matches, inliers, frac, valid = match_pair(
            ref, image, sift=sift, reference_features=reference_features)
        flag = bool(valid and matches >= 15 and inliers >= 12 and frac >= 0.55)
        rows.append({
            "sequence_id": target["id"], "capture_prefix": target["prefix"],
            "sift_keypoints_uded": n1, "sift_keypoints_multicue": n2,
            "ratio_matches": matches, "ransac_inliers": inliers,
            "inlier_fraction": frac, "homography_valid": valid,
            "review_status": "REVIEW_LOCAL_FEATURE_MATCH" if flag else "NO_LOCAL_FEATURE_FLAG",
        })
        if i % 20 == 0:
            print(f"SIFT checked {i}/100 original frames (no GT/F1)", flush=True)
    rows.sort(key=lambda row: (-row["ransac_inliers"], -row["inlier_fraction"], row["sequence_id"]))
    csv_path = root / "multicue_uded09_geometric_overlap_candidates.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLS)
        writer.writeheader()
        writer.writerows(rows)
    top = [{k: r[k] for k in ("sequence_id", "capture_prefix", "ratio_matches",
                              "ransac_inliers", "inlier_fraction", "review_status")}
           for r in rows[:15]]
    report = {
        "status": "LOCAL_FEATURE_IMAGE_ONLY_REVIEW_NOT_CERTIFIED",
        "source_reference_original": str(reference),
        "multicue_originals_analyzed": len(rows),
        "flag_count": sum(r["review_status"] == "REVIEW_LOCAL_FEATURE_MATCH" for r in rows),
        "top_15": top,
        "csv": str(csv_path),
        "gt_h5_f1_accessed": False,
        "no_automatic_exclusions": True,
        "cohort_frozen": False,
        "limitations": [
            "SIFT/RANSAC flags require review; weak texture and major transformations can be missed",
            "Only 100 final-left frames, not all frames or alternate MDBD archives, were searched",
            "Historical UDED 09-MDBD-1C visually matches MultiCue 4113_left_0082; hold entire capture prefix",
        ],
    }
    (root / "multicue_uded09_geometric_overlap_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
