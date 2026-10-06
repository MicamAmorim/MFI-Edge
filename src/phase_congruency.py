from __future__ import annotations

"""Fixed-parameter oriented phase-congruency edge moment.

This is a compact NumPy implementation of the PC2 construction described by
Kovesi (1999, 2000).  It is intentionally not a tunable detector family: the
defaults match the long-standing ``phasecong3`` reference defaults and Stage
14j treats only the resulting maximum covariance moment as a candidate context
feature.
"""

import numpy as np

from .features import gray_float


EPS = 1.0e-4


def _frequency_grid(shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = (int(shape[0]), int(shape[1]))
    if cols % 2:
        x = np.arange(-(cols - 1) / 2, (cols - 1) / 2 + 1) / (cols - 1)
    else:
        x = np.arange(-cols / 2, cols / 2) / cols
    if rows % 2:
        y = np.arange(-(rows - 1) / 2, (rows - 1) / 2 + 1) / (rows - 1)
    else:
        y = np.arange(-rows / 2, rows / 2) / rows
    xx, yy = np.meshgrid(x, y)
    radius = np.fft.ifftshift(np.hypot(xx, yy))
    theta = np.fft.ifftshift(np.arctan2(-yy, xx))
    radius[0, 0] = 1.0
    return radius, theta


def _lowpass(radius: np.ndarray, cutoff: float = 0.45, order: int = 15) -> np.ndarray:
    return 1.0 / (1.0 + np.power(radius / float(cutoff), 2 * int(order)))


def phase_congruency_edge_moment(
    image: np.ndarray,
    *,
    nscale: int = 4,
    norient: int = 6,
    min_wavelength: float = 3.0,
    mult: float = 2.1,
    sigma_on_f: float = 0.55,
    k: float = 2.0,
    cutoff: float = 0.5,
    spread_gain: float = 10.0,
) -> np.ndarray:
    """Return Kovesi's maximum phase-congruency covariance moment in [0, 1]."""
    source = np.asarray(image)
    if source.ndim not in (2, 3):
        raise ValueError(f"phase congruency expects a 2-D/RGB image, got {source.shape}")
    if source.size == 0:
        return np.zeros(source.shape[:2], dtype=np.float32)
    x = gray_float(source)
    x = np.clip(np.nan_to_num(x), 0.0, 1.0)

    radius, theta = _frequency_grid(x.shape)
    sintheta, costheta = np.sin(theta), np.cos(theta)
    lowpass = _lowpass(radius)
    log_gabor = []
    for scale in range(int(nscale)):
        wavelength = float(min_wavelength) * float(mult) ** scale
        center_frequency = 1.0 / wavelength
        radial = np.exp(
            -(np.log(radius / center_frequency) ** 2)
            / (2.0 * np.log(float(sigma_on_f)) ** 2)
        )
        radial *= lowpass
        radial[0, 0] = 0.0
        log_gabor.append(radial)

    image_fft = np.fft.fft2(x)
    covx2 = np.zeros_like(x, dtype=float)
    covy2 = np.zeros_like(x, dtype=float)
    covxy = np.zeros_like(x, dtype=float)

    for orient in range(int(norient)):
        angle = orient * np.pi / float(norient)
        ds = sintheta * np.cos(angle) - costheta * np.sin(angle)
        dc = costheta * np.cos(angle) + sintheta * np.sin(angle)
        dtheta = np.minimum(np.abs(np.arctan2(ds, dc)) * norient / 2.0, np.pi)
        spread = (np.cos(dtheta) + 1.0) / 2.0

        responses = []
        sum_e = np.zeros_like(x, dtype=float)
        sum_o = np.zeros_like(x, dtype=float)
        sum_an = np.zeros_like(x, dtype=float)
        max_an = np.zeros_like(x, dtype=float)
        tau = 0.0
        for scale, radial in enumerate(log_gabor):
            response = np.fft.ifft2(image_fft * radial * spread)
            amplitude = np.abs(response)
            responses.append(response)
            sum_e += response.real
            sum_o += response.imag
            sum_an += amplitude
            max_an = np.maximum(max_an, amplitude)
            if scale == 0:
                tau = float(np.median(amplitude)) / np.sqrt(np.log(4.0))

        magnitude = np.hypot(sum_e, sum_o) + EPS
        mean_e, mean_o = sum_e / magnitude, sum_o / magnitude
        energy = np.zeros_like(x, dtype=float)
        for response in responses:
            even, odd = response.real, response.imag
            energy += (
                even * mean_e
                + odd * mean_o
                - np.abs(even * mean_o - odd * mean_e)
            )

        total_tau = tau * (1.0 - (1.0 / mult) ** nscale) / (1.0 - 1.0 / mult)
        noise_mean = total_tau * np.sqrt(np.pi / 2.0)
        noise_sigma = total_tau * np.sqrt((4.0 - np.pi) / 2.0)
        energy = np.maximum(energy - (noise_mean + float(k) * noise_sigma), 0.0)

        width = (sum_an / (max_an + EPS) - 1.0) / max(int(nscale) - 1, 1)
        weight = 1.0 / (1.0 + np.exp((float(cutoff) - width) * float(spread_gain)))
        pc = weight * energy / (sum_an + EPS)

        covx = pc * np.cos(angle)
        covy = pc * np.sin(angle)
        covx2 += covx * covx
        covy2 += covy * covy
        covxy += covx * covy

    covx2 /= norient / 2.0
    covy2 /= norient / 2.0
    covxy *= 4.0 / norient
    denom = np.sqrt(covxy * covxy + (covx2 - covy2) ** 2) + EPS
    maximum_moment = (covx2 + covy2 + denom) / 2.0
    return np.clip(np.nan_to_num(maximum_moment), 0.0, 1.0).astype(np.float32)
