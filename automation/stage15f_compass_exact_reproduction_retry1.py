from __future__ import annotations

"""Finalize the frozen Stage-15f Compass maps after MATLAB exit corruption."""

from pathlib import Path
import csv
import hashlib
import json
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.stage15f_compass_build_preflight import (  # noqa: E402
    ARCHIVE_SHA256, AUTHOR_URL, AUTHOR_VENDOR, SOURCE_HASHES,
)
from evaluation.bsds_official.run_official_bsds import (  # noqa: E402
    DEFAULT_CONFIG, _ensure_benchmark_sources, _incumbent_predictions, _load_json,
)
from run_stage15f_compass_reproduction import (  # noqa: E402
    EXPERIMENT_ID, OUT, PREDICTIONS, _preview,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    cfg = _load_json(DEFAULT_CONFIG)
    bsds_root, _ = _ensure_benchmark_sources(cfg, "val")
    image_dir = bsds_root / "BSDS500" / "data" / "images" / "val"
    gt_dir = bsds_root / "BSDS500" / "data" / "groundTruth" / "val"
    images = sorted(image_dir.glob("*.jpg"))
    if len(images) != 100:
        raise RuntimeError(f"expected 100 BSDS500-val images, found {len(images)}")

    observed_sources = {relative: _sha256(AUTHOR_VENDOR / relative) for relative in SOURCE_HASHES}
    if observed_sources != SOURCE_HASHES:
        raise RuntimeError("pinned Compass source hashes do not match registration")

    runtime_path = PREDICTIONS / "per_image_runtime.csv"
    with runtime_path.open(newline="", encoding="utf-8") as handle:
        runtime_rows = list(csv.DictReader(handle))
    expected_ids = [path.stem for path in images]
    if [row["image_id"] for row in runtime_rows] != expected_ids:
        raise RuntimeError("frozen Compass runtime rows are incomplete or out of order")

    map_dir = PREDICTIONS / "compass"
    hashes: dict[str, str] = {}
    for image_path in images:
        prediction = map_dir / f"{image_path.stem}.png"
        if not prediction.is_file():
            raise RuntimeError(f"missing frozen Compass map: {prediction}")
        with Image.open(image_path) as image, Image.open(prediction) as result:
            if result.mode != "L" or result.size != image.size:
                raise RuntimeError(f"invalid frozen Compass map contract: {prediction}")
        hashes[image_path.stem] = _sha256(prediction)
    unexpected = sorted(path.stem for path in map_dir.glob("*.png") if path.stem not in hashes)
    if unexpected:
        raise RuntimeError(f"unexpected frozen Compass maps: {unexpected}")
    (PREDICTIONS / "map_hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")

    export = {
        "method": "Ruzon-Tomasi color Compass maximum-EMD strength",
        "implementation_fidelity": "unmodified hash-verified author C/MEX detector; repository adapter supplies compatible-ABI build, batch I/O, native-coordinate padding, validation, timing, and serialization",
        "training_class": "strictly untrained",
        "author_page": "https://ai.stanford.edu/~ruzon/compass/",
        "archive": {"url": AUTHOR_URL, "sha256": ARCHIVE_SHA256},
        "source_hashes": SOURCE_HASHES,
        "source_notice": "no explicit software license found; ignored local dependency, not redistributed",
        "fixed_parameters": {"sigma": 4, "radius": 12, "spacing": 1, "angle_degrees": 180, "wedges_per_quarter": 6, "max_clusters": 10},
        "dataset": "BSDS500", "split": "val", "bsds_ground_truth_read": False,
        "native_resolution": True,
        "output": "author-valid maximum-EMD strength zero-padded at the radius-12 border and directly rounded to uint8 [0,255], without per-image normalization",
        "author_rng": "unchanged compass.c srand(clock()) behavior; no seed suppression or repeat selection",
        "n_maps": len(images),
        "total_detector_seconds": sum(float(row["seconds"]) for row in runtime_rows),
        "recovery": {
            "kind": "attachment-only finalization of frozen maps",
            "source_event": EXPERIMENT_ID,
            "source_completion_marker": "STAGE15F_COMPASS_EXPORT_OK images=100",
            "source_process_exit": "0xc0000374 heap corruption after completion marker",
            "detector_rerun": False,
            "validation": "100 ordered runtime rows; 100 native-size grayscale PNG maps; hashes computed before attachment",
        },
    }
    (PREDICTIONS / "export_manifest.json").write_text(json.dumps(export, indent=2), encoding="utf-8")

    incumbent_dir, incumbent_provenance = _incumbent_predictions(cfg, image_dir=image_dir, gt_dir=gt_dir, split="val")
    preview = _preview(image_dir, gt_dir, incumbent_dir)
    manifest = {
        "schema_version": 1, "split": "val", "include_incumbent": True,
        "methods": [{"name": "stage15f_exact_author_compass", "prediction_dir": str(map_dir.relative_to(ROOT)).replace("\\", "/"), "exporter": "frozen maps finalized by automation/stage15f_compass_exact_reproduction_retry1.py"}],
    }
    manifest_path = OUT / "official_eval_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary = {
        "stage": "15f-compass-exact-reproduction-attachment-retry-1",
        "role": "matched_protocol_reproduction_attachment", "architecture_changed": False,
        "question": "What does the fixed published sigma-4 exact author Compass response obtain under the common BSDS500-validation path?",
        "implementation": export,
        "dataset": {"name": "BSDS500", "split": "validation", "role": "development/matched-protocol reproduction", "n_images": len(images), "protected_split_used": False, "native_resolution": True, "ground_truth_use_by_detector": False},
        "incumbent_export": incumbent_provenance, "preview": preview,
        "official_evaluation": {"status": "pending controller attachment", "protocol": "all annotations, 99 thresholds, maxDist=0.0075, thinning, native resolution", "stage15a_caveat": "the unmodified Windows matcher remains stochastic and reference-uncertified; the fixed-seed diagnostic matcher is forbidden", "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/")},
        "decision_semantics": "reproduction baseline only; retain results without tuning Compass or changing MFI before Stage 15o",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    retry_out = ROOT / "results" / "automation" / "stage15f_compass_exact_reproduction_retry1"
    retry_out.mkdir(parents=True, exist_ok=True)
    (retry_out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15F_COMPASS_FROZEN_MAPS_FINALIZED")
    print(OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
