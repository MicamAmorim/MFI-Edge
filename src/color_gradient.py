from __future__ import annotations

"""Fixed analytical vector-color gradients for non-neural localization."""

import numpy as np
from scipy import ndimage as ndi
from skimage import color

from src.classical_detectors import robust01
from src.postprocess import non_maximum_suppression


_SCHARR_X = np.asarray(
    [[-3.0, 0.0, 3.0], [-10.0, 0.0, 10.0], [-3.0, 0.0, 3.0]],
    dtype=float,
) / 32.0
_SCHARR_Y = _SCHARR_X.T


def _rgb01(image: np.ndarray) -> np.ndarray:
    x = np.asarray(image)
    if x.ndim != 3 or x.shape[-1] < 3:
        raise ValueError("A three-channel RGB image is required")
    x = x[..., :3].astype(float)
    if np.issubdtype(np.asarray(image).dtype, np.integer):
        x /= float(np.iinfo(np.asarray(image).dtype).max)
    elif np.nanmax(x) > 1.0:
        x /= 255.0
    return np.clip(x, 0.0, 1.0)


def lab_di_zenzo_scharr_nms(image: np.ndarray, median_size: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """Return NMS score and maximal-change direction for a CIELAB tensor gradient.

    RGB is converted to CIELAB, each Lab channel receives the incumbent 3x3
    median conditioning independently, and fixed Scharr derivatives form the
    Di Zenzo 2x2 metric tensor.  All Lab channels share a common factor of
    1/100, preserving the perceptual Lab metric while keeping values moderate.
    The maximal tensor eigenvalue supplies magnitude and its eigenvector angle
    supplies the edge-normal direction used by the existing four-bin NMS.
    """

    lab = color.rgb2lab(_rgb01(image)).astype(float) / 100.0
    size = max(1, int(median_size))
    if size > 1:
        lab = ndi.median_filter(lab, size=(size, size, 1), mode="reflect")

    dx = np.stack(
        [ndi.correlate(lab[..., channel], _SCHARR_X, mode="reflect") for channel in range(3)],
        axis=-1,
    )
    dy = np.stack(
        [ndi.correlate(lab[..., channel], _SCHARR_Y, mode="reflect") for channel in range(3)],
        axis=-1,
    )
    gxx = np.sum(dx * dx, axis=-1)
    gyy = np.sum(dy * dy, axis=-1)
    gxy = np.sum(dx * dy, axis=-1)
    discriminant = np.sqrt(np.maximum((gxx - gyy) ** 2 + 4.0 * gxy * gxy, 0.0))
    lambda_max = 0.5 * (gxx + gyy + discriminant)
    magnitude = robust01(np.sqrt(np.maximum(lambda_max, 0.0)))
    orientation = 0.5 * np.arctan2(2.0 * gxy, gxx - gyy)
    return (
        non_maximum_suppression(magnitude, orientation).astype(np.float32),
        orientation.astype(np.float32),
    )
