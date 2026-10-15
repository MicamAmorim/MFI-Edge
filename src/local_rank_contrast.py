from __future__ import annotations

"""Fixed local Mann-Whitney rank contrast for Stage 17b.

The cue is a repository realization of the nonparametric edge-statistic line
of Bovik, Huang and Munson (Pattern Recognition 1986) and the normalized,
orientation-selective ranklet construction of Smeraldi (ICPR 2002).  It is a
local spatial two-sample statistic, not an image-wide rank normalization.
"""

import numpy as np

from src.classical_detectors import gray01


RADIUS = 2
ORIENTATIONS = ("vertical", "horizontal", "diagonal_down", "diagonal_up")


def _shift_reflect(image: np.ndarray, dy: int, dx: int) -> np.ndarray:
    radius_y, radius_x = abs(int(dy)), abs(int(dx))
    padded = np.pad(image, ((radius_y, radius_y), (radius_x, radius_x)), mode="reflect")
    y0 = radius_y + int(dy)
    x0 = radius_x + int(dx)
    return padded[y0:y0 + image.shape[0], x0:x0 + image.shape[1]]


def _partition_offsets(radius: int, orientation: str) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    negative: list[tuple[int, int]] = []
    positive: list[tuple[int, int]] = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            coordinate = {
                "vertical": dx,
                "horizontal": dy,
                "diagonal_down": dx - dy,
                "diagonal_up": dx + dy,
            }[orientation]
            if coordinate < 0:
                negative.append((dy, dx))
            elif coordinate > 0:
                positive.append((dy, dx))
    if len(negative) != len(positive) or not negative:
        raise RuntimeError(f"unbalanced local-rank partition for {orientation}")
    return negative, positive


def _normalized_mann_whitney(
    image: np.ndarray,
    negative: list[tuple[int, int]],
    positive: list[tuple[int, int]],
) -> np.ndarray:
    """Return signed normalized pairwise rank contrast in ``[-1, 1]``.

    Each positive/negative sample pair contributes +1, -1, or 0 for greater,
    less, or tied intensity.  This is equivalent to twice the tie-corrected
    Mann-Whitney probability minus one, without forming per-pixel ranks.
    """
    neg = [_shift_reflect(image, dy, dx) for dy, dx in negative]
    pos = [_shift_reflect(image, dy, dx) for dy, dx in positive]
    signed = np.zeros_like(image, dtype=np.float32)
    for p_value in pos:
        for n_value in neg:
            signed += (p_value > n_value).astype(np.float32)
            signed -= (p_value < n_value).astype(np.float32)
    signed /= float(len(negative) * len(positive))
    return signed


def local_rank_contrast(image: np.ndarray, *, radius: int = RADIUS) -> np.ndarray:
    """Return maximum absolute four-orientation local rank contrast."""
    gray = gray01(image).astype(np.float32, copy=False)
    responses = []
    for orientation in ORIENTATIONS:
        negative, positive = _partition_offsets(int(radius), orientation)
        responses.append(np.abs(_normalized_mann_whitney(gray, negative, positive)))
    return np.clip(np.maximum.reduce(responses), 0.0, 1.0).astype(np.float32)


def synthetic_contract() -> dict[str, float | bool]:
    """Deterministic boundary, flat-field, and monotone-invariance checks."""
    step = np.zeros((64, 64), dtype=np.float32)
    step[:, 32:] = 1.0
    yy, xx = np.indices(step.shape)
    probe = ((3 * yy + 5 * xx) % 97).astype(np.float32) / 96.0
    ramped = probe * probe
    flat = np.full_like(step, 0.37)

    first = local_rank_contrast(step)
    second = local_rank_contrast(step)
    probe_response = local_rank_contrast(probe)
    monotone = local_rank_contrast(ramped)
    flat_response = local_rank_contrast(flat)
    repeat_delta = float(np.max(np.abs(first - second)))
    monotone_delta = float(np.max(np.abs(probe_response - monotone)))
    step_band = float(np.mean(first[:, 29:35]))
    remote = float(np.mean(np.concatenate([first[:, :12], first[:, -12:]], axis=1)))
    flat_max = float(np.max(flat_response))
    return {
        "finite": bool(np.all(np.isfinite(first)) and np.all(np.isfinite(flat_response))),
        "bounded": bool(np.min(first) >= 0.0 and np.max(first) <= 1.0),
        "repeat_max_abs_delta": repeat_delta,
        "monotone_transform_max_abs_delta": monotone_delta,
        "step_band_mean": step_band,
        "remote_band_mean": remote,
        "flat_max": flat_max,
        "step_exceeds_remote": bool(step_band > remote),
        "flat_is_zero": bool(flat_max == 0.0),
    }
