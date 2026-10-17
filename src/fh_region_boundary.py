from __future__ import annotations

"""Felzenszwalb-Huttenlocher region-boundary evidence for Stage 18b."""

import numpy as np
from skimage.segmentation import felzenszwalb


GAUSSIAN_SIGMA = 0.8
OBSERVATION_SCALE = 300.0
MINIMUM_COMPONENT_SIZE = 1
CONNECTIVITY = 8


def _symmetric_region_boundary(labels: np.ndarray) -> np.ndarray:
    """Rasterize every between-component 8-neighbour edge on both endpoints."""

    values = np.asarray(labels)
    if values.ndim != 2:
        raise ValueError("region labels must be a two-dimensional raster")
    height, width = values.shape
    boundary = np.zeros((height, width), dtype=bool)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        y0a, y1a = max(0, dy), height + min(0, dy)
        x0a, x1a = max(0, dx), width + min(0, dx)
        y0b, y1b = max(0, -dy), height + min(0, -dy)
        x0b, x1b = max(0, -dx), width + min(0, -dx)
        different = values[y0a:y1a, x0a:x1a] != values[y0b:y1b, x0b:x1b]
        boundary[y0a:y1a, x0a:x1a] |= different
        boundary[y0b:y1b, x0b:x1b] |= different
    return boundary


def fh_region_boundary_evidence(image: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Return fixed FH region-partition boundaries on one conditioned gray image."""

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("FH context requires one finite grayscale raster")
    if float(np.min(values)) < 0.0 or float(np.max(values)) > 1.0:
        raise ValueError("FH context expects values in [0,1]")

    labels = felzenszwalb(
        values,
        scale=OBSERVATION_SCALE,
        sigma=GAUSSIAN_SIGMA,
        min_size=MINIMUM_COMPONENT_SIZE,
        channel_axis=None,
    )
    labels = np.asarray(labels, dtype=np.int64)
    boundary = _symmetric_region_boundary(labels).astype(np.float32)
    _unique, counts = np.unique(labels, return_counts=True)
    return boundary, {
        "segment_count": float(counts.size),
        "boundary_fraction": float(np.mean(boundary > 0.0)),
        "mean_component_area": float(np.mean(counts)),
        "median_component_area": float(np.median(counts)),
        "largest_component_fraction": float(np.max(counts) / values.size),
        "evidence_mean": float(np.mean(boundary)),
        "evidence_q90": float(np.quantile(boundary, 0.9)),
        "evidence_max": float(np.max(boundary)),
        "positive_fraction": float(np.mean(boundary > 0.0)),
    }


def synthetic_contract() -> dict[str, object]:
    size = 64
    flat = np.full((size, size), 0.5, dtype=np.float64)
    step = np.full((size, size), 0.25, dtype=np.float64)
    step[:, size // 2 :] = 0.75
    checker = 0.5 + 0.05 * (2.0 * (np.indices((size, size)).sum(axis=0) % 2) - 1.0)
    rng = np.random.default_rng(18002)
    noise = np.clip(0.5 + rng.normal(0.0, 0.01, (size, size)), 0.0, 1.0)

    flat_map, flat_diag = fh_region_boundary_evidence(flat)
    step_map, step_diag = fh_region_boundary_evidence(step)
    repeat_map, _ = fh_region_boundary_evidence(step)
    checker_map, checker_diag = fh_region_boundary_evidence(checker)
    noise_map, noise_diag = fh_region_boundary_evidence(noise)
    offset_map, _ = fh_region_boundary_evidence(step + 0.1)

    band = step_map[:, size // 2 - 2 : size // 2 + 2]
    outside = np.concatenate(
        (step_map[:, : size // 2 - 8].ravel(), step_map[:, size // 2 + 8 :].ravel())
    )
    maps = (flat_map, step_map, checker_map, noise_map)
    finite = bool(all(np.all(np.isfinite(value)) for value in maps))
    binary = bool(all(np.all(np.isin(value, (0.0, 1.0))) for value in maps))
    step_band_mean = float(np.mean(band))
    checker_mean = float(np.mean(checker_map))
    noise_mean = float(np.mean(noise_map))
    return {
        "finite": finite,
        "binary": binary,
        # Compatibility fields consumed by the reused Stage-17h experiment
        # harness.  They remain direct FH synthetic-contract assertions.
        "bounded": binary,
        "step_exceeds_checker": bool(step_band_mean > checker_mean),
        "step_exceeds_noise": bool(step_band_mean > noise_mean),
        "flat_segment_count": int(flat_diag["segment_count"]),
        "flat_max": float(np.max(flat_map)),
        "step_segment_count": int(step_diag["segment_count"]),
        "checker_segment_count": int(checker_diag["segment_count"]),
        "noise_segment_count": int(noise_diag["segment_count"]),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat_map))),
        "additive_offset_max_abs_delta": float(np.max(np.abs(step_map - offset_map))),
        "step_boundary_band_mean": step_band_mean,
        "checker_boundary_mean": checker_mean,
        "noise_boundary_mean": noise_mean,
        "step_outside_mean": float(np.mean(outside)),
        "step_localized": bool(float(np.mean(band)) > 5.0 * max(float(np.mean(outside)), 1.0e-12)),
    }
