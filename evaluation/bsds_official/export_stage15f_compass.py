from __future__ import annotations

"""Export the fixed exact-author Compass response for Stage 15f."""

from pathlib import Path
import csv
import hashlib
import json
import os
import subprocess
import time

from PIL import Image

from automation.stage15f_compass_build_preflight import (
    ARCHIVE_SHA256,
    AUTHOR_URL,
    AUTHOR_VENDOR,
    SOURCE_HASHES,
)


ROOT = Path(__file__).resolve().parents[2]
MATLAB_DIR = ROOT / "evaluation" / "bsds_official" / "matlab"
DEFAULT_MATLAB = Path(r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _quote(value: Path) -> str:
    return str(value.resolve()).replace("'", "''").replace("\\", "/")


def export_compass_maps(
    image_dir: Path, output_dir: Path, *, split: str, timeout_minutes: float = 360
) -> dict:
    image_dir = image_dir.resolve()
    output_dir = output_dir.resolve()
    source_dir = AUTHOR_VENDOR / "ruzon"
    observed = {
        relative: _sha256(AUTHOR_VENDOR / relative) for relative in SOURCE_HASHES
    }
    if observed != SOURCE_HASHES:
        raise RuntimeError("pinned Compass source hashes do not match registration")
    image_paths = sorted(image_dir.glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no JPG images found in {image_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    map_dir = output_dir / "compass"
    map_dir.mkdir(parents=True, exist_ok=True)
    build_dir = output_dir / "matlab_build"
    runtime_csv = output_dir / "per_image_runtime.csv"
    matlab = Path(os.environ.get("MATLAB_EXE", str(DEFAULT_MATLAB))).resolve()
    prefdir = output_dir / "matlab_preferences"
    prefdir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["MATLAB_PREFDIR"] = str(prefdir)
    expression = (
        f"addpath('{_quote(MATLAB_DIR)}');stage15f_export_compass("
        f"'{_quote(source_dir)}','{_quote(build_dir)}','{_quote(image_dir)}',"
        f"'{_quote(map_dir)}','{_quote(runtime_csv)}');"
    )
    started = time.perf_counter()
    completed = subprocess.run(
        [str(matlab), "-batch", expression], cwd=ROOT, env=env, text=True,
        encoding="utf-8", errors="replace", stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=timeout_minutes * 60, check=False,
    )
    wall_seconds = time.perf_counter() - started
    if completed.returncode:
        raise RuntimeError("Compass MATLAB export failed:\n" + "\n".join(completed.stdout.splitlines()[-100:]))
    hashes = {}
    for image_path in image_paths:
        prediction = map_dir / f"{image_path.stem}.png"
        with Image.open(image_path) as image, Image.open(prediction) as result:
            if result.mode != "L" or result.size != image.size:
                raise RuntimeError(f"invalid Compass map contract: {prediction}")
        hashes[image_path.stem] = _sha256(prediction)
    (output_dir / "map_hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    with runtime_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(image_paths):
        raise RuntimeError("Compass runtime table is incomplete")
    manifest = {
        "method": "Ruzon-Tomasi color Compass maximum-EMD strength",
        "implementation_fidelity": "unmodified hash-verified author C/MEX detector; repository adapter supplies compatible-ABI build, batch I/O, native-coordinate padding, validation, timing, and serialization",
        "training_class": "strictly untrained",
        "author_page": "https://ai.stanford.edu/~ruzon/compass/",
        "archive": {"url": AUTHOR_URL, "sha256": ARCHIVE_SHA256},
        "source_hashes": SOURCE_HASHES,
        "source_notice": "no explicit software license found; ignored local dependency, not redistributed",
        "fixed_parameters": {"sigma": 4, "radius": 12, "spacing": 1, "angle_degrees": 180, "wedges_per_quarter": 6, "max_clusters": 10},
        "dataset": "BSDS500", "split": split, "bsds_ground_truth_read": False,
        "native_resolution": True,
        "output": "author-valid maximum-EMD strength zero-padded at the radius-12 border and directly rounded to uint8 [0,255], without per-image normalization",
        "author_rng": "unchanged compass.c srand(clock()) behavior; no seed suppression or repeat selection",
        "n_maps": len(image_paths),
        "total_detector_seconds": sum(float(row["seconds"]) for row in rows),
        "total_export_wall_seconds": wall_seconds,
        "matlab_executable": str(matlab),
        "stdout_tail": "\n".join(completed.stdout.splitlines()[-40:]),
    }
    (output_dir / "export_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
