from __future__ import annotations

"""Stage 23B: certify extract-once/reuse-everywhere cache semantics.

Synthetic arrays only. No dataset or ground-truth access.
"""

from pathlib import Path
import hashlib
import json
import shutil

import numpy as np

from src.stage23_cache import (
    CacheCorruptionError,
    CacheError,
    CacheIdentity,
    artifact_paths,
    get_or_compute,
    load_cached,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage23b_cache_certification"
CACHE = ROOT / "cache" / "local_dev" / "stage23" / "_certification"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    # Dedicated certification namespace may be rebuilt because this experiment
    # exists specifically to test cache repair/identity semantics.
    if CACHE.exists():
        shutil.rmtree(CACHE)

    calls = {"base": 0, "changed": 0}

    base = CacheIdentity(
        dataset="synthetic-certification",
        split="dev",
        image_id="img001",
        artifact_type="descriptors",
        artifact_id="toy_gradient",
        preprocessing_id="identity-v1",
        parameters={"sigma": 1.0, "scale": 5},
        implementation="automation.stage23b_cache_certification:toy",
        implementation_version="1",
        code_version="stage23b-cert-v1",
        source_sha256=_sha256_bytes(b"synthetic-image-001"),
        gt_used=False,
    )

    expected = np.arange(35, dtype=np.float32).reshape(5, 7) / 34.0

    def compute_base() -> np.ndarray:
        calls["base"] += 1
        return expected.copy()

    first, first_hit = get_or_compute(base, compute_base, CACHE)
    second, second_hit = get_or_compute(base, compute_base, CACHE)
    exact_reuse_ok = (
        first_hit is False
        and second_hit is True
        and calls["base"] == 1
        and np.array_equal(first, expected)
        and np.array_equal(second, expected)
    )

    changed = CacheIdentity(
        **{
            **base.__dict__,
            "parameters": {"sigma": 2.0, "scale": 5},
        }
    )

    def compute_changed() -> np.ndarray:
        calls["changed"] += 1
        return (expected * 2.0).astype(np.float32)

    changed_arr, changed_hit = get_or_compute(changed, compute_changed, CACHE)
    distinct_key_ok = (
        base.cache_key() != changed.cache_key()
        and changed_hit is False
        and calls["changed"] == 1
        and np.array_equal(changed_arr, expected * 2.0)
    )

    data_path, meta_path, _lock_path = artifact_paths(base, CACHE)
    metadata_before = json.loads(meta_path.read_text(encoding="utf-8"))
    with data_path.open("ab") as handle:
        handle.write(b"CORRUPTION")
    corruption_failed_closed = False
    try:
        load_cached(base, CACHE)
    except CacheCorruptionError:
        corruption_failed_closed = True

    gt_guard_ok = False
    gt_identity = CacheIdentity(
        **{
            **base.__dict__,
            "image_id": "img_gt_forbidden",
            "gt_used": True,
        }
    )
    try:
        get_or_compute(gt_identity, lambda: expected.copy(), CACHE)
    except CacheError:
        gt_guard_ok = True

    summary = {
        "status": "completed" if all([exact_reuse_ok, distinct_key_ok, corruption_failed_closed, gt_guard_ok]) else "failed",
        "experiment_id": "stage23b_cache_certification",
        "dataset_access": "synthetic_only",
        "cache_root": str(CACHE.relative_to(ROOT)).replace("\\", "/"),
        "checks": {
            "first_call_computes_second_call_hits_without_recompute": exact_reuse_ok,
            "base_compute_calls": calls["base"],
            "parameter_change_creates_distinct_key": distinct_key_ok,
            "changed_compute_calls": calls["changed"],
            "corrupt_artifact_fails_closed": corruption_failed_closed,
            "gt_marked_inference_evidence_is_rejected": gt_guard_ok,
            "base_cache_key": base.cache_key(),
            "changed_cache_key": changed.cache_key(),
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
