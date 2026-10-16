from __future__ import annotations

"""Fixed Shiozaki-style local brightness-entropy evidence.

Shiozaki (CVGIP 1986, DOI 10.1016/S0734-189X(86)80025-1) defines a
local brightness distribution by normalizing the intensities in a small
neighbourhood.  Its entropy is maximal when those intensities are equal and
falls when brightness is concentrated unevenly, as at a sharp transition.
This module exposes the normalized entropy deficit of the published 3x3
operator as a bounded positive context cue.  It is not a complete reproduction
of the paper's thresholded edge-picture pipeline.
"""

import numpy as np
from scipy import ndimage as ndi


WINDOW_SIZE = 3
WINDOW_AREA = WINDOW_SIZE * WINDOW_SIZE
MAX_ENTROPY = float(np.log(WINDOW_AREA))


def _gray01(image: np.ndarray) -> np.ndarray:
    x = np.asarray(image, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("brightness entropy expects a conditioned grayscale image")
    if x.size and float(np.nanmax(x)) > 1.5:
        x = x / 255.0
    return np.clip(x, 0.0, 1.0)


def local_brightness_entropy_deficit(
    image: np.ndarray,
    *,
    window_size: int = WINDOW_SIZE,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return ``1 - H(p)/log(9)`` for the fixed local brightness distribution.

    For a neighbourhood with intensities ``I_i`` and positive sum ``S``, the
    distribution is ``p_i=I_i/S``.  The implementation evaluates
    ``H=log(S)-sum(I_i log(I_i))/S`` without histogram bins.  An all-zero
    neighbourhood is assigned zero evidence.  Reflection is the fixed finite-
    raster convention, and no image-wise normalization is applied.
    """

    if int(window_size) != WINDOW_SIZE:
        raise ValueError(f"fixed window size must be {WINDOW_SIZE}")
    x = _gray01(image)
    local_sum = ndi.uniform_filter(x, size=WINDOW_SIZE, mode="reflect") * WINDOW_AREA
    x_log_x = np.zeros_like(x)
    positive = x > 0.0
    x_log_x[positive] = x[positive] * np.log(x[positive])
    local_x_log_x = (
        ndi.uniform_filter(x_log_x, size=WINDOW_SIZE, mode="reflect") * WINDOW_AREA
    )

    entropy = np.zeros_like(x)
    defined = local_sum > np.finfo(np.float64).eps
    entropy[defined] = (
        np.log(local_sum[defined])
        - local_x_log_x[defined] / local_sum[defined]
    )
    evidence = np.zeros_like(x)
    evidence[defined] = np.clip(
        1.0 - entropy[defined] / MAX_ENTROPY,
        0.0,
        1.0,
    )
    diagnostics = {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "entropy_mean": float(np.mean(entropy[defined])) if np.any(defined) else 0.0,
        "entropy_q10": float(np.quantile(entropy[defined], 0.1)) if np.any(defined) else 0.0,
        "max_evidence": float(np.max(evidence)),
        "zero_sum_fraction": float(np.mean(~defined)),
    }
    return evidence.astype(np.float32), diagnostics


def synthetic_contract() -> dict[str, float | bool]:
    size = 65
    center = size // 2
    flat = np.full((size, size), 0.4, dtype=np.float64)
    step = np.full((size, size), 0.2, dtype=np.float64)
    step[:, center:] = 0.8
    checker = 0.45 + 0.10 * (
        (np.indices((size, size)).sum(axis=0) % 2).astype(np.float64)
    )
    rng = np.random.default_rng(1710)
    noise = np.clip(0.5 + 0.03 * rng.standard_normal((size, size)), 0.0, 1.0)

    flat_evidence, _ = local_brightness_entropy_deficit(flat)
    step_evidence, _ = local_brightness_entropy_deficit(step)
    checker_evidence, _ = local_brightness_entropy_deficit(checker)
    noise_evidence, _ = local_brightness_entropy_deficit(noise)
    repeat, _ = local_brightness_entropy_deficit(step)
    scaled, _ = local_brightness_entropy_deficit(0.5 * step)
    band = slice(center - 1, center + 2)
    step_band = float(np.mean(step_evidence[:, band]))
    checker_mean = float(np.mean(checker_evidence))
    noise_mean = float(np.mean(noise_evidence))
    return {
        "finite": bool(
            np.all(np.isfinite(flat_evidence))
            and np.all(np.isfinite(step_evidence))
            and np.all(np.isfinite(checker_evidence))
            and np.all(np.isfinite(noise_evidence))
        ),
        "bounded": bool(
            min(
                float(np.min(flat_evidence)),
                float(np.min(step_evidence)),
                float(np.min(checker_evidence)),
                float(np.min(noise_evidence)),
            )
            >= 0.0
            and max(
                float(np.max(flat_evidence)),
                float(np.max(step_evidence)),
                float(np.max(checker_evidence)),
                float(np.max(noise_evidence)),
            )
            <= 1.0
        ),
        "flat_max": float(np.max(flat_evidence)),
        "step_band_mean": step_band,
        "checker_mean": checker_mean,
        "noise_mean": noise_mean,
        "step_exceeds_checker": bool(step_band > checker_mean + 1.0e-4),
        "step_exceeds_noise": bool(step_band > noise_mean + 1.0e-4),
        "multiplicative_scale_max_abs_delta": float(
            np.max(np.abs(step_evidence - scaled))
        ),
        "repeat_max_abs_delta": float(np.max(np.abs(step_evidence - repeat))),
    }
