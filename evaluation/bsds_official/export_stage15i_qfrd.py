from __future__ import annotations

"""Export the pinned exact-author QFrD response for Stage 15i."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
AUTHOR_ROOT = ROOT / "external" / "QFrD_stage15i_retry1"
AUTHOR_REPOSITORY = "https://github.com/renhu9120/QFrD.git"
AUTHOR_COMMIT = "8dcc8d846e6dcbe1bc4b931b89f1c814f5f9a245"
TRACKED_MANIFEST_SHA256 = "49dbc518659eb7a0cd3742c90f040ef93bdb1a4b5ccf3ac6774c7a4fb11c3c72"


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "safe.directory=*", *args], cwd=AUTHOR_ROOT,
        check=False, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "QFrD git provenance check failed")
    return completed.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_author_tree() -> dict[str, object]:
    if not AUTHOR_ROOT.exists():
        raise FileNotFoundError("the passed Stage-15i preflight checkout is missing")
    if _git("rev-parse", "HEAD") != AUTHOR_COMMIT:
        raise RuntimeError("QFrD checkout is not at the registered commit")
    if _git("status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("QFrD checkout is dirty; refusing exact-code reproduction")
    tracked = sorted(item for item in _git("ls-files", "-z").split("\0") if item)
    aggregate = hashlib.sha256()
    for relative in tracked:
        file_hash = _sha256(AUTHOR_ROOT / relative)
        aggregate.update(relative.replace("\\", "/").encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(file_hash.encode("ascii"))
        aggregate.update(b"\n")
    if aggregate.hexdigest() != TRACKED_MANIFEST_SHA256:
        raise RuntimeError("QFrD tracked-file manifest differs from the passed preflight")
    return {"repository": AUTHOR_REPOSITORY, "commit": AUTHOR_COMMIT,
            "tracked_file_count": len(tracked), "tracked_manifest_sha256": aggregate.hexdigest()}


def export_qfrd_maps(image_dir: Path, output_dir: Path, *, split: str) -> dict[str, object]:
    import torch

    image_dir, output_dir = image_dir.resolve(), output_dir.resolve()
    image_paths = sorted(image_dir.glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no JPG images found in {image_dir}")
    provenance = _verify_author_tree()
    output_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(AUTHOR_ROOT))
    try:
        from algorithm.alg_q_3_gfrcht_fft import alg_gfrcht, default_gfrcht_config
        from core.utils_color import img_load_rgb_as_tensor

        cfg = default_gfrcht_config(device="cpu", dtype=torch.float64, alpha_1=0.8,
                                    alpha_2=1.0, pad=64, gauss_sigma=2.0,
                                    low=0.8, high=2.5)
        runtimes: list[dict[str, object]] = []
        hashes: dict[str, str] = {}
        with torch.no_grad():
            for index, image_path in enumerate(image_paths, 1):
                image = img_load_rgb_as_tensor(str(image_path)).to(device="cpu", dtype=torch.float64)
                started = time.perf_counter()
                _edge, _angle, soft = alg_gfrcht(image, cfg)
                seconds = time.perf_counter() - started
                array = soft.squeeze().detach().cpu().numpy()
                with Image.open(image_path) as source:
                    expected = (source.height, source.width)
                if array.ndim != 2 or tuple(array.shape) != expected:
                    raise RuntimeError(f"invalid QFrD map shape for {image_path.stem}: {array.shape} vs {expected}")
                if not np.isfinite(array).all():
                    raise RuntimeError(f"non-finite QFrD map for {image_path.stem}")
                output = output_dir / f"{image_path.stem}.png"
                Image.fromarray(np.rint(np.clip(array, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L").save(output)
                hashes[image_path.stem] = _sha256(output)
                runtimes.append({"image_id": image_path.stem, "seconds": seconds})
                print(f"QFrD {index:03d}/{len(image_paths):03d} {image_path.stem} {seconds:.6f}s", flush=True)
    finally:
        if sys.path and sys.path[0] == str(AUTHOR_ROOT):
            sys.path.pop(0)

    with (output_dir / "per_image_runtime.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image_id", "seconds"])
        writer.writeheader()
        writer.writerows(runtimes)
    (output_dir / "map_hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    manifest = {
        "method": "QFrD exact author-code Fractional Dirac detector",
        "implementation_fidelity": "exact pinned author code; paper/code multiplication-order equivalence is not claimed",
        "training_class": "parameter-fixed but author-tuned", "author_source": provenance,
        "source_notice": "no explicit software license found; ignored local dependency, not redistributed",
        "fixed_parameters": {"alpha_1": 0.8, "alpha_2": 1.0, "mu": [0.0, 1.0, 1.0, 1.0], "pad": 64, "pad_mode": "replicate", "gauss_sigma": 2.0, "nms_radius": 1.5, "hysteresis_low": 0.8, "hysteresis_high": 2.5},
        "paper_code_order_caveat": "paper describes M(alpha,theta)Q; pinned core/q_gfrcht.py computes q_mul(Q, M_full)",
        "dataset": "BSDS500", "split": split, "bsds_ground_truth_read": False, "native_resolution": True,
        "output": "author thin_raw_crop soft NMS map, clipped to [0,1] and rounded directly to uint8 without per-image normalization",
        "n_maps": len(image_paths), "total_detector_seconds": sum(float(row["seconds"]) for row in runtimes),
        "torch_version": torch.__version__,
    }
    (output_dir / "export_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--split", default="val")
    args = parser.parse_args()
    export_qfrd_maps(Path(args.image_dir), Path(args.output_dir), split=args.split)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
