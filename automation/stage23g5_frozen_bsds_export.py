from __future__ import annotations

"""Hash-validated export of frozen Stage-23G5 BSDS candidate maps."""

from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/local_dev/stage23g5_sco_persistence_equal_mean/frozen_maps/stage23g5_sco_persistence_equal_mean"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--split", default="val")
    args = ap.parse_args()
    if args.split != "val":
        raise RuntimeError("Stage-23G5 frozen candidate exporter is validation-only")
    images = sorted(Path(args.image_dir).glob("*.jpg"))
    if len(images) != 100:
        raise RuntimeError(f"expected 100 BSDS500-val images, found {len(images)}")
    output = Path(args.output_dir); output.mkdir(parents=True, exist_ok=True)
    for image_path in images:
        source = SOURCE / f"{image_path.stem}.png"
        sidecar = source.with_suffix(".json")
        if not source.is_file() or not sidecar.is_file():
            raise RuntimeError(f"missing frozen candidate artifact: {image_path.stem}")
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        expected = record.get("png_sha256")
        if not expected or sha256(source) != expected:
            raise RuntimeError(f"frozen candidate hash mismatch: {image_path.stem}")
        with Image.open(image_path) as image, Image.open(source) as score:
            if score.mode != "L" or score.size != image.size:
                raise RuntimeError(f"frozen candidate shape mismatch: {image_path.stem}")
        target = output / source.name
        if target.exists():
            if sha256(target) != expected:
                raise RuntimeError(f"existing export mismatch: {image_path.stem}")
            print(f"STAGE23G5_BSDS skip complete {image_path.stem}", flush=True); continue
        tmp = target.with_suffix(".png.tmp"); shutil.copyfile(source, tmp)
        if sha256(tmp) != expected:
            raise RuntimeError(f"temporary export mismatch: {image_path.stem}")
        os.replace(tmp, target)
        print(f"STAGE23G5_BSDS reuse frozen {image_path.stem}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
