#!/usr/bin/env python3
"""Stage24G-L complete scientific evidence packaging; no network uploads.

Tier 1 (Git): complete per-group/fold JSON and original Berkeley text outputs,
stored as size-bounded compressed ZIP shards alongside CSV summaries.
Tier 2 (external deposit): locally staged immutable ZIP parts of float32
descriptor caches and generated Berkeley prediction maps (NO source images/GT).
Each file and ZIP gets SHA256; user must review third-party redistribution
permissions before publishing any external package.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/local_dev/stage24_paper_a_recertification"
OFFICIAL = ROOT / "results/official_eval/stage24_paper_a_recertification"
DEST = ROOT / "results/paper_a_evidence/stage24gl"
BINARY_DEST = ROOT / "results/local_dev/stage24gl_binary_publication"
CACHE = ROOT / "cache/local_dev/stage24"
PRED = ROOT / "automation/runtime/official_eval_cache/experiments/stage24_paper_a_recertification"
SMALL_SUFFIX = frozenset({".json", ".csv", ".txt", ".md"})
FLOAT_SUFFIX = frozenset({".npy", ".json", ".png"})
GIT_SHARD_UNCOMPRESSED = 24 * 1024 * 1024
BINARY_SHARD_UNCOMPRESSED = 400 * 1024 * 1024
MAX_GIT_ARCHIVE = 180 * 1024 * 1024


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, sort_keys=True, indent=2), encoding="utf-8")


def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def find_sources(base, extensions):
    if not base.is_dir():
        return []
    if base.is_symlink():
        raise RuntimeError("Refusing symlink source directory " + str(base))
    out = []
    for path in base.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("Refusing symlink scientific source " + str(path))
        if path.is_file() and path.suffix.lower() in extensions:
            if path.stat().st_size == 0 or path.name.endswith(".tmp"):
                raise RuntimeError("Empty or transient scientific source " + str(path))
            out.append(path)
    return sorted(out)


def create_shards(files, dest, prefix, root, limit):
    """Create reproducible-layout ZIP shards, source and ZIP SHA256 inventory."""
    dest.mkdir(parents=True, exist_ok=True)
    if not files:
        return [], []
    groups = []
    current, bytes_ = [], 0
    for path in files:
        n = path.stat().st_size
        if n > limit:
            raise RuntimeError(f"File too large for a reproducibility shard: {path} ({n})")
        if current and bytes_ + n > limit:
            groups.append(current)
            current, bytes_ = [], 0
        current.append(path)
        bytes_ += n
    if current:
        groups.append(current)

    listing, archives = [], []
    for index, group in enumerate(groups, 1):
        filename = f"{prefix}_part_{index:03d}.zip"
        outfile = dest / filename
        with zipfile.ZipFile(outfile, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6, allowZip64=True) as z:
            for source in group:
                name = source.relative_to(root).as_posix()
                z.write(source, arcname=name)
                listing.append({
                    "source": source.relative_to(ROOT).as_posix(),
                    "archive": filename,
                    "member": name,
                    "bytes": source.stat().st_size,
                    "sha256": sha256(source),
                })
        with zipfile.ZipFile(outfile, "r") as z:
            bad = z.testzip()
            if bad is not None:
                raise RuntimeError("CRC failed for " + bad)
        archives.append({"archive": filename, "sha256": sha256(outfile),
                         "bytes": outfile.stat().st_size,
                         "source_files": len(group)})
    return listing, archives


def git_numeric_archive(require_complete=True):
    folders = [SOURCE / "folds", SOURCE / "literature_folds"]
    sources = []
    for folder in folders:
        sources.extend(find_sources(folder, SMALL_SUFFIX))
    fold_keys = {path.parent.name for path in (SOURCE / "folds").glob("r*_f*/pair_screen.json")}
    if require_complete and len(fold_keys) != 15:
        raise RuntimeError(
            f"Expected 15 audited fold pair screens, found {len(fold_keys)}")
    if require_complete and not sources:
        raise RuntimeError("No fold checkpoint files found to archive")

    original = find_sources(OFFICIAL / "matlab", SMALL_SUFFIX)
    official_summary = OFFICIAL / "summary.json"
    if require_complete and not official_summary.is_file():
        raise RuntimeError("Missing original Berkeley summary")

    target = DEST / "reproducibility"
    if target.exists():
        shutil.rmtree(target)
    folderspec = [
        ("cv", sources, ROOT),
        ("berkeley_original", original, ROOT),
    ]
    all_rows, all_zips = [], []
    for label, files, root in folderspec:
        rows, archives = create_shards(files, target, label, root,
                                      GIT_SHARD_UNCOMPRESSED)
        for r in archives:
            r["category"] = label
        all_rows.extend(rows)
        all_zips.extend(archives)
    total = sum(z["bytes"] for z in all_zips)
    if total > MAX_GIT_ARCHIVE:
        raise RuntimeError(
            f"Full compact scientific archive {total} bytes exceeds "
            "the 180 MiB Git ceiling; split into an external deposit.")
    write_csv(target / "source_to_archive.csv", all_rows,
              ["source","archive","member","bytes","sha256"])
    write_json(target / "reproduction_manifest.json", {
        "schema_version": 1,
        "purpose": "independent per-fold and Berkeley evaluation audit",
        "source_files": len(all_rows),
        "per_fold_checkpoint_source_files": len(sources),
        "berkeley_original_source_files": len(original),
        "folds_found": len(fold_keys),
        "git_archive_bytes": total,
        "parts": all_zips,
        "status": "complete" if len(fold_keys) == 15 and original else "partial",
        "rights": "only derived metrics and model checkpoints; no third-party images or GT",
        "verify": "python scripts/verify_stage24gl_repro.py --check-git",
    })
    return {"source_files": len(all_rows), "parts": len(all_zips),
            "total_bytes": total, "status": "complete" if original else "partial"}


def build_binary_deposit():
    """Prepare but DO NOT publish potentially rights-restricted derived maps."""
    bases = [
        (CACHE / "descriptors", "cache_descriptor_scores"),
        (SOURCE / "float_predictions_uded", "uded_native_float_predictions"),
        (SOURCE / "float_predictions_bsds", "bsds_native_float_predictions"),
        (PRED, "berkeley_prediction_png"),
    ]
    # Include only native derived cache and generated outputs: never original
    # UDED/BSDS images, GTs, third-party model weights or external detector maps.
    files = []
    types = {}
    for folder, kind in bases:
        selected = find_sources(folder, FLOAT_SUFFIX)
        files.extend(selected)
        types[kind] = len(selected)
    if not files:
        raise RuntimeError("No float descriptor caches or generated scores "
                           "found; cannot claim complete reproducibility")
    size = sum(x.stat().st_size for x in files)
    free = shutil.disk_usage(BINARY_DEST.parent).free
    if free < max(size * 2, 512 * 1024 * 1024):
        raise RuntimeError("Insufficient free disk to safely package source "
                           "scores; existing files have not been deleted.")
    # Rebuild manifests from scratch only within a dedicated local directory.
    BINARY_DEST.mkdir(parents=True, exist_ok=True)
    for old in BINARY_DEST.glob("stage24gl_float_part_*.zip"):
        old.unlink()
    entries, packs = create_shards(
        files, BINARY_DEST, "stage24gl_float", ROOT,
        BINARY_SHARD_UNCOMPRESSED)
    report = {
        "schema_version": 1, "prepared": True, "uploaded": False,
        "requires_redistribution_rights_review": True,
        "third_party_original_images_included": False,
        "third_party_ground_truth_included": False,
        "external_literature_maps_included": False,
        "score_cache_file_count": types["cache_descriptor_scores"],
        "uded_native_float_prediction_count": types["uded_native_float_predictions"],
        "bsds_native_float_prediction_count": types["bsds_native_float_predictions"],
        "official_prediction_file_count": types["berkeley_prediction_png"],
        "bsds_float_completeness": "CHECK_AGAINST_FROZEN_MODELS_AND_100_IMAGE_IDS",
        "total_source_bytes": size,
        "assets": packs, "files": entries,
        "publication_target": "GitHub Release assets or Zenodo dataset record",
        "requires_manual_review": [
            "Inspect licenses of datasets and whether derived score maps can be redistributed",
            "Confirm external/native float detector assets are available from original sources",
            "Publish these ZIP files only after review and record their DOI or release URL",
        ],
    }
    write_json(BINARY_DEST / "binary_deposit_manifest.json", report)
    # A digest-only link from the Git archive to local binary package.
    public = {
        "prepared_locally": True, "uploaded": False,
        "publication_status": "PENDING_USER_PUBLICATION",
        "rights_review_required": True,
        "parts": packs,
        "manifest_sha256": sha256(BINARY_DEST / "binary_deposit_manifest.json"),
        "dataset_doi": None, "github_release_url": None,
    }
    write_json(DEST / "reproducibility" / "external_data_reference.json", public)
    return {"parts": len(packs), "source_files": len(entries),
            "total_source_bytes": size,
            "local_folder": str(BINARY_DEST.relative_to(ROOT))}


def prepare(require_complete=True, build_binary=True):
    compact = git_numeric_archive(require_complete=require_complete)
    binary = build_binary_deposit() if build_binary else {"status": "SKIPPED"}
    if not build_binary:
        write_json(DEST / "reproducibility" / "external_data_reference.json", {
            "prepared_locally": False, "uploaded": False,
            "publication_status": "PENDING_BINARY_DEPOSIT",
            "rights_review_required": True,
        })
    return {"git_numeric_evidence": compact, "external_binary_deposit": binary}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-binary-bundle", action="store_true")
    ap.add_argument("--allow-partial", action="store_true")
    args = ap.parse_args()
    print(json.dumps(prepare(not args.allow_partial, not args.no_binary_bundle),
                     indent=2))
