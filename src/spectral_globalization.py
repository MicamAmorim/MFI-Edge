from __future__ import annotations

"""Fixed coarse-grid spectral globalization cue for Stage 16x.

This is a bounded repository surrogate of the spectral-Pb construction in
Arbelaez et al. (TPAMI 2011).  It consumes an existing soft local-boundary
map, builds intervening-contour affinities, and converts the lowest nontrivial
normalized-Laplacian eigenvectors back into a soft boundary-support map.
"""

from functools import lru_cache

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh
from skimage.transform import resize


GRAPH_MAX_SIDE = 96
AFFINITY_RADIUS = 5
AFFINITY_RHO = 0.1
N_EIGENVECTORS = 16
EIGEN_TOLERANCE = 1.0e-5


@lru_cache(maxsize=None)
def _line_samples(dy: int, dx: int) -> tuple[tuple[int, int], ...]:
    """Return deterministic integer samples on a segment from (0, 0)."""
    steps = max(abs(int(dy)), abs(int(dx)))
    if steps == 0:
        return ((0, 0),)
    points: list[tuple[int, int]] = []
    for step in range(steps + 1):
        y = int(np.rint(step * dy / steps))
        x = int(np.rint(step * dx / steps))
        point = (y, x)
        if not points or points[-1] != point:
            points.append(point)
    return tuple(points)


@lru_cache(maxsize=None)
def _half_disk_offsets(radius: int = AFFINITY_RADIUS) -> tuple[tuple[int, int], ...]:
    offsets = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dy == 0 and dx == 0:
                continue
            if dy * dy + dx * dx > radius * radius:
                continue
            if dy > 0 or (dy == 0 and dx > 0):
                offsets.append((dy, dx))
    return tuple(offsets)


def _coarse_map(local_boundary: np.ndarray, max_side: int) -> np.ndarray:
    x = np.asarray(local_boundary, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError(f"spectral globalization expects a 2-D map, got {x.shape}")
    if not np.all(np.isfinite(x)):
        raise ValueError("local boundary map contains non-finite values")
    x = np.clip(x, 0.0, 1.0)
    scale = min(1.0, float(max_side) / max(x.shape))
    shape = tuple(max(2, int(np.rint(size * scale))) for size in x.shape)
    if shape == x.shape:
        return x
    return np.asarray(
        resize(
            x,
            shape,
            order=1,
            mode="reflect",
            anti_aliasing=True,
            preserve_range=True,
        ),
        dtype=np.float64,
    )


def _intervening_affinity(boundary: np.ndarray, radius: int, rho: float) -> sparse.csr_matrix:
    height, width = boundary.shape
    rows: list[np.ndarray] = []
    cols: list[np.ndarray] = []
    values: list[np.ndarray] = []
    grid = np.arange(height * width, dtype=np.int64).reshape(height, width)

    for dy, dx in _half_disk_offsets(radius):
        y0 = max(0, -dy)
        y1 = min(height, height - dy)
        x0 = max(0, -dx)
        x1 = min(width, width - dx)
        if y0 >= y1 or x0 >= x1:
            continue
        barrier = np.zeros((y1 - y0, x1 - x0), dtype=np.float64)
        for sy, sx in _line_samples(dy, dx):
            barrier = np.maximum(
                barrier,
                boundary[y0 + sy : y1 + sy, x0 + sx : x1 + sx],
            )
        source = grid[y0:y1, x0:x1].ravel()
        target = grid[y0 + dy : y1 + dy, x0 + dx : x1 + dx].ravel()
        affinity = np.exp(-barrier.ravel() / float(rho))
        rows.extend((source, target))
        cols.extend((target, source))
        values.extend((affinity, affinity))

    row = np.concatenate(rows)
    col = np.concatenate(cols)
    value = np.concatenate(values)
    return sparse.coo_matrix(
        (value, (row, col)), shape=(height * width, height * width)
    ).tocsr()


def spectral_globalization(
    local_boundary: np.ndarray,
    *,
    graph_max_side: int = GRAPH_MAX_SIDE,
    radius: int = AFFINITY_RADIUS,
    rho: float = AFFINITY_RHO,
    n_eigenvectors: int = N_EIGENVECTORS,
) -> np.ndarray:
    """Return a finite soft spectral-boundary support cue in ``[0, 1)``.

    The graph is evaluated on a fixed bounded grid for tractable development
    scoring.  The paper-fixed radius, affinity scale, and number of nontrivial
    eigenvectors are otherwise retained.  The final ``x/(1+x)`` map is a
    parameter-free monotone compression used only to stabilize fold fitting.
    """
    original = np.asarray(local_boundary)
    coarse = _coarse_map(original, int(graph_max_side))
    affinity = _intervening_affinity(coarse, int(radius), float(rho))
    degree = np.asarray(affinity.sum(axis=1)).ravel()
    if np.any(degree <= 0.0) or not np.all(np.isfinite(degree)):
        raise RuntimeError("spectral affinity graph has invalid vertex degree")
    inv_sqrt_degree = 1.0 / np.sqrt(degree)
    normalized_affinity = sparse.diags(inv_sqrt_degree) @ affinity @ sparse.diags(inv_sqrt_degree)
    laplacian = sparse.eye(affinity.shape[0], format="csr") - normalized_affinity
    k = min(int(n_eigenvectors) + 1, laplacian.shape[0] - 1)
    if k < 2:
        return np.zeros(original.shape, dtype=np.float32)
    v0 = np.cos(np.arange(laplacian.shape[0], dtype=np.float64) * 0.6180339887498949)
    eigenvalues, eigenvectors = eigsh(
        laplacian,
        k=k,
        which="SM",
        tol=EIGEN_TOLERANCE,
        v0=v0,
        maxiter=max(1000, 5 * laplacian.shape[0]),
    )
    order = np.argsort(eigenvalues)
    eigenvalues = np.asarray(eigenvalues[order], dtype=np.float64)
    eigenvectors = np.asarray(eigenvectors[:, order], dtype=np.float64)
    keep = np.flatnonzero(eigenvalues > 1.0e-8)[: int(n_eigenvectors)]
    if keep.size == 0:
        return np.zeros(original.shape, dtype=np.float32)

    spectral = np.zeros(coarse.shape, dtype=np.float64)
    for index in keep:
        field = eigenvectors[:, index].reshape(coarse.shape)
        gy, gx = np.gradient(field)
        magnitude = np.hypot(gx, gy)
        spectral += magnitude / np.sqrt(eigenvalues[index])
    spectral = spectral / (1.0 + spectral)
    if spectral.shape != original.shape:
        spectral = resize(
            spectral,
            original.shape,
            order=1,
            mode="reflect",
            anti_aliasing=False,
            preserve_range=True,
        )
    return np.clip(np.nan_to_num(spectral), 0.0, 1.0).astype(np.float32)


def synthetic_contract() -> dict[str, float | bool]:
    """Small deterministic contract used by the Stage-16x runner."""
    image = np.zeros((32, 48), dtype=np.float32)
    image[:, 24] = 1.0
    first = spectral_globalization(image, graph_max_side=48)
    second = spectral_globalization(image, graph_max_side=48)
    repeat_delta = float(np.max(np.abs(first - second)))
    step_band = float(np.mean(first[:, 22:27]))
    far_band = float(np.mean(np.concatenate([first[:, :8], first[:, -8:]], axis=1)))
    return {
        "finite": bool(np.all(np.isfinite(first))),
        "bounded": bool(np.min(first) >= 0.0 and np.max(first) <= 1.0),
        "repeat_max_abs_delta": repeat_delta,
        "step_band_mean": step_band,
        "far_band_mean": far_band,
        "step_exceeds_far": bool(step_band > far_band),
    }
