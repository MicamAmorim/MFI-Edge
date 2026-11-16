#!/usr/bin/env python3
"""Targeted image-only review of UDED 09-MDBD-1C versus 100 MultiCue sources.

Independent of F1/GT: reads only *original* UDED 09-MDBD-1C PNG
and previously materialized 100 MultiCue last-left source PNGs.
Ranks visual similarity by dHash and pHash, displays two review sheets.
The results CANNOT certify absence of same-scene lineage across other frames.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from audit_paper_a_multicue_image_overlap import (
    MULTICUE, ROOT, UDED_ROOT, font, hashes,
    prepare_targets, read_original, sha256,
)

SOURCE_NAME = "09-MDBD-1C.png"
COLUMNS = ["rank_dhash", "rank_phash", "sequence_id",
           "capture_prefix", "dhash_distance", "phash_distance",
           "target_sha256", "reference_sha256", "visual_review_status"]


def tile(img: Image.Image, title: str, stats: str, w=300, h=180) -> Image.Image:
    result = Image.new("RGB", (w, h + 56), "white")
    draw = ImageDraw.Draw(result)
    thumb = ImageOps.contain(img, (w - 12, h - 8), Image.Resampling.LANCZOS)
    result.paste(thumb, ((w - thumb.width) // 2, (h - thumb.height) // 2))
    draw.text((9, h + 4), title[:46], fill="#202020", font=font(16))
    draw.text((9, h + 28), stats[:58], fill="#3e3e3e", font=font(13))
    return result


def render_sheet(reference: Image.Image, target: list[dict], title: str,
                 filename: Path, top_k: int):
    cols, w, h, pad = 4, 300, 236, 18
    nrows = (top_k + cols - 1) // cols
    total_h = 320 + nrows * h
    sheet = Image.new("RGB", (cols * w + 2 * pad, total_h), "#f1f1f1")
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 8), title, font=font(24), fill="#1b1b1b")
    draw.text((pad, 39), "Source: UDED 09-MDBD-1C (prior development image; no GT)",
              font=font(15), fill="#444444")
    ref = ImageOps.contain(reference, (1000, 235), Image.Resampling.LANCZOS)
    sheet.paste(ref, ((sheet.width - ref.width) // 2, 72))
    for i, item in enumerate(target[:top_k]):
        col, row = i % cols, i // cols
        img = read_original(item["path"])
        metadata = (f"dHash {item['dhash_distance']}/64 | "
                    f"pHash {item['phash_distance']}/63")
        picture = tile(img, item["sequence_id"], metadata)
        sheet.paste(picture, (pad + col * w, 320 + row * h))
    sheet.save(filename)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--multicue-root", type=Path, default=MULTICUE)
    ap.add_argument("--top-k", type=int, default=12)
    args = ap.parse_args()
    if not 1 <= args.top_k <= 20:
        ap.error("Top K must be 1..20 to maintain readable local review sheets")

    multi = args.multicue_root.expanduser().resolve()
    previous = multi / "multicue_image_only_overlap_summary.json"
    if not previous.is_file():
        ap.error("Run audit_paper_a_multicue_image_overlap.py first")
    audit = json.loads(previous.read_text(encoding="utf-8"))
    if (audit.get("status") != "IMAGE_ONLY_OVERLAP_SCREEN_NOT_CERTIFIED"
        or audit.get("multicue_h5_anchored_sequences") != 100
        or audit.get("ground_truth_or_h5_opened") is not False
        or audit.get("model_or_f1_run") is not False):
        ap.error("Prior image-only overlap report is missing or unexpected")

    source = UDED_ROOT / SOURCE_NAME
    if not source.is_file():
        ap.error("Known historical UDED source is missing: " + str(source))
    # This specific named UDED case is not the protected BSDS test lineage.
    reference = read_original(source)
    reference_sha = sha256(source)
    rd, rp = hashes(reference)

    targets = prepare_targets(multi)
    ranked = []
    for target in targets:
        hd = (rd ^ target["dhash"]).bit_count()
        hp = (rp ^ target["phash"]).bit_count()
        ranked.append({
            **target,
            "dhash_distance": hd,
            "phash_distance": hp,
            "reference_sha256": reference_sha,
        })
    sort_d = sorted(ranked, key=lambda x: (x["dhash_distance"], x["phash_distance"], x["id"]))
    sort_p = sorted(ranked, key=lambda x: (x["phash_distance"], x["dhash_distance"], x["id"]))
    rankd = {r["id"]: i+1 for i, r in enumerate(sort_d)}
    rankp = {r["id"]: i+1 for i, r in enumerate(sort_p)}
    output_csv = multi / "multicue_uded09_ranked_image_only_review.csv"
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for item in sorted(ranked, key=lambda x: (rankd[x["id"]] + rankp[x["id"]], rankp[x["id"]], x["id"])):
            writer.writerow({
                "rank_dhash": rankd[item["id"]],
                "rank_phash": rankp[item["id"]],
                "sequence_id": item["id"],
                "capture_prefix": item["prefix"],
                "dhash_distance": item["dhash_distance"],
                "phash_distance": item["phash_distance"],
                "target_sha256": item["sha256"],
                "reference_sha256": reference_sha,
                "visual_review_status": "PENDING",
            })
    d_sheet = multi / "multicue_uded09_nearest_by_dhash.png"
    p_sheet = multi / "multicue_uded09_nearest_by_phash.png"
    render_sheet(reference, sort_d, "UDED 09-MDBD-1C | vizinhos por dHash",
                 d_sheet, args.top_k)
    render_sheet(reference, sort_p, "UDED 09-MDBD-1C | vizinhos por pHash",
                 p_sheet, args.top_k)

    report = {
        "status": "UDED_MDBD_LINEAGE_VISUAL_REVIEW_PENDING",
        "source_original": str(source),
        "source_sha256": reference_sha,
        "multicue_originals_ranked": len(ranked),
        "top_k_each_method": args.top_k,
        "ranked_csv": str(output_csv),
        "dhash_review_sheet": str(d_sheet),
        "phash_review_sheet": str(p_sheet),
        "top_dhash": [
            {"id": r["id"], "prefix": r["prefix"],
             "dhash": r["dhash_distance"], "phash": r["phash_distance"]}
            for r in sort_d[:args.top_k]
        ],
        "top_phash": [
            {"id": r["id"], "prefix": r["prefix"],
             "dhash": r["dhash_distance"], "phash": r["phash_distance"]}
            for r in sort_p[:args.top_k]
        ],
        "ground_truth_or_hdf5_opened": False,
        "f1_or_inference_run": False,
        "automatic_exclusions_made": 0,
        "cohort_confirmatory_eligible": False,
        "warning": (
            "Ranks are image-only aids for manual scene-lineage examination. "
            "They cannot rule out matching a DIFFERENT VIDEO FRAME, crops, "
            "heavy transformations, or outside-scene associations. "
            "Do not promote candidates or use F1 on this basis."
        ),
    }
    result = multi / "multicue_uded09_ranked_image_only_review.json"
    result.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
