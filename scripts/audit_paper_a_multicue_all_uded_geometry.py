#!/usr/bin/env python3
"""Cached SIFT lineage screen, 27 historical UDED originals x 100 MultiCue.

Original RGB images ONLY; never open GT, H5, maps, predictions or F1.
SIFT features and each UDED reference's comparisons are checkpointed on F:
to avoid recomputing after interruption. Flags require visual adjudication.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

import cv2
import numpy as np

from audit_paper_a_multicue_image_overlap import (
    MULTICUE, prepare_targets, prepare_uded,
)

ALGORITHM = "SIFT3500_max1280_FLANN_KDTree4_checks64_ratio077_RANSAC4_v1"
POSITIVE_UDED = "09-MDBD-1C"
POSITIVE_MULTICUE = "4113_left_0082"
COLUMNS = ["uded_original_id", "multicue_sequence_id", "capture_prefix",
           "ratio_matches", "ransac_inliers", "inlier_fraction",
           "homography_valid", "review_status"]


def digest_records(records):
    payload = "\n".join(sorted(x["id"] + "|" + x["sha256"] for x in records))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def features(record, cache, sift):
    destination = cache / ("sift_" + record["sha256"] + ".npz")
    if destination.exists():
        with np.load(destination, allow_pickle=False) as array:
            if (str(array["sha"].item()) != record["sha256"]
                    or str(array["algorithm"].item()) != ALGORITHM
                    or str(array["opencv"].item()) != cv2.__version__):
                raise ValueError("Feature cache provenance mismatch: " + str(destination))
            coords = np.asarray(array["coords"], dtype=np.float32)
            desc = np.asarray(array["desc"], dtype=np.float32)
        if coords.shape != (len(desc), 2) or desc.ndim != 2 or desc.shape[1] != 128:
            raise ValueError("Corrupted SIFT cache: " + str(destination))
        return coords, np.ascontiguousarray(desc)

    path = Path(record["path"])
    if not path.is_file() or path.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("Invalid original source image: " + str(path))
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None or not 8 <= image.shape[0] <= 10000 or not 8 <= image.shape[1] <= 10000:
        raise ValueError("Cannot decode safe original image: " + str(path))
    h, w = image.shape
    if max(h, w) > 1280:
        scale = 1280 / max(h, w)
        image = cv2.resize(image, (round(w * scale), round(h * scale)),
                           interpolation=cv2.INTER_AREA)
    keypoints, desc = sift.detectAndCompute(image, None)
    coords = np.asarray([p.pt for p in keypoints], dtype=np.float32).reshape(-1, 2)
    desc = (np.asarray(desc, dtype=np.float32).reshape(-1, 128)
            if desc is not None else np.empty((0, 128), dtype=np.float32))
    partial = destination.with_suffix(".npz.part")
    if partial.exists() and not destination.exists():
        partial.unlink()  # Safe removal of interrupted cache TEMP only
    try:
        with partial.open("xb") as out:
            np.savez_compressed(
                out, sha=record["sha256"], algorithm=ALGORITHM,
                opencv=cv2.__version__, coords=coords, desc=desc)
        os.replace(partial, destination)
    finally:
        if partial.exists():
            partial.unlink()
    return coords, np.ascontiguousarray(desc)


def flann_index(desc):
    if len(desc) < 4:
        return None
    index = cv2.FlannBasedMatcher(dict(algorithm=1, trees=4), dict(checks=64))
    index.add([desc])
    index.train()
    return index


def compare(a_xy, a_desc, b_xy, b_desc, index):
    if index is None or len(a_desc) < 4 or len(b_desc) < 4:
        return 0, 0, 0.0, False
    pairs = index.knnMatch(np.ascontiguousarray(a_desc), k=2)
    good = [p[0] for p in pairs if len(p) == 2
            and p[0].distance < 0.77 * p[1].distance]
    if len(good) < 4:
        return len(good), 0, 0.0, False
    a = a_xy[[p.queryIdx for p in good]].reshape(-1, 1, 2)
    b = b_xy[[p.trainIdx for p in good]].reshape(-1, 1, 2)
    cv2.setRNGSeed(20261115)
    H, mask = cv2.findHomography(a, b, cv2.RANSAC, 4.0,
                                 maxIters=3000, confidence=0.995)
    valid = bool(H is not None and np.isfinite(H).all()
                 and abs(float(np.linalg.det(H))) > 1e-8)
    inliers = int(mask.sum()) if valid and mask is not None else 0
    return len(good), inliers, round(inliers / len(good), 5), valid


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--multicue-root", type=Path, default=MULTICUE)
    args = ap.parse_args()
    root = args.multicue_root.expanduser().resolve()
    if root.drive and root.drive.lower() == Path.home().drive.lower():
        ap.error("Refusing to write research caches on the near-full system drive")
    prior_path = root / "multicue_uded09_geometric_overlap_summary.json"
    if not prior_path.is_file():
        ap.error("Run audit_paper_a_multicue_mdbd_geometry.py first")
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    if (prior.get("status") != "LOCAL_FEATURE_IMAGE_ONLY_REVIEW_NOT_CERTIFIED"
            or prior.get("multicue_originals_analyzed") != 100
            or prior.get("flag_count") != 1
            or prior.get("top_15", [{}])[0].get("sequence_id") != POSITIVE_MULTICUE
            or prior.get("gt_h5_f1_accessed") is not False):
        ap.error("Known original-image SIFT positive control missing")
    targets = prepare_targets(root)  # verifies 100 original image SHA256s
    uded, skipped = prepare_uded()   # protected BSDS-test lineage is not decoded
    if len(targets) != 100 or len(uded) != 27 or len(skipped) != 3:
        ap.error("Unexpected image-only counts; do not silently change scope")
    if not any(x["id"] == POSITIVE_UDED for x in uded):
        ap.error("Missing known UDED original positive control")
    cache = root / "predata_sift_cache"
    checkpoint_dir = cache / "reference_checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    manifest_digest = digest_records(targets)
    sift = cv2.SIFT_create(nfeatures=3500)

    target_feats = {}
    indexes = {}
    for i, target in enumerate(targets, 1):
        x, d = features(target, cache, sift)
        target_feats[target["id"]] = (x, d)
        indexes[target["id"]] = flann_index(d)
        if i % 25 == 0:
            print(f"Prepared {i}/100 MultiCue source features", flush=True)

    all_rows = []
    flags = []
    cache_hits = 0
    for number, reference in enumerate(uded, 1):
        checkpoint = checkpoint_dir / (reference["sha256"] + ".json")
        reused = checkpoint.exists()
        if reused:
            record = json.loads(checkpoint.read_text(encoding="utf-8"))
            rows = record.get("pairs", [])
            if (record.get("reference_id") != reference["id"]
                    or record.get("reference_sha256") != reference["sha256"]
                    or record.get("target_manifest_digest") != manifest_digest
                    or record.get("algorithm") != ALGORITHM
                    or record.get("opencv") != cv2.__version__
                    or record.get("gt_h5_f1_accessed") is not False
                    or len(rows) != 100
                    or {r["multicue_sequence_id"] for r in rows}
                    != {t["id"] for t in targets}):
                raise ValueError("Incompatible per-reference checkpoint: " + str(checkpoint))
            cache_hits += 1
        else:
            x, d = features(reference, cache, sift)
            rows = []
            for target in targets:
                tx, td = target_feats[target["id"]]
                matches, inliers, fraction, valid = compare(
                    x, d, tx, td, indexes[target["id"]])
                flagged = bool(valid and matches >= 15
                               and inliers >= 12 and fraction >= 0.55)
                rows.append({
                    "uded_original_id": reference["id"],
                    "multicue_sequence_id": target["id"],
                    "capture_prefix": target["prefix"],
                    "ratio_matches": matches,
                    "ransac_inliers": inliers,
                    "inlier_fraction": fraction,
                    "homography_valid": valid,
                    "review_status": ("REVIEW_LOCAL_FEATURE_MATCH" if flagged
                                      else "NO_LOCAL_FEATURE_FLAG")
                })
            contents = {
                "reference_id": reference["id"],
                "reference_sha256": reference["sha256"],
                "target_manifest_digest": manifest_digest,
                "algorithm": ALGORITHM,
                "opencv": cv2.__version__,
                "gt_h5_f1_accessed": False,
                "pairs": rows,
            }
            partial = checkpoint.with_suffix(".json.part")
            if partial.exists():
                partial.unlink()
            try:
                with partial.open("x", encoding="utf-8") as stream:
                    json.dump(contents, stream, ensure_ascii=False)
                os.replace(partial, checkpoint)
            finally:
                if partial.exists():
                    partial.unlink()
        all_rows.extend(rows)
        flags.extend(r for r in rows if r["review_status"] == "REVIEW_LOCAL_FEATURE_MATCH")
        print(f"UDED {number}/27: {reference['id']}; "
              f"flags={sum(r['review_status'] == 'REVIEW_LOCAL_FEATURE_MATCH' for r in rows)}; "
              f"checkpoint={'reused' if reused else 'saved'}", flush=True)

    control = next((r for r in all_rows
                    if r["uded_original_id"] == POSITIVE_UDED
                    and r["multicue_sequence_id"] == POSITIVE_MULTICUE), None)
    if control is None or control["review_status"] != "REVIEW_LOCAL_FEATURE_MATCH":
        raise RuntimeError("Known 4113 overlap was missed; cannot trust negative flags")
    csvpath = root / "multicue_all_uded_geometric_overlap_pairs.csv"
    with csvpath.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)
    report = {
        "status": "ALL_UDED_GEOMETRY_SCREEN_REVIEW_ONLY",
        "algorithm": ALGORITHM, "opencv": cv2.__version__,
        "multicue_frames": len(targets), "uded_history_originals": len(uded),
        "uded_protected_bsds_test_lineage_skipped": skipped,
        "image_only_pairs": len(all_rows),
        "reused_reference_checkpoints": cache_hits,
        "geometric_flags_total": len(flags),
        "flagged_uded_ids": sorted({r["uded_original_id"] for r in flags}),
        "flagged_multicue_prefixes": sorted({r["capture_prefix"] for r in flags}),
        "flags": sorted(flags, key=lambda r: (-r["ransac_inliers"], -r["inlier_fraction"]))[:100],
        "known_positive_control": control,
        "pairs_csv": str(csvpath),
        "sift_cache": str(cache),
        "gt_h5_model_f1_opened": False, "cohort_frozen": False,
        "automatic_exclusions": 0,
        "warning": (
            "Flags require visual review; missing flags do not prove independence. "
            "Only one annotated last-left frame per sequence was compared. "
            "Already-exposed capture prefix 4113 remains held in full."
        ),
    }
    (root / "multicue_all_uded_geometric_overlap_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
