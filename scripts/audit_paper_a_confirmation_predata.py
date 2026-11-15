#!/usr/bin/env python3
"""Pre-outcome audit of original images ONLY. Never opens GT, edge maps or F1.

This tool flags exact and visual-near duplicates but cannot certify independence.
The BSDS test and BIPED test files are read solely for raw SHA256 (no decoding).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None
    ImageOps = None

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = ROOT / "results/local_dev/paper_a_confirmation_inventory/candidates.csv"
DEFAULT_OUTPUT = ROOT / "results/local_dev/paper_a_confirmation_inventory/predata_audit"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
SKIP_DIRS = {"gt", "gts", "ground_truth", "groundtruth", "edge_maps", "labels",
             "masks", "annotations", "outputs", "predictions", "results"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def dhash(path: Path) -> int | None:
    if Image is None:
        return None
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        gray = im.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(gray.getdata())
    result = 0
    for row in range(8):
        for col in range(8):
            result = (result << 1) | int(pixels[row * 9 + col] > pixels[row * 9 + col + 1])
    return result


def original_files(folder: Path):
    if not folder.is_dir():
        return []
    if SKIP_DIRS.intersection({x.lower() for x in folder.parts}):
        raise ValueError(f"Refusing ground-truth/output root: {folder}")
    return sorted(p for p in folder.rglob("*")
                  if p.is_file() and p.suffix.lower() in IMAGE_EXT
                  and not SKIP_DIRS.intersection({x.lower() for x in p.relative_to(folder).parts[:-1]}))


def historical_hashes(repo: Path):
    manifests = [
        repo / "results/paper_a_evidence/stage24gl/campaign/native_dataset_manifest.json",
        repo / "results/paper_a_evidence/stage24/stage24_additional/native_dataset_manifest.json",
        repo / "results/paper_a_evidence/stage24/historical_stage23_NOT_CORRECTED/stage23c_cached_uded_descriptor_baselines/overlap_clean_dataset_manifest.json",
    ]
    known = defaultdict(list)
    for manifest in manifests:
        if not manifest.is_file():
            continue
        obj = json.loads(manifest.read_text(encoding="utf-8"))
        for record in obj.get("records", []):
            value = record.get("source_sha256")
            if value and len(value) == 64:
                known[value.lower()].append(f"{manifest.name}:{record.get('image_id', 'unknown')}")
    return known


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    ap.add_argument("--candidate-root", type=Path,
                    default=ROOT / "datasets/BIPEDv2/edges/imgs/train/rgbr/real")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--dhash-distance", type=int, default=5)
    ap.add_argument("--no-dhash", action="store_true", help="Only exact hashes, no Pillow required")
    args = ap.parse_args()
    if not 0 <= args.dhash_distance <= 8:
        ap.error("--dhash-distance must be between 0 and 8; only flags, never automatic exclusions")
    if not args.no_dhash and Image is None:
        ap.error("Pillow required for image-only near-duplicate warnings; pip install pillow, or --no-dhash")
    repo, folder = args.repo_root.resolve(), args.candidate_root.resolve()
    if SKIP_DIRS.intersection({x.lower() for x in folder.parts}):
        ap.error("Candidate root cannot be a ground-truth/output folder")
    if "test" in {x.lower() for x in folder.parts}:
        ap.error("Candidate source is a protected test folder")
    with args.inventory.open(encoding="utf-8-sig", newline="") as f:
        records = list(csv.DictReader(f))
    required = {"dataset", "image_id", "relative_path", "sha256", "review_status"}
    if not records or not required.issubset(records[0]):
        ap.error("Inventory CSV incomplete: run inventory_paper_a_confirmation_images.py first")
    if any(r["dataset"] != "BIPEDv2_train" for r in records):
        ap.error("Current audit profile supports only the BIPEDv2_train candidate inventory")
    if len(records) != 200:
        ap.error(f"Expected 200 candidates, got {len(records)}; stop for data-integrity review")

    historical = historical_hashes(repo)
    # UDED is previously exposed: its originals may be decoded for visual warnings.
    references = [
        ("UDED_development", repo / "external/UDED/imgs", True),
        ("BIPED_test_previously_used", repo / "datasets/BIPEDv2/edges/imgs/test/rgbr", False),
        ("BSDS_test_protected", repo / "datasets/BSDS500/images/test", False),
    ]
    reference_hash = defaultdict(list)
    reference_visual = []
    ref_stats = {}
    # The UDED directory may include a known protected BSDS-test lineage (35028).
    # Never decode a file bearing any protected BSDS-test stem, even via UDED.
    protected_bsds_stems = {
        p.stem for p in original_files(repo / "datasets/BSDS500/images/test")
    } | {"35028"}
    def is_protected_stem(stem: str) -> bool:
        # UDED names may prefix the original BSDS ID, e.g. "03-35028".
        # Compare complete identifiers, never a substring in the middle.
        return any(stem == known or stem.endswith("-" + known)
                   for known in protected_bsds_stems)
    for label, path, allow_decode in references:
        paths = original_files(path)
        n_decoded = 0
        n_protected_skipped = 0
        ref_stats[label] = {"n_image_files": len(paths), "decoded": False}
        for f in paths:
            reference_hash[sha256(f)].append(f"{label}:{f.name}")
            if is_protected_stem(f.stem):
                n_protected_skipped += 1
                continue  # SHA comparison only; no image decoding.
            if allow_decode and not args.no_dhash:
                reference_visual.append((label, f.name, dhash(f)))
                n_decoded += 1
        ref_stats[label]["n_decoded"] = n_decoded
        ref_stats[label]["n_protected_stems_excluded_from_decode"] = n_protected_skipped
        ref_stats[label]["decoded"] = n_decoded > 0

    candidates = []
    observed = defaultdict(list)
    for row in records:
        rel = Path(row["relative_path"])
        if rel.is_absolute() or ".." in rel.parts:
            ap.error(f"Unsafe candidate relative path: {rel}")
        path = folder / rel
        if not path.is_file():
            ap.error(f"Missing candidate: {path}")
        if SKIP_DIRS.intersection({x.lower() for x in rel.parts}):
            ap.error(f"Candidate points to excluded folder: {rel}")
        actual = sha256(path)
        expected = row["sha256"].lower().strip()
        if actual != expected:
            ap.error(f"Inventory hash mismatch (must rerun inventory): {path}")
        visual = None if args.no_dhash else dhash(path)
        record = {**row, "sha256": actual, "dhash64": format(visual, "016x") if visual is not None else ""}
        record["exact_historical_sources"] = "|".join(sorted(set(
            reference_hash.get(actual, []) + historical.get(actual, [])
        )))
        record["near_image_flags"] = ""
        record["status"] = "BLOCK_EXACT" if record["exact_historical_sources"] else "REVIEW_NOT_CERTIFIED"
        candidates.append((record, visual))
        observed[actual].append(record["image_id"])

    collision_counts = Counter()
    for record, visual in candidates:
        nearby = []
        if len(observed[record["sha256"]]) > 1:
            collision_counts["candidate_exact"] += 1
            record["status"] = "BLOCK_EXACT"
            nearby.append("IDENTICAL_IMAGE_IN_COHORT")
        if visual is not None:
            for other, otherhash in candidates:
                if other is record or otherhash is None:
                    continue
                if (visual ^ otherhash).bit_count() <= args.dhash_distance:
                    nearby.append(f"BIPED_train:{other['image_id']}")
            for label, filename, originalhash in reference_visual:
                if originalhash is not None and (visual ^ originalhash).bit_count() <= args.dhash_distance:
                    nearby.append(f"{label}:{filename}")
        record["near_image_flags"] = "|".join(sorted(set(nearby)))
        if nearby and record["status"] != "BLOCK_EXACT":
            record["status"] = "REVIEW_NEAR_DUPLICATE"

    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows = [r for r, _ in candidates]
    fieldnames = list(rows[0])
    csvfile = out / "candidate_review.csv"
    with csvfile.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    statuses = Counter(r["status"] for r in rows)
    report = {
        "status": "PRE_DATA_AUDIT_NOT_CONFIRMATION",
        "n_candidates": len(rows),
        "candidate_root": str(folder),
        "candidate_review_csv": str(csvfile),
        "status_counts": dict(statuses),
        "flagged_cases": [
            {
                "image_id": r["image_id"],
                "status": r["status"],
                "near_image_flags": r["near_image_flags"],
                "exact_historical_sources": r["exact_historical_sources"],
            }
            for r in rows if r["status"] != "REVIEW_NOT_CERTIFIED"
        ],
        "historical_manifest_sha_count": len(historical),
        "reference_counts": ref_stats,
        "dhash_warning_distance": None if args.no_dhash else args.dhash_distance,
        "warnings": [
            "Never auto-approve a BIPED_train image from this scanner",
            "dHash can miss crops, geometric transforms or high-level scene duplication",
            "Protected test splits are hashed only, with no decoding or GT inspection",
            "Previously recorded image exposure from other Git branches/runs must be reviewed",
            "Scene/sequence dependence and near duplicates require an independent lineage audit",
            "No GT or F1 values accessed, no research hypotheses evaluated",
        ],
    }
    (out / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
