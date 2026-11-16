#!/usr/bin/env python3
"""Render all 25 flagged original-image UDED/MultiCue pairs for human review.

INPUT: completed cached SIFT comparison CSV/JSON and verified image-only
original manifests. NO descriptor recomputation, no TAR re-read, GT, H5,
model predictions, F1, or scene exclusions. Writes contact sheets to F:.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from audit_paper_a_multicue_image_overlap import MULTICUE, UDED_ROOT
from audit_paper_a_multicue_all_uded_geometry import ALGORITHM, digest_records

REQUIRED_STATUS = "ALL_UDED_GEOMETRY_SCREEN_REVIEW_ONLY"
EXPECTED_POSITIVE = ("09-MDBD-1C", "4113_left_0082")
VALID_ID = re.compile(r"^[a-zA-Z0-9_-]+$")
OUTPUT_DIRECTORY = "multicue_uded_geometric_visual_review"
PAIR_COLUMNS = {"uded_original_id", "multicue_sequence_id", "capture_prefix",
                "ratio_matches", "ransac_inliers", "inlier_fraction",
                "homography_valid", "review_status"}
INDEX_COLUMNS = ["page", "position", "uded_original_id", "multicue_sequence_id",
                 "capture_prefix", "ratio_matches", "ransac_inliers",
                 "inlier_fraction", "prior_decision", "human_decision", "notes"]


def read_csv(path: Path, required: set[str]) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("Unexpected CSV structure: " + str(path))
        return list(reader)


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def get_font(size: int):
    for name in ("C:/Windows/Fonts/arial.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def load_photo(path: Path):
    if not path.is_file() or path.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("Original photo absent or unexpectedly large: " + str(path))
    with Image.open(path) as im:
        if im.width > 10000 or im.height > 10000:
            raise ValueError("Original photo dimensions outside safety limits")
        return ImageOps.exif_transpose(im).convert("RGB")


def render_page(items: list[dict], output: Path, page: int, pages: int):
    width, height = 1180, 180 + len(items) * 323
    canvas = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 12), f"Paper A | Revisao visual UDED x MultiCue | {page}/{pages}",
              font=get_font(26), fill="#1c1c1c")
    draw.text((20, 54),
              "Somente fotos originais; sem GT, F1 ou inferencia. SIFT = alerta, nao prova.",
              font=get_font(18), fill="#555555")
    draw.text((20, 92), "UDED historica (esquerda)", font=get_font(18), fill="#111111")
    draw.text((600, 92), "MultiCue frame original (direita)",
              font=get_font(18), fill="#111111")
    for i, item in enumerate(items):
        y = 128 + i * 323
        positive = (item["uded_original_id"],
                    item["multicue_sequence_id"]) == EXPECTED_POSITIVE
        draw.rectangle((12, y-5, width-12, y+310),
                       outline="#25835e" if positive else "#bdbdbd", width=3 if positive else 1)
        head = (f"{item['uded_original_id']}  x  {item['multicue_sequence_id']}"
                f"  |  {item['ransac_inliers']}/{item['ratio_matches']} inliers"
                f"  |  {100 * float(item['inlier_fraction']):.1f}%")
        draw.text((22, y+2), head, font=get_font(19),
                  fill="#186242" if positive else "#151515")
        if positive:
            draw.text((970, y+3), "EXPOSTA", font=get_font(18), fill="#186242")
        for col, key in enumerate(("uded_path", "multicue_path")):
            original = load_photo(Path(item[key]))
            thumb = ImageOps.contain(original, (550, 244), Image.Resampling.LANCZOS)
            xleft = 22 + col * 580
            canvas.paste(thumb, (xleft + (550 - thumb.width)//2,
                                 y + 35 + (244 - thumb.height)//2))
        draw.text((22, y+286), "Decisao visual: MESMA CENA / DIFERENTE / INCERTO",
                  font=get_font(14), fill="#505050")
    canvas.save(output, optimize=True)


def load_verified_inputs(root: Path):
    result_path = root / "multicue_all_uded_geometric_overlap_summary.json"
    report = json.loads(result_path.read_text(encoding="utf-8"))
    if (report.get("status") != REQUIRED_STATUS
            or report.get("algorithm") != ALGORITHM
            or report.get("image_only_pairs") != 2700
            or report.get("multicue_frames") != 100
            or report.get("uded_history_originals") != 27
            or report.get("gt_h5_model_f1_opened") is not False
            or report.get("cohort_frozen") is not False
            or report.get("automatic_exclusions") != 0):
        raise ValueError("Invalid image-only geometry report; cannot render")
    if len(report.get("uded_protected_bsds_test_lineage_skipped", [])) != 3:
        raise ValueError("Protected UDED source lineage unexpectedly changed")
    pairs_csv = Path(report["pairs_csv"]).resolve()
    if pairs_csv != (root / "multicue_all_uded_geometric_overlap_pairs.csv").resolve():
        raise ValueError("Unexpected geometric comparison CSV path")
    pairs = read_csv(pairs_csv, PAIR_COLUMNS)
    if len(pairs) != 2700:
        raise ValueError("Incomplete UDED x MultiCue comparisons")
    flagged = [r for r in pairs if r["review_status"] == "REVIEW_LOCAL_FEATURE_MATCH"]
    if len(flagged) != report["geometric_flags_total"] or len(flagged) != len(report["flags"]):
        raise ValueError("Flags in pair CSV disagree with audit summary")
    pairs_by_id = {(r["uded_original_id"], r["multicue_sequence_id"]): r for r in pairs}
    if len(pairs_by_id) != 2700 or EXPECTED_POSITIVE not in pairs_by_id:
        raise ValueError("Missing/duplicated comparison keys or positive control")
    for row in report["flags"]:
        key = (row["uded_original_id"], row["multicue_sequence_id"])
        if key not in pairs_by_id or pairs_by_id[key]["review_status"] != "REVIEW_LOCAL_FEATURE_MATCH":
            raise ValueError("Flagged pair mismatch in source CSV")
    source_manifest = read_csv(
        root / "multicue_source_frames_only_manifest.csv",
        {"sequence_id", "capture_prefix", "local_original_frame_path", "sha256"}
    )
    by_sequence = {r["sequence_id"]: r for r in source_manifest}
    if len(source_manifest) != 100 or len(by_sequence) != 100:
        raise ValueError("Incomplete source-only MultiCue manifest")
    checkpoint_dir = root / "predata_sift_cache" / "reference_checkpoints"
    references = {}
    for path in checkpoint_dir.glob("*.json"):
        checkpoint = json.loads(path.read_text(encoding="utf-8"))
        uid = checkpoint.get("reference_id")
        if (checkpoint.get("algorithm") != ALGORITHM
                or checkpoint.get("gt_h5_f1_accessed") is not False
                or not isinstance(uid, str) or not VALID_ID.fullmatch(uid)
                or uid in references):
            raise ValueError("Incorrect or conflicting UDED checkpoint: " + str(path))
        references[uid] = checkpoint
    if len(references) != 27:
        raise ValueError("Expected 27 cached historical UDED references")
    if not all(r["uded_original_id"] in references for r in flagged):
        raise ValueError("Flagged UDED original is absent from provenance checkpoints")

    linked = []
    for r in flagged:
        id1, id2 = r["uded_original_id"], r["multicue_sequence_id"]
        if not VALID_ID.fullmatch(id1) or id2 not in by_sequence:
            raise ValueError("Unexpected original image ID")
        reference = (UDED_ROOT / (id1 + ".png")).resolve()
        if reference.parent != UDED_ROOT.resolve():
            raise ValueError("Unsafe UDED reference path")
        target = Path(by_sequence[id2]["local_original_frame_path"]).resolve()
        if target.parent != (root / "source_frames_only").resolve():
            raise ValueError("Unsafe MultiCue source path")
        if r["capture_prefix"] != by_sequence[id2]["capture_prefix"]:
            raise ValueError("Capture-prefix mismatch")
        if sha256(reference) != references[id1]["reference_sha256"]:
            raise ValueError("Changed historical UDED original: " + id1)
        if sha256(target) != by_sequence[id2]["sha256"]:
            raise ValueError("Changed original MultiCue frame: " + id2)
        linked.append({
            **r, "uded_path": str(reference),
            "multicue_path": str(target)
        })
    linked.sort(key=lambda r: (-int(r["ransac_inliers"]),
                               -float(r["inlier_fraction"]),
                               r["uded_original_id"], r["multicue_sequence_id"]))
    return report, linked


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--multicue-root", type=Path, default=MULTICUE)
    ap.add_argument("--pairs-per-page", type=int, default=5)
    args = ap.parse_args()
    if not 1 <= args.pairs_per_page <= 6:
        ap.error("Choose 1..6 pairs per page")
    root = args.multicue_root.expanduser().resolve()
    if root.drive and root.drive.lower() == Path.home().drive.lower():
        ap.error("Keep review outputs off the near-full C: drive")
    report, flags = load_verified_inputs(root)
    directory = root / OUTPUT_DIRECTORY
    if directory.exists() and any(directory.iterdir()):
        ap.error("Refusing to overwrite nonempty review directory; inspect existing sheets")
    directory.mkdir(parents=True, exist_ok=True)
    pages = math.ceil(len(flags) / args.pairs_per_page)
    index = []
    for p in range(pages):
        rows = flags[p * args.pairs_per_page:(p + 1) * args.pairs_per_page]
        filename = directory / f"review_{p+1:02d}_of_{pages:02d}.png"
        render_page(rows, filename, p+1, pages)
        for k, row in enumerate(rows, 1):
            positive = (row["uded_original_id"], row["multicue_sequence_id"]) == EXPECTED_POSITIVE
            index.append({
                "page": p+1, "position": k,
                "uded_original_id": row["uded_original_id"],
                "multicue_sequence_id": row["multicue_sequence_id"],
                "capture_prefix": row["capture_prefix"],
                "ratio_matches": row["ratio_matches"],
                "ransac_inliers": row["ransac_inliers"],
                "inlier_fraction": row["inlier_fraction"],
                "prior_decision": ("EXCLUDE_PRIOR_EXPOSURE" if positive
                                   else "PENDING_MANUAL_REVIEW"),
                "human_decision": ("SAME_SCENE_CONFIRMED" if positive else ""),
                "notes": ("Known UDED 09-MDBD source-image exposure" if positive else ""),
            })
        print(f"Review page {p+1}/{pages} generated | {len(rows)} image pairs", flush=True)
    decisions = directory / "human_review_template.csv"
    with decisions.open("w", encoding="utf-8-sig", newline="") as dest:
        writer = csv.DictWriter(dest, fieldnames=INDEX_COLUMNS)
        writer.writeheader()
        writer.writerows(index)
    summary = {
        "status": "MANUAL_SCENE_OVERLAP_REVIEW_PENDING",
        "prior_geometry_status": report["status"],
        "pair_count": len(flags),
        "review_pages": pages,
        "images_per_page": args.pairs_per_page,
        "directory": str(directory),
        "page_files": [str(directory / f"review_{p+1:02d}_of_{pages:02d}.png")
                       for p in range(pages)],
        "manual_decisions_csv": str(decisions),
        "known_prior_exposure": "09-MDBD-1C versus 4113_left_0082",
        "additional_scene_exclusions_made": 0,
        "gt_h5_model_f1_accessed": False,
        "cohort_frozen": False,
        "instructions": [
            "Inspect each pair for same underlying scene, including cropping",
            "Record SAME_SCENE, DIFFERENT_SCENE, or UNCERTAIN in the review CSV",
            "Keep all flagged prefixes on review-hold until documented",
            "No automatic exclusion; review does not certify unseen frames",
        ],
    }
    (directory / "review_sheet_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
