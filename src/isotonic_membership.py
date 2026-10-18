from __future__ import annotations

"""Deterministic weighted isotonic calibration for scalar fuzzy memberships."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class IsotonicCalibrator:
    upper_bounds: np.ndarray
    values: np.ndarray


def fit_isotonic_calibrator(
    scores: np.ndarray,
    labels: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> IsotonicCalibrator:
    """Fit the weighted squared-loss monotone PAV solution.

    Equal score values are aggregated before pool-adjacent-violators fitting.
    Prediction is the fitted piecewise-constant value of the first block whose
    upper score bound is not below the query.
    """
    x = np.asarray(scores, dtype=np.float64).ravel()
    y = np.asarray(labels, dtype=np.float64).ravel()
    if x.size == 0 or x.shape != y.shape:
        raise ValueError("scores and labels must be nonempty and shape-matched")
    if sample_weight is None:
        w = np.ones_like(x)
    else:
        w = np.asarray(sample_weight, dtype=np.float64).ravel()
        if w.shape != x.shape:
            raise ValueError("sample_weight must match scores")
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y)) and np.all(np.isfinite(w))):
        raise ValueError("isotonic inputs must be finite")
    if np.any(w <= 0.0) or np.any((y < 0.0) | (y > 1.0)):
        raise ValueError("weights must be positive and labels must lie in [0,1]")

    order = np.argsort(x, kind="mergesort")
    x, y, w = x[order], y[order], w[order]
    unique, starts = np.unique(x, return_index=True)
    group_weight = np.add.reduceat(w, starts)
    group_sum = np.add.reduceat(w * y, starts)

    blocks: list[list[float]] = []
    for upper, weight, weighted_sum in zip(unique, group_weight, group_sum):
        blocks.append([float(upper), float(weight), float(weighted_sum)])
        while len(blocks) >= 2:
            left = blocks[-2][2] / blocks[-2][1]
            right = blocks[-1][2] / blocks[-1][1]
            if left <= right:
                break
            merged = [
                blocks[-1][0],
                blocks[-2][1] + blocks[-1][1],
                blocks[-2][2] + blocks[-1][2],
            ]
            blocks[-2:] = [merged]

    upper_bounds = np.asarray([block[0] for block in blocks], dtype=np.float64)
    values = np.asarray([block[2] / block[1] for block in blocks], dtype=np.float64)
    return IsotonicCalibrator(
        upper_bounds=upper_bounds,
        values=np.clip(values, 0.0, 1.0),
    )


def apply_isotonic_calibrator(
    scores: np.ndarray, calibrator: IsotonicCalibrator
) -> np.ndarray:
    x = np.asarray(scores, dtype=np.float64)
    bounds = np.asarray(calibrator.upper_bounds, dtype=np.float64)
    values = np.asarray(calibrator.values, dtype=np.float64)
    if bounds.ndim != 1 or values.shape != bounds.shape or bounds.size == 0:
        raise ValueError("invalid isotonic calibrator")
    indices = np.searchsorted(bounds, x, side="left")
    indices = np.clip(indices, 0, values.size - 1)
    return values[indices].astype(np.float32)


def calibrator_to_record(calibrator: IsotonicCalibrator) -> dict:
    return {
        "upper_bounds": calibrator.upper_bounds.tolist(),
        "values": calibrator.values.tolist(),
        "n_blocks": int(calibrator.values.size),
    }


def calibrator_from_record(record: dict) -> IsotonicCalibrator:
    return IsotonicCalibrator(
        upper_bounds=np.asarray(record["upper_bounds"], dtype=np.float64),
        values=np.asarray(record["values"], dtype=np.float64),
    )
