from __future__ import annotations

"""Fixed two-sided morphological edge strength for Stage 17v.

Van Vliet, Young, and Beckers (CVGIP, 1989) write Lee's blur-minimum
morphological edge strength as ``min(gradmax, -gradmin)``.  With the paper's
unit square mask this is the smaller of the center pixel's distances to the
local maximum and minimum.  It is positive only when a pixel has brighter and
darker support in the same neighborhood, unlike a range or one-sided gradient.

Stage 17v uses the smallest published square support (3x3) as a context cue.
It does not run the paper's nonlinear-Laplacian zero-crossing detector,
Gaussian smoothing, distance transforms, thresholding, or contour extraction.
"""

import numpy as np
from scipy import ndimage as ndi


SUPPORT_SIZE = 3


def _gray01(image: np.ndarray) -> np.ndarray:
    x = np.asarray(image, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("morphological blur-minimum context expects a 2-D image")
    if not np.all(np.isfinite(x)):
        raise ValueError("morphological blur-minimum context received non-finite input")
    if x.size and float(np.max(x)) > 1.5:
        x = x / 255.0
    return np.clip(x, 0.0, 1.0)


def morphological_blur_minimum_evidence(
    image: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return the fixed 3x3 two-sided order-statistic strength.

    For conditioned intensity ``I``, ``u=max_3x3(I)-I`` and
    ``d=I-min_3x3(I)``.  The evidence is exactly ``min(u, d)``.  Reflection is
    the fixed finite-raster convention and no image-wise normalization is used.
    For input in ``[0,1]`` the evidence lies in ``[0,0.5]``.
    """

    x = _gray01(image)
    local_max = ndi.maximum_filter(x, size=SUPPORT_SIZE, mode="reflect")
    local_min = ndi.minimum_filter(x, size=SUPPORT_SIZE, mode="reflect")
    upper_distance = np.maximum(local_max - x, 0.0)
    lower_distance = np.maximum(x - local_min, 0.0)
    evidence = np.minimum(upper_distance, lower_distance)
    evidence = np.clip(evidence, 0.0, 0.5).astype(np.float32)
    if not np.all(np.isfinite(evidence)):
        raise RuntimeError("non-finite morphological blur-minimum evidence")

    diagnostics = {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "max_evidence": float(np.max(evidence)),
        "active_fraction": float(np.mean(evidence > 0.0)),
        "upper_distance_mean": float(np.mean(upper_distance)),
        "lower_distance_mean": float(np.mean(lower_distance)),
        "local_range_mean": float(np.mean(local_max - local_min)),
    }
    return evidence, diagnostics


def synthetic_contract() -> dict[str, float | bool]:
    size = 65
    center = size // 2
    flat = np.full((size, size), 0.4, dtype=np.float64)
    sharp_step = np.zeros((size, size), dtype=np.float64)
    sharp_step[:, center:] = 1.0
    checker = (np.indices((size, size)).sum(axis=0) % 2).astype(np.float64)
    impulse = np.zeros((size, size), dtype=np.float64)
    impulse[center, center] = 1.0
    rng = np.random.default_rng(17018)
    noise = np.clip(0.5 + 0.001 * rng.standard_normal((size, size)), 0.0, 1.0)
    ramp = np.zeros((size, size), dtype=np.float64)
    ramp[:, : center - 1] = 0.25
    ramp[:, center - 1] = 0.25
    ramp[:, center] = 0.50
    ramp[:, center + 1 :] = 0.75

    flat_map, _ = morphological_blur_minimum_evidence(flat)
    step_map, _ = morphological_blur_minimum_evidence(sharp_step)
    checker_map, _ = morphological_blur_minimum_evidence(checker)
    impulse_map, _ = morphological_blur_minimum_evidence(impulse)
    noise_map, _ = morphological_blur_minimum_evidence(noise)
    ramp_map, _ = morphological_blur_minimum_evidence(ramp)
    repeat, _ = morphological_blur_minimum_evidence(ramp)
    scaled, _ = morphological_blur_minimum_evidence(0.5 * ramp)
    shifted, _ = morphological_blur_minimum_evidence(ramp + 0.1)
    inverted, _ = morphological_blur_minimum_evidence(1.0 - ramp)

    ramp_center = float(ramp_map[center, center])
    return {
        "finite": bool(
            all(
                np.all(np.isfinite(value))
                for value in (
                    flat_map,
                    step_map,
                    checker_map,
                    impulse_map,
                    noise_map,
                    ramp_map,
                )
            )
        ),
        "bounded": bool(
            float(np.min(ramp_map)) >= 0.0 and float(np.max(ramp_map)) <= 0.5
        ),
        "flat_max": float(np.max(np.abs(flat_map))),
        "sharp_step_max": float(np.max(np.abs(step_map))),
        "checker_max": float(np.max(np.abs(checker_map))),
        "impulse_center": float(impulse_map[center, center]),
        "noise_mean": float(np.mean(noise_map[2:-2, 2:-2])),
        "ramp_center": ramp_center,
        "ramp_exceeds_sharp_step": bool(ramp_center > float(np.max(step_map))),
        "ramp_exceeds_checker": bool(ramp_center > float(np.max(checker_map))),
        "ramp_exceeds_impulse_center": bool(ramp_center > float(impulse_map[center, center])),
        "ramp_exceeds_noise": bool(ramp_center > float(np.mean(noise_map[2:-2, 2:-2]))),
        # Compatibility aliases consumed by the shared Stage-17 context harness.
        "step_exceeds_checker": bool(ramp_center > float(np.max(checker_map))),
        "step_exceeds_noise": bool(ramp_center > float(np.mean(noise_map[2:-2, 2:-2]))),
        "repeat_max_abs_delta": float(np.max(np.abs(ramp_map - repeat))),
        "positive_scale_max_abs_error": float(
            np.max(np.abs(scaled - 0.5 * ramp_map))
        ),
        "offset_max_abs_delta": float(np.max(np.abs(shifted - ramp_map))),
        "polarity_max_abs_delta": float(np.max(np.abs(inverted - ramp_map))),
        "support_size": SUPPORT_SIZE,
    }
