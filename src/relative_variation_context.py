from __future__ import annotations

"""Signed-gradient coherence from relative-total-variation primitives."""

import numpy as np
from scipy.ndimage import gaussian_filter


GAUSSIAN_SIGMA = 3.0
GAUSSIAN_RADIUS = 7


def _forward_differences(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    dx = np.zeros_like(values, dtype=np.float64)
    dy = np.zeros_like(values, dtype=np.float64)
    dx[:, :-1] = values[:, 1:] - values[:, :-1]
    dy[:-1, :] = values[1:, :] - values[:-1, :]
    return dx, dy


def relative_variation_context(image: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Return the bounded inherent/total-variation coherence ratio.

    The numerator is the sum of the magnitudes of Gaussian-windowed signed
    forward differences.  The denominator applies the same window to the
    difference magnitudes.  The triangle inequality therefore bounds the
    ratio in [0, 1]; flat support is assigned zero.
    """

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("relative-variation context requires one finite grayscale raster")
    if float(np.min(values)) < 0.0 or float(np.max(values)) > 1.0:
        raise ValueError("relative-variation context expects values in [0,1]")

    dx, dy = _forward_differences(values)
    options = {
        "sigma": GAUSSIAN_SIGMA,
        "radius": GAUSSIAN_RADIUS,
        "mode": "reflect",
    }
    inherent_x = np.abs(gaussian_filter(dx, **options))
    inherent_y = np.abs(gaussian_filter(dy, **options))
    total_x = gaussian_filter(np.abs(dx), **options)
    total_y = gaussian_filter(np.abs(dy), **options)
    inherent = inherent_x + inherent_y
    total = total_x + total_y
    evidence = np.zeros_like(values, dtype=np.float64)
    np.divide(inherent, total, out=evidence, where=total > 1.0e-12)
    evidence = np.clip(evidence, 0.0, 1.0).astype(np.float32)

    active = total > 1.0e-12
    return evidence, {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "evidence_max": float(np.max(evidence)),
        "positive_fraction": float(np.mean(evidence > 0.0)),
        "active_fraction": float(np.mean(active)),
        "inherent_mean": float(np.mean(inherent)),
        "total_variation_mean": float(np.mean(total)),
        "active_coherence_mean": float(np.mean(evidence[active])) if np.any(active) else 0.0,
    }


def synthetic_contract() -> dict[str, object]:
    size = 65
    flat = np.full((size, size), 0.5, dtype=np.float64)
    step = np.full((size, size), 0.25, dtype=np.float64)
    step[:, size // 2 :] = 0.75
    checker = 0.5 + 0.2 * (2.0 * (np.indices((size, size)).sum(axis=0) % 2) - 1.0)
    rng = np.random.default_rng(18022)
    noise = np.clip(0.5 + rng.normal(0.0, 0.12, (size, size)), 0.0, 1.0)

    flat_map, _ = relative_variation_context(flat)
    step_map, _ = relative_variation_context(step)
    checker_map, _ = relative_variation_context(checker)
    noise_map, _ = relative_variation_context(noise)
    repeat_map, _ = relative_variation_context(step)
    offset_map, _ = relative_variation_context(step + 0.1)
    scaled_map, _ = relative_variation_context(step * 0.8)

    band = step_map[:, size // 2 - 4 : size // 2 + 5]
    checker_mean = float(np.mean(checker_map))
    noise_mean = float(np.mean(noise_map))
    step_band_mean = float(np.mean(band))
    maps = (flat_map, step_map, checker_map, noise_map)
    return {
        "finite": bool(all(np.all(np.isfinite(value)) for value in maps)),
        "bounded": bool(all(float(np.min(value)) >= 0.0 and float(np.max(value)) <= 1.0 for value in maps)),
        "flat_max": float(np.max(flat_map)),
        "step_boundary_band_mean": step_band_mean,
        "checker_mean": checker_mean,
        "noise_mean": noise_mean,
        "step_exceeds_checker": bool(step_band_mean > checker_mean),
        "step_exceeds_noise": bool(step_band_mean > noise_mean),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat_map))),
        "additive_offset_max_abs_delta": float(np.max(np.abs(step_map - offset_map))),
        "positive_scale_max_abs_delta": float(np.max(np.abs(step_map - scaled_map))),
    }
