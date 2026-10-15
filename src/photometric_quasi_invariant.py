from __future__ import annotations

"""Fixed shadow-shading photometric quasi-invariant derivative energy.

This is an equation-level implementation of van de Weijer, Gevers, and
Geusebroek (TPAMI 2005), equations (5)-(6), evaluated in both image axes.
The repository's retained 3x3 median conditioning is applied independently to
RGB channels before the paper's sigma-1 Gaussian derivatives.
"""

import numpy as np
from scipy import ndimage as ndi


DERIVATIVE_SIGMA = 1.0
MEDIAN_SIZE = 3


def _rgb01(image: np.ndarray) -> np.ndarray:
    raw = np.asarray(image)
    if raw.ndim == 2:
        raw = np.repeat(raw[..., None], 3, axis=2)
    if raw.ndim != 3 or raw.shape[2] < 3:
        raise ValueError("expected a grayscale or RGB image")
    rgb = raw[..., :3].astype(np.float64, copy=False)
    if np.issubdtype(raw.dtype, np.integer):
        rgb = rgb / float(np.iinfo(raw.dtype).max)
    elif rgb.size and float(np.nanmax(rgb)) > 1.5:
        rgb = rgb / 255.0
    return np.clip(rgb, 0.0, 1.0)


def photometric_quasi_invariant_energy(
    image: np.ndarray,
    *,
    derivative_sigma: float = DERIVATIVE_SIGMA,
    median_size: int = MEDIAN_SIZE,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return the 2-D energy of the shadow-shading quasi-invariant.

    For each spatial derivative ``d``, the paper's shadow/shading variant is
    ``dot(d, f_hat) * f_hat``.  The quasi-invariant is its orthogonal residual.
    Energies from horizontal and vertical residual vectors are combined by an
    L2 norm.  No image-wise normalization or data-dependent parameter is used.
    """

    rgb = _rgb01(image)
    conditioned = ndi.median_filter(
        rgb,
        size=(int(median_size), int(median_size), 1),
        mode="reflect",
    )
    sigma = (float(derivative_sigma), float(derivative_sigma), 0.0)
    dx = ndi.gaussian_filter(conditioned, sigma=sigma, order=(0, 1, 0), mode="reflect")
    dy = ndi.gaussian_filter(conditioned, sigma=sigma, order=(1, 0, 0), mode="reflect")

    norm = np.linalg.norm(conditioned, axis=2, keepdims=True)
    fhat = np.divide(
        conditioned,
        norm,
        out=np.zeros_like(conditioned),
        where=norm > np.finfo(np.float64).eps,
    )
    residual_x = dx - np.sum(dx * fhat, axis=2, keepdims=True) * fhat
    residual_y = dy - np.sum(dy * fhat, axis=2, keepdims=True) * fhat
    energy = np.sqrt(
        np.sum(residual_x * residual_x + residual_y * residual_y, axis=2)
    )
    orthogonality = max(
        float(np.max(np.abs(np.sum(residual_x * fhat, axis=2)))),
        float(np.max(np.abs(np.sum(residual_y * fhat, axis=2)))),
    )
    diagnostics = {
        "energy_mean": float(np.mean(energy)),
        "energy_q90": float(np.quantile(energy, 0.9)),
        "max_projection_residual_dot": orthogonality,
    }
    return energy.astype(np.float32), diagnostics


def synthetic_contract() -> dict[str, float | bool]:
    height = width = 65
    achromatic = np.full((height, width, 3), 0.2, dtype=np.float64)
    achromatic[:, width // 2 :, :] = 0.8
    chromatic = np.zeros_like(achromatic)
    chromatic[:, : width // 2, :] = (0.65, 0.15, 0.15)
    chromatic[:, width // 2 :, :] = (0.15, 0.65, 0.15)
    flat = np.full_like(achromatic, (0.3, 0.5, 0.2))

    shadow, shadow_diag = photometric_quasi_invariant_energy(achromatic)
    color, color_diag = photometric_quasi_invariant_energy(chromatic)
    flat_energy, _ = photometric_quasi_invariant_energy(flat)
    repeat, _ = photometric_quasi_invariant_energy(chromatic)
    band = slice(width // 2 - 3, width // 2 + 4)
    shadow_band = float(np.mean(shadow[:, band]))
    color_band = float(np.mean(color[:, band]))
    return {
        "finite": bool(
            np.all(np.isfinite(shadow))
            and np.all(np.isfinite(color))
            and np.all(np.isfinite(flat_energy))
        ),
        "nonnegative": bool(
            float(np.min(shadow)) >= 0.0
            and float(np.min(color)) >= 0.0
            and float(np.min(flat_energy)) >= 0.0
        ),
        "chromatic_step_band_mean": color_band,
        "achromatic_step_band_mean": shadow_band,
        "chromatic_exceeds_achromatic": bool(color_band > shadow_band + 1.0e-4),
        "flat_max": float(np.max(flat_energy)),
        "repeat_max_abs_delta": float(np.max(np.abs(color - repeat))),
        "max_projection_residual_dot": max(
            float(shadow_diag["max_projection_residual_dot"]),
            float(color_diag["max_projection_residual_dot"]),
        ),
    }
