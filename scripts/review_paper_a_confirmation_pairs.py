#!/usr/bin/env python3
"""Create an image-only visual review sheet for BIPED train dHash warnings.

Reads only original BIPED TRAIN images and the candidate_review.csv from the
predata audit. Does NOT open GT, BIPED test, BSDS test, evaluate, or certify.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = ROOT / "results/local_dev/paper_a_confirmation_inventory/predata_audit/candidate_review.csv"
DEFAULT_IMAGES = ROOT / "datasets/BIPEDv2/edges/imgs/train/rgbr/real"
DEFAULT_OUT = ROOT / "results/local_dev/paper_a_confirmation_inventory/predata_audit"
DISALLOWED = {"test", "edge_maps", "gt", "ground_truth", "labels", "masks", "annotations", "results"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def font(size: int):
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    ]
    for p in candidates:
        if p.is_file():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def dhash(img: Image.Image) -> int:
    px = list(img.convert("L").resize((9, 8), Image.Resampling.LANCZOS).getdata())
    value = 0
    for row in range(8):
        for col in range(8):
            value = (value << 1) | int(px[row * 9 + col] > px[row * 9 + col + 1])
    return value


def safe_original(root: Path, row: dict) -> Path:
    relative = Path(row["relative_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Unsafe image path in predata CSV")
    if DISALLOWED.intersection(x.lower() for x in relative.parts):
        raise ValueError("Prohibited image source folder in predata CSV")
    p = root / relative
    if not p.is_file() or sha256(p) != row["sha256"].lower():
        raise ValueError(f"Missing/changed image: {relative}")
    return p


def render_tile(img: Image.Image, title: str, subtitle: str, box_w=680, image_h=390):
    pad = 14
    result = Image.new("RGB", (box_w, image_h + 90), "#f2f2f2")
    d = ImageDraw.Draw(result)
    d.text((pad, 8), title, fill="#151515", font=font(26))
    d.text((pad, 43), subtitle, fill="#4e4e4e", font=font(15))
    fitted = ImageOps.contain(img.convert("RGB"), (box_w - 2 * pad, image_h - 10))
    x = (box_w - fitted.width) // 2
    y = 80 + (image_h - fitted.height) // 2
    result.paste(fitted, (x, y))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    ap.add_argument("--images", type=Path, default=DEFAULT_IMAGES)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    source = args.images.resolve()
    if not source.is_dir() or DISALLOWED.intersection(p.lower() for p in source.parts):
        ap.error("Only an original TRAIN image directory is permitted")
    if "train" not in {p.lower() for p in source.parts}:
        ap.error("Expected a train image root, never a test or ground-truth directory")

    with args.inventory.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or not {"image_id", "relative_path", "sha256", "near_image_flags", "status"}.issubset(rows[0]):
        ap.error("Unexpected inventory schema; run audit_paper_a_confirmation_predata.py first")
    selected = {r["image_id"]: r for r in rows}
    edges = set()
    for r in rows:
        if r["status"] != "REVIEW_NEAR_DUPLICATE":
            continue
        for flag in r["near_image_flags"].split("|"):
            if flag.startswith("BIPED_train:"):
                other = flag.split(":", 1)[1]
                if other not in selected:
                    raise ValueError(f"Referenced candidate ID not present: {other}")
                if r["image_id"] != other:
                    edges.add(tuple(sorted((r["image_id"], other))))
    if not edges:
        print(json.dumps({"status": "NO_WITHIN_TRAIN_PAIRS", "message": "No BIPED_train pairs in audit CSV"}, indent=2))
        return 0
    if len(edges) > 20:
        ap.error("Too many pairs for manual review sheet; inspect CSV first")

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    W, H = 1420, 610
    sheet = Image.new("RGB", (W, H * len(edges) + 70), "#ffffff")
    textdraw = ImageDraw.Draw(sheet)
    textdraw.text((22, 14), "BIPED train | revisao visual de pares suspeitos | SEM GT", fill="#202020", font=font(24))
    reports = []
    for k, (ida, idb) in enumerate(sorted(edges), start=1):
        pa, pb = safe_original(source, selected[ida]), safe_original(source, selected[idb])
        with Image.open(pa) as imga, Image.open(pb) as imgb:
            a = ImageOps.exif_transpose(imga).convert("RGB")
            b = ImageOps.exif_transpose(imgb).convert("RGB")
            distance = (dhash(a) ^ dhash(b)).bit_count()
            y = 70 + (k - 1) * H
            d = ImageDraw.Draw(sheet)
            d.text((22, y + 6), f"PAR {k} | dHash distancia de Hamming = {distance}/64", fill="#202020", font=font(21))
            for j, (id, img, row) in enumerate(((ida, a, selected[ida]), (idb, b, selected[idb]))):
                title = f"{id}  ({img.width} x {img.height})"
                subtitle = f"SHA256: {row['sha256'][:16]}...   |   imagem original, sem anotacao"
                tile = render_tile(img, title, subtitle)
                sheet.paste(tile, (22 + j * 700, y + 60))
            reports.append({
                "pair": k, "image_a": ida, "image_b": idb,
                "dhash_distance": distance, "decision": "PENDING",
                "same_scene": "PENDING", "same_sequence": "PENDING",
                "notes": "Inspect manually; no automatic removal or inclusion"
            })
    output_image = out / "biped_train_near_duplicate_review.png"
    sheet.save(output_image)
    output_csv = out / "biped_train_near_duplicate_decisions.csv"
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(reports[0]))
        writer.writeheader()
        writer.writerows(reports)
    print(json.dumps({
        "status": "MANUAL_REVIEW_REQUIRED", "pairs": len(reports),
        "original_images_loaded": len(edges) * 2,
        "review_image": str(output_image),
        "decisions_template": str(output_csv),
        "pair_details": reports,
        "note": "No GT/test images accessed; keep decisions pending until visual and historical-lineage review"
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
