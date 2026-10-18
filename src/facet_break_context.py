from __future__ import annotations

"""Fixed local sloped-facet structural-break evidence.

Haralick (CGIP 1980) models image regions as sloped planes and measures an
edge by an F statistic for the difference between planes fitted on opposing
neighbourhoods.  This module implements one bounded, fixed raster surrogate:
for each of four axes it compares two disjoint 3x3 planar fits, centred two
pixels to either side of the candidate location, with one pooled planar fit.
The maximum Chow-style F evidence is returned.  It is context only and does
not replace the repository's Scharr+NMS localizer.
"""

import numpy as np


PLANE_PARAMETERS = 3
NEIGHBOURHOOD_SIDE = 3
CENTRE_OFFSET = 2
AXES = ((1, 0), (0, 1), (1, 1), (1, -1))  # (dx, dy)
SUPPORT_RADIUS = 3
RELATIVE_RESIDUAL_TOLERANCE = 1.0e-12


def _axis_design(dx: int, dy: int) -> tuple[np.ndarray, np.ndarray, list[tuple[int, int]]]:
    offsets: list[tuple[int, int]] = []
    groups: list[int] = []
    for group, sign in enumerate((-1, 1)):
        center_x = sign * CENTRE_OFFSET * dx
        center_y = sign * CENTRE_OFFSET * dy
        for local_y in (-1, 0, 1):
            for local_x in (-1, 0, 1):
                offsets.append((center_y + local_y, center_x + local_x))
                groups.append(group)
    coordinates = np.asarray([[1.0, oy, ox] for oy, ox in offsets], dtype=np.float64)
    pooled_projection = coordinates @ np.linalg.pinv(coordinates)
    separate_projection = np.zeros((len(offsets), len(offsets)), dtype=np.float64)
    groups_array = np.asarray(groups)
    for group in (0, 1):
        ids = np.flatnonzero(groups_array == group)
        design = coordinates[ids]
        separate_projection[np.ix_(ids, ids)] = design @ np.linalg.pinv(design)
    return pooled_projection, separate_projection, offsets


_AXIS_MODELS = tuple(_axis_design(dx, dy) for dx, dy in AXES)


def _samples(image: np.ndarray, offsets: list[tuple[int, int]]) -> np.ndarray:
    padded = np.pad(image, SUPPORT_RADIUS, mode="reflect")
    height, width = image.shape
    return np.stack(
        [
            padded[
                SUPPORT_RADIUS + oy : SUPPORT_RADIUS + oy + height,
                SUPPORT_RADIUS + ox : SUPPORT_RADIUS + ox + width,
            ]
            for oy, ox in offsets
        ],
        axis=0,
    )


def _axis_evidence(
    image: np.ndarray,
    pooled_projection: np.ndarray,
    separate_projection: np.ndarray,
    offsets: list[tuple[int, int]],
) -> np.ndarray:
    values = _samples(image, offsets)
    flat = values.reshape(values.shape[0], -1)
    pooled_residual = flat - pooled_projection @ flat
    separate_residual = flat - separate_projection @ flat
    pooled_rss = np.sum(pooled_residual * pooled_residual, axis=0)
    separate_rss = np.sum(separate_residual * separate_residual, axis=0)
    improvement = np.maximum(pooled_rss - separate_rss, 0.0)

    residual_degrees = values.shape[0] - 2 * PLANE_PARAMETERS
    scale = np.sum(flat * flat, axis=0) + 1.0
    tolerance = RELATIVE_RESIDUAL_TOLERANCE * scale
    numerator = improvement / float(PLANE_PARAMETERS)
    denominator = separate_rss / float(residual_degrees)
    finite = denominator > tolerance
    statistic = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator),
        where=finite,
    )
    evidence = np.divide(
        statistic,
        1.0 + statistic,
        out=np.zeros_like(statistic),
        where=np.isfinite(statistic),
    )
    exact_break = (~finite) & (improvement > tolerance)
    evidence[exact_break] = 1.0
    return np.clip(evidence.reshape(image.shape), 0.0, 1.0)


def facet_break_context(image: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Return maximum four-axis bounded two-plane structural-break evidence."""

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("facet break context requires one finite grayscale raster")
    if float(np.min(values)) < 0.0 or float(np.max(values)) > 1.0:
        raise ValueError("facet break context expects values in [0,1]")

    axis_maps = np.stack(
        [_axis_evidence(values, pooled, separate, offsets) for pooled, separate, offsets in _AXIS_MODELS],
        axis=0,
    )
    cue = np.max(axis_maps, axis=0)
    winning_axis = np.argmax(axis_maps, axis=0)
    cue = np.asarray(cue, dtype=np.float32)
    diagnostics = {
        "cue_mean": float(np.mean(cue)),
        "cue_q90": float(np.quantile(cue, 0.9)),
        "cue_max": float(np.max(cue)),
        "positive_fraction": float(np.mean(cue > 0.0)),
    }
    for index in range(len(AXES)):
        diagnostics[f"winning_axis_{index}_fraction"] = float(np.mean(winning_axis == index))
    return cue, diagnostics


def synthetic_contract() -> dict[str, object]:
    size = 96
    yy, xx = np.indices((size, size), dtype=np.float64)
    flat = np.full((size, size), 0.25, dtype=np.float64)
    ramp = 0.15 + 0.003 * xx + 0.002 * yy
    step = ramp.copy()
    step[:, size // 2 :] += 0.35
    checker = np.where(((yy // 3) + (xx // 3)) % 2 == 0, 0.25, 0.75)
    rng = np.random.default_rng(20261018)
    noise = np.clip(0.45 + rng.normal(0.0, 0.12, (size, size)), 0.0, 1.0)

    flat_map, _ = facet_break_context(flat)
    ramp_map, _ = facet_break_context(ramp)
    step_map, _ = facet_break_context(step)
    repeat_map, _ = facet_break_context(step)
    reversed_map, _ = facet_break_context(1.0 - step)
    affine_map, _ = facet_break_context(0.2 + 0.6 * step)
    checker_map, _ = facet_break_context(checker)
    noise_map, _ = facet_break_context(noise)

    band = np.abs(xx - size // 2) <= 2
    interior = (
        (np.abs(xx - size // 2) >= 12)
        & (xx >= 6) & (xx < size - 6)
        & (yy >= 6) & (yy < size - 6)
    )
    step_band_mean = float(np.mean(step_map[band]))
    checker_mean = float(np.mean(checker_map))
    noise_mean = float(np.mean(noise_map))
    return {
        "finite": bool(all(np.all(np.isfinite(value)) for value in (
            flat_map, ramp_map, step_map, reversed_map, affine_map, checker_map, noise_map
        ))),
        "bounded": bool(all(float(np.min(value)) >= 0.0 and float(np.max(value)) <= 1.0 for value in (
            flat_map, ramp_map, step_map, reversed_map, affine_map, checker_map, noise_map
        ))),
        "flat_max": float(np.max(flat_map)),
        "ramp_interior_max": float(np.max(ramp_map[interior])),
        "step_band_mean": step_band_mean,
        "checker_mean": checker_mean,
        "noise_mean": noise_mean,
        "step_exceeds_checker": bool(step_band_mean > checker_mean),
        "step_exceeds_noise": bool(step_band_mean > noise_mean),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat_map))),
        "polarity_reversal_max_abs_delta": float(np.max(np.abs(step_map - reversed_map))),
        "positive_affine_max_abs_delta": float(np.max(np.abs(step_map - affine_map))),
    }
