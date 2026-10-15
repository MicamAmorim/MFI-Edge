from __future__ import annotations

"""Fixed local fractional-Brownian scaling evidence for boundary context.

Toennies and Schnabel (CBMS 1994) model local gray-level variation with
fractional Brownian motion and use departures in local fractal behavior to
separate deterministic edges from stochastic image interiors and noise.  This
module is a bounded repository surrogate, not a reproduction of their full
detector.  It estimates a local first-order structure-function exponent at the
three dyadic pixel lags that fit in the smallest centered support, then weights
the exponent by fit reliability and variation amplitude.
"""

import numpy as np
from scipy import ndimage as ndi


OFFSETS = (1, 2, 4)
SUPPORT_SIZE = 2 * max(OFFSETS) + 1
_DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


def _gray01(image: np.ndarray) -> np.ndarray:
    x = np.asarray(image, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("local fractal evidence expects a conditioned grayscale image")
    if x.size and float(np.nanmax(x)) > 1.5:
        x = x / 255.0
    return np.clip(x, 0.0, 1.0)


def local_fractal_edge_evidence(
    image: np.ndarray,
    *,
    offsets: tuple[int, ...] = OFFSETS,
    support_size: int = SUPPORT_SIZE,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return reliable high-Holder-exponent variation as positive evidence.

    For each dyadic lag ``h``, ``S1(h)`` is the local mean absolute increment
    over horizontal, vertical and two diagonal axes.  A least-squares line is
    fitted to ``log S1(h)`` versus ``log h``.  The evidence is

    ``clip(H, 0, 1) * clip(R^2, 0, 1) * S1(h_max)``.

    Thus a deterministic step has a reliable, high scaling exponent and
    nonzero amplitude, a flat patch remains exactly zero, and rapidly
    alternating/noise-like structure is attenuated.  Reflection is fixed at
    the finite raster boundary.  There is no image-wise normalization.
    """

    x = _gray01(image)
    if tuple(int(v) for v in offsets) != OFFSETS:
        raise ValueError(f"fixed offsets must be {OFFSETS}")
    if int(support_size) != SUPPORT_SIZE:
        raise ValueError(f"fixed support size must be {SUPPORT_SIZE}")

    structure = []
    for lag in OFFSETS:
        increments = []
        for dy, dx in _DIRECTIONS:
            shifted = ndi.shift(
                x,
                shift=(dy * lag, dx * lag),
                order=0,
                mode="reflect",
                prefilter=False,
            )
            increments.append(np.abs(x - shifted))
        mean_increment = np.mean(np.stack(increments, axis=-1), axis=-1)
        structure.append(
            ndi.uniform_filter(mean_increment, size=SUPPORT_SIZE, mode="reflect")
        )
    values = np.stack(structure, axis=-1)

    eps = np.finfo(np.float64).eps
    log_values = np.log(np.maximum(values, eps))
    log_lags = np.log(np.asarray(OFFSETS, dtype=np.float64))
    centered_lags = log_lags - float(np.mean(log_lags))
    centered_values = log_values - np.mean(log_values, axis=-1, keepdims=True)
    holder = np.sum(centered_values * centered_lags, axis=-1) / float(
        np.dot(centered_lags, centered_lags)
    )
    fitted = (
        np.mean(log_values, axis=-1, keepdims=True)
        + holder[..., None] * centered_lags
    )
    residual_ss = np.sum((log_values - fitted) ** 2, axis=-1)
    total_ss = np.sum(centered_values**2, axis=-1)
    r2 = np.zeros_like(total_ss)
    nondegenerate = total_ss > eps
    r2[nondegenerate] = 1.0 - residual_ss[nondegenerate] / total_ss[nondegenerate]

    reliable_holder = np.clip(holder, 0.0, 1.0) * np.clip(r2, 0.0, 1.0)
    evidence = reliable_holder * values[..., -1]
    diagnostics = {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "holder_mean": float(np.mean(holder)),
        "holder_q90": float(np.quantile(holder, 0.9)),
        "r2_mean": float(np.mean(np.clip(r2, 0.0, 1.0))),
        "max_evidence": float(np.max(evidence)),
    }
    return evidence.astype(np.float32), diagnostics


def synthetic_contract() -> dict[str, float | bool]:
    size = 65
    center = size // 2
    flat = np.full((size, size), 0.4, dtype=np.float64)
    step = np.full((size, size), 0.2, dtype=np.float64)
    step[:, center:] = 0.8
    checker = 0.2 + 0.6 * ((np.indices((size, size)).sum(axis=0) % 2).astype(float))
    rng = np.random.default_rng(1708)
    noise = np.clip(0.5 + 0.12 * rng.standard_normal((size, size)), 0.0, 1.0)

    flat_evidence, _ = local_fractal_edge_evidence(flat)
    step_evidence, _ = local_fractal_edge_evidence(step)
    checker_evidence, _ = local_fractal_edge_evidence(checker)
    noise_evidence, _ = local_fractal_edge_evidence(noise)
    repeat, _ = local_fractal_edge_evidence(step)
    band = slice(center - max(OFFSETS), center + max(OFFSETS) + 1)
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
        "repeat_max_abs_delta": float(np.max(np.abs(step_evidence - repeat))),
    }
