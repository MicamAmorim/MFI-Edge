from __future__ import annotations

from dataclasses import dataclass
from math import factorial
from typing import Callable, Dict, Iterable, List, Sequence

import numpy as np

EPS = 1e-12


@dataclass
class ShapleyResult:
    values: np.ndarray
    normalized: np.ndarray
    samples: int
    mode: str


def exact_shapley(n_features: int, utility_fn: Callable[[np.ndarray], float]) -> ShapleyResult:
    """Exact Shapley values over all coalitions.

    Practical for the current MFI descriptor count (n=8 -> 256 coalitions).
    `utility_fn(mask)` receives a boolean feature mask.
    """
    n = int(n_features)
    if n < 1 or n > 20:
        raise ValueError("exact_shapley is intended for 1..20 features")
    cache: Dict[int, float] = {}

    def value(mask_int: int) -> float:
        if mask_int not in cache:
            mask = np.array([(mask_int >> i) & 1 for i in range(n)], dtype=bool)
            cache[mask_int] = float(utility_fn(mask))
        return cache[mask_int]

    phi = np.zeros(n, dtype=float)
    nf = factorial(n)
    for i in range(n):
        bit = 1 << i
        for s in range(1 << n):
            if s & bit:
                continue
            k = int(s.bit_count())
            coef = factorial(k) * factorial(n - k - 1) / nf
            phi[i] += coef * (value(s | bit) - value(s))
    z = np.maximum(phi, 0.0)
    norm = z / max(float(z.sum()), EPS)
    return ShapleyResult(phi, norm, len(cache), "exact")


def monte_carlo_shapley(
    n_features: int,
    utility_fn: Callable[[np.ndarray], float],
    n_permutations: int = 256,
    seed: int = 0,
) -> ShapleyResult:
    """Monte-Carlo permutation estimate for expensive utility functions."""
    n = int(n_features)
    rng = np.random.default_rng(seed)
    phi = np.zeros(n, dtype=float)
    calls = 0
    for _ in range(int(n_permutations)):
        order = rng.permutation(n)
        mask = np.zeros(n, dtype=bool)
        prev = float(utility_fn(mask)); calls += 1
        for i in order:
            mask[i] = True
            cur = float(utility_fn(mask)); calls += 1
            phi[i] += cur - prev
            prev = cur
    phi /= max(int(n_permutations), 1)
    z = np.maximum(phi, 0.0)
    norm = z / max(float(z.sum()), EPS)
    return ShapleyResult(phi, norm, calls, "monte_carlo")


def soft_gate_from_importance(
    importance: Sequence[float],
    threshold: float = 0.05,
    temperature: float = 0.04,
    floor: float = 0.05,
) -> np.ndarray:
    """Continuous descriptor gate from Shapley/importances."""
    w = np.asarray(importance, dtype=float)
    if w.ndim != 1:
        raise ValueError("importance must be one-dimensional")
    w = np.maximum(w, 0.0)
    if w.sum() > EPS:
        w = w / w.sum()
    t = max(float(temperature), 1e-6)
    gate = 1.0 / (1.0 + np.exp(-(w - float(threshold)) / t))
    return np.clip(float(floor) + (1.0 - float(floor)) * gate, 0.0, 1.0)


def topk_gate(importance: Sequence[float], k: int, floor: float = 0.0) -> np.ndarray:
    w = np.asarray(importance, dtype=float)
    n = len(w)
    k = max(1, min(int(k), n))
    idx = np.argsort(w)[::-1][:k]
    gate = np.full(n, float(floor), dtype=float)
    gate[idx] = 1.0
    return gate


def apply_descriptor_gate(X: np.ndarray, gate: Sequence[float]) -> np.ndarray:
    x = np.asarray(X, dtype=float)
    g = np.asarray(gate, dtype=float)
    if x.shape[-1] != g.size:
        raise ValueError(f"gate has {g.size} entries but X has {x.shape[-1]} descriptors")
    return x * g.reshape((1,) * (x.ndim - 1) + (g.size,))


def regime_gate(
    regime_weights: Dict[str, np.ndarray],
    regime_importance: Dict[str, Sequence[float]],
    threshold: float = 0.05,
    temperature: float = 0.04,
    floor: float = 0.05,
) -> np.ndarray:
    """Per-pixel soft descriptor gate from soft regime memberships.

    Returns H x W x D. Missing regimes are ignored and remaining memberships
    are renormalized locally.
    """
    keys = [k for k in regime_weights if k in regime_importance]
    if not keys:
        raise ValueError("no overlapping regimes between weights and importances")
    first = np.asarray(regime_weights[keys[0]], dtype=float)
    d = len(np.asarray(regime_importance[keys[0]]))
    out = np.zeros(first.shape + (d,), dtype=float)
    den = np.zeros(first.shape, dtype=float)
    for k in keys:
        rw = np.asarray(regime_weights[k], dtype=float)
        g = soft_gate_from_importance(regime_importance[k], threshold, temperature, floor)
        out += rw[..., None] * g
        den += rw
    return out / np.maximum(den[..., None], EPS)


def apply_spatial_gate(X: np.ndarray, gate_map: np.ndarray) -> np.ndarray:
    x = np.asarray(X, dtype=float)
    g = np.asarray(gate_map, dtype=float)
    if x.shape != g.shape:
        raise ValueError(f"spatial gate shape {g.shape} must equal descriptor tensor shape {x.shape}")
    return x * np.clip(g, 0.0, 1.0)
