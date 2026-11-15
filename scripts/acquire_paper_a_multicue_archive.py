#!/usr/bin/env python3
"""Download the official MultiCue archive to a NON-SYSTEM drive, explicitly opt-in.

No GT/images are extracted or inspected. No F1/model inference is performed.
--download is required for any network access or file transfer.
Uses the Hugging Face client to pin the repository revision and record SHA256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as installed_version
from pathlib import Path

DATASET = "Serrelab/multicue-boundary-detection"
FILENAME = "multicue-dataset.tar.bz2"
SOURCE = "https://huggingface.co/datasets/Serrelab/multicue-boundary-detection"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def get_sha_from_lfs(sibling) -> str | None:
    lfs = getattr(sibling, "lfs", None)
    if isinstance(lfs, dict):
        return lfs.get("sha256")
    return getattr(lfs, "sha256", None)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--destination", type=Path, required=True,
                    help="Non-system drive directory, e.g. F:\\MFI-Edge-Data\\MultiCue")
    ap.add_argument("--download", action="store_true",
                    help="Explicit consent to fetch the ~3.4 GB archive over HTTPS")
    ap.add_argument("--min-free-gib", type=float, default=15.0,
                    help="Refuse download if the target volume has less free space")
    args = ap.parse_args()
    destination = args.destination.expanduser().resolve()
    cache = destination.parent / "HFCache"
    temp = destination.parent / "HFTemp"
    parent = destination
    while not parent.exists():
        if parent.parent == parent:
            ap.error(f"Cannot resolve a destination volume for {destination}")
        parent = parent.parent
    if not parent.is_dir():
        ap.error("Destination ancestor must be a directory")
    free = shutil.disk_usage(parent).free
    info = {
        "status": "DRY_RUN_NO_NETWORK" if not args.download else "PREPARING_DOWNLOAD",
        "dataset": DATASET,
        "source": SOURCE,
        "destination": str(destination),
        "expected_archive": str(destination / FILENAME),
        "cache_root": str(cache),
        "temporary_root": str(temp),
        "free_gib": round(free / (1024**3), 2),
        "minimum_free_gib": args.min_free_gib,
        "download_requested": args.download,
        "extract_requested": False,
        "gt_accessed": False,
        "confirmatory_evaluation": False,
    }
    print(json.dumps(info, ensure_ascii=False, indent=2), flush=True)
    if not args.download:
        return 0
    if destination.drive.lower() == Path.home().drive.lower():
        ap.error(
            "Destination points to the Windows system/home drive. "
            "Use --destination F:\\MFI-Edge-Data\\MultiCue to keep C: untouched."
        )
    if free < int(args.min_free_gib * 1024**3):
        ap.error(
            f"Insufficient free disk space: {free / (1024**3):.2f} GiB "
            f"< required {args.min_free_gib:.2f} GiB."
        )
    destination.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    temp.mkdir(parents=True, exist_ok=True)
    # Configure cache and temporary directories BEFORE importing huggingface_hub.
    os.environ["HF_HOME"] = str(cache)
    os.environ["HF_HUB_CACHE"] = str(cache / "hub")
    os.environ["HF_XET_CACHE"] = str(cache / "xet")
    os.environ["TMP"] = str(temp)
    os.environ["TEMP"] = str(temp)
    os.environ["TMPDIR"] = str(temp)

    # Pin an isolated environment for reproducibility. Hub 2.4.0 brought
    # incompatible tokenizers requirements and Windows truststore recursion.
    expected_hub_version = "1.33.0"
    try:
        current_hub_version = installed_version("huggingface_hub")
    except PackageNotFoundError:
        current_hub_version = None
    if current_hub_version != expected_hub_version:
        raise SystemExit(
            f"Unsupported huggingface_hub version {current_hub_version!r}; "
            f"required {expected_hub_version}. Use "
            "scripts/setup_paper_a_multicue_env.ps1 and invoke this script "
            "with F:\\MFI-Edge-Data\\Venvs\\multicue-download\\Scripts\\python.exe. "
            "Never disable TLS certificate verification."
        )
    try:
        from huggingface_hub import HfApi, hf_hub_download
    except ImportError as exc:
        raise SystemExit("Hugging Face import failed inside isolated environment") from exc

    api = HfApi()
    try:
        metadata = api.dataset_info(DATASET, files_metadata=True)
    except RecursionError as exc:
        raise RuntimeError(
            "TLS/SSL recursion detected before downloading. Verify the isolated "
            "venv and pinned Hub 1.33.0 installation; never disable SSL checks."
        ) from exc
    revision = str(metadata.sha)
    if not revision or len(revision) < 20:
        raise RuntimeError("No immutable repository commit returned: stopping.")
    matches = [s for s in metadata.siblings if s.rfilename == FILENAME]
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one official archive, stopping.")
    sibling = matches[0]
    declared_size = getattr(sibling, "size", None)
    lfs_sha = get_sha_from_lfs(sibling)
    if declared_size and free < declared_size + 5 * 1024**3:
        raise RuntimeError("Volume cannot retain archive plus 5 GiB safety reserve.")
    print(json.dumps({
        "status": "PINNED_SOURCE_READY",
        "immutable_source_revision": revision,
        "archive_size_metadata_bytes": declared_size,
        "archive_lfs_sha256": lfs_sha,
        "archive_only": True,
    }, indent=2), flush=True)

    downloaded = Path(hf_hub_download(
        repo_id=DATASET,
        filename=FILENAME,
        repo_type="dataset",
        revision=revision,
        local_dir=str(destination),
    )).resolve()
    if downloaded.parent != destination or downloaded.name != FILENAME:
        raise RuntimeError(f"Unexpected downloaded file location: {downloaded}")
    actual_size = downloaded.stat().st_size
    if declared_size is not None and actual_size != declared_size:
        raise RuntimeError(
            f"File size mismatch (got {actual_size}, expected {declared_size})"
        )
    actual_sha = digest(downloaded)
    if lfs_sha and actual_sha.lower() != str(lfs_sha).lower():
        raise RuntimeError("Official LFS SHA256 mismatch: do not use archive.")
    result = {
        "status": "ARCHIVE_DOWNLOADED_NOT_EXTRACTED",
        "official_source": SOURCE,
        "dataset": DATASET,
        "repository_commit_sha": revision,
        "archive": str(downloaded),
        "archive_bytes": actual_size,
        "archive_sha256": actual_sha,
        "huggingface_hub_version": current_hub_version,
        "official_lfs_sha256": lfs_sha,
        "official_lfs_sha256_verified": bool(lfs_sha),
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "images_or_ground_truth_read": False,
        "model_inference_run": False,
        "confirmatory_outcomes_opened": False,
        "next_step": "Audit tar member names and exact scene/annotation layout BEFORE any selective extraction or GT use",
    }
    manifest = destination / "archive_provenance.json"
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
