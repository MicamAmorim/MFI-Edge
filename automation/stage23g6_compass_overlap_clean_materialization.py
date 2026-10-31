from __future__ import annotations

"""Materialize exact author Compass on Stage-23 overlap-clean UDED rasters."""

from pathlib import Path
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.stage15f_compass_build_preflight import (  # noqa: E402
    ARCHIVE_SHA256,
    AUTHOR_VENDOR,
    SOURCE_HASHES,
)
from automation.visual_report import write_panel_grid, write_png  # noqa: E402
from benchmark_uded import DEFAULT_UDED  # noqa: E402
from evaluation.bsds_official.export_stage15f_compass import DEFAULT_MATLAB  # noqa: E402
from run_stage23c_cached_uded_descriptor_baselines import (  # noqa: E402
    _load_overlap_clean_selection,
)


EXPERIMENT_ID = "stage23g6_compass_overlap_clean_materialization"
OUT = ROOT / "results/local_dev" / EXPERIMENT_ID
MATLAB_WRAPPER = ROOT / "evaluation/bsds_official/matlab"
BSDS_OFFICIAL = ROOT / "results/official_eval/stage15f_compass_exact_reproduction_retry1/summary.json"
PARAMETERS = {
    "sigma": 4, "radius": 12, "spacing": 1, "angle_degrees": 180,
    "wedges_per_quarter": 6, "orientation_step_degrees": 15, "max_clusters": 10,
}
RASTER_ADAPTER = "stage23c_maxside256_bilinear_then_round_uint8_png_v1"
PREVIEW_POSITIONS = (0, 6, 13)
MARKER = re.compile(
    r"STAGE23G6_COMPASS_OK seconds=([0-9.eE+-]+) min=([0-9.eE+-]+) max=([0-9.eE+-]+)"
)


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


def source_bundle_hash() -> str:
    digest = hashlib.sha256()
    for name, value in sorted(SOURCE_HASHES.items()):
        digest.update(name.encode("utf-8")); digest.update(value.encode("ascii"))
    return digest.hexdigest()


def matlab_quote(value: Path | str) -> str:
    return str(value).replace("'", "''").replace("\\", "/")


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
            raise RuntimeError(f"Stage-23G6 adapter hash mismatch: {path}")
        temporary.unlink()
    else:
        os.replace(temporary, path)
    return expected


def validate_sources() -> str:
    if not AUTHOR_VENDOR.is_dir():
        raise FileNotFoundError("pinned Compass author tree is absent; rerun only its source materialization preflight")
    observed = {name: sha256(AUTHOR_VENDOR / name) for name in SOURCE_HASHES}
    if observed != SOURCE_HASHES:
        raise RuntimeError("pinned Compass source hashes do not match Stage-15F registration")
    return source_bundle_hash()


def validate_complete(record: dict[str, object], item: dict, adapter: Path, output: Path,
                      bundle_hash: str) -> None:
    expected = {
        "image_id": item["id"], "source_sha256": item["source_sha256"],
        "adapter_sha256": sha256(adapter), "author_archive_sha256": ARCHIVE_SHA256,
        "author_source_bundle_sha256": bundle_hash, "parameters": PARAMETERS,
        "evaluation_shape": list(item["gt"].shape), "raster_adapter": RASTER_ADAPTER,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"Stage-23G6 provenance mismatch for {item['id']}: {key}")
    if not output.is_file() or sha256(output) != record.get("output_sha256"):
        raise RuntimeError(f"Stage-23G6 output hash mismatch for {item['id']}")
    with Image.open(output) as score:
        if score.mode != "L" or score.size != (item["gt"].shape[1], item["gt"].shape[0]):
            raise RuntimeError(f"Stage-23G6 output shape mismatch for {item['id']}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    items, dataset_manifest = _load_overlap_clean_selection(Path(DEFAULT_UDED))
    if any(row.get("excluded") and row.get("bytes_read") for row in dataset_manifest["records"]):
        raise RuntimeError("protected-lineage bytes were read")
    atomic_json(OUT / "overlap_clean_dataset_manifest.json", dataset_manifest)
    bundle_hash = validate_sources()
    source_dir = AUTHOR_VENDOR / "ruzon"
    adapter_dir, map_dir, build_dir = OUT / "adapter_inputs", OUT / "predictions", OUT / "matlab_build"
    adapter_dir.mkdir(exist_ok=True); map_dir.mkdir(exist_ok=True); build_dir.mkdir(exist_ok=True)
    record_path = OUT / "map_provenance.jsonl"
    records = load_records(record_path)
    matlab = Path(os.environ.get("MATLAB_EXE", str(DEFAULT_MATLAB))).resolve()
    if not matlab.exists():
        raise FileNotFoundError(f"MATLAB executable missing: {matlab}")
    prefdir = OUT / "matlab_preferences"; prefdir.mkdir(exist_ok=True)
    env = os.environ.copy(); env["MATLAB_PREFDIR"] = str(prefdir)

    detector_calls = 0
    for number, item in enumerate(items, start=1):
        image_id = str(item["id"])
        adapter = adapter_dir / f"{image_id}.png"
        adapter_sha = ensure_adapter(adapter, np.asarray(item["img"]))
        output = map_dir / f"{image_id}.png"
        if image_id in records:
            validate_complete(records[image_id], item, adapter, output, bundle_hash)
            print(f"STAGE23G6 skip complete {number:02d}/14 {image_id}", flush=True)
            continue
        if output.exists():
            raise RuntimeError(f"unmanifested Stage-23G6 output fails closed: {output}")
        print(f"STAGE23G6 compute new {number:02d}/14 {image_id}", flush=True)
        expression = (
            f"addpath('{matlab_quote(MATLAB_WRAPPER)}');"
            f"stage23g6_export_compass_one('{matlab_quote(source_dir)}','{matlab_quote(build_dir)}',"
            f"'{matlab_quote(adapter)}','{matlab_quote(output)}');"
        )
        started = time.perf_counter()
        result = subprocess.run(
            [str(matlab), "-batch", expression], cwd=ROOT, env=env, text=True,
            encoding="utf-8", errors="replace", stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=45 * 60, check=False,
        )
        wall = time.perf_counter() - started
        match = MARKER.search(result.stdout)
        if not match or not output.is_file():
            raise RuntimeError(f"Compass failed for {image_id}:\n" + "\n".join(result.stdout.splitlines()[-100:]))
        if result.returncode not in (0, 3221226356):
            raise RuntimeError(
                f"Compass emitted a completion marker but exited unexpectedly for {image_id}: "
                f"{result.returncode}\n" + "\n".join(result.stdout.splitlines()[-100:])
            )
        with Image.open(output) as score:
            array = np.asarray(score)
            if score.mode != "L" or score.size != (item["gt"].shape[1], item["gt"].shape[0]):
                raise RuntimeError(f"invalid Compass output for {image_id}")
            if not np.isfinite(array).all():
                raise RuntimeError(f"nonfinite Compass output for {image_id}")
        records[image_id] = {
            "image_id": image_id, "source_sha256": item["source_sha256"],
            "adapter_sha256": adapter_sha, "author_archive_sha256": ARCHIVE_SHA256,
            "author_source_bundle_sha256": bundle_hash, "parameters": PARAMETERS,
            "evaluation_shape": list(item["gt"].shape), "raster_adapter": RASTER_ADAPTER,
            "output_sha256": sha256(output), "detector_seconds": float(match.group(1)),
            "wall_seconds": wall, "min_strength": float(match.group(2)),
            "max_strength": float(match.group(3)), "matlab_returncode": result.returncode,
            "post_marker_nonzero_exit": result.returncode == 3221226356,
            "author_rng": "unchanged srand(clock())",
            "gt_used_by_detector": False,
        }
        write_records(record_path, records)
        detector_calls += 1

    for item in items:
        validate_complete(records[str(item["id"])], item,
                          adapter_dir / f"{item['id']}.png", map_dir / f"{item['id']}.png",
                          bundle_hash)
    if len(records) != 14:
        raise RuntimeError(f"expected 14 exact Compass records, found {len(records)}")

    atomic_json(OUT / "map_hashes.json", {
        image_id: records[image_id]["output_sha256"] for image_id in sorted(records)
    })
    with (OUT / "per_image_runtime.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["image_id", "detector_seconds", "wall_seconds", "min_strength", "max_strength",
                  "matlab_returncode", "post_marker_nonzero_exit"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
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
    prior = official["methods"]["stage15f_exact_author_compass"]
    manifest = {
        "schema_version": 1, "split": "val", "include_incumbent": False,
        "methods": [{
            "name": "stage23g6_exact_author_compass_frozen_baseline",
            "export": {"script": "automation/stage23g6_compass_frozen_bsds_export.py",
                       "args": ["--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"]},
        }],
        "reuse_note": "hash-validated byte reuse of 100 frozen Stage-15F Compass maps; no detector rerun",
    }
    atomic_json(OUT / "official_eval_manifest.json", manifest)
    summary = {
        "status": "completed", "experiment_id": EXPERIMENT_ID,
        "scientific_role": "exact_target_baseline_materialization_no_scoring_or_intervention",
        "target": "Ruzon-Tomasi exact author Compass maximum-EMD color-distribution detector",
        "implementation_fidelity": "exact author detector on declared Stage-23 max-side-256 UDED raster adapter",
        "fixed_parameters": PARAMETERS, "author_rng": "unchanged clock-seeded clustering; one persisted draw per image",
        "raster_adapter": RASTER_ADAPTER, "n_images": 14,
        "protected_lineage_excluded_before_bytes": True,
        "detector_calls_this_invocation": detector_calls,
        "second_traversal_cache_hits": 14, "second_traversal_detector_calls": 0,
        "gt_use": "preview only; no scoring, fitting, thresholding, or detector access",
        "existing_bsds_validation_baseline": {key: prior[key] for key in ("ODS", "OIS", "AP")},
        "preview": {"path": preview_path.relative_to(ROOT).as_posix(),
                    "selection": "overlap-clean UDED positions 1, 7, 14",
                    "panel_order": ["input", "GT", "exact author Compass maximum-EMD score"],
                    "optimization_use": "none"},
        "decision_semantics": "pass authorizes only a separately preregistered cross-domain gap diagnosis; no cue, aggregation, intervention, or incumbent decision",
    }
    atomic_json(OUT / "summary.json", summary)
    print("STAGE23G6_COMPASS_OVERLAP_CLEAN_MATERIALIZATION_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
