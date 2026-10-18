from __future__ import annotations

"""Fixed oriented-edge closure support from the image-torque principle.

Nishigaki, Fermuller, and DeMenthon (CVPR 2012) define image torque as
the moment of oriented edge tangents about a patch centre.  This module keeps
that equation and the paper's illustrated 5, 21, and 45 pixel square supports,
then backprojects coherent signed patch torque to the edge samples that can
support it.  It is a bounded repository surrogate, not the paper's learned
logistic edge-strengthening model.
"""

import numpy as np
from scipy import ndimage as ndi


PATCH_SIDES = (5, 21, 45)


def _scale_support(
    tangent_x: np.ndarray,
    tangent_y: np.ndarray,
    magnitude: np.ndarray,
    side: int,
) -> tuple[np.ndarray, np.ndarray]:
    radius = int(side) // 2
    dy, dx = np.mgrid[-radius : radius + 1, -radius : radius + 1]
    distance = np.hypot(dx, dy).astype(np.float64)
    dx = dx.astype(np.float64)
    dy = dy.astype(np.float64)

    # Eq. 6 in the paper, evaluated densely with gradient magnitude supplying
    # a threshold-free edge measure.  The denominator is the triangle-
    # inequality upper bound, making the signed coherence lie in [-1, 1].
    torque = (
        ndi.correlate(tangent_y, dx, mode="reflect")
        - ndi.correlate(tangent_x, dy, mode="reflect")
    )
    torque_bound = ndi.correlate(magnitude, distance, mode="reflect")
    coherence = np.divide(
        torque,
        torque_bound,
        out=np.zeros_like(torque),
        where=torque_bound > 1.0e-12,
    )
    coherence = np.clip(coherence, -1.0, 1.0)

    # Parameter-free counterpart of the paper's Eq. 12: each signed patch
    # coherence votes back to tangents whose moment has the same orientation.
    moment_x = ndi.convolve(coherence, dx, mode="reflect")
    moment_y = ndi.convolve(coherence, dy, mode="reflect")
    aligned = tangent_y * moment_x - tangent_x * moment_y
    aligned_bound = ndi.convolve(np.abs(coherence), distance, mode="reflect")
    support = np.divide(
        np.maximum(aligned, 0.0),
        aligned_bound,
        out=np.zeros_like(aligned),
        where=aligned_bound > 1.0e-12,
    )
    return np.clip(support, 0.0, 1.0), coherence


def image_torque_context(image: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Return bounded closure participation for the fixed three square supports."""

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("image torque requires one finite grayscale raster")
    if float(np.min(values)) < 0.0 or float(np.max(values)) > 1.0:
        raise ValueError("image torque expects values in [0,1]")

    scharr_x = np.asarray(
        [[-3.0, 0.0, 3.0], [-10.0, 0.0, 10.0], [-3.0, 0.0, 3.0]],
        dtype=np.float64,
    ) / 16.0
    gx = ndi.correlate(values, scharr_x, mode="reflect")
    gy = ndi.correlate(values, scharr_x.T, mode="reflect")
    magnitude = np.hypot(gx, gy)
    tangent_x = np.divide(gy, magnitude, out=np.zeros_like(gy), where=magnitude > 1.0e-12)
    tangent_y = np.divide(-gx, magnitude, out=np.zeros_like(gx), where=magnitude > 1.0e-12)
    tangent_x *= magnitude
    tangent_y *= magnitude

    support_maps: list[np.ndarray] = []
    coherence_maps: list[np.ndarray] = []
    for side in PATCH_SIDES:
        support, coherence = _scale_support(tangent_x, tangent_y, magnitude, side)
        support_maps.append(support)
        coherence_maps.append(coherence)

    cue = np.max(np.stack(support_maps, axis=0), axis=0)
    cue[magnitude <= 1.0e-12] = 0.0
    cue = np.clip(cue, 0.0, 1.0).astype(np.float32)
    absolute_coherence = np.max(np.abs(np.stack(coherence_maps, axis=0)), axis=0)
    return cue, {
        "cue_mean": float(np.mean(cue)),
        "cue_q90": float(np.quantile(cue, 0.9)),
        "cue_max": float(np.max(cue)),
        "positive_fraction": float(np.mean(cue > 0.0)),
        "max_abs_patch_coherence": float(np.max(absolute_coherence)),
        "mean_abs_patch_coherence": float(np.mean(absolute_coherence)),
    }


def synthetic_contract() -> dict[str, object]:
    size = 96
    yy, xx = np.indices((size, size))
    flat = np.full((size, size), 0.25, dtype=np.float64)
    circle = np.full((size, size), 0.25, dtype=np.float64)
    circle[(xx - 48) ** 2 + (yy - 48) ** 2 <= 24 ** 2] = 0.75
    open_step = flat.copy()
    open_step[:, size // 2 :] = 0.75
    checker = np.where(((yy // 3) + (xx // 3)) % 2 == 0, 0.25, 0.75)

    flat_map, _ = image_torque_context(flat)
    circle_map, _ = image_torque_context(circle)
    repeat_map, _ = image_torque_context(circle)
    reversed_map, _ = image_torque_context(1.0 - circle)
    step_map, _ = image_torque_context(open_step)
    checker_map, _ = image_torque_context(checker)

    ring = np.abs(np.hypot(xx - 48, yy - 48) - 24.0) <= 2.0
    step_band = np.abs(xx - size // 2) <= 2
    maps = (flat_map, circle_map, step_map, checker_map, reversed_map)
    circle_ring_mean = float(np.mean(circle_map[ring]))
    step_band_mean = float(np.mean(step_map[step_band]))
    checker_mean = float(np.mean(checker_map))
    closed_exceeds_open = bool(circle_ring_mean > step_band_mean)
    closed_exceeds_checker = bool(circle_ring_mean > checker_mean)
    return {
        "finite": bool(all(np.all(np.isfinite(value)) for value in maps)),
        "bounded": bool(all(float(np.min(value)) >= 0.0 and float(np.max(value)) <= 1.0 for value in maps)),
        "flat_max": float(np.max(flat_map)),
        "circle_ring_mean": circle_ring_mean,
        "open_step_band_mean": step_band_mean,
        "checker_mean": checker_mean,
        "closed_exceeds_open": closed_exceeds_open,
        "closed_exceeds_checker": closed_exceeds_checker,
        # Compatibility names consumed by the shared Stage-17h execution
        # harness.  Here "step" means the registered positive closure case.
        "step_exceeds_checker": closed_exceeds_checker,
        "step_exceeds_noise": closed_exceeds_open,
        "repeat_max_abs_delta": float(np.max(np.abs(circle_map - repeat_map))),
        "polarity_reversal_max_abs_delta": float(np.max(np.abs(circle_map - reversed_map))),
    }
