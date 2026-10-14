from __future__ import annotations

"""Finite-scale surrogate of Lindeberg's automatic edge-scale selection."""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

from .classical_detectors import robust01
from .features import gray_float
from .postprocess import non_maximum_suppression


@dataclass(frozen=True)
class ScaleSpaceLocalizerResult:
    localizer: np.ndarray
    selected_sigma: np.ndarray
    selected_strength: np.ndarray
    normalized_strengths: np.ndarray


def scale_normalized_edge_localizer(
    image: np.ndarray,
    *,
    sigmas: tuple[float, ...] = (1.0, 2.0, 4.0),
    gamma_edge: float = 0.5,
) -> ScaleSpaceLocalizerResult:
    """Select a spatially non-maximal-suppressed edge response over scale.

    For first-order Gaussian derivatives, gamma normalization multiplies the
    gradient magnitude by ``sigma**gamma_edge``.  The winning scale is chosen
    from the normalized response before spatial NMS; a response survives only
    when it is also a gradient-direction maximum at that same scale.

    This deliberately bounded discrete implementation omits continuous
    scale-space curve tracing and integrated saliency ranking.
    """
    if len(sigmas) < 2 or any(float(sigma) <= 0.0 for sigma in sigmas):
        raise ValueError("sigmas must contain at least two positive scales")
    if not np.isfinite(gamma_edge):
        raise ValueError("gamma_edge must be finite")

    source = np.asarray(gray_float(image), dtype=np.float64)
    if source.ndim != 2 or not np.all(np.isfinite(source)):
        raise ValueError("scale-space localization requires a finite grayscale image")

    strengths: list[np.ndarray] = []
    spatial_maxima: list[np.ndarray] = []
    for sigma in sigmas:
        sigma = float(sigma)
        gx = ndi.gaussian_filter(source, sigma=sigma, order=(0, 1), mode="reflect")
        gy = ndi.gaussian_filter(source, sigma=sigma, order=(1, 0), mode="reflect")
        normalized = (sigma**float(gamma_edge)) * np.hypot(gx, gy)
        orientation = np.arctan2(gy, gx)
        strengths.append(normalized)
        spatial_maxima.append(non_maximum_suppression(normalized, orientation))

    strength_stack = np.stack(strengths, axis=0)
    nms_stack = np.stack(spatial_maxima, axis=0)
    winner = np.argmax(strength_stack, axis=0)
    selected_strength = np.take_along_axis(nms_stack, winner[None, ...], axis=0)[0]
    sigma_values = np.asarray(sigmas, dtype=np.float32)
    selected_sigma = sigma_values[winner]
    localizer = robust01(selected_strength).astype(np.float32)
    return ScaleSpaceLocalizerResult(
        localizer=localizer,
        selected_sigma=selected_sigma.astype(np.float32),
        selected_strength=selected_strength.astype(np.float32),
        normalized_strengths=strength_stack.astype(np.float32),
    )
