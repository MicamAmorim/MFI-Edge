#!/usr/bin/env python3
"""Read-only, no-download preflight for possible MultiCue confirmatory domain.

Checks only local paths, archive presence/size and free disk space. Never reads
images, annotations, or evaluation outputs. The metadata is from the public
official Serre Lab Hugging Face card; nothing is downloaded automatically.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_URL = "https://huggingface.co/datasets/Serrelab/multicue-boundary-detection"
ARCHIVE_FILE = "multicue-dataset.tar.bz2"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ROOT / "external/MultiCue")
    args = parser.parse_args()
    destination = args.destination.expanduser().resolve()
    # Directory may not exist yet; find nearest existing ancestor for disk usage.
    parent = destination
    while not parent.exists():
        parent = parent.parent
    if not parent.is_dir():
        parser.error(f"Nearest existing destination ancestor not a directory: {parent}")
    space = shutil.disk_usage(parent)
    candidates = [
        destination / ARCHIVE_FILE,
        ROOT / "external/multicue-dataset.tar.bz2",
        ROOT / "datasets/MultiCue/multicue-dataset.tar.bz2",
        ROOT / "external/MDBD/multicue-dataset.tar.bz2",
    ]
    archives = [
        {"path": str(p), "size_bytes": p.stat().st_size}
        for p in candidates if p.is_file()
    ]
    locations = [
        ROOT / "datasets/MultiCue",
        ROOT / "datasets/MDBD",
        ROOT / "external/MultiCue",
        ROOT / "external/MDBD",
    ]
    local_dirs = [str(p) for p in locations if p.is_dir()]
    report = {
        "status": "PRE_DATA_SOURCE_PREFLIGHT_NO_DOWNLOAD",
        "dataset": "Serrelab/multicue-boundary-detection",
        "official_source": REPOSITORY_URL,
        "official_card": "100 natural scenes; 10-frame left/right videos; 1280x720",
        "archive_name": ARCHIVE_FILE,
        "source_archive_approx_size_gb": 3.4,
        "planned_destination": str(destination),
        "nearest_existing_destination_parent": str(parent),
        "free_disk_bytes": space.free,
        "free_disk_gib_approx": round(space.free / (1024**3), 2),
        "local_candidate_directories": local_dirs,
        "local_archive_candidates": archives,
        "data_downloaded_by_script": False,
        "contents_examined": False,
        "next_decisions": [
            "Confirm source/archive integrity and available space before any download",
            "Inspect archive member names only to determine exact frame/annotation paths",
            "Exclude any previously used UDED/MDBD scene and all correlated frames",
            "Use at most one annotated left-view frame per distinct scene",
            "Choose boundary annotation definition and evaluation policy before freeze",
        ],
        "warning": (
            "A file/directory existing locally is not proof of dataset completeness. "
            "No download or confirmatory evaluation has been performed."
        ),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
