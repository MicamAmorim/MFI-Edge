from __future__ import annotations

"""Fixed semi-global scanline change-point support for Stage 17x.

Jevnisek and Avidan (CVIU, 2016) detect boundaries by optimally segmenting
one-dimensional scanlines and merging evidence across directions.  Stage 17x
isolates that mid-level principle in a deterministic repository surrogate:
piecewise-constant row and column models are selected by exact dynamic
programming with a Schwarz/BIC penalty, and adjacent-segment contrast is
written symmetrically to the two raster samples bordering every change point.

This is not the complete SGBD detector.  It omits the authors' learned texton
representation, semi-global smoothing, marginalization over segment counts,
and optional ultrametric-contour postprocessing.
"""

import numpy as np
from scipy import ndimage as ndi


MAX_WORKING_SIDE = 256
SCAN_DIRECTIONS = ("rows", "columns")
_MAD_NORMALIZER = 0.6744897501960817 * np.sqrt(2.0)


def _gray01(image: np.ndarray) -> np.ndarray:
    x = np.asarray(image, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("semi-global change-point context expects a 2-D image")
    if not np.all(np.isfinite(x)):
        raise ValueError("semi-global change-point context received non-finite input")
    if x.size and float(np.max(x)) > 1.5:
        x = x / 255.0
    return np.clip(x, 0.0, 1.0)


def _working_grid(image: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    shape = tuple(int(v) for v in image.shape)
    largest = max(shape, default=0)
    if largest <= MAX_WORKING_SIDE:
        return image, shape
    scale = MAX_WORKING_SIDE / float(largest)
    target = tuple(max(2, int(round(v * scale))) for v in shape)
    factors = tuple(target[d] / float(shape[d]) for d in range(2))
    reduced = ndi.zoom(image, factors, order=1, mode="reflect", prefilter=False)
    return np.asarray(reduced, dtype=np.float64), shape


def _noise_variance(line: np.ndarray) -> float:
    differences = np.diff(line)
    if differences.size == 0:
        return 0.0
    center = float(np.median(differences))
    sigma = float(np.median(np.abs(differences - center))) / _MAD_NORMALIZER
    if sigma <= np.finfo(np.float64).eps:
        sigma = float(np.sqrt(np.mean(np.square(differences)) / 2.0))
    return sigma * sigma


def _segment_line(line: np.ndarray) -> tuple[np.ndarray, int, float]:
    """Return symmetric raster support for the BIC-selected exact partition."""

    values = np.asarray(line, dtype=np.float64)
    n = int(values.size)
    evidence = np.zeros(n, dtype=np.float64)
    if n < 2 or float(np.ptp(values)) <= np.finfo(np.float64).eps:
        return evidence, 1, 0.0

    variance = _noise_variance(values)
    penalty = max(variance, np.finfo(np.float64).eps) * np.log(float(n))
    prefix = np.concatenate(([0.0], np.cumsum(values)))
    prefix2 = np.concatenate(([0.0], np.cumsum(np.square(values))))
    optimum = np.full(n + 1, np.inf, dtype=np.float64)
    previous = np.full(n + 1, -1, dtype=np.int32)
    optimum[0] = 0.0

    for end in range(1, n + 1):
        starts = np.arange(end, dtype=np.int32)
        lengths = end - starts
        sums = prefix[end] - prefix[starts]
        sums2 = prefix2[end] - prefix2[starts]
        residual = np.maximum(sums2 - np.square(sums) / lengths, 0.0)
        objectives = optimum[starts] + residual + penalty
        best = int(np.argmin(objectives))
        optimum[end] = float(objectives[best])
        previous[end] = int(starts[best])

    boundaries = [n]
    cursor = n
    while cursor > 0:
        cursor = int(previous[cursor])
        if cursor < 0:
            raise RuntimeError("invalid semi-global dynamic-programming traceback")
        boundaries.append(cursor)
    boundaries = sorted(boundaries)
    segment_count = len(boundaries) - 1
    for segment in range(1, segment_count):
        left_start, boundary, right_end = (
            boundaries[segment - 1],
            boundaries[segment],
            boundaries[segment + 1],
        )
        left_mean = (prefix[boundary] - prefix[left_start]) / (boundary - left_start)
        right_mean = (prefix[right_end] - prefix[boundary]) / (right_end - boundary)
        strength = min(abs(float(right_mean - left_mean)), 1.0)
        evidence[boundary - 1] = max(evidence[boundary - 1], strength)
        evidence[boundary] = max(evidence[boundary], strength)
    return evidence, segment_count, float(penalty)


def _axis_evidence(image: np.ndarray, axis: int) -> tuple[np.ndarray, list[int], list[float]]:
    oriented = image if axis == 1 else image.T
    evidence = np.zeros_like(oriented, dtype=np.float64)
    segments: list[int] = []
    penalties: list[float] = []
    for index, line in enumerate(oriented):
        response, count, penalty = _segment_line(line)
        evidence[index] = response
        segments.append(count)
        penalties.append(penalty)
    return (evidence if axis == 1 else evidence.T), segments, penalties


def semiglobal_changepoint_evidence(
    image: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return fixed row/column BIC change-point contrast in ``[0,1]``."""

    x = _gray01(image)
    working, original_shape = _working_grid(x)
    row_map, row_segments, row_penalties = _axis_evidence(working, axis=1)
    column_map, column_segments, column_penalties = _axis_evidence(working, axis=0)
    evidence = np.maximum(row_map, column_map)
    if tuple(evidence.shape) != original_shape:
        factors = tuple(original_shape[d] / float(evidence.shape[d]) for d in range(2))
        evidence = ndi.zoom(
            evidence, factors, order=1, mode="reflect", prefilter=False
        )
        evidence = evidence[: original_shape[0], : original_shape[1]]
        if tuple(evidence.shape) != original_shape:
            raise RuntimeError("semi-global evidence resize did not preserve raster shape")
    evidence = np.clip(evidence, 0.0, 1.0).astype(np.float32)
    active = evidence > 0.0
    diagnostics = {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "max_evidence": float(np.max(evidence)),
        "active_fraction": float(np.mean(active)),
        "row_mean_segments": float(np.mean(row_segments)),
        "column_mean_segments": float(np.mean(column_segments)),
        "row_mean_penalty": float(np.mean(row_penalties)),
        "column_mean_penalty": float(np.mean(column_penalties)),
        "working_height": float(working.shape[0]),
        "working_width": float(working.shape[1]),
    }
    return evidence, diagnostics


def synthetic_contract() -> dict[str, float | bool]:
    size = 65
    center = size // 2
    flat = np.full((size, size), 0.4, dtype=np.float64)
    step = np.full((size, size), 0.2, dtype=np.float64)
    step[:, center:] = 0.8
    checker = (np.indices((size, size)).sum(axis=0) % 2).astype(np.float64)
    rng = np.random.default_rng(17020)
    noise = np.clip(0.5 + 0.001 * rng.standard_normal((size, size)), 0.0, 1.0)

    flat_map, _ = semiglobal_changepoint_evidence(flat)
    step_map, _ = semiglobal_changepoint_evidence(step)
    checker_map, _ = semiglobal_changepoint_evidence(checker)
    noise_map, _ = semiglobal_changepoint_evidence(noise)
    repeat, _ = semiglobal_changepoint_evidence(step)
    scaled, _ = semiglobal_changepoint_evidence(0.5 * step)
    shifted, _ = semiglobal_changepoint_evidence(step + 0.1)
    inverted, _ = semiglobal_changepoint_evidence(1.0 - step)
    step_strength = float(np.max(step_map))
    return {
        "finite": bool(
            all(
                np.all(np.isfinite(value))
                for value in (flat_map, step_map, checker_map, noise_map)
            )
        ),
        "bounded": bool(float(np.min(step_map)) >= 0.0 and step_strength <= 1.0),
        "flat_max": float(np.max(np.abs(flat_map))),
        "step_max": step_strength,
        "checker_max": float(np.max(np.abs(checker_map))),
        "noise_mean": float(np.mean(noise_map)),
        "step_exceeds_checker": bool(step_strength > float(np.max(checker_map))),
        "step_exceeds_noise": bool(step_strength > float(np.mean(noise_map))),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat))),
        "positive_scale_max_abs_error": float(np.max(np.abs(scaled - 0.5 * step_map))),
        "offset_max_abs_delta": float(np.max(np.abs(shifted - step_map))),
        "polarity_max_abs_delta": float(np.max(np.abs(inverted - step_map))),
        "max_working_side": MAX_WORKING_SIDE,
    }
