from __future__ import annotations

"""Export the fixed Stage-15a Canny and repository-Scharr audit baselines.

Neither method reads BSDS ground truth.  The Canny map is deliberately binary:
it audits the complete classical detector at one preregistered operating point,
not a soft ranking surrogate.  The Scharr map exactly follows the incumbent's
localizer path before contextual gating, including median conditioning and the
detector's intrinsic robust response scaling.  PNG export adds no normalization.
"""

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image
from skimage import feature
from skimage.io import imread

from src.classical_detectors import detector_score, gray01
from src.conditioning import apply_conditioning
from src.postprocess import gradient_orientation, non_maximum_suppression


CANNY_PARAMETERS = {
    "sigma": 1.0,
    "low_threshold": 0.10,
    "high_threshold": 0.20,
    "use_quantiles": False,
    "mode": "constant",
    "cval": 0.0,
}


def baseline_score(image: np.ndarray, method: str) -> np.ndarray:
    name = str(method).lower()
    if name == "canny":
        return feature.canny(gray01(image), **CANNY_PARAMETERS).astype(np.float32)
    if name == "scharr":
        conditioned = apply_conditioning(image, "median", size=3)
        orientation = gradient_orientation(conditioned, 1.0)
        response = detector_score(conditioned, "scharr", 1.0)
        return non_maximum_suppression(response, orientation).astype(np.float32)
    raise ValueError(f"unknown Stage-15a baseline: {method}")


def save_soft_png(score: np.ndarray, path: Path) -> None:
    value = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(value)):
        raise RuntimeError(f"non-finite score for {path.stem}")
    quantized = np.rint(np.clip(value, 0.0, 1.0) * 255.0).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(quantized, mode="L").save(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--split", default="val")
    parser.add_argument("--method", choices=("canny", "scharr"), required=True)
    args = parser.parse_args()

    image_dir = Path(args.image_dir)
    output_dir = Path(args.output_dir)
    image_paths = sorted(image_dir.glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no JPG images found in {image_dir}")

    for index, image_path in enumerate(image_paths, start=1):
        print(
            f"STAGE15A_EXPORT {args.method} {index:03d}/{len(image_paths):03d} "
            f"{image_path.stem}",
            flush=True,
        )
        save_soft_png(
            baseline_score(imread(image_path), args.method),
            output_dir / f"{image_path.stem}.png",
        )

    metadata = {
        "stage": "15a",
        "method": args.method,
        "training_class": "strictly untrained",
        "split": args.split,
        "ground_truth_read": False,
        "native_resolution": True,
        "png_export": "uint8 [0,255], no export-time per-image normalization",
        "parameters": (
            CANNY_PARAMETERS
            if args.method == "canny"
            else {
                "conditioning": "median3",
                "response": "skimage Scharr magnitude with repository robust01 scaling",
                "orientation": "sigma-1 smoothed gradient",
                "localization": "repository four-direction NMS",
            }
        ),
        "interpretation": (
            "fixed binary full-Canny operating-point audit"
            if args.method == "canny"
            else "ungated incumbent localizer audit"
        ),
        "n_maps": len(image_paths),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "export_manifest.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
