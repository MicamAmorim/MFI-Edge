from __future__ import annotations

"""Fixed Sugeno aggregation for the retained compact positive context."""

import numpy as np


EPS = 1.0e-8


def distorted_capacity_sugeno(
    memberships: np.ndarray,
    weights: np.ndarray,
    gamma: float,
) -> np.ndarray:
    """Discrete Sugeno integral for m(A)=(sum_{i in A} w_i)^gamma.

    Memberships are sorted in ascending order.  For each suffix coalition A_i,
    the candidate level is min(x_(i), m(A_i)); the integral is their maximum.
    The capacity is exactly the compact controller's normalized distorted-
    probability capacity, so this changes aggregation semantics only.
    """
    x = np.asarray(memberships, dtype=np.float64)
    if x.ndim < 1 or x.shape[-1] == 0:
        return np.zeros(x.shape[:-1], dtype=np.float32)
    w = np.asarray(weights, dtype=np.float64)
    if w.ndim != 1 or w.size != x.shape[-1]:
        raise ValueError("weights must be one-dimensional and match memberships")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(w)):
        raise ValueError("memberships and weights must be finite")
    if np.any(w < 0.0) or float(w.sum()) <= 0.0:
        raise ValueError("weights must be nonnegative with positive sum")
    if float(gamma) <= 0.0:
        raise ValueError("gamma must be positive")

    x = np.clip(x, 0.0, 1.0)
    w = w / float(w.sum())
    order = np.argsort(x, axis=-1, kind="stable")
    xs = np.take_along_axis(x, order, axis=-1)
    ww = np.take_along_axis(np.broadcast_to(w, x.shape), order, axis=-1)
    suffix_weight = np.flip(np.cumsum(np.flip(ww, axis=-1), axis=-1), axis=-1)
    capacity = np.power(np.clip(suffix_weight, 0.0, 1.0), float(gamma))
    out = np.max(np.minimum(xs, capacity), axis=-1)
    return np.clip(out, 0.0, 1.0).astype(np.float32)
