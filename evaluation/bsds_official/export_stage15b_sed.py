from __future__ import annotations

"""Export exact author-code SED maps for the Stage-15b reproduction.

The public author repository is fetched at one immutable commit into the
ignored evaluator vendor directory. Its MATLAB detector files are verified
byte-for-byte and executed without modification. This adapter supplies only
batch I/O, range checks, and the required 8-bit PNG serialization; it never
reads BSDS ground truth.
"""

from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
AUTHOR_REPOSITORY = "https://github.com/ArashAkbarinia/BoundaryDetection.git"
AUTHOR_COMMIT = "11514b80162e5cd93fd244515189649656105a14"
AUTHOR_VENDOR = (
    ROOT / "evaluation" / "bsds_official" / "vendor" / f"sed_author_{AUTHOR_COMMIT[:12]}"
)
MATLAB_WRAPPER_DIR = ROOT / "evaluation" / "bsds_official" / "matlab"
DEFAULT_MATLAB = Path(r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe")

# All files reachable from the published full-model entry point. Hashes were
# recorded from the pinned author commit before registration.
AUTHOR_MATLAB_HASHES = {
    "CalculateGaussianWidth.m": "2f0010798ab0450e722a0eb22e34589a7c04146ba3c2d4c4db2141676ef2e394",
    "CentreCircularZero.m": "83ecc91e0ac255f25d2a0be8418485e345351b018420a5e518ca53de958a6047",
    "CentreZero.m": "e0bc4990dcd45f93b83c86a02192aeeec9750da9a9e88ddedbaefa3b27142634",
    "CircularAverage.m": "8b74919871381317f6fe8b5765c09e0a20ebb17f8b934694d225f1696203e203",
    "CircularLocalStdContrast.m": "30758c7b6781812354889d6f5d3e3bd9c0bffb9f29d5240dccd7e6f10ee46180",
    "Gaussian2Gradient1.m": "1553f7bf16b320743217d772c1a0b38cc8f0ae365ad917ed6a520f32660a4811",
    "GaussianFilter2.m": "19822ccfbd933b552327bafed69c6f498f023b7dfc283335367c3ad13d39cd9f",
    "nonmax.m": "86569ba4366165f8409f26d24b642effb63439e873954ae97ddedd7fb439fc70",
    "NormaliseChannel.m": "e7f9aec831b3bbfef1a5d01fbf1bf2c29be642467645e3a8ff3e057d45b6325c",
    "SurroundModulationEdgeDetector.m": "d34ccef455186682ea049d6e926d7771605ac6cac6d1b2beb940e840ece08bd8",
}


def _run(command: list[str], *, timeout: float, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if result.returncode:
        tail = "\n".join((result.stdout or "").splitlines()[-80:])
        raise RuntimeError(
            f"command failed with exit code {result.returncode}: {command[0]}\n{tail}"
        )
    return result


def _git(*args: str, cwd: Path | None = None, timeout: float = 300) -> str:
    prefix = ["-C", str(cwd)] if cwd is not None else []
    result = _run(
        ["git", *prefix, *args],
        timeout=timeout,
    )
    return (result.stdout or "").strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_author_source() -> Path:
    """Return the verified unmodified MATLAB source directory."""

    if not AUTHOR_VENDOR.exists():
        AUTHOR_VENDOR.parent.mkdir(parents=True, exist_ok=True)
        # Sparse checkout avoids redistributing or retaining the repository's
        # large published result collection. Only the unmodified MATLAB source
        # is materialized locally.
        _git(
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            AUTHOR_REPOSITORY,
            str(AUTHOR_VENDOR),
            timeout=900,
        )
        _git("sparse-checkout", "init", "--cone", cwd=AUTHOR_VENDOR)
        _git("sparse-checkout", "set", "src/matlab", cwd=AUTHOR_VENDOR)
        _git("checkout", "--detach", AUTHOR_COMMIT, cwd=AUTHOR_VENDOR, timeout=900)

    head = _git("rev-parse", "HEAD", cwd=AUTHOR_VENDOR)
    if head != AUTHOR_COMMIT:
        raise RuntimeError(
            f"SED author checkout is at {head}, expected immutable commit {AUTHOR_COMMIT}"
        )
    if _git("status", "--porcelain", "--untracked-files=no", cwd=AUTHOR_VENDOR):
        raise RuntimeError("tracked files in the SED author checkout were modified")

    source_dir = AUTHOR_VENDOR / "src" / "matlab"
    observed = {name: _sha256(source_dir / name) for name in AUTHOR_MATLAB_HASHES}
    if observed != AUTHOR_MATLAB_HASHES:
        raise RuntimeError("pinned SED MATLAB source hashes do not match registration")
    return source_dir


def _matlab_quote(value: Path | str) -> str:
    return str(value).replace("'", "''").replace("\\", "/")


def export_sed_maps(
    image_dir: Path,
    output_dir: Path,
    *,
    split: str,
    timeout_minutes: float = 180,
) -> dict:
    image_dir = image_dir.resolve()
    output_dir = output_dir.resolve()
    image_paths = sorted(image_dir.glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {image_dir}")

    author_source = ensure_author_source()
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime_csv = output_dir / "per_image_runtime.csv"
    matlab = Path(os.environ.get("MATLAB_EXE", str(DEFAULT_MATLAB))).resolve()
    if not matlab.exists():
        raise FileNotFoundError(f"MATLAB executable not found: {matlab}")

    prefdir = output_dir / "matlab_preferences"
    prefdir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["MATLAB_PREFDIR"] = str(prefdir)
    expression = (
        f"addpath('{_matlab_quote(MATLAB_WRAPPER_DIR)}');"
        "stage15b_export_sed("
        f"'{_matlab_quote(author_source)}',"
        f"'{_matlab_quote(image_dir)}',"
        f"'{_matlab_quote(output_dir)}',"
        f"'{_matlab_quote(runtime_csv)}');"
    )
    started = time.perf_counter()
    result = _run(
        [str(matlab), "-batch", expression],
        timeout=timeout_minutes * 60.0,
        env=env,
    )
    elapsed = time.perf_counter() - started

    map_hashes: dict[str, str] = {}
    for image_path in image_paths:
        output = output_dir / f"{image_path.stem}.png"
        if not output.exists():
            raise RuntimeError(f"missing SED map: {output}")
        with Image.open(image_path) as image, Image.open(output) as prediction:
            if prediction.mode != "L":
                raise RuntimeError(f"SED map is not single-channel 8-bit PNG: {output}")
            if prediction.size != image.size:
                raise RuntimeError(
                    f"SED map/image size mismatch for {image_path.stem}: "
                    f"{prediction.size} vs {image.size}"
                )
        map_hashes[image_path.stem] = _sha256(output)

    hashes_path = output_dir / "map_hashes.json"
    hashes_path.write_text(json.dumps(map_hashes, indent=2), encoding="utf-8")
    manifest = {
        "method": "SED full model (Akbarinia and Parraga, IJCV 2018)",
        "implementation_fidelity": (
            "exact unmodified author MATLAB detector with repository batch-I/O adapter"
        ),
        "training_class": "strictly untrained; fixed author parameters",
        "author_repository": AUTHOR_REPOSITORY,
        "author_commit": AUTHOR_COMMIT,
        "author_source_license": (
            "no explicit license file found; source kept as an ignored local dependency "
            "and not redistributed"
        ),
        "author_matlab_hashes": AUTHOR_MATLAB_HASHES,
        "dataset": "BSDS500",
        "split": split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "output": (
            "author score after intrinsic normalization and NMS, serialized directly "
            "to uint8 [0,255] without adapter normalization"
        ),
        "n_maps": len(image_paths),
        "total_export_seconds": elapsed,
        "matlab_executable": str(matlab),
        "stdout_tail": "\n".join((result.stdout or "").splitlines()[-30:]),
        "published_bsds500_test_colour_metrics_document_only": {
            "ODS": 0.71,
            "OIS": 0.74,
            "AP": 0.74,
        },
    }
    (output_dir / "export_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--split", default="val")
    parser.add_argument("--timeout-minutes", type=float, default=180)
    args = parser.parse_args()
    export_sed_maps(
        Path(args.image_dir),
        Path(args.output_dir),
        split=args.split,
        timeout_minutes=args.timeout_minutes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
