from __future__ import annotations

"""Read-only preflight for the frozen Stage-12d BIPEDv2 replication."""

import argparse
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "datasets" / "BIPEDv2"
FROZEN = ROOT / "results" / "local_dev" / "stage12d_bipolar_cv" / "frozen_candidates.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--out", default=str(ROOT / "results" / "automation" / "stage13c_biped_preflight" / "summary.json"))
    args = parser.parse_args()
    root = Path(args.root)
    findings: dict[str, object] = {"stage": "13c-biped-preflight", "dataset": "BIPEDv2", "root": str(root), "split_role": "train=unused; test=frozen_external_replication", "checks": {}, "errors": []}
    errors: list[str] = findings["errors"]  # type: ignore[assignment]
    checks: dict[str, object] = findings["checks"]  # type: ignore[assignment]
    if not FROZEN.is_file():
        errors.append(f"Missing frozen Stage-12d candidate file: {FROZEN}")
    else:
        checks["frozen_candidates"] = str(FROZEN)

    # Canonical BIPEDv2 layout documented by the dataset authors and DexiNed.
    layout = root / "edges"
    for split, expected in (("train", 200), ("test", 50)):
        image_dir = layout / "imgs" / split / "rgbr" / ("real" if split == "train" else "")
        gt_dir = layout / "edge_maps" / split / "rgbr" / ("real" if split == "train" else "")
        image_dir, gt_dir = Path(str(image_dir).rstrip("\\/")), Path(str(gt_dir).rstrip("\\/"))
        images = sorted(p for p in image_dir.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"}) if image_dir.is_dir() else []
        gts = sorted(p for p in gt_dir.glob("*") if p.suffix.lower() in {".png", ".bmp", ".jpg", ".jpeg"}) if gt_dir.is_dir() else []
        gt_by_stem = {p.stem: p for p in gts}
        missing = [p.name for p in images if p.stem not in gt_by_stem]
        extra = sorted(p.name for p in gts if p.stem not in {im.stem for im in images})
        check = {"image_dir": str(image_dir), "gt_dir": str(gt_dir), "images": len(images), "ground_truth": len(gts), "expected_images": expected, "missing_gt": missing[:10], "unpaired_gt": extra[:10]}
        checks[split] = check
        if len(images) != expected or len(gts) != expected or missing or extra:
            errors.append(f"{split}: expected {expected} paired image/GT files; found {len(images)} images, {len(gts)} GTs, missing={len(missing)}, extra={len(extra)}")
        for image_path in images:
            try:
                with Image.open(image_path) as im:
                    if im.size != (1280, 720):
                        errors.append(f"Unexpected image size {im.size}: {image_path}")
                        break
                gt_path = gt_by_stem.get(image_path.stem)
                if gt_path:
                    with Image.open(gt_path) as im:
                        if im.size != (1280, 720):
                            errors.append(f"Unexpected GT size {im.size}: {gt_path}")
                            break
            except Exception as exc:
                errors.append(f"Unreadable image/GT near {image_path}: {exc}")
                break
    findings["ready"] = not errors
    findings["protocol"] = "Use only the author-designated test split for final frozen replication; train split is not used for fitting/calibration. Preserve native 1280x720 resolution. Report the repository's fixed threshold metrics as transfer diagnostics; do not select thresholds on BIPED test."
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(findings, indent=2), encoding="utf-8")
    print(json.dumps(findings, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
