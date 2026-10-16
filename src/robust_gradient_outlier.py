from __future__ import annotations

"""Fixed local robust-gradient outlier evidence for Stage 17p.

Black and Sapiro (Scale-Space 1999) interpret edges as gradient-magnitude
outliers relative to local robust variation.  Stage 17p uses only that local
statistical representation as context; it does not perform their anisotropic
diffusion or reproduce their complete smoothing algorithm.
"""

import numpy as np
from skimage.filters import scharr


WINDOW_SIZE = 9
MAD_NORMALIZATION = 1.4826
EPSILON = 1.0e-12


def robust_gradient_outlier_evidence(
    image: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return bounded local gradient-outlier evidence.

    The unchanged median-conditioned grayscale image is converted to Scharr
    magnitude ``g``.  A centered 9x9 window supplies the local median ``m``
    and normalized median absolute deviation ``s``.  The positive excess
    ``d=max(g-m,0)`` is mapped to ``d/(d+s)``.  This is zero in flat regions,
    bounded in [0,1], and invariant to positive global intensity scaling.
    """

    x = np.asarray(image, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("robust gradient outlier context expects a two-dimensional image")
    if not np.all(np.isfinite(x)):
        raise ValueError("robust gradient outlier context received non-finite input")

    gradient = np.asarray(scharr(x), dtype=np.float32)
    radius = WINDOW_SIZE // 2
    # NumPy's symmetric padding matches the intended half-sample-reflected
    # finite-raster extension.  The strided view keeps the window geometry
    # exact without constructing 81 shifted full-image copies.
    padded = np.pad(gradient, radius, mode="symmetric")
    windows = np.lib.stride_tricks.sliding_window_view(
        padded, (WINDOW_SIZE, WINDOW_SIZE)
    )
    local_median = np.median(windows, axis=(-2, -1))
    local_mad = np.median(
        np.abs(windows - local_median[..., None, None]), axis=(-2, -1)
    )
    robust_scale = MAD_NORMALIZATION * local_mad
    positive_excess = np.maximum(gradient - local_median, 0.0)
    denominator = positive_excess + robust_scale
    evidence = np.divide(
        positive_excess,
        denominator,
        out=np.zeros_like(positive_excess),
        where=denominator > EPSILON,
    )
    evidence = np.clip(evidence, 0.0, 1.0).astype(np.float32)
    if not np.all(np.isfinite(evidence)):
        raise RuntimeError("non-finite robust gradient outlier evidence")

    diagnostics = {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "max_evidence": float(np.max(evidence)),
        "active_fraction": float(np.mean(evidence > 0.0)),
        "gradient_mean": float(np.mean(gradient)),
        "local_median_mean": float(np.mean(local_median)),
        "robust_scale_mean": float(np.mean(robust_scale)),
    }
    return evidence, diagnostics


def synthetic_contract() -> dict[str, float | bool]:
    size = 65
    step = np.zeros((size, size), dtype=np.float64)
    step[:, size // 2 :] = 1.0
    checker = (np.indices((size, size)).sum(axis=0) % 2).astype(np.float64)
    rng = np.random.default_rng(17016)
    noise = rng.random((size, size))
    flat = np.full((size, size), 0.37, dtype=np.float64)

    step_map, _ = robust_gradient_outlier_evidence(step)
    repeat, _ = robust_gradient_outlier_evidence(step)
    scaled, _ = robust_gradient_outlier_evidence(0.5 * step)
    checker_map, _ = robust_gradient_outlier_evidence(checker)
    noise_map, _ = robust_gradient_outlier_evidence(noise)
    flat_map, _ = robust_gradient_outlier_evidence(flat)

    border = WINDOW_SIZE
    core = np.s_[border:-border, border:-border]
    step_strength = float(np.max(step_map[core]))
    checker_strength = float(np.max(checker_map[core]))
    noise_q99 = float(np.quantile(noise_map[core], 0.99))
    scale_delta = float(np.max(np.abs(scaled - step_map)))
    return {
        "finite": bool(all(np.all(np.isfinite(x)) for x in (step_map, checker_map, noise_map, flat_map))),
        "bounded": bool(float(np.min(step_map)) >= 0.0 and float(np.max(step_map)) <= 1.0),
        "flat_max": float(np.max(np.abs(flat_map))),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat))),
        "positive_scale_max_abs_delta": scale_delta,
        "step_strength": step_strength,
        "checker_strength": checker_strength,
        "noise_q99": noise_q99,
        "step_exceeds_checker": bool(step_strength > checker_strength),
        "step_exceeds_noise": bool(step_strength > noise_q99),
        "window_size": WINDOW_SIZE,
        "mad_normalization": MAD_NORMALIZATION,
    }
