from __future__ import annotations

"""Fixed directional patch-recurrence evidence for Stage 17r."""

import time

import numpy as np
from scipy.ndimage import uniform_filter


PATCH_SIZE = 5
SEARCH_SIZE = 51
BAND_WIDTH = 8
DIRECTIONS_DEGREES = (0.0, 45.0, 90.0, 135.0)
MATCHES_PER_DIRECTION = 16
SIMILARITY_H = 0.3
_BATCH_OFFSETS = 24


def _reflect_shift(image: np.ndarray, dy: int, dx: int) -> np.ndarray:
    radius = SEARCH_SIZE // 2
    padded = np.pad(image, radius, mode="reflect")
    y0 = radius + int(dy)
    x0 = radius + int(dx)
    return padded[y0:y0 + image.shape[0], x0:x0 + image.shape[1]]


def directional_offsets() -> tuple[tuple[tuple[int, int], ...], ...]:
    """Return the fixed four disjoint-from-centre bidirectional raster bands."""
    radius = SEARCH_SIZE // 2
    half_width = BAND_WIDTH / 2.0
    candidates: list[tuple[int, int, tuple[bool, ...]]] = []
    angles = np.deg2rad(np.asarray(DIRECTIONS_DEGREES, dtype=np.float64))
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            memberships = tuple(
                abs(-np.sin(angle) * dx + np.cos(angle) * dy) <= half_width
                for angle in angles
            )
            candidates.append((dy, dx, memberships))
    # Xu et al. exclude the intersection shared by all directional bands.
    bands: list[tuple[tuple[int, int], ...]] = []
    for direction in range(len(DIRECTIONS_DEGREES)):
        offsets = tuple(
            (dy, dx)
            for dy, dx, memberships in candidates
            if memberships[direction] and not all(memberships)
        )
        if len(offsets) < MATCHES_PER_DIRECTION:
            raise RuntimeError("directional recurrence band has too few candidates")
        bands.append(offsets)
    return tuple(bands)


OFFSETS = directional_offsets()


def _directional_prediction(image: np.ndarray, offsets: tuple[tuple[int, int], ...]) -> tuple[np.ndarray, np.ndarray]:
    height, width = image.shape
    best_dist = np.full((MATCHES_PER_DIRECTION, height, width), np.inf, dtype=np.float32)
    best_value = np.zeros_like(best_dist)
    for start in range(0, len(offsets), _BATCH_OFFSETS):
        distance_parts, value_parts = [], []
        for dy, dx in offsets[start:start + _BATCH_OFFSETS]:
            shifted = _reflect_shift(image, dy, dx).astype(np.float32, copy=False)
            squared = np.square(image - shifted, dtype=np.float32)
            patch_ssd = uniform_filter(squared, size=PATCH_SIZE, mode="reflect") * float(PATCH_SIZE ** 2)
            distance_parts.append(patch_ssd.astype(np.float32, copy=False))
            value_parts.append(shifted)
        distances = np.concatenate((best_dist, np.stack(distance_parts)), axis=0)
        values = np.concatenate((best_value, np.stack(value_parts)), axis=0)
        keep = np.argpartition(distances, MATCHES_PER_DIRECTION - 1, axis=0)[:MATCHES_PER_DIRECTION]
        best_dist = np.take_along_axis(distances, keep, axis=0)
        best_value = np.take_along_axis(values, keep, axis=0)
    # Subtracting the best distance is algebraically neutral after normalization
    # and avoids numerical underflow in the paper's exp(-SSD/h) weights.
    stabilized = best_dist - np.min(best_dist, axis=0, keepdims=True)
    weights = np.exp(-stabilized / SIMILARITY_H).astype(np.float32, copy=False)
    prediction = np.sum(weights * best_value, axis=0) / np.maximum(np.sum(weights, axis=0), 1.0e-12)
    recurrence = np.mean(np.exp(-best_dist / SIMILARITY_H), axis=0)
    return prediction.astype(np.float64), recurrence.astype(np.float64)


def discriminative_patch_recurrence_evidence(image: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Mean absolute directional nonlocal residual from Xu et al.'s Eq. (6)."""
    started = time.perf_counter()
    source = np.asarray(image, dtype=np.float32)
    if source.ndim != 2:
        raise ValueError("directional patch recurrence requires a 2-D grayscale image")
    if not np.all(np.isfinite(source)):
        raise ValueError("directional patch recurrence requires finite input")
    source = np.clip(source, 0.0, 1.0)
    residuals, recurrences = [], []
    for offsets in OFFSETS:
        prediction, recurrence = _directional_prediction(source, offsets)
        residuals.append(np.abs(source.astype(np.float64) - prediction))
        recurrences.append(recurrence)
    stack = np.stack(residuals, axis=0)
    evidence = np.clip(np.mean(stack, axis=0), 0.0, 1.0)
    recurrence_stack = np.stack(recurrences, axis=0)
    diagnostics = {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.90)),
        "max_evidence": float(np.max(evidence)),
        "active_fraction": float(np.mean(evidence > 1.0e-12)),
        "directional_residual_mean": float(np.mean(stack)),
        "directional_residual_max": float(np.max(stack)),
        "mean_patch_recurrence": float(np.mean(recurrence_stack)),
        "directional_recurrence_range_mean": float(np.mean(np.ptp(recurrence_stack, axis=0))),
        "runtime_seconds": float(time.perf_counter() - started),
    }
    return evidence, diagnostics


def synthetic_contract() -> dict[str, float | bool | list[int]]:
    size = 65
    flat = np.full((size, size), 0.5, dtype=np.float64)
    step = np.zeros((size, size), dtype=np.float64)
    step[:, size // 2:] = 1.0
    yy, xx = np.indices((size, size))
    checker = ((yy + xx) % 2).astype(np.float64)
    rng = np.random.default_rng(17017)
    noise = np.clip(0.5 + 0.001 * rng.standard_normal((size, size)), 0.0, 1.0)
    first, _ = discriminative_patch_recurrence_evidence(step)
    second, _ = discriminative_patch_recurrence_evidence(step)
    flat_map, _ = discriminative_patch_recurrence_evidence(flat)
    checker_map, _ = discriminative_patch_recurrence_evidence(checker)
    noise_map, _ = discriminative_patch_recurrence_evidence(noise)
    centre = size // 2
    edge_slice = np.s_[8:-8, centre - 2:centre + 3]
    return {
        "finite": bool(np.all(np.isfinite(first))),
        "bounded": bool(float(np.min(first)) >= 0.0 and float(np.max(first)) <= 1.0),
        "flat_max": float(np.max(flat_map)),
        "repeat_max_abs_delta": float(np.max(np.abs(first - second))),
        "step_edge_mean": float(np.mean(first[edge_slice])),
        "checker_mean": float(np.mean(checker_map[8:-8, 8:-8])),
        "noise_mean": float(np.mean(noise_map[8:-8, 8:-8])),
        "step_exceeds_checker": bool(np.mean(first[edge_slice]) > np.mean(checker_map[8:-8, 8:-8])),
        "step_exceeds_noise": bool(np.mean(first[edge_slice]) > np.mean(noise_map[8:-8, 8:-8])),
        "band_offset_counts": [len(offsets) for offsets in OFFSETS],
    }
