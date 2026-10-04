from __future__ import annotations

from dataclasses import dataclass
from math import factorial
from typing import Any, Dict, Mapping, Optional

import numpy as np
from scipy import ndimage as ndi
from scipy.optimize import brentq

EPS = 1e-12


def _normalise_weights(w):
    w = np.clip(np.asarray(w, dtype=float), 0.0, None)
    s = float(w.sum())
    if s <= EPS:
        return np.ones_like(w) / max(len(w), 1)
    return w / s


def _robust01(a, lo=2.0, hi=98.0):
    a = np.asarray(a, dtype=float)
    finite = np.isfinite(a)
    if not finite.any():
        return np.zeros_like(a)
    p0, p1 = np.percentile(a[finite], [lo, hi])
    if p1 <= p0 + EPS:
        return np.zeros_like(a)
    return np.clip((a - p0) / (p1 - p0), 0.0, 1.0)


def tail_masks_from_order(order):
    """Bit masks of A_(i)={sigma(i),...,sigma(n)} for ascending feature order."""
    order = np.asarray(order, dtype=np.int64)
    n = order.shape[-1]
    if n > 62:
        raise ValueError("bit-mask implementation supports at most 62 criteria")
    masks = np.zeros(order.shape, dtype=np.int64)
    cur = np.zeros(order.shape[:-1], dtype=np.int64)
    for i in range(n - 1, -1, -1):
        cur = cur | (np.int64(1) << order[..., i])
        masks[..., i] = cur
    return masks


def power_tail_capacities(n, q=0.1, lead_shape=()):
    sizes = np.arange(n, 0, -1, dtype=float) / float(n)
    if np.ndim(q) == 0:
        return np.broadcast_to(np.power(sizes, float(q)), tuple(lead_shape) + (n,))
    q = np.asarray(q, dtype=float)
    return np.power(sizes.reshape((1,) * q.ndim + (n,)), q[..., None])


def adaptive_q_from_features(X, mode="mean", q_min=0.02, q_max=1.0):
    """SWAFED-inspired local q from the descriptor vector at each pixel.

    The 2024/2025 sliding-window adaptive-measure work computes the exponent of a
    power measure from local information. Here the same mechanism is transferred
    from ordered neighbourhood differences to the current MFI descriptor vector.
    """
    x = np.clip(np.asarray(X, dtype=float), EPS, 1.0)
    n = x.shape[-1]
    mode = str(mode).lower()
    if mode == "max":
        q = np.max(x, axis=-1)
    elif mode == "min":
        q = np.min(x, axis=-1)
    elif mode == "prod":
        q = np.prod(x, axis=-1)
    elif mode == "mean":
        q = np.mean(x, axis=-1)
    elif mode in ("geomean", "geometric"):
        q = np.exp(np.mean(np.log(x), axis=-1))
    elif mode in ("harmmean", "harmonic"):
        q = n / np.sum(1.0 / x, axis=-1)
    elif mode in ("lukasiewicz", "tl"):
        q = np.maximum(np.sum(x, axis=-1) - (n - 1.0), 0.0)
    elif mode in ("hamacher", "thp"):
        qsum = np.sum(x, axis=-1)
        qprod = np.prod(x, axis=-1)
        q = np.where(qsum - qprod > EPS, qprod / (qsum - qprod), 0.0)
    elif mode == "odiv":
        q = (np.prod(x, axis=-1) + np.min(x, axis=-1)) / float(n)
    elif mode == "dispersion":
        # Larger descriptor disagreement -> larger q -> more conservative capacity.
        q = np.std(x, axis=-1) / (np.mean(x, axis=-1) + EPS)
        q = _robust01(q)
    else:
        raise ValueError(f"unknown adaptive-q mode: {mode}")
    return np.clip(q, float(q_min), float(q_max))


def solve_sugeno_lambda(densities):
    """Solve 1+lambda = prod_i(1+lambda*g_i), lambda>-1.

    lambda=0 is the additive limiting case when singleton densities sum to one.
    """
    g = np.clip(np.asarray(densities, dtype=float), 0.0, 1.0)
    s = float(g.sum())
    if abs(s - 1.0) < 1e-9:
        return 0.0

    def f(lam):
        return float(np.prod(1.0 + lam * g) - (1.0 + lam))

    # lambda=0 is always an algebraic root. We seek the non-zero lambda-measure root.
    if s < 1.0:
        lo, hi = 1e-9, 1.0
        while f(hi) <= 0.0 and hi < 1e9:
            hi *= 2.0
        if hi >= 1e9:
            return 0.0
        return float(brentq(f, lo, hi, maxiter=200))
    lo, hi = -1.0 + 1e-9, -1e-9
    # Near -1 the sign can be numerically awkward; scan for a valid bracket.
    grid = np.linspace(lo, hi, 4096)
    vals = np.asarray([f(z) for z in grid])
    for a, b, fa, fb in zip(grid[:-1], grid[1:], vals[:-1], vals[1:]):
        if fa == 0:
            return float(a)
        if fa * fb < 0:
            return float(brentq(f, float(a), float(b), maxiter=200))
    return 0.0


def capacity_table_additive(weights):
    w = _normalise_weights(weights)
    n = len(w)
    table = np.zeros(1 << n, dtype=float)
    for mask in range(1, 1 << n):
        lsb = mask & -mask
        i = int(lsb.bit_length() - 1)
        table[mask] = table[mask ^ lsb] + w[i]
    table[-1] = 1.0
    return table


def capacity_table_sugeno(densities):
    g = np.clip(np.asarray(densities, dtype=float), 0.0, 1.0)
    n = len(g)
    lam = solve_sugeno_lambda(g)
    table = np.zeros(1 << n, dtype=float)
    if abs(lam) < 1e-9:
        # In the limiting additive case, normalise to remove small density rounding error.
        return capacity_table_additive(g)
    for mask in range(1, 1 << n):
        inds = [i for i in range(n) if mask & (1 << i)]
        table[mask] = (np.prod(1.0 + lam * g[inds]) - 1.0) / lam
    table = np.clip(table, 0.0, 1.0)
    table[-1] = 1.0
    return table


def capacity_table_2additive(singletons, pairs):
    singletons = np.asarray(singletons, dtype=float)
    pairs = np.asarray(pairs, dtype=float)
    n = len(singletons)
    if pairs.shape != (n, n):
        raise ValueError("pairs must be an n x n symmetric matrix")
    table = np.zeros(1 << n, dtype=float)
    for mask in range(1, 1 << n):
        inds = np.flatnonzero([(mask >> i) & 1 for i in range(n)])
        z = float(singletons[inds].sum())
        for a in range(len(inds)):
            for b in range(a + 1, len(inds)):
                z += float(pairs[inds[a], inds[b]])
        table[mask] = z
    total = float(table[-1])
    if abs(total) > EPS:
        table /= total
    table[-1] = 1.0
    return table


def validate_capacity_table(table, tol=1e-8):
    table = np.asarray(table, dtype=float)
    n = int(round(np.log2(len(table))))
    if len(table) != (1 << n):
        return False
    if abs(table[0]) > tol or abs(table[-1] - 1.0) > tol:
        return False
    if np.min(table) < -tol or np.max(table) > 1.0 + tol:
        return False
    for mask in range(1 << n):
        for i in range(n):
            if not (mask & (1 << i)):
                if table[mask | (1 << i)] + tol < table[mask]:
                    return False
    return True


def _local_additive_weights(X, mode="evidence", temperature=4.0, window=5, gamma=1.0, floor=1e-3):
    X = np.clip(np.asarray(X, dtype=float), 0.0, 1.0)
    mode = str(mode).lower()
    if mode == "evidence":
        z = np.power(X + floor, float(gamma))
    elif mode == "softmax":
        z = np.exp(float(temperature) * (X - np.max(X, axis=-1, keepdims=True)))
    elif mode in ("reliability", "snr"):
        if X.ndim < 3:
            z = np.power(X + floor, float(gamma))
        else:
            size = (int(window),) * (X.ndim - 1) + (1,)
            mean = ndi.uniform_filter(X, size=size, mode="reflect")
            mean2 = ndi.uniform_filter(X * X, size=size, mode="reflect")
            std = np.sqrt(np.maximum(mean2 - mean * mean, 0.0))
            rel = mean / (std + 0.05)
            z = (X + floor) * np.maximum(rel, floor)
    else:
        raise ValueError(f"unknown local additive mode: {mode}")
    return z / np.maximum(np.sum(z, axis=-1, keepdims=True), EPS)


def resolve_measure_spec(spec: Optional[Mapping[str, Any]], scale=None, context=None):
    if spec is None:
        return {"kind": "power", "q": 0.1}
    spec = dict(spec)
    kind = str(spec.get("kind", "power")).lower()
    if kind == "scale_router":
        measures = spec.get("measures", {})
        key = str(scale)
        return dict(measures.get(key, measures.get(scale, spec.get("default", {"kind": "power", "q": 0.1}))))
    if kind == "context_router":
        context = context or {}
        label = context.get("context_label", context.get("label", "default"))
        measures = spec.get("measures", {})
        return dict(measures.get(label, spec.get("default", {"kind": "power", "q": 0.1})))
    return spec


def tail_capacities(X, spec=None, context=None, scale=None):
    """Return mu(A_(i)) aligned with ascending-sorted X for each sample/pixel."""
    X = np.clip(np.asarray(X, dtype=float), 0.0, 1.0)
    n = X.shape[-1]
    context = context or {}
    spec = resolve_measure_spec(spec, scale=scale, context=context)
    kind = str(spec.get("kind", "power")).lower()
    order = np.argsort(X, axis=-1, kind="stable")

    if kind in ("power", "symmetric_power"):
        return power_tail_capacities(n, spec.get("q", 0.1), X.shape[:-1])

    if kind in ("adaptive_power", "swafed_power", "local_power"):
        qmap = adaptive_q_from_features(
            X, spec.get("mode", "mean"), spec.get("q_min", 0.02), spec.get("q_max", 1.0)
        )
        return power_tail_capacities(n, qmap, X.shape[:-1])

    if kind in ("heterogeneity_power", "context_power"):
        h = context.get("heterogeneity")
        if h is None:
            raise ValueError("heterogeneity_power requires context['heterogeneity']")
        z = _robust01(h)
        if bool(spec.get("inverse", False)):
            z = 1.0 - z
        qmap = float(spec.get("q_min", 0.05)) + z * (float(spec.get("q_max", 1.0)) - float(spec.get("q_min", 0.05)))
        return power_tail_capacities(n, qmap, X.shape[:-1])

    if kind in ("additive", "weighted"):
        w = _normalise_weights(spec.get("weights", np.ones(n)))
        return np.cumsum(w[order][..., ::-1], axis=-1)[..., ::-1]

    if kind in ("local_additive", "adaptive_additive"):
        w = _local_additive_weights(
            X,
            mode=spec.get("mode", "reliability"),
            temperature=spec.get("temperature", 4.0),
            window=spec.get("window", 5),
            gamma=spec.get("gamma", 1.0),
            floor=spec.get("floor", 1e-3),
        )
        ws = np.take_along_axis(w, order, axis=-1)
        return np.cumsum(ws[..., ::-1], axis=-1)[..., ::-1]

    if kind in ("sugeno_lambda", "lambda"):
        if "capacity_table" in spec:
            table = np.asarray(spec["capacity_table"], dtype=float)
        else:
            densities = np.asarray(spec.get("densities", np.ones(n) / n), dtype=float)
            table = capacity_table_sugeno(densities)
        masks = tail_masks_from_order(order)
        return table[masks]

    if kind in ("two_additive", "2additive", "2-additive"):
        if "capacity_table" in spec:
            table = np.asarray(spec["capacity_table"], dtype=float)
        else:
            table = capacity_table_2additive(spec["singletons"], spec["pairs"])
        masks = tail_masks_from_order(order)
        return table[masks]

    if kind in ("capacity", "learned_capacity", "full_capacity"):
        table = np.asarray(spec["capacity_table"], dtype=float)
        if len(table) != (1 << n):
            raise ValueError("capacity table dimension does not match X")
        masks = tail_masks_from_order(order)
        return table[masks]

    raise ValueError(f"unknown fuzzy-measure kind: {kind}")


def shapley_values(capacity_table):
    mu = np.asarray(capacity_table, dtype=float)
    n = int(round(np.log2(len(mu))))
    out = np.zeros(n, dtype=float)
    nf = factorial(n)
    for i in range(n):
        bit = 1 << i
        for S in range(1 << n):
            if S & bit:
                continue
            s = int(S.bit_count())
            coef = factorial(s) * factorial(n - s - 1) / nf
            out[i] += coef * (mu[S | bit] - mu[S])
    return out


def interaction_matrix(capacity_table):
    """Grabisch-style pair interaction index; positive=synergy, negative=redundancy."""
    mu = np.asarray(capacity_table, dtype=float)
    n = int(round(np.log2(len(mu))))
    I = np.zeros((n, n), dtype=float)
    den = factorial(max(n - 1, 1))
    for i in range(n):
        bi = 1 << i
        for j in range(i + 1, n):
            bj = 1 << j
            z = 0.0
            for S in range(1 << n):
                if S & (bi | bj):
                    continue
                s = int(S.bit_count())
                coef = factorial(s) * factorial(n - s - 2) / den
                d = mu[S | bi | bj] - mu[S | bi] - mu[S | bj] + mu[S]
                z += coef * d
            I[i, j] = I[j, i] = z
    return I


def measure_registry(n, learned=None):
    """Baseline exploratory registry. Learned specs can be appended by benchmark code."""
    learned = learned or {}
    specs = []
    for q in (0.05, 0.1, 0.2, 0.4, 0.7, 1.0, 1.5, 2.0):
        specs.append({"name": f"power_q{q:g}", "kind": "power", "q": q})
    specs.append({"name": "additive_uniform", "kind": "additive", "weights": [1.0 / n] * n})
    for mode in ("max", "min", "prod", "mean", "geomean", "harmmean", "lukasiewicz", "hamacher", "odiv", "dispersion"):
        specs.append({"name": f"adaptive_power_{mode}", "kind": "adaptive_power", "mode": mode, "q_min": 0.02, "q_max": 1.0})
    specs += [
        {"name": "hetero_power_direct", "kind": "heterogeneity_power", "q_min": 0.05, "q_max": 1.2, "inverse": False},
        {"name": "hetero_power_inverse", "kind": "heterogeneity_power", "q_min": 0.05, "q_max": 1.2, "inverse": True},
        {"name": "local_additive_evidence", "kind": "local_additive", "mode": "evidence", "gamma": 1.5},
        {"name": "local_additive_softmax", "kind": "local_additive", "mode": "softmax", "temperature": 4.0},
        {"name": "local_additive_reliability", "kind": "local_additive", "mode": "reliability", "window": 5},
    ]
    for name, spec in learned.items():
        d = dict(spec)
        d["name"] = name
        specs.append(d)
    return specs
