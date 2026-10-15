from __future__ import annotations

"""Local Fisher L-information for an isotropic pairwise Gaussian MRF."""

import numpy as np


NEIGHBORHOOD = "second-order 8-neighbour"


def _neighbor_sum(image: np.ndarray) -> np.ndarray:
    x = np.asarray(image, dtype=np.float64)
    padded = np.pad(x, 1, mode="reflect")
    total = np.zeros_like(x, dtype=np.float64)
    for row_offset in range(3):
        for col_offset in range(3):
            if row_offset == 1 and col_offset == 1:
                continue
            total += padded[
                row_offset : row_offset + x.shape[0],
                col_offset : col_offset + x.shape[1],
            ]
    return total


def gmrf_l_information(image: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Return the type-I/type-II local observed-Fisher ratio.

    Equations (4), (6), (10), and (12) of Levada (2014) reduce the local
    ratio to the squared standardized conditional innovation
    ``(x_i - mu - beta * sum_j(x_j - mu))**2 / sigma**2``.  Writing the
    conditional mean as ``alpha + beta * sum_j(x_j)`` makes the joint
    Gaussian maximum-pseudo-likelihood fit ordinary least squares in
    ``(alpha, beta)``; this is the numerically stable form used below.  The
    only exceptional branch is a numerically constant image, for which the
    cue is defined as zero because neither spatial dependence nor innovation
    is identifiable.
    """

    x = np.asarray(image, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("GMRF L-information expects a two-dimensional image")
    if not np.all(np.isfinite(x)):
        raise ValueError("GMRF L-information received non-finite pixels")

    mean = float(np.mean(x))
    neighbor_sum = _neighbor_sum(x)
    neighbor_mean = float(np.mean(neighbor_sum))
    centered = x - mean
    centered_neighbor_sum = neighbor_sum - neighbor_mean
    denominator = float(
        np.sum(centered_neighbor_sum * centered_neighbor_sum, dtype=np.float64)
    )
    numerical_floor = float(np.finfo(np.float64).eps * max(1, x.size))
    if denominator <= numerical_floor:
        return np.zeros_like(x, dtype=np.float32), {
            "mean": mean,
            "conditional_intercept": mean,
            "beta_mpl": 0.0,
            "sigma2_mpl": 0.0,
        }

    beta = float(
        np.sum(centered * centered_neighbor_sum, dtype=np.float64) / denominator
    )
    intercept = float(mean - beta * neighbor_mean)
    innovation = x - intercept - beta * neighbor_sum
    sigma2 = float(np.mean(innovation * innovation, dtype=np.float64))
    if sigma2 <= numerical_floor:
        cue = np.zeros_like(x, dtype=np.float64)
    else:
        cue = innovation * innovation / sigma2
    if not np.all(np.isfinite(cue)) or np.min(cue) < 0.0:
        raise RuntimeError("invalid GMRF L-information result")
    return cue.astype(np.float32), {
        "mean": mean,
        "conditional_intercept": intercept,
        "beta_mpl": beta,
        "sigma2_mpl": sigma2,
    }


def synthetic_contract() -> dict[str, float | bool]:
    height = width = 65
    flat = np.full((height, width), 0.4, dtype=np.float64)
    step = np.full((height, width), 0.2, dtype=np.float64)
    step[:, width // 2 :] = 0.8
    first, fit = gmrf_l_information(step)
    second, _ = gmrf_l_information(step)
    affine, _ = gmrf_l_information(0.63 * step + 0.17)
    flat_cue, _ = gmrf_l_information(flat)
    boundary = first[:, width // 2 - 1 : width // 2 + 1]
    remote = np.concatenate([first[:, 4:12].ravel(), first[:, -12:-4].ravel()])
    return {
        "finite": bool(np.all(np.isfinite(first))),
        "nonnegative": bool(np.min(first) >= 0.0),
        "step_exceeds_remote": bool(float(np.mean(boundary)) > float(np.mean(remote))),
        "flat_is_zero": bool(np.max(np.abs(flat_cue)) == 0.0),
        "affine_transform_max_abs_delta": float(np.max(np.abs(first - affine))),
        "repeat_max_abs_delta": float(np.max(np.abs(first - second))),
        "step_beta_mpl": float(fit["beta_mpl"]),
        "step_sigma2_mpl": float(fit["sigma2_mpl"]),
    }
