from __future__ import annotations

"""Deterministic fold-fitted independent-component concentration context."""

from hashlib import sha256

import numpy as np
from scipy import ndimage


PATCH_SIZE = 7
N_COMPONENTS = 16
PATCHES_PER_IMAGE = 256
MAX_ITERATIONS = 500
TOLERANCE = 1.0e-6


def _sym_decorrelation(matrix: np.ndarray) -> np.ndarray:
    gram = matrix @ matrix.T
    values, vectors = np.linalg.eigh(gram)
    values = np.maximum(values, 1.0e-12)
    return (vectors * (1.0 / np.sqrt(values))[None, :]) @ vectors.T @ matrix


def _sample_patches(image: np.ndarray, count: int, rng: np.random.Generator) -> np.ndarray:
    values = np.asarray(image, dtype=np.float64)
    radius = PATCH_SIZE // 2
    padded = np.pad(values, radius, mode="reflect")
    windows = np.lib.stride_tricks.sliding_window_view(
        padded, (PATCH_SIZE, PATCH_SIZE)
    ).reshape(-1, PATCH_SIZE * PATCH_SIZE)
    take = min(int(count), int(windows.shape[0]))
    indices = rng.choice(windows.shape[0], size=take, replace=False)
    patches = np.array(windows[indices], dtype=np.float64, copy=True)
    patches -= np.mean(patches, axis=1, keepdims=True)
    norms = np.linalg.norm(patches, axis=1)
    keep = norms > 1.0e-8
    return patches[keep] / norms[keep, None]


def fit_ica_context(
    images: list[np.ndarray],
    seed: int,
    patches_per_image: int = PATCHES_PER_IMAGE,
) -> tuple[dict[str, object], dict[str, float]]:
    """Fit a compact FastICA analysis bank without using boundary labels."""

    if not images:
        raise ValueError("ICA context fitting requires at least one image")
    rng = np.random.default_rng(int(seed))
    sampled = []
    for image in images:
        values = np.asarray(image, dtype=np.float64)
        if values.ndim != 2 or not np.all(np.isfinite(values)):
            raise ValueError("ICA context requires finite grayscale rasters")
        sampled.append(_sample_patches(values, patches_per_image, rng))
    x = np.concatenate(sampled, axis=0)
    if x.shape[0] < 4 * N_COMPONENTS:
        raise RuntimeError("too few nonconstant patches for the fixed ICA bank")

    feature_mean = np.mean(x, axis=0)
    centered = x - feature_mean[None, :]
    covariance = (centered.T @ centered) / float(centered.shape[0])
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1][:N_COMPONENTS]
    retained = eigenvalues[order]
    if float(np.min(retained)) <= 1.0e-10:
        raise RuntimeError("fixed ICA rank is unsupported by the sampled patches")
    basis = eigenvectors[:, order]
    whitening = basis / np.sqrt(retained)[None, :]
    z = centered @ whitening

    initial = rng.normal(size=(N_COMPONENTS, N_COMPONENTS))
    w = _sym_decorrelation(initial)
    convergence = float("inf")
    iterations = 0
    for iterations in range(1, MAX_ITERATIONS + 1):
        projected = z @ w.T
        nonlinear = np.tanh(projected)
        derivative_mean = np.mean(1.0 - nonlinear * nonlinear, axis=0)
        update = (nonlinear.T @ z) / float(z.shape[0]) - derivative_mean[:, None] * w
        update = _sym_decorrelation(update)
        convergence = float(
            np.max(np.abs(np.abs(np.diag(update @ w.T)) - 1.0))
        )
        w = update
        if convergence <= TOLERANCE:
            break

    filters = w @ whitening.T
    filters -= np.mean(filters, axis=1, keepdims=True)
    norms = np.linalg.norm(filters, axis=1)
    if np.any(norms <= 1.0e-12):
        raise RuntimeError("ICA produced a degenerate analysis filter")
    filters /= norms[:, None]
    offsets = filters @ feature_mean

    for row in filters:
        pivot = int(np.argmax(np.abs(row)))
        if row[pivot] < 0.0:
            row *= -1.0
    offsets = filters @ feature_mean
    digest = sha256(
        np.ascontiguousarray(filters, dtype=np.float64).tobytes()
        + np.ascontiguousarray(offsets, dtype=np.float64).tobytes()
    ).hexdigest()
    model: dict[str, object] = {
        "patch_size": PATCH_SIZE,
        "n_components": N_COMPONENTS,
        "filters": filters.tolist(),
        "offsets": offsets.tolist(),
        "model_sha256": digest,
        "seed": int(seed),
    }
    diagnostics = {
        "sample_count": float(x.shape[0]),
        "iterations": float(iterations),
        "convergence": convergence,
        "converged": float(convergence <= TOLERANCE),
        "minimum_retained_eigenvalue": float(np.min(retained)),
        "maximum_retained_eigenvalue": float(np.max(retained)),
        "whitened_covariance_max_abs_error": float(
            np.max(np.abs((z.T @ z) / float(z.shape[0]) - np.eye(N_COMPONENTS)))
        ),
        "unmixing_orthogonality_max_abs_error": float(
            np.max(np.abs(w @ w.T - np.eye(N_COMPONENTS)))
        ),
    }
    return model, diagnostics


def ica_concentration_context(
    image: np.ndarray, model: dict[str, object]
) -> tuple[np.ndarray, dict[str, float]]:
    """Return bounded dominance of one learned independent component."""

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("ICA context requires one finite grayscale raster")
    filters = np.asarray(model["filters"], dtype=np.float64)
    offsets = np.asarray(model["offsets"], dtype=np.float64)
    expected = PATCH_SIZE * PATCH_SIZE
    if filters.shape != (N_COMPONENTS, expected) or offsets.shape != (N_COMPONENTS,):
        raise ValueError("ICA model does not satisfy the fixed Stage-18z contract")

    local_mean = ndimage.uniform_filter(values, size=PATCH_SIZE, mode="mirror")
    local_square = ndimage.uniform_filter(values * values, size=PATCH_SIZE, mode="mirror")
    local_norm = np.sqrt(
        np.maximum((local_square - local_mean * local_mean) * expected, 0.0)
    )
    responses = []
    # The variance expression is susceptible to roundoff on exactly constant
    # windows; this absolute guard is far below one 8-bit gray-level step.
    safe = local_norm > 1.0e-6
    for filter_row, offset in zip(filters, offsets):
        kernel = filter_row.reshape(PATCH_SIZE, PATCH_SIZE)
        response = ndimage.correlate(values, kernel, mode="mirror")
        normalized = np.zeros_like(response)
        normalized[safe] = response[safe] / local_norm[safe] - float(offset)
        responses.append(np.abs(normalized))
    stack = np.stack(responses, axis=-1)
    l2 = np.sqrt(np.sum(stack * stack, axis=-1))
    ratio = np.zeros_like(l2)
    active = l2 > 1.0e-10
    ratio[active] = np.max(stack[active], axis=-1) / l2[active]
    lower = 1.0 / np.sqrt(float(N_COMPONENTS))
    evidence = np.zeros_like(ratio)
    evidence[active] = np.clip((ratio[active] - lower) / (1.0 - lower), 0.0, 1.0)
    evidence = evidence.astype(np.float32)
    return evidence, {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "evidence_max": float(np.max(evidence)),
        "active_fraction": float(np.mean(active)),
        "response_l2_mean": float(np.mean(l2)),
        "model_sha256_prefix": float(int(str(model["model_sha256"])[:12], 16)),
    }


def synthetic_contract() -> dict[str, object]:
    size = 49
    coordinate = np.linspace(0.0, 1.0, size)
    horizontal = np.tile(coordinate[:, None], (1, size))
    vertical = horizontal.T
    step_h = (horizontal >= 0.5).astype(np.float64)
    step_v = step_h.T
    diagonal = (np.add.outer(np.arange(size), np.arange(size)) >= size).astype(np.float64)
    checker = ((np.indices((size, size)).sum(axis=0) // 3) % 2).astype(np.float64)
    rng = np.random.default_rng(18026)
    noise = np.clip(0.5 + rng.normal(0.0, 0.12, (size, size)), 0.0, 1.0)
    training = [horizontal, vertical, step_h, step_v, diagonal, checker, noise]
    model_a, fit_a = fit_ica_context(training, seed=20261019, patches_per_image=192)
    model_b, fit_b = fit_ica_context(training, seed=20261019, patches_per_image=192)
    flat = np.full((size, size), 0.4, dtype=np.float64)
    step_map, _ = ica_concentration_context(step_h, model_a)
    flat_map, _ = ica_concentration_context(flat, model_a)
    repeat_map, _ = ica_concentration_context(step_h, model_a)
    affine_map, _ = ica_concentration_context(0.2 + 0.6 * step_h, model_a)
    return {
        "finite": bool(np.all(np.isfinite(step_map)) and np.all(np.isfinite(flat_map))),
        "bounded": bool(float(np.min(step_map)) >= 0.0 and float(np.max(step_map)) <= 1.0),
        "flat_max": float(np.max(flat_map)),
        "step_boundary_mean": float(np.mean(step_map[:, size // 2 - 2 : size // 2 + 2])),
        "step_positive": bool(float(np.max(step_map)) > 0.0),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat_map))),
        "positive_affine_max_abs_delta": float(np.max(np.abs(step_map - affine_map))),
        "model_repeat_equal": bool(model_a["model_sha256"] == model_b["model_sha256"]),
        "fit_converged": bool(fit_a["converged"] and fit_b["converged"]),
        "fit_repeat_max_abs_delta": float(
            max(abs(float(fit_a[key]) - float(fit_b[key])) for key in fit_a)
        ),
        "fit_diagnostics": fit_a,
    }
