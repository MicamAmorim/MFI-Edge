from __future__ import annotations

"""Fixed signed-gradient continuation support for compact MFI context.

Geisler and Perry (Visual Neuroscience 2009) show that natural-contour
grouping depends jointly on edge-element geometry and contrast polarity.  This
module isolates that mechanism in a small repository surrogate: at each pixel,
the signed unit Scharr gradient is compared with samples on both sides along
its local tangent.  A response requires same-polarity, similarly oriented
support in both tangent directions.  It does not link contours, diffuse a
score, or alter the localizer.
"""

import numpy as np
from scipy import ndimage as ndi


TANGENT_OFFSETS = (1, 2, 4)
EPSILON = 1.0e-12


def _sample(values: np.ndarray, y: np.ndarray, x: np.ndarray) -> np.ndarray:
    return ndi.map_coordinates(
        values,
        np.stack([y, x], axis=0),
        order=1,
        mode="reflect",
        prefilter=False,
    )


def polarity_continuation_context(
    image: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return bounded bilateral same-polarity tangent-continuation evidence."""

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("polarity continuation requires one finite grayscale raster")
    if float(np.min(values)) < 0.0 or float(np.max(values)) > 1.0:
        raise ValueError("polarity continuation expects values in [0,1]")

    scharr_x = np.asarray(
        [[-3.0, 0.0, 3.0], [-10.0, 0.0, 10.0], [-3.0, 0.0, 3.0]],
        dtype=np.float64,
    ) / 16.0
    gx = ndi.correlate(values, scharr_x, mode="reflect")
    gy = ndi.correlate(values, scharr_x.T, mode="reflect")
    magnitude = np.hypot(gx, gy)
    unit_x = np.divide(gx, magnitude, out=np.zeros_like(gx), where=magnitude > EPSILON)
    unit_y = np.divide(gy, magnitude, out=np.zeros_like(gy), where=magnitude > EPSILON)

    # A signed normal determines a tangent direction.  Because evidence uses
    # symmetric samples, globally reversing contrast merely swaps the sides.
    tangent_x = -unit_y
    tangent_y = unit_x
    yy, xx = np.indices(values.shape, dtype=np.float64)

    scale_support: list[np.ndarray] = []
    for distance in TANGENT_OFFSETS:
        step = float(distance)
        plus_y = yy + step * tangent_y
        plus_x = xx + step * tangent_x
        minus_y = yy - step * tangent_y
        minus_x = xx - step * tangent_x

        plus_x_unit = _sample(unit_x, plus_y, plus_x)
        plus_y_unit = _sample(unit_y, plus_y, plus_x)
        minus_x_unit = _sample(unit_x, minus_y, minus_x)
        minus_y_unit = _sample(unit_y, minus_y, minus_x)

        plus_alignment = np.maximum(
            unit_x * plus_x_unit + unit_y * plus_y_unit,
            0.0,
        )
        minus_alignment = np.maximum(
            unit_x * minus_x_unit + unit_y * minus_y_unit,
            0.0,
        )
        scale_support.append(np.sqrt(plus_alignment * minus_alignment))

    support_stack = np.stack(scale_support, axis=0)
    cue = np.mean(support_stack, axis=0)
    cue[magnitude <= EPSILON] = 0.0
    cue = np.clip(cue, 0.0, 1.0).astype(np.float32)
    return cue, {
        "cue_mean": float(np.mean(cue)),
        "cue_q90": float(np.quantile(cue, 0.9)),
        "cue_max": float(np.max(cue)),
        "positive_fraction": float(np.mean(cue > 0.0)),
        **{
            f"offset_{distance}_mean": float(np.mean(support))
            for distance, support in zip(TANGENT_OFFSETS, scale_support)
        },
    }


def synthetic_contract() -> dict[str, float | bool]:
    """Deterministic mechanism checks independent of benchmark feedback."""

    side = 65
    flat = np.full((side, side), 0.4, dtype=np.float64)
    step = np.zeros((side, side), dtype=np.float64)
    step[:, side // 2 :] = 1.0
    reversal = step.copy()
    reversal[side // 2 :, :] = 1.0 - reversal[side // 2 :, :]
    yy, xx = np.indices((side, side))
    checker = ((yy // 4 + xx // 4) % 2).astype(np.float64)
    noise = np.random.default_rng(20261018).random((side, side))

    flat_map, _ = polarity_continuation_context(flat)
    step_map, _ = polarity_continuation_context(step)
    reversal_map, _ = polarity_continuation_context(reversal)
    checker_map, _ = polarity_continuation_context(checker)
    noise_map, _ = polarity_continuation_context(noise)
    inverted_map, _ = polarity_continuation_context(1.0 - step)
    affine_map, _ = polarity_continuation_context(0.2 + 0.6 * step)
    rotated_map, _ = polarity_continuation_context(np.rot90(step))
    repeated_map, _ = polarity_continuation_context(step)

    edge_columns = slice(side // 2 - 1, side // 2 + 1)
    interior_rows = slice(8, side - 8)
    reversal_rows = slice(side // 2 - 2, side // 2 + 3)
    straight_support = float(np.mean(step_map[interior_rows, edge_columns]))
    reversal_support = float(np.mean(reversal_map[reversal_rows, edge_columns]))
    rotation_delta = float(
        np.max(np.abs(np.rot90(step_map) - rotated_map))
    )
    return {
        "finite": bool(
            np.all(np.isfinite(flat_map))
            and np.all(np.isfinite(step_map))
            and np.all(np.isfinite(reversal_map))
        ),
        "bounded": bool(
            min(float(np.min(flat_map)), float(np.min(step_map))) >= 0.0
            and max(float(np.max(flat_map)), float(np.max(step_map))) <= 1.0
        ),
        "flat_max": float(np.max(flat_map)),
        "straight_edge_support": straight_support,
        "checker_max": float(np.max(checker_map)),
        "noise_max": float(np.max(noise_map)),
        # Compatibility aliases consumed by the shared cue harness.  Here the
        # comparison is between the canonical straight-edge support and the
        # strongest response in the distractor raster.
        "step_exceeds_checker": bool(straight_support > float(np.max(checker_map))),
        "step_exceeds_noise": bool(straight_support > float(np.max(noise_map))),
        "polarity_reversal_junction_support": reversal_support,
        "reversal_suppressed": bool(reversal_support + 0.25 <= straight_support),
        "global_inversion_max_abs_delta": float(np.max(np.abs(step_map - inverted_map))),
        "positive_affine_max_abs_delta": float(np.max(np.abs(step_map - affine_map))),
        "rotation_max_abs_delta": rotation_delta,
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeated_map))),
    }
