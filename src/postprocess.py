from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi
from skimage import filters, morphology

def gradient_orientation(img, sigma: float = 1.0):
    """Return edge-normal orientation (radians) from a smoothed grayscale image."""
    g = np.asarray(img, dtype=float)
    if g.ndim == 3:
        g = g[..., :3].mean(axis=2)
    if g.max() > 1.0:
        g = g / 255.0
    if sigma > 0:
        g = filters.gaussian(g, sigma=sigma, preserve_range=True)
    gx = ndi.sobel(g, axis=1, mode="reflect")
    gy = ndi.sobel(g, axis=0, mode="reflect")
    return np.arctan2(gy, gx)

def non_maximum_suppression(score, theta):
    """Classic 4-direction NMS on a scalar edge score using edge-normal orientation."""
    s = np.asarray(score, dtype=float)
    a = (np.rad2deg(theta) + 180.0) % 180.0
    out = np.zeros_like(s)
    left, right = np.roll(s, 1, 1), np.roll(s, -1, 1)
    up, down = np.roll(s, 1, 0), np.roll(s, -1, 0)
    up_left = np.roll(up, 1, 1)
    up_right = np.roll(up, -1, 1)
    down_left = np.roll(down, 1, 1)
    down_right = np.roll(down, -1, 1)
    masks = [
        ((a < 22.5) | (a >= 157.5), left, right),
        ((a >= 22.5) & (a < 67.5), up_right, down_left),
        ((a >= 67.5) & (a < 112.5), up, down),
        ((a >= 112.5) & (a < 157.5), up_left, down_right),
    ]
    for m, n1, n2 in masks:
        keep = m & (s >= n1) & (s >= n2)
        out[keep] = s[keep]
    out[[0, -1], :] = 0
    out[:, [0, -1]] = 0
    return out

def hysteresis_binary(score, low, high):
    """Binary hysteresis: weak pixels survive only if connected to strong pixels."""
    return filters.apply_hysteresis_threshold(np.asarray(score, float), low, high)

def thin_binary(edge_map):
    return morphology.thin(np.asarray(edge_map, bool))
