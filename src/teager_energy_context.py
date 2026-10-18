from __future__ import annotations

"""Dual-stencil 2-D Teager-Kaiser energy consensus."""

import numpy as np


def teager_energy_context(image: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Return bounded positive consensus of axial and diagonal 2-D TKEO.

    Boudraa and Diop give complementary Type-1A (axial) and Type-1B
    (diagonal) discrete 2-D Teager-Kaiser operators.  Each lies in [-2, 2]
    for an input in [0, 1].  This fixed context cue rectifies their positive
    parts and uses their geometric mean, requiring activity in both stencils.
    Division by two supplies an analytic [0, 1] bound.
    """

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("Teager-energy context requires one finite grayscale raster")
    if float(np.min(values)) < 0.0 or float(np.max(values)) > 1.0:
        raise ValueError("Teager-energy context expects values in [0,1]")

    padded = np.pad(values, 1, mode="reflect")
    center = padded[1:-1, 1:-1]
    left = padded[1:-1, :-2]
    right = padded[1:-1, 2:]
    up = padded[:-2, 1:-1]
    down = padded[2:, 1:-1]
    upper_left = padded[:-2, :-2]
    upper_right = padded[:-2, 2:]
    lower_left = padded[2:, :-2]
    lower_right = padded[2:, 2:]

    axial = 2.0 * center * center - left * right - up * down
    diagonal = 2.0 * center * center - upper_left * lower_right - upper_right * lower_left
    axial_positive = np.clip(axial, 0.0, 2.0)
    diagonal_positive = np.clip(diagonal, 0.0, 2.0)
    evidence = (0.5 * np.sqrt(axial_positive * diagonal_positive)).astype(np.float32)

    return evidence, {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "evidence_max": float(np.max(evidence)),
        "positive_fraction": float(np.mean(evidence > 0.0)),
        "axial_positive_mean": float(np.mean(axial_positive)),
        "diagonal_positive_mean": float(np.mean(diagonal_positive)),
        "both_positive_fraction": float(np.mean((axial > 0.0) & (diagonal > 0.0))),
        "either_negative_fraction": float(np.mean((axial < 0.0) | (diagonal < 0.0))),
    }


def synthetic_contract() -> dict[str, object]:
    size = 65
    flat = np.full((size, size), 0.5, dtype=np.float64)
    step = np.full((size, size), 0.25, dtype=np.float64)
    step[:, size // 2 :] = 0.75
    checker = 0.5 + 0.2 * (2.0 * (np.indices((size, size)).sum(axis=0) % 2) - 1.0)
    rng = np.random.default_rng(18024)
    noise = np.clip(0.5 + rng.normal(0.0, 0.03, (size, size)), 0.0, 1.0)

    flat_map, _ = teager_energy_context(flat)
    step_map, _ = teager_energy_context(step)
    checker_map, _ = teager_energy_context(checker)
    noise_map, _ = teager_energy_context(noise)
    repeat_map, _ = teager_energy_context(step)
    scaled_map, _ = teager_energy_context(step * 0.8)

    band = step_map[:, size // 2 - 1 : size // 2 + 1]
    step_band_mean = float(np.mean(band))
    checker_mean = float(np.mean(checker_map))
    noise_mean = float(np.mean(noise_map))
    maps = (flat_map, step_map, checker_map, noise_map)
    expected_scaled = step_map * np.float32(0.8**2)
    return {
        "finite": bool(all(np.all(np.isfinite(value)) for value in maps)),
        "bounded": bool(all(float(np.min(value)) >= 0.0 and float(np.max(value)) <= 1.0 for value in maps)),
        "flat_max": float(np.max(flat_map)),
        "step_boundary_band_mean": step_band_mean,
        "checker_mean": checker_mean,
        "noise_mean": noise_mean,
        "step_exceeds_checker": bool(step_band_mean > checker_mean),
        "step_exceeds_noise": bool(step_band_mean > noise_mean),
        "checker_max": float(np.max(checker_map)),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat_map))),
        "quadratic_scale_max_abs_delta": float(np.max(np.abs(scaled_map - expected_scaled))),
    }
