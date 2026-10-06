from __future__ import annotations

"""Fixed, non-neural texture-distribution boundary cues.

This module implements a compact surrogate for the Berkeley texture-gradient
mechanism: compare categorical texture distributions in opposed half-discs.
The categorical image uses the rotation-invariant uniform LBP code rather than
learned filter-bank textons, so inference has no fitted dictionary.
"""

import math

import numpy as np
from scipy import ndimage as ndi
from skimage.feature import local_binary_pattern

from .features import gray_float, robust01


def _half_disc_pair(radius: int, theta: float) -> tuple[np.ndarray, np.ndarray]:
    r = max(int(radius), 1)
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    disc = (xx * xx + yy * yy) <= r * r
    projection = xx * math.cos(float(theta)) + yy * math.sin(float(theta))
    positive = disc & (projection >= 0.0)
    negative = disc & (projection < 0.0)
    # Exclude the centre from one side so the two empirical distributions have
    # disjoint support and a point cannot vote for both halves.
    positive[r, r] = False
    return positive.astype(np.float32), negative.astype(np.float32)


def lbp_half_disc_texture_gradient(
    image: np.ndarray,
    *,
    radius_fraction: float = 0.02,
    lbp_points: int = 8,
    lbp_radius: float = 1.0,
    orientations: int = 8,
    minimum_radius: int = 3,
) -> tuple[np.ndarray, dict[str, int | float | str]]:
    """Return maximum oriented chi-square contrast of LBP half-disc histograms.

    The half-disc radius is a fixed fraction of image diagonal.  For every
    orientation, categorical LBP histograms are accumulated on the two sides
    and compared with the chi-square distance.  The maximum orientation is the
    scalar texture-boundary evidence used by Stage 14l.
    """

    g = gray_float(image)
    p = int(lbp_points)
    if p < 1:
        raise ValueError("lbp_points must be positive")
    n_orient = int(orientations)
    if n_orient < 1:
        raise ValueError("orientations must be positive")
    radius = max(
        int(minimum_radius),
        int(round(float(radius_fraction) * math.hypot(*g.shape))),
    )

    # Quantize before LBP so the comparison is deterministic across platforms
    # and avoids unstable equality decisions on floating-point intensities.
    u8 = np.clip(np.rint(g * 255.0), 0, 255).astype(np.uint8)
    labels = local_binary_pattern(u8, p, float(lbp_radius), method="uniform")
    labels = np.asarray(np.rint(labels), dtype=np.int16)
    n_bins = p + 2
    channels = [(labels == index).astype(np.float32) for index in range(n_bins)]

    best = np.zeros(g.shape, dtype=np.float32)
    eps = 1.0e-8
    for theta in np.linspace(0.0, math.pi, n_orient, endpoint=False):
        left, right = _half_disc_pair(radius, float(theta))
        left /= max(float(left.sum()), 1.0)
        right /= max(float(right.sum()), 1.0)
        distance = np.zeros(g.shape, dtype=np.float32)
        for channel in channels:
            h_left = ndi.convolve(channel, left, mode="reflect")
            h_right = ndi.convolve(channel, right, mode="reflect")
            distance += 0.5 * (h_left - h_right) ** 2 / (
                h_left + h_right + eps
            )
        best = np.maximum(best, distance)

    metadata: dict[str, int | float | str] = {
        "descriptor": "rotation-invariant uniform LBP",
        "lbp_points": p,
        "lbp_radius": float(lbp_radius),
        "lbp_bins": n_bins,
        "half_disc_radius": radius,
        "radius_fraction_of_diagonal": float(radius_fraction),
        "orientations": n_orient,
        "comparison": "chi-square",
    }
    return robust01(best).astype(np.float32), metadata
