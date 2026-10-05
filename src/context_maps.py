from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
from scipy import ndimage as ndi

from .advanced_fusion import tied_percentile

EPS = 1e-9


def gray01(img: np.ndarray) -> np.ndarray:
    x = np.asarray(img, dtype=float)
    if x.ndim == 3:
        x = x[..., :3]
        x = 0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]
    if x.size == 0:
        return np.asarray(x, dtype=float)
    mx = float(np.nanmax(x))
    if mx > 1.0:
        x = x / 255.0
    return np.clip(np.nan_to_num(x), 0.0, 1.0)


def _local_std(x: np.ndarray, size: int = 5) -> np.ndarray:
    size = max(3, int(size) | 1)
    m1 = ndi.uniform_filter(x, size=size, mode="reflect")
    m2 = ndi.uniform_filter(x * x, size=size, mode="reflect")
    return np.sqrt(np.maximum(m2 - m1 * m1, 0.0))


@dataclass
class ContextMaps:
    heterogeneity: np.ndarray
    blur: np.ndarray
    texture: np.ndarray
    high_frequency: np.ndarray
    low_frequency: np.ndarray
    noise: np.ndarray
    coherence: np.ndarray
    orientation: np.ndarray

    def as_dict(self) -> Dict[str, np.ndarray]:
        return {
            "heterogeneity": self.heterogeneity,
            "blur": self.blur,
            "texture": self.texture,
            "high_frequency": self.high_frequency,
            "low_frequency": self.low_frequency,
            "noise": self.noise,
            "coherence": self.coherence,
            "orientation": self.orientation,
        }


def analyze_context(img: np.ndarray, window: int = 7) -> ContextMaps:
    """Estimate local image regime maps in [0,1].

    These are deliberately lightweight, non-learned proxies used by exploratory
    routers. They are contextual descriptors, not calibrated probabilities.
    """
    x = gray01(img)
    sm1 = ndi.gaussian_filter(x, 1.0, mode="reflect")
    sm2 = ndi.gaussian_filter(x, 2.0, mode="reflect")

    gx = ndi.sobel(sm1, axis=1, mode="reflect")
    gy = ndi.sobel(sm1, axis=0, mode="reflect")
    grad = np.hypot(gx, gy)
    local_std = _local_std(sm1, window)

    hf = np.abs(x - sm1) + 0.5 * np.abs(sm1 - sm2)
    high_frequency = tied_percentile(hf)
    low_frequency = tied_percentile(np.hypot(
        ndi.sobel(sm2, axis=1, mode="reflect"),
        ndi.sobel(sm2, axis=0, mode="reflect"),
    ))

    # Texture: local variance reinforced by high-frequency energy.
    texture = tied_percentile(0.65 * tied_percentile(local_std) + 0.35 * high_frequency)

    # Impulsive/noise proxy: residual from a small median filter.
    med = ndi.median_filter(x, size=3, mode="reflect")
    noise = tied_percentile(np.abs(x - med))

    # Blur proxy: weak local Laplacian/high-frequency response indicates blur.
    lap = np.abs(ndi.laplace(sm1, mode="reflect"))
    sharpness = tied_percentile(0.65 * lap + 0.35 * hf)
    blur = 1.0 - sharpness

    # Structure-tensor coherence and normal orientation.
    jxx = ndi.gaussian_filter(gx * gx, 1.25, mode="reflect")
    jyy = ndi.gaussian_filter(gy * gy, 1.25, mode="reflect")
    jxy = ndi.gaussian_filter(gx * gy, 1.25, mode="reflect")
    disc = np.sqrt(np.maximum((jxx - jyy) ** 2 + 4.0 * jxy * jxy, 0.0))
    coherence = np.clip(disc / (jxx + jyy + EPS), 0.0, 1.0)
    orientation = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy)

    heterogeneity = tied_percentile(
        0.40 * tied_percentile(local_std)
        + 0.30 * tied_percentile(grad)
        + 0.20 * texture
        + 0.10 * noise
    )

    return ContextMaps(
        heterogeneity=np.asarray(heterogeneity, np.float32),
        blur=np.asarray(blur, np.float32),
        texture=np.asarray(texture, np.float32),
        high_frequency=np.asarray(high_frequency, np.float32),
        low_frequency=np.asarray(low_frequency, np.float32),
        noise=np.asarray(noise, np.float32),
        coherence=np.asarray(coherence, np.float32),
        orientation=np.asarray(orientation, np.float32),
    )


def regime_soft_weights(ctx: ContextMaps, sharpness: float = 5.0) -> Dict[str, np.ndarray]:
    """Soft regime memberships used by conditional operators/routers."""
    def sig(z):
        z = np.clip(float(sharpness) * z, -20.0, 20.0)
        return 1.0 / (1.0 + np.exp(-z))

    texture = sig(ctx.texture - 0.55)
    blur = sig(ctx.blur - 0.58)
    noise = sig(ctx.noise - 0.60)
    clean = np.clip(1.0 - np.maximum.reduce([texture, blur, noise]), 0.0, 1.0)
    den = clean + texture + blur + noise + EPS
    return {
        "clean": clean / den,
        "texture": texture / den,
        "blur": blur / den,
        "noise": noise / den,
    }
