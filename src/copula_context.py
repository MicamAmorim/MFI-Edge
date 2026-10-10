from __future__ import annotations

"""Image-internal empirical-copula normalization for fuzzy memberships."""

import numpy as np
from scipy.stats import rankdata


def empirical_midrank(values: np.ndarray) -> np.ndarray:
    """Map one image-valued cue to deterministic empirical-CDF midranks.

    Equal values receive equal average ranks.  ``(rank - 0.5) / n`` keeps the
    finite result strictly inside ``(0, 1)`` and preserves all strict ordering.
    """
    x = np.asarray(values, dtype=np.float64)
    if x.size == 0:
        raise ValueError("empirical_midrank requires at least one value")
    if not np.all(np.isfinite(x)):
        raise ValueError("empirical_midrank requires finite values")
    ranks = rankdata(x.ravel(), method="average")
    transformed = (ranks - 0.5) / float(x.size)
    return transformed.reshape(x.shape).astype(np.float32)


def empirical_copula_memberships(memberships: np.ndarray) -> np.ndarray:
    """Apply image-wise empirical-CDF midranks to every membership channel."""
    x = np.asarray(memberships, dtype=np.float32)
    if x.ndim != 3 or x.shape[-1] < 1:
        raise ValueError(f"expected HxWxF memberships, got {x.shape}")
    transformed = np.stack(
        [empirical_midrank(x[..., index]) for index in range(x.shape[-1])],
        axis=-1,
    )
    if not np.all(np.isfinite(transformed)):
        raise RuntimeError("empirical-copula memberships are non-finite")
    if float(np.min(transformed)) <= 0.0 or float(np.max(transformed)) >= 1.0:
        raise RuntimeError("empirical-copula memberships must lie strictly in (0, 1)")
    return transformed.astype(np.float32)
