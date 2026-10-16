from __future__ import annotations

"""Fixed annular surround-isolation evidence for a local edge-energy map.

Grigorescu, Petkov, and Westenberg (Image and Vision Computing 22, 2004,
DOI 10.1016/j.imavis.2003.12.004) define isotropic surround suppression by
convolving gradient magnitude with the positive part of a difference of
Gaussians whose standard deviations are ``sigma`` and ``4*sigma``.  Their
suppression slope is ``atan(t / M)``.  This module uses the complementary,
bounded quantity as positive evidence that a response is isolated from dense
nearby edge energy.  It does not implement the paper's suppression factor,
hysteresis, or complete detector.
"""

import numpy as np
from scipy import ndimage as ndi


INNER_SIGMA = 1.0
OUTER_SIGMA = 4.0
KERNEL_RADIUS = 12
EPS = 1.0e-12


def _annular_kernel() -> np.ndarray:
    axis = np.arange(-KERNEL_RADIUS, KERNEL_RADIUS + 1, dtype=np.float64)
    yy, xx = np.meshgrid(axis, axis, indexing="ij")
    radius2 = xx * xx + yy * yy
    inner = np.exp(-radius2 / (2.0 * INNER_SIGMA**2)) / (
        2.0 * np.pi * INNER_SIGMA**2
    )
    outer = np.exp(-radius2 / (2.0 * OUTER_SIGMA**2)) / (
        2.0 * np.pi * OUTER_SIGMA**2
    )
    positive_dog = np.maximum(outer - inner, 0.0)
    total = float(np.sum(positive_dog))
    if total <= EPS:
        raise RuntimeError("annular surround kernel has zero mass")
    return positive_dog / total


ANNULAR_KERNEL = _annular_kernel()


def surround_isolation_evidence(
    energy: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return bounded positive evidence complementary to suppression slope.

    ``energy`` is the unchanged nonnegative local edge-energy response.  The
    surround term is its reflection-padded convolution with the fixed annular
    kernel.  At positive-energy pixels, evidence is
    ``1 - (2/pi)*atan(surround/energy)``; zero-energy pixels receive zero.
    The ratio makes the cue invariant to positive global rescaling.
    """

    response = np.asarray(energy, dtype=np.float64)
    if response.ndim != 2:
        raise ValueError("surround isolation expects a two-dimensional energy map")
    if not np.all(np.isfinite(response)) or float(np.min(response)) < 0.0:
        raise ValueError("surround isolation requires finite nonnegative energy")
    surround = ndi.convolve(response, ANNULAR_KERNEL, mode="reflect")
    active = response > EPS
    evidence = np.zeros_like(response)
    ratio = np.zeros_like(response)
    ratio[active] = surround[active] / response[active]
    evidence[active] = 1.0 - (2.0 / np.pi) * np.arctan(ratio[active])
    evidence = np.clip(evidence, 0.0, 1.0)
    diagnostics = {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "active_evidence_mean": float(np.mean(evidence[active])) if np.any(active) else 0.0,
        "surround_mean": float(np.mean(surround)),
        "suppression_ratio_q90": float(np.quantile(ratio[active], 0.9)) if np.any(active) else 0.0,
        "active_fraction": float(np.mean(active)),
        "max_evidence": float(np.max(evidence)) if evidence.size else 0.0,
    }
    return evidence.astype(np.float32), diagnostics


def synthetic_contract() -> dict[str, float | bool]:
    size = 65
    center = size // 2
    flat = np.zeros((size, size), dtype=np.float64)
    isolated = np.zeros_like(flat)
    isolated[8:-8, center] = 1.0
    dense = np.zeros_like(flat)
    dense[8:-8, 8:-8:4] = 1.0
    rng = np.random.default_rng(1712)
    random_texture = (rng.random((size, size)) < 0.18).astype(np.float64)

    flat_evidence, _ = surround_isolation_evidence(flat)
    isolated_evidence, _ = surround_isolation_evidence(isolated)
    dense_evidence, _ = surround_isolation_evidence(dense)
    random_evidence, _ = surround_isolation_evidence(random_texture)
    repeat, _ = surround_isolation_evidence(isolated)
    scaled, _ = surround_isolation_evidence(0.5 * isolated)
    isolated_mean = float(np.mean(isolated_evidence[isolated > 0.0]))
    dense_mean = float(np.mean(dense_evidence[dense > 0.0]))
    random_mean = float(np.mean(random_evidence[random_texture > 0.0]))
    return {
        "finite": bool(
            np.all(np.isfinite(flat_evidence))
            and np.all(np.isfinite(isolated_evidence))
            and np.all(np.isfinite(dense_evidence))
            and np.all(np.isfinite(random_evidence))
        ),
        "bounded": bool(
            min(
                float(np.min(flat_evidence)),
                float(np.min(isolated_evidence)),
                float(np.min(dense_evidence)),
                float(np.min(random_evidence)),
            ) >= 0.0
            and max(
                float(np.max(flat_evidence)),
                float(np.max(isolated_evidence)),
                float(np.max(dense_evidence)),
                float(np.max(random_evidence)),
            ) <= 1.0
        ),
        "flat_max": float(np.max(flat_evidence)),
        "isolated_active_mean": isolated_mean,
        "dense_active_mean": dense_mean,
        "random_active_mean": random_mean,
        # Compatibility names used by the shared Stage-17 harness contract.
        "step_exceeds_checker": bool(isolated_mean > dense_mean + 1.0e-4),
        "step_exceeds_noise": bool(isolated_mean > random_mean + 1.0e-4),
        "positive_scale_max_abs_delta": float(np.max(np.abs(isolated_evidence - scaled))),
        "repeat_max_abs_delta": float(np.max(np.abs(isolated_evidence - repeat))),
        "kernel_sum": float(np.sum(ANNULAR_KERNEL)),
        "kernel_center": float(ANNULAR_KERNEL[KERNEL_RADIUS, KERNEL_RADIUS]),
    }
