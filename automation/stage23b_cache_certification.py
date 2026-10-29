from __future__ import annotations

"""Stage 23B: certify extract-once/reuse-everywhere cache semantics.

Synthetic arrays only. No dataset or ground-truth access.
"""

from pathlib import Path
import hashlib
import inspect
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from src.stage23_cache import (
    CacheCorruptionError,
    CacheError,
    CacheIdentity,
    artifact_paths,
    get_or_compute,
    manifest_path,
    sha256_file,
    validate_manifest_record,
)

OUT = ROOT / "results" / "automation" / "stage23b_cache_certification"
CACHE = ROOT / "cache" / "local_dev" / "stage23" / "_certification"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    # Dedicated certification namespace may be rebuilt because this experiment
    # exists specifically to test cache repair/identity semantics.
    cache_parent = (ROOT / "cache" / "local_dev" / "stage23").resolve()
    cache_resolved = CACHE.resolve()
    if cache_resolved.parent != cache_parent or cache_resolved.name != "_certification":
        raise RuntimeError(f"unsafe certification cache target: {cache_resolved}")
    if CACHE.exists():
        shutil.rmtree(CACHE)

    calls = {
        "base": 0,
        "changed_parameter": 0,
        "changed_preprocessing": 0,
        "derived_transform": 0,
        "corrupt_recompute": 0,
        "gt": 0,
    }

    images = {
        "flat": np.zeros((5, 7), dtype=np.float32),
        "ramp": np.tile(np.linspace(0.0, 1.0, 7, dtype=np.float32), (5, 1)),
        "step": np.pad(np.ones((3, 3), dtype=np.float32), ((1, 1), (2, 2))),
    }

    def toy_gradient(image: np.ndarray, gain: float) -> np.ndarray:
        gy, gx = np.gradient(np.asarray(image, dtype=np.float32))
        return (gain * np.hypot(gx, gy)).astype(np.float32)

    identities: list[CacheIdentity] = []
    first_arrays: dict[str, np.ndarray] = {}
    first_hashes: dict[str, str] = {}
    first_hits: list[bool] = []
    second_hits: list[bool] = []
    for image_id, image in images.items():
        identity = CacheIdentity(
            dataset="synthetic-certification",
            split="dev",
            image_id=image_id,
            artifact_type="descriptors",
            artifact_id="toy_gradient",
            preprocessing_id="identity-v1",
            parameters={"gain": 1.0},
            implementation="automation.stage23b_cache_certification:toy_gradient",
            implementation_version="1",
            code_version="stage23b-cert-v2",
            source_sha256=_sha256_bytes(image.tobytes()),
            representation="synthetic_certification",
            gt_used=False,
        )
        identities.append(identity)

        def compute_base(image: np.ndarray = image) -> np.ndarray:
            calls["base"] += 1
            return toy_gradient(image, 1.0)

        first, first_hit = get_or_compute(identity, compute_base, CACHE)
        data_path, _meta_path, _lock_path = artifact_paths(identity, CACHE)
        first_arrays[image_id] = first.copy()
        first_hashes[image_id] = sha256_file(data_path)
        second, second_hit = get_or_compute(identity, compute_base, CACHE)
        first_hits.append(first_hit)
        second_hits.append(second_hit)
        if not np.array_equal(first, second):
            raise AssertionError(f"cache round trip changed {image_id}")

    base = identities[1]
    expected = toy_gradient(images["ramp"], 1.0)
    base_data_path, _base_meta_path, _base_lock_path = artifact_paths(base, CACHE)
    exact_reuse_ok = (
        first_hits == [False, False, False]
        and second_hits == [True, True, True]
        and calls["base"] == len(images)
        and np.array_equal(first_arrays["ramp"], expected)
        and sha256_file(base_data_path) == first_hashes["ramp"]
    )

    changed = CacheIdentity(
        **{
            **base.__dict__,
            "parameters": {"gain": 2.0},
        }
    )

    def compute_changed() -> np.ndarray:
        calls["changed_parameter"] += 1
        return toy_gradient(images["ramp"], 2.0)

    changed_arr, changed_hit = get_or_compute(changed, compute_changed, CACHE)
    distinct_key_ok = (
        base.cache_key() != changed.cache_key()
        and changed_hit is False
        and calls["changed_parameter"] == 1
        and np.array_equal(changed_arr, expected * 2.0)
    )

    changed_preprocessing = CacheIdentity(
        **{
            **base.__dict__,
            "preprocessing_id": "identity-v2",
        }
    )

    def compute_changed_preprocessing() -> np.ndarray:
        calls["changed_preprocessing"] += 1
        return expected.copy()

    pre_arr, pre_hit = get_or_compute(
        changed_preprocessing, compute_changed_preprocessing, CACHE
    )
    preprocessing_key_ok = (
        base.cache_key() != changed_preprocessing.cache_key()
        and pre_hit is False
        and calls["changed_preprocessing"] == 1
        and np.array_equal(pre_arr, expected)
    )

    transform_identity = CacheIdentity(
        dataset="synthetic-certification",
        split="dev",
        image_id="ramp",
        artifact_type="transforms",
        artifact_id="toy_unit_interval",
        preprocessing_id="identity-v1",
        parameters={"source_descriptor": "toy_gradient"},
        implementation="automation.stage23b_cache_certification:toy_transform",
        implementation_version="1",
        code_version="stage23b-cert-v2",
        source_sha256=first_hashes["ramp"],
        representation="derived_transform",
        gt_used=False,
    )

    def compute_transform() -> np.ndarray:
        calls["derived_transform"] += 1
        peak = float(np.max(expected))
        return (expected / peak if peak > 0 else expected).astype(np.float32)

    transformed_first, transform_first_hit = get_or_compute(
        transform_identity, compute_transform, CACHE
    )
    transformed_second, transform_second_hit = get_or_compute(
        transform_identity, compute_transform, CACHE
    )
    transform_record = validate_manifest_record(transform_identity, CACHE)
    transform_manifest = manifest_path(transform_identity, CACHE)
    transform_manifest_lines = [
        line
        for line in transform_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    transform_cache_ok = (
        transform_first_hit is False
        and transform_second_hit is True
        and calls["derived_transform"] == 1
        and np.array_equal(transformed_first, transformed_second)
        and transform_record["representation"] == "derived_transform"
        and len(transform_manifest_lines) == 1
    )

    data_path, meta_path, _lock_path = artifact_paths(base, CACHE)
    metadata_before = json.loads(meta_path.read_text(encoding="utf-8"))
    manifest_record = validate_manifest_record(base, CACHE)
    manifest = manifest_path(base, CACHE)
    manifest_lines = [
        line for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    manifest_ok = (
        manifest_record["cache_key"] == base.cache_key()
        and manifest_record["artifact_sha256"] == metadata_before["artifact_sha256"]
        and len(manifest_lines) == len(images) + 2
    )
    with data_path.open("ab") as handle:
        handle.write(b"CORRUPTION")
    corruption_failed_closed = False
    try:
        def forbidden_corrupt_recompute() -> np.ndarray:
            calls["corrupt_recompute"] += 1
            return expected.copy()

        get_or_compute(base, forbidden_corrupt_recompute, CACHE)
    except CacheCorruptionError:
        corruption_failed_closed = calls["corrupt_recompute"] == 0

    gt_guard_ok = False
    gt_identity = CacheIdentity(
        **{
            **base.__dict__,
            "image_id": "img_gt_forbidden",
            "gt_used": True,
        }
    )
    try:
        def forbidden_gt_compute() -> np.ndarray:
            calls["gt"] += 1
            return expected.copy()

        get_or_compute(gt_identity, forbidden_gt_compute, CACHE)
    except CacheError:
        gt_guard_ok = calls["gt"] == 0

    extractor_inputs = list(inspect.signature(toy_gradient).parameters)
    inference_surface_ok = extractor_inputs == ["image", "gain"]
    temp_files = list(CACHE.rglob("*.tmp-*"))
    atomic_cleanup_ok = not temp_files

    all_checks = [
        exact_reuse_ok,
        distinct_key_ok,
        preprocessing_key_ok,
        transform_cache_ok,
        manifest_ok,
        corruption_failed_closed,
        gt_guard_ok,
        inference_surface_ok,
        atomic_cleanup_ok,
    ]

    summary = {
        "status": "completed" if all(all_checks) else "failed",
        "experiment_id": "stage23b_cache_certification",
        "dataset_access": "synthetic_only",
        "cache_root": str(CACHE.relative_to(ROOT)).replace("\\", "/"),
        "checks": {
            "first_call_computes_second_call_hits_without_recompute": exact_reuse_ok,
            "base_compute_calls": calls["base"],
            "parameter_change_creates_distinct_key": distinct_key_ok,
            "parameter_changed_compute_calls": calls["changed_parameter"],
            "preprocessing_change_creates_distinct_key": preprocessing_key_ok,
            "preprocessing_changed_compute_calls": calls["changed_preprocessing"],
            "derived_transform_exact_reuse": transform_cache_ok,
            "derived_transform_compute_calls": calls["derived_transform"],
            "transform_manifest_path": str(transform_manifest.relative_to(ROOT)).replace("\\", "/"),
            "byte_hash_identity_on_reuse": first_hashes["ramp"] == metadata_before.get("artifact_sha256"),
            "manifest_record_and_count_valid": manifest_ok,
            "manifest_path": str(manifest.relative_to(ROOT)).replace("\\", "/"),
            "corrupt_artifact_fails_closed": corruption_failed_closed,
            "corrupt_artifact_recompute_calls": calls["corrupt_recompute"],
            "gt_marked_inference_evidence_is_rejected": gt_guard_ok,
            "gt_compute_calls": calls["gt"],
            "inference_extractor_has_no_path_or_gt_argument": inference_surface_ok,
            "inference_extractor_inputs": extractor_inputs,
            "atomic_write_temp_files_absent": atomic_cleanup_ok,
            "base_cache_key": base.cache_key(),
            "changed_cache_key": changed.cache_key(),
            "changed_preprocessing_cache_key": changed_preprocessing.cache_key(),
            "recorded_shape": metadata_before.get("shape"),
            "recorded_dtype": metadata_before.get("dtype"),
            "recorded_artifact_sha256": metadata_before.get("artifact_sha256"),
        },
        "next_contract": "Large descriptor extraction is authorized only if every certification check is true. Ordinary Stage-23 experiments must never silently rebuild a corrupt exact-key artifact.",
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE23B_CACHE_CERTIFICATION", summary["status"].upper())
    print(path)
    return 0 if summary["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
