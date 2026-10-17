from __future__ import annotations

"""Pinned-author PolyEdge residual evidence for Stage 17z.

The third-party checkout is intentionally ignored and unmodified.  This
module verifies its immutable revision before importing the author pipeline.
"""

from functools import lru_cache
from pathlib import Path
import subprocess
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
AUTHOR_ROOT = ROOT / "vendor" / "polyedge"
AUTHOR_SRC = AUTHOR_ROOT / "src"
AUTHOR_COMMIT = "53277503faae02514cc9249bccd2083210c00138"
AUTHOR_LICENSE_SHA256 = "35e58ad809fbb6cb472767259279eb1e17f3d71d559e62c7e14911a368339983"

DEGREE = 6
MAX_DEPTH = 8
MIN_SIZE = 4
RMSE_TOLERANCE = 1.0e-3
GAUSSIAN_SIGMA = 1.0
COMBINATION = "average"


def _git(*args: str) -> str:
    trust = f"safe.directory={AUTHOR_ROOT.resolve().as_posix()}"
    completed = subprocess.run(
        ["git", "-c", trust, "-C", str(AUTHOR_ROOT), *args],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


@lru_cache(maxsize=1)
def verify_author_dependency() -> dict[str, object]:
    if not AUTHOR_ROOT.is_dir():
        raise RuntimeError(
            "pinned PolyEdge checkout missing at vendor/polyedge; expected "
            f"DimitriKenne/polyedge commit {AUTHOR_COMMIT}"
        )
    head = _git("rev-parse", "HEAD")
    dirty = _git("status", "--porcelain", "--untracked-files=no")
    license_hash = _git("hash-object", "LICENSE")
    # Git's object hash is recorded only as an extra diagnostic; SHA-256 is
    # checked without importing a second repository utility.
    import hashlib

    sha256 = hashlib.sha256((AUTHOR_ROOT / "LICENSE").read_bytes()).hexdigest()
    if head != AUTHOR_COMMIT or dirty:
        raise RuntimeError("pinned PolyEdge author checkout has the wrong revision or tracked modifications")
    if sha256 != AUTHOR_LICENSE_SHA256:
        raise RuntimeError("pinned PolyEdge license hash differs from the registered value")
    return {
        "repository": "https://github.com/DimitriKenne/polyedge",
        "commit": head,
        "tracked_clean": True,
        "license": "MIT",
        "license_sha256": sha256,
        "license_git_blob": license_hash,
    }


@lru_cache(maxsize=1)
def _author_api():
    verify_author_dependency()
    source = str(AUTHOR_SRC.resolve())
    if source not in sys.path:
        sys.path.insert(0, source)
    from polyedge.pipeline import PolyEdgeConfig, run_polyedge_pipeline

    return PolyEdgeConfig, run_polyedge_pipeline


def adaptive_polynomial_residual_evidence(image: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Return the exact author average residual at the paper's Section-7 settings."""

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("PolyEdge context requires one finite grayscale raster")
    if float(np.min(values)) < 0.0 or float(np.max(values)) > 1.0:
        raise ValueError("PolyEdge context expects values in [0,1]")

    PolyEdgeConfig, run_polyedge_pipeline = _author_api()
    config = PolyEdgeConfig(
        degree=DEGREE,
        node_family="chebyshev_admissible_mesh",
        max_depth=MAX_DEPTH,
        min_size=MIN_SIZE,
        stopping_criterion="rmse",
        tolerance=RMSE_TOLERANCE,
        sampler="continuous",
        gaussian_sigma=GAUSSIAN_SIGMA,
        combination_strategy=COMBINATION,
        weighted_sum_weights=(1.0, 1.0, 1.0, 1.0),
        compute_error_map=False,
    )
    result = run_polyedge_pipeline(values, config)
    response = np.asarray(result.residual, dtype=np.float64)
    if response.shape != values.shape or not np.all(np.isfinite(response)):
        raise RuntimeError("author PolyEdge returned an invalid residual raster")
    response = np.clip(response, 0.0, 1.0)
    original_leaves = result.quadtree.leaf_regions()
    smoothed_leaves = result.quadtree_smoothed.leaf_regions()
    return response, {
        "evidence_mean": float(np.mean(response)),
        "evidence_q90": float(np.quantile(response, 0.9)),
        "evidence_max": float(np.max(response)),
        "positive_fraction": float(np.mean(response > 0.0)),
        "original_leaf_regions": float(len(original_leaves)),
        "smoothed_leaf_regions": float(len(smoothed_leaves)),
        "original_maximum_depth": float(max((leaf.depth for leaf in original_leaves), default=0)),
        "smoothed_maximum_depth": float(max((leaf.depth for leaf in smoothed_leaves), default=0)),
    }


def synthetic_contract() -> dict[str, object]:
    size = 64
    flat = np.full((size, size), 0.5, dtype=np.float64)
    step = np.full((size, size), 0.25, dtype=np.float64)
    step[:, size // 2 :] = 0.75
    checker = 0.5 + 0.05 * (2.0 * (np.indices((size, size)).sum(axis=0) % 2) - 1.0)
    rng = np.random.default_rng(17022)
    noise = np.clip(0.5 + rng.normal(0.0, 0.01, (size, size)), 0.0, 1.0)

    flat_map, _ = adaptive_polynomial_residual_evidence(flat)
    step_map, _ = adaptive_polynomial_residual_evidence(step)
    repeat_map, _ = adaptive_polynomial_residual_evidence(step)
    checker_map, _ = adaptive_polynomial_residual_evidence(checker)
    noise_map, _ = adaptive_polynomial_residual_evidence(noise)
    offset_map, _ = adaptive_polynomial_residual_evidence(0.1 + 0.8 * step)

    band = step_map[:, size // 2 - 2 : size // 2 + 2]
    outside = np.concatenate((step_map[:, : size // 2 - 8].ravel(), step_map[:, size // 2 + 8 :].ravel()))
    return {
        "finite": bool(all(np.all(np.isfinite(value)) for value in (flat_map, step_map, checker_map, noise_map))),
        "bounded": bool(all(float(np.min(value)) >= 0.0 and float(np.max(value)) <= 1.0 for value in (flat_map, step_map, checker_map, noise_map))),
        "flat_max": float(np.max(flat_map)),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat_map))),
        "affine_photometric_max_abs_delta": float(np.max(np.abs(step_map - offset_map))),
        "step_max": float(np.max(step_map)),
        "checker_max": float(np.max(checker_map)),
        "noise_max": float(np.max(noise_map)),
        "step_exceeds_checker": bool(float(np.max(step_map)) > float(np.max(checker_map))),
        "step_exceeds_noise": bool(float(np.max(step_map)) > float(np.max(noise_map))),
        "step_boundary_band_mean": float(np.mean(band)),
        "step_outside_mean": float(np.mean(outside)),
        "step_localized": bool(float(np.mean(band)) > 10.0 * max(float(np.mean(outside)), 1.0e-12)),
    }
