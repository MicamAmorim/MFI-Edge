from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
from scipy import ndimage as ndi

from .advanced_fusion import tied_percentile
from .context_maps import ContextMaps, gray01

EPS = 1e-9


@dataclass
class LocalizerResult:
    fused: np.ndarray
    bank: Dict[str, np.ndarray]
    weights: Dict[str, np.ndarray]


def _norm(x):
    return tied_percentile(np.asarray(x, dtype=float))


def localizer_bank(img: np.ndarray) -> Dict[str, np.ndarray]:
    """Small interpretable bank spanning fine to coarse derivative scales."""
    x = gray01(img)

    sx = ndi.sobel(x, axis=1, mode="reflect")
    sy = ndi.sobel(x, axis=0, mode="reflect")
    sobel = np.hypot(sx, sy)

    # Scharr-like 3x3 kernels implemented without requiring cv2 here.
    kx = np.array([[-3.0, 0.0, 3.0], [-10.0, 0.0, 10.0], [-3.0, 0.0, 3.0]]) / 16.0
    ky = kx.T
    gx = ndi.convolve(x, kx, mode="reflect")
    gy = ndi.convolve(x, ky, mode="reflect")
    scharr = np.hypot(gx, gy)

    dog1x = ndi.gaussian_filter(x, sigma=1.0, order=(0, 1), mode="reflect")
    dog1y = ndi.gaussian_filter(x, sigma=1.0, order=(1, 0), mode="reflect")
    dog2x = ndi.gaussian_filter(x, sigma=2.0, order=(0, 1), mode="reflect")
    dog2y = ndi.gaussian_filter(x, sigma=2.0, order=(1, 0), mode="reflect")
    dog1 = np.hypot(dog1x, dog1y)
    dog2 = np.hypot(dog2x, dog2y)

    return {
        "scharr": _norm(scharr).astype(np.float32),
        "sobel": _norm(sobel).astype(np.float32),
        "dog1": _norm(dog1).astype(np.float32),
        "dog2": _norm(dog2).astype(np.float32),
    }


def context_localizer_weights(ctx: ContextMaps, mode: str = "adaptive") -> Dict[str, np.ndarray]:
    """Pixelwise localizer weights.

    High blur shifts mass to coarser derivative-of-Gaussian filters. High noise
    suppresses fine Scharr response. High directional coherence preserves the
    fine localizer. This is a hand-designed exploratory router, not a learned posterior.
    """
    shape = ctx.blur.shape
    if mode == "uniform":
        return {k: np.full(shape, 0.25, dtype=np.float32) for k in ("scharr", "sobel", "dog1", "dog2")}

    blur = np.clip(ctx.blur, 0.0, 1.0)
    noise = np.clip(ctx.noise, 0.0, 1.0)
    coh = np.clip(ctx.coherence, 0.0, 1.0)
    tex = np.clip(ctx.texture, 0.0, 1.0)

    raw = {
        "scharr": 0.25 + 0.85 * (1.0 - blur) * (1.0 - 0.65 * noise) * (0.65 + 0.35 * coh),
        "sobel": 0.20 + 0.45 * (1.0 - 0.55 * blur) * (1.0 - 0.35 * noise),
        "dog1": 0.15 + 0.65 * blur + 0.20 * noise,
        "dog2": 0.10 + 0.95 * blur + 0.20 * tex,
    }
    den = sum(raw.values()) + EPS
    return {k: np.asarray(v / den, np.float32) for k, v in raw.items()}


def dynamic_localizer(img: np.ndarray, ctx: ContextMaps, mode: str = "adaptive") -> LocalizerResult:
    bank = localizer_bank(img)
    weights = context_localizer_weights(ctx, mode=mode)
    fused = np.zeros_like(next(iter(bank.values())), dtype=float)
    for name in bank:
        fused += np.asarray(weights[name], float) * np.asarray(bank[name], float)
    return LocalizerResult(
        fused=np.asarray(_norm(fused), np.float32),
        bank=bank,
        weights=weights,
    )


def oriented_nms(score: np.ndarray) -> np.ndarray:
    """Fast orientation-aware non-maximum suppression for a continuous score."""
    s = np.asarray(score, dtype=float)
    gx = ndi.sobel(s, axis=1, mode="reflect")
    gy = ndi.sobel(s, axis=0, mode="reflect")
    ang = (np.rad2deg(np.arctan2(gy, gx)) + 180.0) % 180.0
    out = np.zeros_like(s)

    def keep(mask, a, b):
        nonlocal out
        out[mask & (s >= a) & (s >= b)] = s[mask & (s >= a) & (s >= b)]

    left = np.roll(s, 1, axis=1); right = np.roll(s, -1, axis=1)
    up = np.roll(s, 1, axis=0); down = np.roll(s, -1, axis=0)
    ul = np.roll(up, 1, axis=1); ur = np.roll(up, -1, axis=1)
    dl = np.roll(down, 1, axis=1); dr = np.roll(down, -1, axis=1)

    keep((ang < 22.5) | (ang >= 157.5), left, right)
    keep((ang >= 22.5) & (ang < 67.5), ur, dl)
    keep((ang >= 67.5) & (ang < 112.5), up, down)
    keep((ang >= 112.5) & (ang < 157.5), ul, dr)
    out[[0, -1], :] = 0.0
    out[:, [0, -1]] = 0.0
    return np.asarray(out, np.float32)
