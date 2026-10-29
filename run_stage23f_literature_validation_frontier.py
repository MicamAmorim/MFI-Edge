from __future__ import annotations

"""Stage 23F: cache and freeze the Stage-23E frontier on BSDS500 validation."""

from pathlib import Path
import argparse
import hashlib
import json
import sys
import time

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED
from run_stage23c_cached_uded_descriptor_baselines import (
    _implementation_hash, _load_overlap_clean_selection, _sha256,
)
from run_stage23e_cached_descriptor_aggregator_landscape import (
    _aggregate, _fit_model, _membership, _model_hash,
)
from src.stage23_cache import CacheIdentity, get_or_compute, validate_manifest_record
from src.stage23_descriptors import compute_descriptor, descriptor_parameters

EXPERIMENT_ID = "stage23f_literature_validation_frontier"
OUT = ROOT / "results/local_dev" / EXPERIMENT_ID
CACHE_ROOT = ROOT / "cache/local_dev/stage23"
FRONTIER_PATH = ROOT / "results/local_dev/stage23e_cached_descriptor_aggregator_landscape/stage23f_frontier.json"
DEFAULT_IMAGE_DIR = ROOT / "evaluation/bsds_official/vendor/BSDS500/BSDS500/data/images/val"
SEED = 20261029
PREVIEW_POSITIONS = (0, 49, 99)


def _read_image(path: Path) -> np.ndarray:
    with Image.open(path) as handle:
        return np.asarray(handle.convert("RGB"))


def _descriptor_identity(image_id: str, source_hash: str, descriptor_id: str, code_hash: str) -> CacheIdentity:
    return CacheIdentity(
        dataset="BSDS500", split="val", image_id=image_id,
        artifact_type="descriptors", artifact_id=descriptor_id,
        preprocessing_id="native_resolution_registered_descriptor_preprocessing_v1",
        parameters={"native_resolution": True, **descriptor_parameters(descriptor_id)},
        implementation="src.stage23_descriptors.compute_descriptor",
        implementation_version="stage23f_frozen_frontier_v1", code_version=code_hash,
        source_sha256=source_hash, representation="raw_evidence", gt_used=False,
    )


def _aggregate_identity(image_id: str, source_hash: str, set_id: str, descriptors: list[str],
                        family: str, model_hash: str, code_hash: str) -> CacheIdentity:
    return CacheIdentity(
        dataset="BSDS500", split="val", image_id=image_id,
        artifact_type="transforms", artifact_id=f"{set_id}__{family}",
        preprocessing_id="stage23e_common_membership_then_frozen_aggregation_v1",
        parameters={"descriptors": descriptors, "aggregator": family, "model_sha256": model_hash},
        implementation="run_stage23f_literature_validation_frontier.aggregate",
        implementation_version="stage23f_frozen_frontier_v1", code_version=code_hash,
        source_sha256=source_hash, representation="aggregated_score", gt_used=False,
    )


def _png(path: Path, score: np.ndarray) -> str:
    value = np.clip(np.rint(np.asarray(score, float) * 255.0), 0, 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(value, mode="L").save(path)
    return _sha256(path)


def _fit_frontier(items: list[dict], frontier: dict) -> tuple[dict, list[dict]]:
    needed = sorted({name for cell in frontier["validation_cells"] for name in cell["descriptors"]})
    code_hash = _implementation_hash()
    from run_stage23c_cached_uded_descriptor_baselines import _identity
    from src.stage23_cache import load_cached
    maps = {name: [] for name in needed}
    for item in items:
        for name in needed:
            value = load_cached(_identity(item, name, code_hash), CACHE_ROOT)
            if value is None:
                raise RuntimeError(f"forbidden missing Stage-23C UDED cache: {name}/{item['id']}")
            maps[name].append(np.asarray(value, np.float32))
    models, rows = {}, []
    for order, primary in enumerate(frontier["primary_cells"], 1):
        spec = {"set_id": primary["set_id"], "descriptors": tuple(primary["descriptors"])}
        model = _fit_model(np.arange(len(items)), spec, maps, items, SEED + order)
        if not model["logistic_ok"] or not model["capacity_ok"]:
            raise RuntimeError(f"frontier fit failed: {spec['set_id']}")
        digest = _model_hash(spec, model)
        models[spec["set_id"]] = model
        rows.append({
            "set_id": spec["set_id"], "descriptors": list(spec["descriptors"]),
            "primary_aggregator": primary["aggregator"], "model_sha256": digest,
            "membership_midpoint": model["membership"]["midpoint"].tolist(),
            "membership_scale": model["membership"]["scale"].tolist(),
            "logistic_beta": model["beta"].tolist(),
            "capacity_table": model["capacity"]["capacity_table"],
        })
    return models, rows


def main() -> int:
    global OUT, CACHE_ROOT
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--image-dir", default=str(DEFAULT_IMAGE_DIR))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--cache-root", default=str(CACHE_ROOT))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(); OUT, CACHE_ROOT = Path(args.out), Path(args.cache_root)
    frontier = json.loads(FRONTIER_PATH.read_text(encoding="utf-8"))
    if len(frontier["primary_cells"]) != 3 or len(frontier["validation_cells"]) != 6:
        raise RuntimeError("Stage-23E frontier cardinality drift")
    if args.smoke:
        assert all(c["aggregator"] in {"minimum_conjunction", "nonnegative_logistic_additive", "median_owa", "equal_arithmetic_mean"} for c in frontier["validation_cells"])
        print("STAGE23F_SMOKE_OK"); return 0

    image_dir = Path(args.image_dir)
    images = sorted(image_dir.glob("*.jpg"))
    if len(images) != 100:
        raise RuntimeError(f"expected 100 BSDS validation images, found {len(images)} at {image_dir}")
    OUT.mkdir(parents=True, exist_ok=True)
    uded, manifest = _load_overlap_clean_selection(Path(args.uded_root))
    if any(r.get("excluded") and r.get("bytes_read") for r in manifest["records"]):
        raise RuntimeError("protected lineage bytes read")
    models, fit_rows = _fit_frontier(uded, frontier)
    (OUT / "frontier_fit_parameters.json").write_text(json.dumps(fit_rows, indent=2), encoding="utf-8")

    needed = sorted({name for cell in frontier["validation_cells"] for name in cell["descriptors"]})
    descriptor_code = _implementation_hash()
    runner_code = hashlib.sha256((ROOT / __file__).read_bytes()).hexdigest()
    aggregate_code = hashlib.sha256(f"{runner_code}:{descriptor_code}".encode("ascii")).hexdigest()
    desc_rows, agg_rows, hash_rows, previews = [], [], [], []
    for position, path in enumerate(images, 1):
        started = time.perf_counter(); image_id, source_hash = path.stem, _sha256(path)
        image = _read_image(path); raw = {}
        for name in needed:
            identity = _descriptor_identity(image_id, source_hash, name, descriptor_code)
            value, hit = get_or_compute(identity, lambda n=name, im=image: compute_descriptor(n, im), CACHE_ROOT)
            record = validate_manifest_record(identity, CACHE_ROOT); value = np.asarray(value, np.float32)
            if value.shape != image.shape[:2] or not np.all(np.isfinite(value)):
                raise RuntimeError(f"invalid BSDS descriptor {name}/{image_id}")
            raw[name] = value
            desc_rows.append({"image_id": image_id, "position": position, "descriptor_id": name,
                              "cache_key": identity.cache_key(), "artifact_sha256": record["artifact_sha256"], "cache_hit": hit})
        cell_scores = {}
        for cell in frontier["validation_cells"]:
            set_id, family, names = cell["set_id"], cell["aggregator"], cell["descriptors"]
            model = models[set_id]; model_hash = next(r["model_sha256"] for r in fit_rows if r["set_id"] == set_id)
            identity = _aggregate_identity(image_id, source_hash, set_id, names, family, model_hash, aggregate_code)
            def calculate(names=names, family=family, model=model):
                x = np.stack([raw[n] for n in names], axis=-1)
                return _aggregate(family, _membership(x, model["membership"]), model)
            score, hit = get_or_compute(identity, calculate, CACHE_ROOT)
            record = validate_manifest_record(identity, CACHE_ROOT); score = np.asarray(score, np.float32)
            if score.shape != image.shape[:2] or not np.all(np.isfinite(score)) or score.min() < 0 or score.max() > 1:
                raise RuntimeError(f"invalid aggregate {set_id}/{family}/{image_id}")
            method = f"stage23f_{set_id}_{family}"; cell_scores[(set_id, family)] = score
            png_path = OUT / "frozen_maps" / method / f"{image_id}.png"
            png_hash = _png(png_path, score)
            agg_rows.append({"image_id": image_id, "position": position, "set_id": set_id, "aggregator": family,
                             "cache_key": identity.cache_key(), "artifact_sha256": record["artifact_sha256"], "cache_hit": hit})
            hash_rows.append({"method": method, "image_id": image_id, "png_sha256": png_hash})
        if position - 1 in PREVIEW_POSITIONS:
            panels = [image]
            for primary in frontier["primary_cells"]:
                panels.extend([cell_scores[(primary["set_id"], primary["aggregator"])], cell_scores[(primary["set_id"], "equal_arithmetic_mean")]])
            previews.append(panels)
        print(f"STAGE23F_IMAGE {position:03d}/100 {image_id} {time.perf_counter()-started:.3f}s", flush=True)

    pd.DataFrame(desc_rows).to_csv(OUT / "descriptor_cache_provenance.csv", index=False)
    pd.DataFrame(agg_rows).to_csv(OUT / "aggregated_cache_provenance.csv", index=False)
    pd.DataFrame(hash_rows).to_csv(OUT / "frozen_map_hashes.csv", index=False)
    if len(desc_rows) != 400 or len(agg_rows) != 600 or len(hash_rows) != 600:
        raise RuntimeError("Stage-23F artifact cardinality failure")
    preview = write_panel_grid(OUT / "best_method_preview.png", previews, panel_height=112, panel_width=112, gap=2)
    methods = []
    for cell in frontier["validation_cells"]:
        name = f"stage23f_{cell['set_id']}_{cell['aggregator']}"
        methods.append({"name": name, "prediction_dir": f"results/local_dev/{EXPERIMENT_ID}/frozen_maps/{name}"})
    official = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": methods,
                "stage23_note": "Frozen Stage-23E frontier only; Stage 23F identifies transfer relationships and does not promote a detector."}
    (OUT / "official_eval_manifest.json").write_text(json.dumps(official, indent=2), encoding="utf-8")
    summary = {
        "status": "completed", "experiment_id": EXPERIMENT_ID,
        "role": "literature_comparable_validation_frontier", "dataset": "BSDS500 validation",
        "images": len(images), "descriptor_ids": needed, "descriptor_requests": len(desc_rows),
        "descriptor_cache_hits": int(sum(bool(r["cache_hit"]) for r in desc_rows)),
        "descriptor_cache_computations": int(sum(not bool(r["cache_hit"]) for r in desc_rows)),
        "aggregated_requests": len(agg_rows), "aggregated_cache_hits": int(sum(bool(r["cache_hit"]) for r in agg_rows)),
        "aggregated_cache_computations": int(sum(not bool(r["cache_hit"]) for r in agg_rows)),
        "frontier": frontier, "validation_gt_used_by_inference": False, "incumbent_changed": False,
        "visual_preview": {"path": preview.relative_to(ROOT).as_posix(), "positions": [1, 50, 100],
                           "panel_order": ["input", "pair03 primary", "pair03 mean", "pair04 primary", "pair04 mean", "triple04 primary", "triple04 mean"],
                           "optimization_use": "none"},
        "decision_rule": "primary vs matched mean: delta ODS >= 0.002 and delta OIS/AP >= 0; relationship identification only",
        "official_attachment": "required standard Berkeley BSDS500-validation scoring of all six frozen cells plus compact MFI",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE23F_LITERATURE_VALIDATION_FRONTIER_COMPLETED"); print(OUT / "summary.json"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
