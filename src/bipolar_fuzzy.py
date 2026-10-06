from __future__ import annotations

"""Bipolar fuzzy evidence utilities for the Stage-12 signature line.

The current model has two semantically distinct evidence banks:

* positive boundary evidence p_i(x) in [0,1]
* texture / anti-boundary evidence n_j(x) in [0,1]

For a separable bi-capacity

    v(A, B) = mu_plus(A) - lambda * mu_minus(B),

a natural CPT-style bipolar Choquet score is

    B(x) = C_{mu_plus}(p(x)) - lambda * C_{mu_minus}(n(x)).

`normalized_separable_bicapacity` maps the natural range [-lambda, 1] to [0,1]
without changing the semantic zero point of the signed score.  The positive and
negative capacities can use independent distortion exponents, which lets the
experiment ask whether pro-edge and anti-texture evidence have different
interaction structure.

This module deliberately contains no GT-dependent logic.  Feature-bank fitting
remains outside the inference operator.
"""

import numpy as np

EPS = 1e-8


def distorted_choquet(memberships: np.ndarray, weights: np.ndarray, gamma: float) -> np.ndarray:
    """Choquet integral for m(A)=(sum_{i in A} w_i)^gamma.

    gamma=1 gives the additive weighted-mean control.  gamma<1 rewards
    distributed support; gamma>1 makes coalitions more selective.
    """
    X = np.asarray(memberships, dtype=float)
    if X.ndim < 1 or X.shape[-1] == 0:
        return np.zeros(X.shape[:-1], dtype=np.float32)
    w = np.asarray(weights, dtype=float)
    w = w / max(float(w.sum()), EPS)
    order = np.argsort(X, axis=-1)
    xs = np.take_along_axis(X, order, axis=-1)
    ww = np.take_along_axis(np.broadcast_to(w, X.shape), order, axis=-1)
    suffix = np.flip(np.cumsum(np.flip(ww, axis=-1), axis=-1), axis=-1)
    cap = np.power(np.clip(suffix, 0.0, 1.0), float(gamma))
    prev = np.concatenate(
        [np.zeros((*xs.shape[:-1], 1), dtype=float), xs[..., :-1]], axis=-1
    )
    out = np.sum((xs - prev) * cap, axis=-1)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def signed_separable_bicapacity(
    positive: np.ndarray,
    negative: np.ndarray,
    lam: float = 1.0,
) -> np.ndarray:
    """Signed score C_plus - lambda*C_minus in the natural range [-lambda,1]."""
    p = np.asarray(positive, dtype=np.float32)
    n = np.asarray(negative, dtype=np.float32)
    return p - float(lam) * n


def normalized_separable_bicapacity(
    positive: np.ndarray,
    negative: np.ndarray,
    lam: float = 1.0,
) -> np.ndarray:
    """Map the separable bi-capacity score from [-lambda,1] to [0,1]."""
    l = max(float(lam), 0.0)
    b = signed_separable_bicapacity(positive, negative, l)
    return np.clip((b + l) / max(1.0 + l, EPS), 0.0, 1.0).astype(np.float32)


def ratio_control(
    positive: np.ndarray,
    negative: np.ndarray,
    lam: float = 1.0,
    prior: float = 0.05,
) -> np.ndarray:
    """Empirical Stage-12b ratio control, retained for a fair comparison."""
    p = np.asarray(positive, dtype=np.float32)
    n = np.asarray(negative, dtype=np.float32)
    q = max(float(prior), EPS)
    return np.clip((p + q) / (p + float(lam) * n + 2.0 * q), 0.0, 1.0).astype(np.float32)


def context_gate(localizer: np.ndarray, context: np.ndarray, strength: float, floor: float) -> np.ndarray:
    """Softly modulate a fixed localizer while retaining a non-zero floor."""
    c = np.clip(np.asarray(context, dtype=np.float32), 0.0, 1.0)
    g = float(floor) + (1.0 - float(floor)) * np.power(c, float(strength))
    return np.asarray(localizer, dtype=np.float32) * g.astype(np.float32)
