from __future__ import annotations

"""Fixed median ordered-weighted aggregation for compact MFI context."""

import numpy as np


def median_owa_context(
    memberships: np.ndarray,
    weights: np.ndarray | None = None,
    gamma: float | None = None,
) -> np.ndarray:
    """Return the median OWA value over an odd number of memberships.

    ``weights`` and ``gamma`` are accepted only for interface compatibility
    with the incumbent aggregation harness.  The registered candidate is the
    parameter-free OWA weight vector that selects the central order statistic,
    so neither argument affects its value.
    """
    x = np.asarray(memberships, dtype=np.float64)
    if x.ndim < 1 or x.shape[-1] == 0 or x.shape[-1] % 2 == 0:
        raise ValueError("median OWA requires a non-empty odd membership axis")
    if not np.all(np.isfinite(x)):
        raise ValueError("memberships must be finite")
    out = np.median(np.clip(x, 0.0, 1.0), axis=-1)
    return np.asarray(out, dtype=np.float32)
