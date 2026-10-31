from __future__ import annotations

"""Reuse the frozen exact Stage-15E SCO maps for the Stage-23G3 attachment."""

from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/local_dev/stage15e_co_sco_exact_reproduction/predictions/sco"
HASHES = ROOT / "results/local_dev/stage15e_co_sco_exact_reproduction/predictions/map_hashes.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--split", default="val")
    args = parser.parse_args()
    if args.split != "val":
        raise RuntimeError("Stage-23G3 frozen SCO exporter is validation-only")
    expected = json.loads(HASHES.read_text(encoding="utf-8"))["sco"]
    images = sorted(Path(args.image_dir).glob("*.jpg"))
    if len(images) != 100:
        raise RuntimeError(f"expected 100 BSDS500-val images, found {len(images)}")
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for image_path in images:
        image_id = image_path.stem
        source = SOURCE / f"{image_id}.png"
        if image_id not in expected or sha256(source) != expected[image_id]:
            raise RuntimeError(f"frozen Stage-15E SCO hash mismatch: {image_id}")
        with Image.open(image_path) as image, Image.open(source) as score:
            if score.mode != "L" or score.size != image.size:
                raise RuntimeError(f"frozen Stage-15E SCO shape mismatch: {image_id}")
        target = output / source.name
        if target.exists():
            if sha256(target) != expected[image_id]:
                raise RuntimeError(f"existing exported SCO map mismatch: {image_id}")
            print(f"STAGE23G3_BSDS skip complete {image_id}", flush=True)
            continue
        temporary = target.with_suffix(".png.tmp")
        shutil.copyfile(source, temporary)
        if sha256(temporary) != expected[image_id]:
            raise RuntimeError(f"temporary SCO copy hash mismatch: {image_id}")
        os.replace(temporary, target)
        print(f"STAGE23G3_BSDS reuse frozen {image_id}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
