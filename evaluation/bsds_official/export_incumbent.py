from __future__ import annotations

"""Export the retained MFI-Edge incumbent as native-resolution BSDS soft maps.

The retained detector is reconstructed only from development data:
- UDED selection learns the analytical membership parameters/bank;
- the universally stable five-feature compact bank is retained;
- distorted Choquet gamma=0.55;
- context gate strength=2.0, floor=0.10;
- grayscale Scharr+NMS is the precise localizer.

No BSDS ground truth is read by this exporter. Images are processed at native
resolution and written as 8-bit soft PNGs in [0,255], matching the Berkeley
MATLAB evaluator's `double(imread(...))/255` input convention.
"""

from pathlib import Path
import argparse
import json
import sys

# This exporter is launched by absolute path from the official-evaluation
# module. In that mode Python places this file's directory, rather than the
# repository root, on sys.path even though the subprocess cwd is the root.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image
from skimage.io import imread

from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from run_stage12b_fuzzy_signature import prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage14c_positive_bank_pruning import (
    COMPACT_FEATURES,
    FLOOR,
    GAMMA,
    STRENGTH,
    _contexts,
    _filter_bank,
)
from src.bipolar_fuzzy import context_gate


def _save_soft_png(score: np.ndarray, path: Path) -> None:
    x = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(x)):
        raise RuntimeError(f"non-finite incumbent score for {path.stem}")
    x = np.clip(x, 0.0, 1.0)
    q = np.rint(x * 255.0).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(q, mode="L").save(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--max-side-development", type=int, default=256)
    ap.add_argument("--seed", type=int, default=20261006)
    args = ap.parse_args()

    image_dir = Path(args.image_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    uded_root = ensure_uded(Path(args.uded_root))
    raw = resize_items(load_uded(uded_root), args.max_side_development)
    selection, base_names = prepare(raw[0::2])
    positive, _negative = learn_banks(
        selection,
        base_names,
        args.seed,
        max_positive=10,
        max_negative=8,
        max_abs_corr=0.88,
    )
    compact = _filter_bank(positive, COMPACT_FEATURES)

    image_paths = sorted(image_dir.glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {image_dir}")

    for idx, path in enumerate(image_paths, start=1):
        iid = path.stem
        out = output_dir / f"{iid}.png"
        print(
            f"INCUMBENT_BSDS_EXPORT {idx:03d}/{len(image_paths):03d} {iid}",
            flush=True,
        )
        raw_item = {"id": iid, "img": imread(path)}
        prepared, names = prepare([raw_item])
        if list(names) != list(base_names):
            raise RuntimeError(f"feature-name mismatch while exporting BSDS image {iid}")
        item = prepared[0]
        ctx = _contexts([item], base_names, compact)[0]
        score = context_gate(item["scharr"], ctx, STRENGTH, FLOOR)
        _save_soft_png(score, out)

    manifest = {
        "method": "incumbent_compact_positive_choquet",
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "output": "8-bit soft PNG, no per-image normalization",
        "conditioning": "median3",
        "localizer": "grayscale Scharr+NMS",
        "compact_features": list(COMPACT_FEATURES),
        "aggregation": {
            "family": "distorted Choquet",
            "gamma": GAMMA,
            "gate_strength": STRENGTH,
            "gate_floor": FLOOR,
        },
        "development_source": "UDED selection only",
        "seed": args.seed,
        "n_maps": len(image_paths),
    }
    (output_dir / "export_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
