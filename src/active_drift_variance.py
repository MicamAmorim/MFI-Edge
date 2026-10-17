from __future__ import annotations

"""Deterministic active-sampling variance evidence for Stage 18d.

This is an equation-level repository adaptation of the S-V-N control in
Schmittwilken and Maertens (2022), not an exact reproduction of their complete
simulation/evaluation pipeline.
"""

import numpy as np
from scipy.ndimage import gaussian_filter


PIXELS_PER_DEGREE = 40.0
DIFFUSION_DEG2_PER_SECOND = 20.0 / (60.0**2)
FIXATION_SECONDS = 0.2
SAMPLING_HZ = 10.0
N_DRIFT_TRIALS = 10
DRIFT_SEED = 20261017
SIGMAS_DEGREES = (0.016, 0.032, 0.064, 0.128, 0.256)
SIGMAS_PIXELS = tuple(value * PIXELS_PER_DEGREE for value in SIGMAS_DEGREES)


def fixed_drift_paths() -> tuple[np.ndarray, ...]:
    """Return ten fixed three-frame integer Brownian-drift paths in pixels."""

    rng = np.random.default_rng(DRIFT_SEED)
    n_steps = int(round(FIXATION_SECONDS * SAMPLING_HZ))
    dt = 1.0 / SAMPLING_HZ
    step_scale = np.sqrt(2.0 * dt * DIFFUSION_DEG2_PER_SECOND)
    paths: list[np.ndarray] = []
    while len(paths) < N_DRIFT_TRIALS:
        increments = rng.normal(0.0, 1.0, (2, n_steps)) * step_scale
        continuous = np.concatenate(
            (np.zeros((2, 1), dtype=np.float64), np.cumsum(increments, axis=1)),
            axis=1,
        )
        integer = np.rint(continuous * PIXELS_PER_DEGREE).astype(np.int64)
        # Match the author implementation's requirement that both axes move.
        if int(integer[0].sum()) * int(integer[1].sum()) != 0:
            paths.append(integer)
    return tuple(paths)


DRIFT_PATHS = fixed_drift_paths()


def _shift_reflect(values: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Integer translate one raster with reflection at the image boundary."""

    height, width = values.shape
    pad = max(abs(int(dy)), abs(int(dx)), 1)
    padded = np.pad(values, pad, mode="reflect")
    y0 = pad + int(dy)
    x0 = pad + int(dx)
    return padded[y0 : y0 + height, x0 : x0 + width]


def active_drift_variance_evidence(
    image: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return bounded multiscale DoG variance under fixed micro-drift."""

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("active-drift context requires one finite grayscale raster")
    if float(np.min(values)) < 0.0 or float(np.max(values)) > 1.0:
        raise ValueError("active-drift context expects values in [0,1]")

    normalized_scales: list[np.ndarray] = []
    scale_means: list[float] = []
    for sigma in SIGMAS_PIXELS:
        dog = gaussian_filter(values, sigma, mode="reflect") - gaussian_filter(
            values, 2.0 * sigma, mode="reflect"
        )
        trial_variances = []
        for path in DRIFT_PATHS:
            frames = np.stack(
                [
                    _shift_reflect(dog, int(path[0, frame]), int(path[1, frame]))
                    for frame in range(path.shape[1])
                ],
                axis=-1,
            )
            trial_variances.append(np.var(frames, axis=-1))
        response = np.mean(np.stack(trial_variances, axis=-1), axis=-1)
        mean_response = float(np.mean(response))
        scale_means.append(mean_response)
        if mean_response > np.finfo(np.float64).eps:
            normalized_scales.append(response / mean_response)
        else:
            normalized_scales.append(np.zeros_like(response))

    raw = np.mean(np.stack(normalized_scales, axis=-1), axis=-1)
    evidence = raw / (1.0 + raw)
    evidence = np.clip(evidence, 0.0, 1.0).astype(np.float32)
    return evidence, {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "evidence_max": float(np.max(evidence)),
        "positive_fraction": float(np.mean(evidence > 0.0)),
        "raw_mean": float(np.mean(raw)),
        "raw_q90": float(np.quantile(raw, 0.9)),
        "minimum_scale_mean": float(np.min(scale_means)),
        "maximum_scale_mean": float(np.max(scale_means)),
        "maximum_absolute_drift_pixels": float(
            max(np.max(np.abs(path)) for path in DRIFT_PATHS)
        ),
    }


def synthetic_contract() -> dict[str, object]:
    size = 96
    flat = np.full((size, size), 0.5, dtype=np.float64)
    step = np.full((size, size), 0.25, dtype=np.float64)
    step[:, size // 2 :] = 0.75
    checker = 0.5 + 0.015 * (
        2.0 * (np.indices((size, size)).sum(axis=0) % 2) - 1.0
    )
    rng = np.random.default_rng(18004)
    noise = np.clip(0.5 + rng.normal(0.0, 0.005, (size, size)), 0.0, 1.0)

    flat_map, _ = active_drift_variance_evidence(flat)
    step_map, _ = active_drift_variance_evidence(step)
    repeat_map, _ = active_drift_variance_evidence(step)
    checker_map, _ = active_drift_variance_evidence(checker)
    noise_map, _ = active_drift_variance_evidence(noise)
    affine_map, _ = active_drift_variance_evidence(0.2 + 0.7 * step)

    band = step_map[:, size // 2 - 5 : size // 2 + 6]
    outside = np.concatenate(
        (step_map[:, : size // 2 - 16].ravel(), step_map[:, size // 2 + 16 :].ravel())
    )
    all_maps = (flat_map, step_map, checker_map, noise_map, affine_map)
    step_peak = float(np.max(step_map))
    step_q90 = float(np.quantile(step_map, 0.9))
    checker_q90 = float(np.quantile(checker_map, 0.9))
    noise_q90 = float(np.quantile(noise_map, 0.9))
    return {
        "finite": bool(all(np.all(np.isfinite(value)) for value in all_maps)),
        "bounded": bool(
            all(float(np.min(value)) >= 0.0 and float(np.max(value)) <= 1.0 for value in all_maps)
        ),
        "flat_max": float(np.max(flat_map)),
        "step_peak": step_peak,
        "checker_peak": float(np.max(checker_map)),
        "noise_peak": float(np.max(noise_map)),
        "step_q90": step_q90,
        "checker_q90": checker_q90,
        "noise_q90": noise_q90,
        "step_exceeds_checker": bool(step_q90 > checker_q90),
        "step_exceeds_noise": bool(step_q90 > noise_q90),
        "step_band_mean": float(np.mean(band)),
        "step_outside_mean": float(np.mean(outside)),
        "step_localized": bool(float(np.mean(band)) > 4.0 * max(float(np.mean(outside)), 1.0e-12)),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat_map))),
        "positive_affine_max_abs_delta": float(np.max(np.abs(step_map - affine_map))),
        "drift_paths": [path.tolist() for path in DRIFT_PATHS],
    }
