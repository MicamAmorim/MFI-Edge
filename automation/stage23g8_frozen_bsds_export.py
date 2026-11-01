from __future__ import annotations

"""Hash-validated export of frozen Stage-23G8 BSDS candidate maps."""

from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/local_dev/stage23g8_compass_persistence_logistic_additive/frozen_maps/stage23g8_compass_persistence_logistic_additive"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--split", default="val")
    args = parser.parse_args()
    if args.split != "val":
        raise RuntimeError("Stage-23G8 frozen candidate exporter is validation-only")
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
            print(f"STAGE23G8_BSDS skip complete {image_path.stem}", flush=True); continue
        temporary = target.with_suffix(".png.tmp"); shutil.copyfile(source, temporary)
        if sha256(temporary) != expected:
            raise RuntimeError(f"temporary export mismatch: {image_path.stem}")
        os.replace(temporary, target)
        print(f"STAGE23G8_BSDS reuse frozen {image_path.stem}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
