#!/usr/bin/env python3
"""Image-only overlap screening for MultiCue versus previously used UDED + BIPED.

Uses ONLY 100 pre-extracted MultiCue original left frames, original UDED inputs
(excluding protected BSDS-test-lineage files from decoding) and 198 eligible-
for-review BIPED train originals. No GT, HDF5, masks, predictions, F1, model
inference, or pretrained embeddings. Flags are NOT automatic exclusions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MULTICUE = Path(r"F:\MFI-Edge-Data\MultiCue")
BIPED_ROOT = ROOT / "datasets/BIPEDv2/edges/imgs/train/rgbr/real"
BIPED_LIST = ROOT / "results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv"
UDED_ROOT = ROOT / "external/UDED/imgs"
BSDS_TEST = ROOT / "datasets/BSDS500/images/test"
SAFE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
EXCLUDE_SEGMENTS = {"test", "ground-truth", "ground_truth", "gt", "edge_maps",
                    "labels", "masks", "annotations", "predictions", "results"}
COS = [
    [math.cos((2 * n + 1) * k * math.pi / 64) for n in range(32)]
    for k in range(8)
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def hashes(image: Image.Image) -> tuple[int, int]:
    gray = image.convert("L")
    small = list(gray.resize((9, 8), Image.Resampling.LANCZOS).getdata())
    dh = 0
    for r in range(8):
        for c in range(8):
            dh = (dh << 1) | int(small[r * 9 + c] > small[r * 9 + c + 1])
    values = list(gray.resize((32, 32), Image.Resampling.LANCZOS).getdata())
    # 8x8 low-frequency 2D-DCT on a 32x32 grayscale thumbnail.
    horiz = [[sum(values[r * 32 + x] * COS[u][x] for x in range(32))
              for u in range(8)] for r in range(32)]
    coeff = [sum(COS[v][y] * horiz[y][u] for y in range(32))
             for v in range(8) for u in range(8)]
    reference = median(coeff[1:])  # Exclude the DC term.
    ph = 0
    for x in coeff[1:]:
        ph = (ph << 1) | int(x > reference)
    return dh, ph


def read_original(path: Path) -> Image.Image:
    if not path.is_file() or path.suffix.lower() not in SAFE_SUFFIXES:
        raise ValueError(f"Missing or unsupported original image: {path}")
    if path.stat().st_size > 25 * 1024 * 1024:
        raise ValueError(f"Image safety limit exceeded: {path}")
    with Image.open(path) as src:
        img = ImageOps.exif_transpose(src)
        if img.width > 10000 or img.height > 10000:
            raise ValueError("Excessive original image dimensions")
        return img.convert("RGB")


def load_csv(path: Path, fields: set[str]) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not fields.issubset(reader.fieldnames):
            raise ValueError(f"Bad inventory schema: {path}")
        return list(reader)


def font(size: int):
    choices = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for choice in choices:
        if choice.is_file():
            return ImageFont.truetype(str(choice), size)
    return ImageFont.load_default()


def prepare_targets(multi: Path) -> list[dict]:
    summary = json.loads((multi / "multicue_source_frames_only_summary.json").read_text(encoding="utf-8"))
    csvpath = multi / "multicue_source_frames_only_manifest.csv"
    if (summary.get("status") != "ORIGINAL_SOURCE_FRAMES_ONLY_OVERLAP_AUDIT_PENDING"
            or summary.get("original_left_frames_materialized") != 100
            or Path(summary.get("manifest_csv", "")).resolve() != csvpath
            or summary.get("ground_truth_members_extracted") != 0
            or summary.get("h5_members_extracted") != 0):
        raise ValueError("Original source-frame materialization was not verified")
    rows = load_csv(csvpath, {"sequence_id", "capture_prefix", "local_original_frame_path",
                              "sha256", "overlap_review_status"})
    if len(rows) != 100 or len({x["sequence_id"] for x in rows}) != 100:
        raise ValueError("Expected 100 unique sequence anchors")
    expected_dir = (multi / "source_frames_only").resolve()
    targets = []
    for r in rows:
        path = Path(r["local_original_frame_path"]).resolve()
        if path.parent != expected_dir or r["overlap_review_status"] != "PENDING":
            raise ValueError("Unexpected target path or changed candidate status")
        if sha256(path) != r["sha256"].lower():
            raise ValueError(f"Source original frame SHA mismatch: {path}")
        im = read_original(path)
        d, p = hashes(im)
        targets.append({
            "group": "MultiCue", "id": r["sequence_id"],
            "prefix": r["capture_prefix"], "path": path,
            "sha256": r["sha256"].lower(), "dhash": d, "phash": p,
        })
    return targets


def prepare_uded() -> tuple[list[dict], list[str]]:
    protected = {"35028"} | {
        p.stem for p in BSDS_TEST.iterdir() if p.is_file() and p.suffix.lower() in SAFE_SUFFIXES
    } if BSDS_TEST.is_dir() else {"35028"}
    def restricted(stem: str):
        return any(stem == x or stem.endswith("-" + x) for x in protected)
    candidates = sorted(p for p in UDED_ROOT.iterdir()
                        if p.is_file() and p.suffix.lower() in SAFE_SUFFIXES)
    if len(candidates) != 30:
        raise ValueError(f"Expected 30 UDED source originals, saw {len(candidates)}")
    skipped = []
    results = []
    for path in candidates:
        if restricted(path.stem):
            skipped.append(path.name)
            continue
        digest = sha256(path)
        d, ph = hashes(read_original(path))
        results.append({"group": "UDED_prior_development", "id": path.stem,
                        "prefix": path.stem, "path": path,
                        "sha256": digest, "dhash": d, "phash": ph})
    return results, skipped


def prepare_biped() -> list[dict]:
    rows = load_csv(BIPED_LIST, {
        "image_id", "relative_path", "sha256", "confirmatory_eligibility"
    })
    if len(rows) != 198:
        raise ValueError("Expected 198 BIPED train candidates after visual dedup")
    results = []
    for row in rows:
        rel = Path(row["relative_path"])
        if rel.is_absolute() or ".." in rel.parts or EXCLUDE_SEGMENTS.intersection(
                part.lower() for part in rel.parts):
            raise ValueError("Unsafe BIPED original relative path")
        path = (BIPED_ROOT / rel).resolve()
        if path.parent != BIPED_ROOT.resolve():
            raise ValueError("BIPED original source has unexpected parent")
        if row["confirmatory_eligibility"] != "PENDING_HISTORICAL_AND_SCENE_LINEAGE_AUDIT":
            raise ValueError("Prematurely approved BIPED candidate")
        if sha256(path) != row["sha256"].lower():
            raise ValueError("BIPED original hash mismatch: " + str(path))
        d, ph = hashes(read_original(path))
        results.append({"group": "BIPED_train", "id": row["image_id"],
                        "prefix": row["image_id"], "path": path,
                        "sha256": row["sha256"].lower(), "dhash": d, "phash": ph})
    return results


def create_sheet(targets: list[dict], uded: list[dict], outfile: Path):
    # An image-only scene overview for manual examination. No GT labels.
    W, TW, TH, COLS = 250, 235, 168, 10
    scene_rows = 10
    preview = Image.new("RGB", (COLS * W, (scene_rows + 1) * TH + 45), "#ffffff")
    d = ImageDraw.Draw(preview)
    d.text((14, 7), "MultiCue — 100 quadros originais esquerdos | sem GT", font=font(22), fill="#1b1b1b")
    for i, record in enumerate(sorted(targets, key=lambda x: x["id"])):
        img = read_original(record["path"])
        thumb = ImageOps.contain(img, (TW - 10, TH - 35))
        col, row = i % COLS, i // COLS
        preview.paste(thumb, (col * W + (W - thumb.width) // 2,
                              43 + row * TH))
        d.text((col * W + 5, 43 + row * TH + TH - 32),
               record["id"], font=font(13), fill="#181818")
    anchor = next((x for x in uded if x["id"] == "09-MDBD-1C"), None)
    if anchor:
        img = read_original(anchor["path"])
        thumb = ImageOps.contain(img, (TW - 10, TH - 35))
        y = 43 + scene_rows * TH
        preview.paste(thumb, ((W - thumb.width) // 2, y))
        d.text((5, y + TH - 32), "UDED 09-MDBD-1C (historico)", font=font(13), fill="#181818")
    preview.save(outfile)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--multicue-root", type=Path, default=MULTICUE)
    ap.add_argument("--dhash-distance", type=int, default=7)
    ap.add_argument("--phash-distance", type=int, default=10)
    args = ap.parse_args()
    if not (0 <= args.dhash_distance <= 12 and 0 <= args.phash_distance <= 16):
        ap.error("Perceptual thresholds out of allowed pre-data audit range")
    multi = args.multicue_root.expanduser().resolve()
    targets = prepare_targets(multi)
    uded, skipped = prepare_uded()
    biped = prepare_biped()
    all_others = uded + biped
    findings = []
    flagged_targets = defaultdict(list)
    exacts = defaultdict(list)

    def compare(a, b):
        d = (a["dhash"] ^ b["dhash"]).bit_count()
        p = (a["phash"] ^ b["phash"]).bit_count()
        exact = a["sha256"] == b["sha256"]
        return d, p, exact

    # Cross-domain historical exposure and BIPED domain leakage.
    for a in targets:
        for b in all_others:
            dist_d, dist_p, exact = compare(a, b)
            if exact or dist_d <= args.dhash_distance or dist_p <= args.phash_distance:
                flag = {
                    "multicue_sequence": a["id"],
                    "multicue_capture_prefix": a["prefix"],
                    "other_domain": b["group"],
                    "other_id": b["id"],
                    "dhash_distance": dist_d,
                    "phash_distance": dist_p,
                    "exact_sha256": exact,
                    "review": "BLOCK_EXACT" if exact else "REVIEW_VISUALLY",
                }
                findings.append(flag)
                flagged_targets[a["id"]].append(flag)
                if exact:
                    exacts[a["id"]].append(flag)
    # Between distinct prefixes: flag visual similarities. Same-prefix groups
    # are structurally held separately, without requiring a perceptual match.
    for i, a in enumerate(targets):
        for b in targets[i+1:]:
            if a["prefix"] == b["prefix"]:
                continue
            dist_d, dist_p, exact = compare(a, b)
            if exact or dist_d <= args.dhash_distance or dist_p <= args.phash_distance:
                flag = {
                    "multicue_sequence": a["id"], "multicue_capture_prefix": a["prefix"],
                    "other_domain": "MultiCue_other_capture",
                    "other_id": b["id"], "dhash_distance": dist_d,
                    "phash_distance": dist_p, "exact_sha256": exact,
                    "review": "BLOCK_EXACT" if exact else "REVIEW_VISUALLY",
                }
                findings.append(flag)
                flagged_targets[a["id"]].append(flag)
                flagged_targets[b["id"]].append(flag)
                if exact:
                    exacts[a["id"]].append(flag)
                    exacts[b["id"]].append(flag)

    groups = Counter(x["prefix"] for x in targets)
    output = multi / "multicue_image_only_overlap_flags.csv"
    with output.open("w", encoding="utf-8", newline="") as f:
        fields = ["multicue_sequence", "multicue_capture_prefix", "other_domain",
                  "other_id", "dhash_distance", "phash_distance", "exact_sha256", "review"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(findings)
    sheet = multi / "multicue_image_only_100_scene_review.png"
    create_sheet(targets, uded, sheet)
    report = {
        "status": "IMAGE_ONLY_OVERLAP_SCREEN_NOT_CERTIFIED",
        "multicue_h5_anchored_sequences": len(targets),
        "multicue_capture_prefixes": len(groups),
        "reused_prefix_groups": {k: v for k, v in sorted(groups.items()) if v > 1},
        "uded_previously_seen_originals_compared": len(uded),
        "uded_protected_bsds_test_lineage_skipped_from_decoding": skipped,
        "biped_train_individuals_compared": len(biped),
        "dhash_flag_distance": args.dhash_distance,
        "phash_flag_distance": args.phash_distance,
        "potential_pair_matches_for_manual_review": len(findings),
        "multicue_sequence_ids_with_flags": len(flagged_targets),
        "multicue_sequences_with_exact_sha_collisions": sorted(exacts),
        "flags_by_other_domain": dict(Counter(x["other_domain"] for x in findings)),
        "closest_uded_flags": sorted(
            [x for x in findings if x["other_domain"] == "UDED_prior_development"],
            key=lambda x: (x["phash_distance"], x["dhash_distance"]))[:30],
        "flags_csv": str(output),
        "all_scenes_review_sheet": str(sheet),
        "ground_truth_or_h5_opened": False,
        "model_or_f1_run": False,
        "cohort_eligible_or_frozen": False,
        "caveats": [
            "Flags are broad visual-similarity warnings, not duplicate proof",
            "No flag is not a proof of scene independence or non-exposure",
            "Protected BSDS test lineage was not perceptually decoded",
            "All reused MultiCue capture prefixes remain held pending independence review",
            "Exclusions/representatives must be documented before the confirmatory freeze",
        ],
    }
    outfile = multi / "multicue_image_only_overlap_summary.json"
    outfile.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
