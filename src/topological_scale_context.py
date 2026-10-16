from __future__ import annotations

"""Fixed two-scale topological-gradient edge evidence for Stage 17n.

This implements the one-point ``h4`` approximation in Amstutz and
Fehrenbach (JMIV 2015, Eq. 36 and the following display) as a scalar positive
context map.  It is not their complete detector: thresholding, hysteresis and
localization remain those of the unchanged MFI controller.
"""

import math

import numpy as np
from scipy.ndimage import gaussian_filter


HEAT_TIME = 2.0
BETA = 1.0 - math.sqrt(1.0 - 4.0 / (math.pi * math.pi))
EARLY_TIME = BETA * HEAT_TIME
LATE_TIME = (2.0 - BETA) * HEAT_TIME
EARLY_SIGMA = math.sqrt(2.0 * EARLY_TIME)
LATE_SIGMA = math.sqrt(2.0 * LATE_TIME)
TRUNCATE = 4.0


def _gradient_at_heat_time(image: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(image, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("topological scale context expects a two-dimensional image")
    gy = gaussian_filter(x, sigma=sigma, order=(1, 0), mode="reflect", truncate=TRUNCATE)
    gx = gaussian_filter(x, sigma=sigma, order=(0, 1), mode="reflect", truncate=TRUNCATE)
    return gx, gy


def topological_scale_evidence(image: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Return positive crack-insertion sensitivity from two heat scales.

    For gradients ``a`` and ``b`` at the analytically coupled heat times, the
    h4 quadratic form is ``-2*pi*T*n' S n`` with
    ``S=(a b' + b a')/2``.  Minimizing over crack normals therefore gives the
    nonnegative evidence ``2*pi*T*max(lambda_max(S), 0)``.
    """

    ax, ay = _gradient_at_heat_time(image, EARLY_SIGMA)
    bx, by = _gradient_at_heat_time(image, LATE_SIGMA)
    sxx = ax * bx
    syy = ay * by
    sxy = 0.5 * (ax * by + ay * bx)
    discriminant = np.sqrt(np.maximum((sxx - syy) ** 2 + 4.0 * sxy**2, 0.0))
    lambda_max = 0.5 * (sxx + syy + discriminant)
    evidence = (2.0 * math.pi * HEAT_TIME * np.maximum(lambda_max, 0.0)).astype(np.float32)
    if not np.all(np.isfinite(evidence)):
        raise RuntimeError("non-finite topological scale evidence")
    diagnostics = {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "max_evidence": float(np.max(evidence)),
        "active_fraction": float(np.mean(evidence > 0.0)),
        "early_gradient_mean": float(np.mean(np.hypot(ax, ay))),
        "late_gradient_mean": float(np.mean(np.hypot(bx, by))),
        "positive_eigenvalue_mean": float(np.mean(np.maximum(lambda_max, 0.0))),
    }
    return evidence, diagnostics


def synthetic_contract() -> dict[str, float | bool]:
    size = 65
    step = np.zeros((size, size), dtype=np.float64)
    step[:, size // 2 :] = 1.0
    checker = (np.indices((size, size)).sum(axis=0) % 2).astype(np.float64)
    rng = np.random.default_rng(17014)
    noise = rng.random((size, size))
    flat = np.full((size, size), 0.37, dtype=np.float64)

    step_map, _ = topological_scale_evidence(step)
    repeat, _ = topological_scale_evidence(step)
    scaled, _ = topological_scale_evidence(0.5 * step)
    checker_map, _ = topological_scale_evidence(checker)
    noise_map, _ = topological_scale_evidence(noise)
    flat_map, _ = topological_scale_evidence(flat)

    border = 10
    core = np.s_[border:-border, border:-border]
    step_strength = float(np.max(step_map[core]))
    checker_strength = float(np.max(checker_map[core]))
    noise_strength = float(np.quantile(noise_map[core], 0.99))
    quadratic_delta = float(np.max(np.abs(scaled - 0.25 * step_map)))
    return {
        "finite": bool(all(np.all(np.isfinite(x)) for x in (step_map, checker_map, noise_map, flat_map))),
        "bounded": bool(float(np.min(step_map)) >= 0.0 and np.isfinite(float(np.max(step_map)))),
        "flat_max": float(np.max(np.abs(flat_map))),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat))),
        "quadratic_scale_max_abs_delta": quadratic_delta,
        "step_strength": step_strength,
        "checker_strength": checker_strength,
        "noise_q99": noise_strength,
        "step_exceeds_checker": bool(step_strength > checker_strength),
        "step_exceeds_noise": bool(step_strength > noise_strength),
        "heat_time": HEAT_TIME,
        "beta": BETA,
        "early_sigma": EARLY_SIGMA,
        "late_sigma": LATE_SIGMA,
    }
