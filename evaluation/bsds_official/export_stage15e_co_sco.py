from __future__ import annotations

"""Export exact author CO/SCO maps for the Stage-15e reproduction.

The two institutional author archives are pinned by SHA-256 and extracted to
ignored vendor storage. Every reachable MATLAB source is verified before the
unmodified detectors are called with the parameters fixed in the 2015 paper.
This adapter never reads BSDS ground truth.
"""

from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import subprocess
import time
import urllib.request

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
AUTHOR_PROJECT_PAGE = "https://www.neuro.uestc.edu.cn/vccl/projcvpr2013.html"
CO_ARCHIVE_URL = "https://www.neuro.uestc.edu.cn/vccl/data/cvpr2013/COBoundary.rar"
SCO_ARCHIVE_URL = "https://www.neuro.uestc.edu.cn/vccl/data/tip2015/SCOboundary.rar"
CO_ARCHIVE_SHA256 = "a8563d595d6db78698ece7c30ac0a31d8e7298e424e187cdcf84658c9a4bcb39"
SCO_ARCHIVE_SHA256 = "01f928da7c9ecacfd3b0ebc0ce5a095fb561d2366745eee6e72e56234a6c9071"
VENDOR_ROOT = ROOT / "evaluation" / "bsds_official" / "vendor"
CO_VENDOR = VENDOR_ROOT / f"co_author_{CO_ARCHIVE_SHA256[:12]}"
SCO_VENDOR = VENDOR_ROOT / f"sco_author_{SCO_ARCHIVE_SHA256[:12]}"
MATLAB_WRAPPER_DIR = ROOT / "evaluation" / "bsds_official" / "matlab"
DEFAULT_MATLAB = Path(r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe")

CO_SOURCE_HASHES = {
    "COBoundary.m": "8541017c53230da6b17df24a9b68f11115ace173aea5916ce2b59e6dbc42ae2c",
    "conByfft.m": "f844cd124f6962d463666fec7bd83b455b22d997acf235d5ed944a345c57feb6",
    "DivGauss2D.m": "32b99a274c23655163462da6e622617e3ab0ea1c0b6708c42479933070703f90",
    "gaus.m": "2aece0dac55f7b2bde9ff94ed841a099c63b62d88b16b73c515d4ec225d32bf7",
    "nonmax.m": "86569ba4366165f8409f26d24b642effb63439e873954ae97ddedd7fb439fc70",
    "OrientedDoubleOpponent.m": "a2eca544a4c3edc5f9a9f1b25e47cc7036ee13ce7703f7a7ac089c5e85f0e737",
    "resDO.m": "c78fe55afb6ce81267a6c6f44b961b70cfc619cae9a0f53dfa14ba32de0c5386",
    "SingleOpponent.m": "252d18afb400f784114e761f9c43ede11b6c969945808642cae0a8c4f0a91e4a",
}
SCO_SOURCE_HASHES = {
    "conByfft.m": "f844cd124f6962d463666fec7bd83b455b22d997acf235d5ed944a345c57feb6",
    "DivGauss2D.m": "32b99a274c23655163462da6e622617e3ab0ea1c0b6708c42479933070703f90",
    "gaus.m": "2aece0dac55f7b2bde9ff94ed841a099c63b62d88b16b73c515d4ec225d32bf7",
    "nonmax.m": "86569ba4366165f8409f26d24b642effb63439e873954ae97ddedd7fb439fc70",
    "OrientedDoubleOpponent.m": "df13c63753568f6c70faa24cce046111c91d008b21bf245c87ebb4ee2957af25",
    "resSCO.m": "ae76bf1736810d894d2b058745a7ce9e9176ae2cfadc1ec4a1b1ee8573133565",
    "SCOBoundary.m": "0dcb96533b2614f0ee25b25487d350d3a8c1a880352f75f7d1fb9101239ba4d3",
    "SingleOpponent.m": "eb6425cf07c1ce3fd811b7b9708fcf1e5a19085c18d55fbe5e76b4897f734ecd",
    "SparIndex.m": "14ac5863c18c7a04b1c6cf9d7e9b1774393775f5a189e8fbde2cd612b445bb92",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(command: list[str], *, timeout: float, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if result.returncode:
        tail = "\n".join((result.stdout or "").splitlines()[-100:])
        raise RuntimeError(f"command failed with exit code {result.returncode}: {command!r}\n{tail}")
    return result.stdout or ""


def _fetch_and_verify(url: str, archive: Path, expected_hash: str) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        temporary = archive.with_suffix(archive.suffix + ".download")
        with urllib.request.urlopen(url, timeout=120) as response:
            temporary.write_bytes(response.read())
        if _sha256(temporary) != expected_hash:
            raise RuntimeError(f"downloaded archive hash mismatch: {url}")
        temporary.replace(archive)
    if _sha256(archive) != expected_hash:
        raise RuntimeError(f"cached archive hash mismatch: {archive}")


def _ensure_source(
    *, url: str, archive_hash: str, vendor: Path, folder: str, hashes: dict[str, str]
) -> Path:
    archive = vendor / f"{folder}.rar"
    source_dir = vendor / folder
    if not source_dir.exists():
        _fetch_and_verify(url, archive, archive_hash)
        # Extract only the executable MATLAB surface. The v1 archive's bundled
        # PDF uses a legacy RAR PPMd stream that Windows bsdtar cannot decode,
        # while its source members extract and verify cleanly.
        members = [f"{folder}/{name}" for name in hashes]
        _run(
            ["tar", "-xf", str(archive), "-C", str(vendor), *members],
            timeout=300,
        )
    observed = {name: _sha256(source_dir / name) for name in hashes}
    if observed != hashes:
        raise RuntimeError(f"pinned {folder} MATLAB source hashes do not match registration")
    return source_dir


def _matlab_quote(value: Path | str) -> str:
    return str(value).replace("'", "''").replace("\\", "/")


def export_co_sco_maps(
    image_dir: Path, output_dir: Path, *, split: str, timeout_minutes: float = 240
) -> dict:
    image_dir = image_dir.resolve()
    output_dir = output_dir.resolve()
    image_paths = sorted(image_dir.glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {image_dir}")
    co_source = _ensure_source(
        url=CO_ARCHIVE_URL,
        archive_hash=CO_ARCHIVE_SHA256,
        vendor=CO_VENDOR,
        folder="COBoundary",
        hashes=CO_SOURCE_HASHES,
    )
    sco_source = _ensure_source(
        url=SCO_ARCHIVE_URL,
        archive_hash=SCO_ARCHIVE_SHA256,
        vendor=SCO_VENDOR,
        folder="SCOboundary",
        hashes=SCO_SOURCE_HASHES,
    )
    co_dir = output_dir / "co"
    sco_dir = output_dir / "sco"
    co_dir.mkdir(parents=True, exist_ok=True)
    sco_dir.mkdir(parents=True, exist_ok=True)
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
        "stage15e_export_co_sco("
        f"'{_matlab_quote(co_source)}','{_matlab_quote(sco_source)}',"
        f"'{_matlab_quote(image_dir)}','{_matlab_quote(co_dir)}',"
        f"'{_matlab_quote(sco_dir)}','{_matlab_quote(runtime_csv)}');"
    )
    started = time.perf_counter()
    stdout = _run(
        [str(matlab), "-batch", expression],
        timeout=timeout_minutes * 60.0,
        env=env,
    )
    wall_seconds = time.perf_counter() - started

    map_hashes: dict[str, dict[str, str]] = {"co": {}, "sco": {}}
    for method, method_dir in (("co", co_dir), ("sco", sco_dir)):
        for image_path in image_paths:
            prediction_path = method_dir / f"{image_path.stem}.png"
            if not prediction_path.exists():
                raise RuntimeError(f"missing {method.upper()} map: {prediction_path}")
            with Image.open(image_path) as image, Image.open(prediction_path) as prediction:
                if prediction.mode != "L" or prediction.size != image.size:
                    raise RuntimeError(f"invalid {method.upper()} map contract: {prediction_path}")
            map_hashes[method][image_path.stem] = _sha256(prediction_path)
    (output_dir / "map_hashes.json").write_text(
        json.dumps(map_hashes, indent=2), encoding="utf-8"
    )
    with runtime_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 2 * len(image_paths):
        raise RuntimeError("CO/SCO runtime table is incomplete")
    detector_seconds = {
        method: sum(float(row["seconds"]) for row in rows if row["method"] == method)
        for method in ("co", "sco")
    }
    manifest = {
        "methods": [
            "CO(-0.7) without SSC using the author COBoundary implementation",
            "SCO(-0.7) with modified SSC using the author SCOBoundary implementation",
        ],
        "implementation_fidelity": (
            "exact unmodified institutional author MATLAB sources; repository adapter "
            "provides batch I/O, published arguments, validation, timing, and serialization"
        ),
        "training_class": (
            "parameter-fixed but author-tuned: sigma=1.1, w=-0.7, and eta=5 were "
            "selected on BSDS300 train in the 2015 paper; no BSDS500-val fitting"
        ),
        "author_project_page": AUTHOR_PROJECT_PAGE,
        "author_archives": {
            "co": {"url": CO_ARCHIVE_URL, "sha256": CO_ARCHIVE_SHA256},
            "sco": {"url": SCO_ARCHIVE_URL, "sha256": SCO_ARCHIVE_SHA256},
        },
        "source_notice": (
            "research-purpose-only notice; no open-source license found; archives remain "
            "in ignored vendor storage and are not redistributed"
        ),
        "source_hashes": {"co": CO_SOURCE_HASHES, "sco": SCO_SOURCE_HASHES},
        "fixed_parameters": {
            "co": {"sigma": 1.1, "orientations": 8, "cone_weight": -0.7},
            "sco": {
                "sigma": 1.1,
                "orientations": 8,
                "cone_weight": -0.7,
                "sparseness_window": 5,
            },
        },
        "dataset": "BSDS500",
        "split": split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "output": (
            "author intrinsically normalized and NMS-suppressed soft maps serialized "
            "directly to uint8 [0,255] without adapter normalization"
        ),
        "n_maps_per_method": len(image_paths),
        "total_detector_seconds": detector_seconds,
        "total_export_wall_seconds": wall_seconds,
        "matlab_executable": str(matlab),
        "stdout_tail": "\n".join(stdout.splitlines()[-40:]),
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
    parser.add_argument("--timeout-minutes", type=float, default=240)
    args = parser.parse_args()
    export_co_sco_maps(
        Path(args.image_dir),
        Path(args.output_dir),
        split=args.split,
        timeout_minutes=args.timeout_minutes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
