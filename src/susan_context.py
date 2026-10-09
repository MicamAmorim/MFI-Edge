from __future__ import annotations

"""Fixed initial SUSAN/USAN edge response for contextual evidence.

This module implements only the initial, pre-NMS response described by Smith
and Brady (1997).  It is intentionally separate from the incumbent localizer:
Stage 16n uses the response as one candidate positive context membership.
"""

import numpy as np

from .features import gray_float


MASK_RADIUS = 3.4
BRIGHTNESS_THRESHOLD = 20.0 / 255.0
SIMILARITY_POWER = 6
GEOMETRIC_FRACTION = 0.75


def _mask_offsets(radius: float = MASK_RADIUS) -> tuple[tuple[int, int], ...]:
    extent = int(np.floor(float(radius)))
    radius2 = float(radius) ** 2
    return tuple(
        (dy, dx)
        for dy in range(-extent, extent + 1)
        for dx in range(-extent, extent + 1)
        if dx * dx + dy * dy <= radius2
    )


MASK_OFFSETS = _mask_offsets()
if len(MASK_OFFSETS) != 37:  # pragma: no cover - import-time contract
    raise RuntimeError(f"expected the published 37-pixel SUSAN mask, got {len(MASK_OFFSETS)}")


def susan_initial_response(
    image: np.ndarray,
    *,
    brightness_threshold: float = BRIGHTNESS_THRESHOLD,
) -> np.ndarray:
    """Return the fixed 37-pixel initial SUSAN edge response in ``[0, 1]``.

    The comparison is ``exp(-((I_neighbor-I_nucleus)/t)^6)`` and the response
    is ``max(0.75*n_max - USAN_area, 0) / (0.75*n_max)``.  Integer mask
    samples use reflected boundary extension.  No SUSAN direction estimate,
    NMS, thinning, or subpixel localization is applied.
    """
    x = np.asarray(gray_float(image), dtype=np.float64)
    x = np.clip(np.nan_to_num(x), 0.0, 1.0)
    if x.ndim != 2:
        raise ValueError(f"SUSAN context expects a grayscale/RGB image, got {x.shape}")
    threshold = float(brightness_threshold)
    if not np.isfinite(threshold) or threshold <= 0.0:
        raise ValueError("brightness_threshold must be finite and positive")

    pad = int(np.floor(MASK_RADIUS))
    padded = np.pad(x, pad_width=pad, mode="reflect")
    height, width = x.shape
    usan_area = np.zeros_like(x, dtype=np.float64)
    for dy, dx in MASK_OFFSETS:
        neighbour = padded[
            pad + dy : pad + dy + height,
            pad + dx : pad + dx + width,
        ]
        normalized = (neighbour - x) / threshold
        usan_area += np.exp(-np.power(normalized, SIMILARITY_POWER))

    geometric_threshold = GEOMETRIC_FRACTION * len(MASK_OFFSETS)
    response = np.maximum(geometric_threshold - usan_area, 0.0) / geometric_threshold
    return np.clip(np.nan_to_num(response), 0.0, 1.0).astype(np.float32)
