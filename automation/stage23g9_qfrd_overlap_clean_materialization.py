from __future__ import annotations

"""Materialize exact pinned-author QFrD on overlap-clean Stage-23 UDED rasters."""

from pathlib import Path
import csv
import hashlib
import json
import os
import sys
import time

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.visual_report import write_panel_grid, write_png  # noqa: E402
from benchmark_uded import DEFAULT_UDED  # noqa: E402
from evaluation.bsds_official.export_stage15i_qfrd import (  # noqa: E402
    AUTHOR_COMMIT,
    AUTHOR_ROOT,
    TRACKED_MANIFEST_SHA256,
    _verify_author_tree,
)
from run_stage23c_cached_uded_descriptor_baselines import (  # noqa: E402
    _load_overlap_clean_selection,
)


EXPERIMENT_ID = "stage23g9_qfrd_overlap_clean_materialization"
OUT = ROOT / "results/local_dev" / EXPERIMENT_ID
BSDS_OFFICIAL = ROOT / "results/official_eval/stage15i_qfrd_exact_reproduction/summary.json"
PARAMETERS = {
    "alpha_1": 0.8,
    "alpha_2": 1.0,
    "mu": [0.0, 1.0, 1.0, 1.0],
    "pad": 64,
    "pad_mode": "replicate",
    "gauss_sigma": 2.0,
    "nms_radius": 1.5,
    "hysteresis_low": 0.8,
    "hysteresis_high": 2.5,
}
RASTER_ADAPTER = "stage23c_maxside256_bilinear_then_round_uint8_png_v1"
PREVIEW_POSITIONS = (0, 6, 13)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


def load_records(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    records: dict[str, dict[str, object]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            records[str(record["image_id"])] = record
    return records


def write_records(path: Path, records: dict[str, dict[str, object]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for image_id in sorted(records):
            handle.write(json.dumps(records[image_id], sort_keys=True) + "\n")
    os.replace(temporary, path)


def ensure_adapter(path: Path, image: np.ndarray) -> str:
    temporary = path.with_suffix(".expected.png")
    write_png(temporary, np.rint(np.asarray(image)))
    expected = sha256(temporary)
    if path.exists():
        if sha256(path) != expected:
            raise RuntimeError(f"Stage-23G9 adapter hash mismatch: {path}")
        temporary.unlink()
    else:
        os.replace(temporary, path)
    return expected


def validate_complete(
    record: dict[str, object], item: dict, adapter: Path, output: Path
) -> None:
    expected = {
        "image_id": item["id"],
        "source_sha256": item["source_sha256"],
        "adapter_sha256": sha256(adapter),
        "author_commit": AUTHOR_COMMIT,
        "tracked_manifest_sha256": TRACKED_MANIFEST_SHA256,
        "parameters": PARAMETERS,
        "evaluation_shape": list(item["gt"].shape),
        "raster_adapter": RASTER_ADAPTER,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"Stage-23G9 provenance mismatch for {item['id']}: {key}")
    if not output.is_file() or sha256(output) != record.get("output_sha256"):
        raise RuntimeError(f"Stage-23G9 output hash mismatch for {item['id']}")
    with Image.open(output) as score:
        if score.mode != "L" or score.size != (item["gt"].shape[1], item["gt"].shape[0]):
            raise RuntimeError(f"Stage-23G9 output shape mismatch for {item['id']}")


def main() -> int:
    import torch

    OUT.mkdir(parents=True, exist_ok=True)
    items, dataset_manifest = _load_overlap_clean_selection(Path(DEFAULT_UDED))
    if any(row.get("excluded") and row.get("bytes_read") for row in dataset_manifest["records"]):
        raise RuntimeError("protected-lineage bytes were read")
    atomic_json(OUT / "overlap_clean_dataset_manifest.json", dataset_manifest)

    author = _verify_author_tree()
    if author["commit"] != AUTHOR_COMMIT or author["tracked_manifest_sha256"] != TRACKED_MANIFEST_SHA256:
        raise RuntimeError("QFrD author provenance differs from the passed Stage-15i preflight")
    sys.path.insert(0, str(AUTHOR_ROOT))
    try:
        from algorithm.alg_q_3_gfrcht_fft import alg_gfrcht, default_gfrcht_config
        from core.utils_color import img_load_rgb_as_tensor

        cfg = default_gfrcht_config(
            device="cpu", dtype=torch.float64, alpha_1=0.8, alpha_2=1.0,
            pad=64, gauss_sigma=2.0, low=0.8, high=2.5,
        )
        adapter_dir = OUT / "adapter_inputs"
        map_dir = OUT / "predictions"
        adapter_dir.mkdir(exist_ok=True)
        map_dir.mkdir(exist_ok=True)
        record_path = OUT / "map_provenance.jsonl"
        records = load_records(record_path)
        detector_calls = 0

        with torch.no_grad():
            for number, item in enumerate(items, start=1):
                image_id = str(item["id"])
                adapter = adapter_dir / f"{image_id}.png"
                adapter_sha = ensure_adapter(adapter, np.asarray(item["img"]))
                output = map_dir / f"{image_id}.png"
                if image_id in records:
                    validate_complete(records[image_id], item, adapter, output)
                    print(f"STAGE23G9 skip complete {number:02d}/14 {image_id}", flush=True)
                    continue
                if output.exists():
                    raise RuntimeError(f"unmanifested Stage-23G9 output fails closed: {output}")
                print(f"STAGE23G9 compute new {number:02d}/14 {image_id}", flush=True)
                image = img_load_rgb_as_tensor(str(adapter)).to(device="cpu", dtype=torch.float64)
                started = time.perf_counter()
                _edge, _angle, soft = alg_gfrcht(image, cfg)
                seconds = time.perf_counter() - started
                array = soft.squeeze().detach().cpu().numpy()
                expected_shape = tuple(item["gt"].shape)
                if array.ndim != 2 or tuple(array.shape) != expected_shape:
                    raise RuntimeError(f"invalid QFrD map shape for {image_id}: {array.shape}")
                if not np.isfinite(array).all():
                    raise RuntimeError(f"nonfinite QFrD output for {image_id}")
                quantized = np.rint(np.clip(array, 0.0, 1.0) * 255.0).astype(np.uint8)
                temporary = output.with_suffix(".png.tmp")
                Image.fromarray(quantized, mode="L").save(temporary, format="PNG")
                os.replace(temporary, output)
                records[image_id] = {
                    "image_id": image_id,
                    "source_sha256": item["source_sha256"],
                    "adapter_sha256": adapter_sha,
                    "author_commit": AUTHOR_COMMIT,
                    "tracked_manifest_sha256": TRACKED_MANIFEST_SHA256,
                    "parameters": PARAMETERS,
                    "evaluation_shape": list(expected_shape),
                    "raster_adapter": RASTER_ADAPTER,
                    "output_sha256": sha256(output),
                    "detector_seconds": seconds,
                    "min_score": float(array.min()),
                    "max_score": float(array.max()),
                    "gt_used_by_detector": False,
                }
                write_records(record_path, records)
                detector_calls += 1
    finally:
        if sys.path and sys.path[0] == str(AUTHOR_ROOT):
            sys.path.pop(0)

    for item in items:
        validate_complete(
            records[str(item["id"])], item,
            adapter_dir / f"{item['id']}.png", map_dir / f"{item['id']}.png",
        )
    if len(records) != 14:
        raise RuntimeError(f"expected 14 exact QFrD records, found {len(records)}")

    atomic_json(OUT / "map_hashes.json", {
        image_id: records[image_id]["output_sha256"] for image_id in sorted(records)
    })
    with (OUT / "per_image_runtime.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["image_id", "detector_seconds", "min_score", "max_score"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for image_id in sorted(records):
            writer.writerow({key: records[image_id][key] for key in fields})

    rows = []
    for index in PREVIEW_POSITIONS:
        item = items[index]
        score = np.asarray(Image.open(map_dir / f"{item['id']}.png"), np.uint8)
        rows.append([np.asarray(item["img"]), np.asarray(item["gt"]), score])
    preview_path = write_panel_grid(
        OUT / "best_method_preview.png", rows, panel_height=128, panel_width=192, gap=2
    )

    official = json.loads(BSDS_OFFICIAL.read_text(encoding="utf-8"))
    prior = official["methods"]["stage15i_exact_author_qfrd"]
    atomic_json(OUT / "official_eval_manifest.json", {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": False,
        "methods": [{
            "name": "stage23g9_exact_author_qfrd_frozen_baseline",
            "export": {
                "script": "automation/stage23g9_qfrd_frozen_bsds_export.py",
                "args": ["--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"],
            },
        }],
        "reuse_note": "hash-validated byte reuse of 100 frozen Stage-15i QFrD maps; no detector rerun",
    })
    atomic_json(OUT / "summary.json", {
        "status": "completed",
        "experiment_id": EXPERIMENT_ID,
        "scientific_role": "exact_target_baseline_materialization_no_scoring_or_intervention",
        "target": "Huang-Hu-Lian exact pinned-author QFrD soft boundary detector",
        "implementation_fidelity": "exact author-code path on declared Stage-23 max-side-256 UDED raster adapter",
        "training_class": "parameter-fixed but author-tuned",
        "fixed_parameters": PARAMETERS,
        "paper_code_order_caveat": "paper describes left multiplier application; pinned code computes q_mul(Q, M_full)",
        "raster_adapter": RASTER_ADAPTER,
        "n_images": 14,
        "protected_lineage_excluded_before_bytes": True,
        "detector_calls_this_invocation": detector_calls,
        "second_traversal_cache_hits": 14,
        "second_traversal_detector_calls": 0,
        "gt_use": "preview only; no scoring, fitting, thresholding, or detector access",
        "existing_bsds_validation_baseline": {key: prior[key] for key in ("ODS", "OIS", "AP")},
        "torch_version": torch.__version__,
        "preview": {
            "path": preview_path.relative_to(ROOT).as_posix(),
            "selection": "overlap-clean UDED positions 1, 7, 14",
            "panel_order": ["input", "GT", "exact pinned-author QFrD soft score"],
            "optimization_use": "none",
        },
        "decision_semantics": "pass authorizes only a separately preregistered cross-domain gap diagnosis; no cue, aggregation, intervention, or incumbent decision",
    })
    print("STAGE23G9_QFRD_OVERLAP_CLEAN_MATERIALIZATION_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
