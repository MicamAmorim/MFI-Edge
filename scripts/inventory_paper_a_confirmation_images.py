#!/usr/bin/env python3
"""Inventory local image candidates for Paper A confirmation, without GT/F1.

This is a read-only image-file crawler. It writes *candidate* metadata only:
neither independence nor historical non-exposure is certified by its output.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
EXCLUDE_DIRS = {
    ".git", ".venv", "__pycache__", "gt", "gts", "ground_truth",
    "groundtruth", "labels", "label", "masks", "mask", "annotations",
    "annotation", "edges", "edge_maps", "boundaries", "boundary",
    "predictions", "prediction", "outputs", "results",
}
OUTPUT_COLUMNS = [
    "dataset", "image_id", "relative_path", "sha256", "size_bytes",
    "historical_exact_hash_match", "historical_id_warning",
    "review_status", "note"
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def historic(root: Path):
    known_hashes, known_uded_ids, known_bsds_ids = set(), set(), set()
    historic_manifests = [
        root / "results/paper_a_evidence/stage24gl/campaign/native_dataset_manifest.json",
        root / "results/paper_a_evidence/stage24/stage24_additional/native_dataset_manifest.json",
    ]
    for manifest in historic_manifests:
        if not manifest.exists():
            continue
        obj = json.loads(manifest.read_text(encoding="utf-8"))
        for item in obj.get("records", []):
            if item.get("source_sha256"):
                known_hashes.add(item["source_sha256"].lower())
            if item.get("image_id"):
                known_uded_ids.add(item["image_id"])
    history_bsds = root / "analise_condicional/bsds_per_image_at_development_ODS_threshold.csv"
    if history_bsds.is_file():
        with history_bsds.open(encoding="utf-8-sig", newline="") as f:
            known_bsds_ids.update(r["image_id"] for r in csv.DictReader(f))
    return known_hashes, known_uded_ids, known_bsds_ids


def roots_from_args(items):
    results = []
    names = set()
    for val in items:
        label, eq, path = val.partition("=")
        if not eq or not label.strip() or not path.strip():
            raise ValueError("Expected --dataset NAME=ABSOLUTE_OR_RELATIVE_DIRECTORY")
        label = label.strip()
        if label in names:
            raise ValueError(f"Duplicate dataset label: {label}")
        names.add(label)
        folder = Path(path.strip()).expanduser().resolve()
        if not folder.is_dir():
            raise ValueError(f"Dataset directory missing: {folder}")
        # Guard even when a GT/output directory was explicitly passed as the root.
        parts = {part.lower() for part in folder.parts}
        forbidden = parts & EXCLUDE_DIRS
        if forbidden:
            raise ValueError(f"Refusing annotation/output root {folder}: {sorted(forbidden)}")
        if "test" in parts:
            raise ValueError(
                f"Test split is protected pending the historical-exposure audit: {folder}. "
                "Do not use this inventory to silently consume held-out test images."
            )
        results.append((label, folder))
    return results


def scan(name, folder, known_hashes, known_uded_ids, known_bsds_ids):
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXT:
            continue
        rel = path.relative_to(folder)
        if any(part.lower() in EXCLUDE_DIRS for part in rel.parts[:-1]):
            continue
        digest = sha256(path)
        file_id = path.stem
        id_warning = file_id in known_uded_ids or file_id in known_bsds_ids
        exact = digest in known_hashes
        yield {
            "dataset": name,
            "image_id": file_id,
            "relative_path": rel.as_posix(),
            "sha256": digest,
            "size_bytes": path.stat().st_size,
            "historical_exact_hash_match": str(exact).lower(),
            "historical_id_warning": str(id_warning).lower(),
            "review_status": "BLOCK_EXACT_MATCH" if exact else "PENDING_MANUAL",
            "note": "Manual exposure, near-duplicate, scene/group and GT availability audit required",
        }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--dataset", action="append", default=[], metavar="NAME=FOLDER",
                    help="Image root; repeat for multiple domains. Never point to ground-truth folders.")
    ap.add_argument("--out", type=Path,
                    default=Path("results/local_dev/paper_a_confirmation_inventory/candidates.csv"))
    args = ap.parse_args()
    root = args.repo_root.resolve()
    try:
        domains = roots_from_args(args.dataset)
    except ValueError as e:
        ap.error(str(e))
    if not domains:
        locations = [root / x for x in ("data", "datasets", "external", "results/local_dev")]
        print(json.dumps({
            "status": "NEED_DATASET_ROOTS",
            "root": str(root),
            "existing_local_roots": [str(x) for x in locations if x.is_dir()],
            "hint": "Run --dataset 'DOMAIN=C:\\path\\to\\images' twice; do not use GT or outputs folders",
        }, ensure_ascii=False, indent=2))
        return 0
    hashes, used_uded, used_bsds = historic(root)
    rows = []
    for name, folder in domains:
        rows.extend(scan(name, folder, hashes, used_uded, used_bsds))
    duplicate_hashes = Counter(r["sha256"] for r in rows)
    duplicate_ids = Counter((r["dataset"], r["image_id"]) for r in rows)
    for row in rows:
        if duplicate_hashes[row["sha256"]] > 1:
            row["review_status"] = "BLOCK_DUPLICATE"
            row["note"] += "; repeated SHA in inventory"
        if duplicate_ids[(row["dataset"], row["image_id"])] > 1:
            row["review_status"] = "BLOCK_DUPLICATE"
            row["note"] += "; repeated basename within dataset"
    out = args.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(r["dataset"] for r in rows)
    statuses = Counter(r["review_status"] for r in rows)
    result = {
        "status": "INVENTORY_ONLY_NOT_CONFIRMATORY",
        "file": str(out),
        "n_images": len(rows),
        "per_dataset": dict(counts),
        "review_status": dict(statuses),
        "historic_hash_count": len(hashes),
        "historic_uded_ids": len(used_uded),
        "historic_bsds_validation_ids": len(used_bsds),
        "limitations": [
            "Only two historical native UDED manifests and BSDS development image IDs are checked",
            "Historical image SHA mismatches may reflect re-encoding or resizing; review visually and by lineage",
            "An unflagged image is NOT certified independent, new, or eligible",
            "No GT file was opened and no performance metric was computed",
            "No dataset is automatically promoted to the confirmatory manifest",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
