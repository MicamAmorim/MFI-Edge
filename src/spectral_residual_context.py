from __future__ import annotations

"""Fixed spectral-innovation context for Stage 18h.

This is an equation-level implementation of Hou and Zhang's spectral-residual
saliency model.  The resulting proto-object saliency is used only as context
for the unchanged MFI localizer; it is not presented as an edge detector or as
an exact reproduction of an author implementation.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, uniform_filter
from skimage.draw import disk
from skimage.transform import resize


WORKING_LONG_SIDE = 64
LOG_SPECTRUM_FILTER_SIZE = 3
SALIENCY_SIGMA = 8.0


def _working_shape(shape: tuple[int, int]) -> tuple[int, int]:
    height, width = shape
    scale = WORKING_LONG_SIDE / float(max(height, width))
    return (
        max(1, int(round(height * scale))),
        max(1, int(round(width * scale))),
    )


def spectral_residual_context(
    image: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return a bounded native-raster spectral-innovation saliency map."""

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("spectral-residual context requires one finite grayscale raster")
    if float(np.min(values)) < 0.0 or float(np.max(values)) > 1.0:
        raise ValueError("spectral-residual context expects values in [0,1]")

    shape = _working_shape(values.shape)
    if float(np.ptp(values)) <= np.finfo(np.float64).eps:
        cue = np.zeros(values.shape, dtype=np.float32)
        return cue, {
            "working_height": float(shape[0]),
            "working_width": float(shape[1]),
            "log_residual_std": 0.0,
            "cue_mean": 0.0,
            "cue_q90": 0.0,
            "cue_max": 0.0,
            "positive_fraction": 0.0,
        }

    working = resize(
        values,
        shape,
        order=1,
        mode="reflect",
        anti_aliasing=True,
        preserve_range=True,
    ).astype(np.float64, copy=False)
    spectrum = np.fft.fft2(working)
    amplitude = np.abs(spectrum)
    phase = np.angle(spectrum)
    floor = np.finfo(np.float64).eps * max(float(np.max(amplitude)), 1.0)
    log_amplitude = np.log(np.maximum(amplitude, floor))
    spectral_average = uniform_filter(
        log_amplitude,
        size=LOG_SPECTRUM_FILTER_SIZE,
        mode="wrap",
    )
    residual = log_amplitude - spectral_average
    reconstruction = np.fft.ifft2(np.exp(residual + 1j * phase))
    raw = np.abs(reconstruction) ** 2
    smoothed = gaussian_filter(raw, SALIENCY_SIGMA, mode="reflect")
    smoothed = np.maximum(smoothed, 0.0)
    maximum = float(np.max(smoothed))
    if maximum > np.finfo(np.float64).eps:
        smoothed = smoothed / maximum
    else:
        smoothed = np.zeros_like(smoothed)

    native = resize(
        smoothed,
        values.shape,
        order=1,
        mode="reflect",
        anti_aliasing=False,
        preserve_range=True,
    )
    cue = np.clip(native, 0.0, 1.0).astype(np.float32)
    return cue, {
        "working_height": float(shape[0]),
        "working_width": float(shape[1]),
        "log_residual_std": float(np.std(residual)),
        "cue_mean": float(np.mean(cue)),
        "cue_q90": float(np.quantile(cue, 0.9)),
        "cue_max": float(np.max(cue)),
        "positive_fraction": float(np.mean(cue > 0.0)),
    }


def synthetic_contract() -> dict[str, object]:
    size = 96
    flat = np.full((size, size), 0.25, dtype=np.float64)
    rare = flat.copy()
    rare_rows, rare_cols = disk((size // 2, size // 2), 10, shape=rare.shape)
    rare[rare_rows, rare_cols] = 0.75

    yy, xx = np.indices((size, size))
    periodic = np.where(((yy // 6) + (xx // 6)) % 2 == 0, 0.25, 0.75)
    rng = np.random.default_rng(18008)
    noise = np.clip(0.25 + rng.normal(0.0, 0.01, (size, size)), 0.0, 1.0)

    flat_map, _ = spectral_residual_context(flat)
    rare_map, _ = spectral_residual_context(rare)
    repeat_map, _ = spectral_residual_context(rare)
    periodic_map, _ = spectral_residual_context(periodic)
    noise_map, _ = spectral_residual_context(noise)
    scaled_map, _ = spectral_residual_context(0.8 * rare)

    object_mask = np.zeros((size, size), dtype=bool)
    object_rows, object_cols = disk((size // 2, size // 2), 18, shape=rare.shape)
    object_mask[object_rows, object_cols] = True
    all_maps = (flat_map, rare_map, periodic_map, noise_map, scaled_map)
    object_mean = float(np.mean(rare_map[object_mask]))
    background_mean = float(np.mean(rare_map[~object_mask]))
    rare_q90 = float(np.quantile(rare_map, 0.9))
    periodic_q90 = float(np.quantile(periodic_map, 0.9))
    noise_q90 = float(np.quantile(noise_map, 0.9))
    rare_concentration = float(np.std(rare_map) / max(float(np.mean(rare_map)), 1.0e-12))
    periodic_concentration = float(
        np.std(periodic_map) / max(float(np.mean(periodic_map)), 1.0e-12)
    )
    noise_concentration = float(
        np.std(noise_map) / max(float(np.mean(noise_map)), 1.0e-12)
    )
    return {
        "finite": bool(all(np.all(np.isfinite(value)) for value in all_maps)),
        "bounded": bool(
            all(float(np.min(value)) >= 0.0 and float(np.max(value)) <= 1.0 for value in all_maps)
        ),
        "flat_max": float(np.max(flat_map)),
        "rare_object_mean": object_mean,
        "rare_background_mean": background_mean,
        "rare_object_localized": bool(object_mean > background_mean),
        "rare_q90": rare_q90,
        "periodic_q90": periodic_q90,
        "noise_q90": noise_q90,
        "rare_concentration": rare_concentration,
        "periodic_concentration": periodic_concentration,
        "noise_concentration": noise_concentration,
        "rare_concentration_exceeds_periodic": bool(
            rare_concentration > periodic_concentration
        ),
        "rare_concentration_exceeds_noise": bool(rare_concentration > noise_concentration),
        "repeat_max_abs_delta": float(np.max(np.abs(rare_map - repeat_map))),
        "multiplicative_scale_max_abs_delta": float(np.max(np.abs(rare_map - scaled_map))),
        # Compatibility names consumed by the shared Stage-17h CV harness.
        "step_exceeds_checker": bool(rare_concentration > periodic_concentration),
        "step_exceeds_noise": bool(rare_concentration > noise_concentration),
        "step_localized": bool(object_mean > background_mean),
    }
