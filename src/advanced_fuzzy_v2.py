from __future__ import annotations

"""Second-wave fuzzy aggregation operators for the local research branch.

This module intentionally keeps experimental generalizations isolated from the
stable Stage-5/7 operator implementation.  Every function is deterministic and
NumPy-only so it can be benchmarked on a CPU workstation.

Implemented families
--------------------
- SWAFED-faithful local power exponents computed from sliding-window absolute
  intensity differences (plus a `lukasiewicz_repo` mode that reproduces the
  published repository expression literally).
- d-Choquet, d-CF, d-XC and d-CC restricted-dissimilarity generalizations.
- Choquet-inspired input-dependent aggregation (Bustince et al., 2026).
- Partition-conditioned Choquet-inspired aggregation (Alcantud, 2026 inspired).
- Compact regularized pair-interaction capacity for low-complexity experiments.

The Choquet-inspired/partitioned functions are research candidates, not claimed
as bit-exact reproductions unless the configuration explicitly says so.
"""

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np
from scipy import ndimage as ndi

from .fuzzy_measures import capacity_table_2additive, tail_capacities
from .operators import FUNCTIONS

EPS = 1e-12


def _gray01(img: np.ndarray) -> np.ndarray:
    x = np.asarray(img, dtype=float)
    if x.ndim == 3:
        x = x[..., :3]
        x = 0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]
    if x.size and float(np.nanmax(x)) > 1.0:
        x = x / 255.0
    return np.clip(np.nan_to_num(x), 0.0, 1.0)


def restricted_dissimilarity(a, b, kind: str = "abs"):
    """RDFs used in the current edge-detection literature.

    `abs`     : |x-y|
    `square`  : (x-y)^2
    `sqrt`    : sqrt(|x-y|)
    `x2`      : |x^2-y^2|
    `sqrt2`   : (sqrt(x)-sqrt(y))^2
    `sin`     : sin(pi/2*|x-y|), exploratory smooth RDF
    """
    x = np.clip(np.asarray(a, float), 0.0, 1.0)
    y = np.clip(np.asarray(b, float), 0.0, 1.0)
    d = np.abs(x - y)
    k = str(kind).lower()
    if k in ("abs", "d0"):
        z = d
    elif k in ("square", "quadratic", "d1"):
        z = d * d
    elif k in ("sqrt", "d2"):
        z = np.sqrt(d)
    elif k in ("x2", "d4"):
        z = np.abs(x * x - y * y)
    elif k in ("sqrt2", "d5"):
        z = np.square(np.sqrt(x) - np.sqrt(y))
    elif k == "sin":
        z = np.sin(0.5 * np.pi * d)
    else:
        raise ValueError(f"unknown restricted dissimilarity: {kind}")
    return np.clip(z, 0.0, 1.0)


def _ordered(X):
    x = np.clip(np.asarray(X, dtype=float), 0.0, 1.0)
    order = np.argsort(x, axis=-1, kind="stable")
    xs = np.take_along_axis(x, order, axis=-1)
    return x, order, xs


def d_choquet_family(
    X: np.ndarray,
    measure_spec: Mapping[str, Any],
    mode: str = "dcf",
    F: str = "CL",
    rdf: str = "abs",
    context: Optional[Mapping[str, Any]] = None,
    scale: Optional[int] = None,
) -> np.ndarray:
    """d-Choquet family following the published definitions.

    dChoquet = sum_i delta(x_i,x_{i-1}) * mu(A_i)
    dCF      = x_1 + sum_{i>=2} F(delta(x_i,x_{i-1}), mu(A_i))
    dXC      = x_1 + sum_{i>=2} delta(x_i*mu_i, x_{i-1}*mu_i)
    dCC      = x_1 + sum_{i>=2} delta(C(x_i,mu_i), C(x_{i-1},mu_i))
    """
    x, _order, xs = _ordered(X)
    m = tail_capacities(x, measure_spec, context=context or {}, scale=scale)
    prev = np.concatenate([np.zeros_like(xs[..., :1]), xs[..., :-1]], axis=-1)
    mode = str(mode).lower()
    f = FUNCTIONS[F]

    if mode in ("dchoquet", "d-ci", "dci"):
        return np.sum(restricted_dissimilarity(xs, prev, rdf) * m, axis=-1)

    if xs.shape[-1] == 1:
        return xs[..., 0]

    if mode in ("dcf", "d-cf"):
        z = xs[..., 0] + np.sum(
            f(restricted_dissimilarity(xs[..., 1:], xs[..., :-1], rdf), m[..., 1:]),
            axis=-1,
        )
        return np.clip(z, 0.0, 1.0)

    if mode in ("dxc", "d-xc", "dxchoquet"):
        a = xs[..., 1:] * m[..., 1:]
        b = xs[..., :-1] * m[..., 1:]
        z = xs[..., 0] + np.sum(restricted_dissimilarity(a, b, rdf), axis=-1)
        return np.clip(z, 0.0, 1.0)

    if mode in ("dcc", "d-cc"):
        a = f(xs[..., 1:], m[..., 1:])
        b = f(xs[..., :-1], m[..., 1:])
        z = xs[..., 0] + np.sum(restricted_dissimilarity(a, b, rdf), axis=-1)
        return np.clip(z, 0.0, 1.0)

    raise ValueError(f"unknown d-Choquet mode: {mode}")


def _sliding_difference_stack(img: np.ndarray, window: int = 3) -> np.ndarray:
    """Absolute centre-neighbour differences used by the SWAFED code path."""
    x = _gray01(img)
    w = max(3, int(window) | 1)
    r = w // 2
    pad = np.pad(x, r, mode="reflect")
    diffs = []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy == 0 and dx == 0:
                continue
            y0 = r + dy
            x0 = r + dx
            neigh = pad[y0:y0 + x.shape[0], x0:x0 + x.shape[1]]
            diffs.append(np.abs(neigh - x))
    return np.stack(diffs, axis=-1)


def swafed_q_map(
    img: np.ndarray,
    window: int = 3,
    mode: str = "mean",
    q_min: float = 1e-4,
    q_max: float = 1.0,
) -> np.ndarray:
    """Local power exponent derived from the official SWAFED formulation.

    The official MATLAB implementation obtains q from ordered centre-neighbour
    differences.  This vectorized port follows those max/min/prod/mean/geomean/
    harmmean/Hamacher/ODiv definitions.  `lukasiewicz_repo` deliberately mirrors
    the repository expression (sum - N - 1); `lukasiewicz` uses the standard
    n-ary Lukasiewicz t-norm max(sum-(N-1),0), letting us test both variants.
    """
    d = np.clip(_sliding_difference_stack(img, window), EPS, 1.0)
    n = d.shape[-1]
    k = str(mode).lower()
    if k == "max":
        q = np.max(d, axis=-1)
    elif k == "min":
        q = np.min(d, axis=-1)
    elif k == "prod":
        q = np.prod(d, axis=-1)
    elif k == "mean":
        q = np.mean(d, axis=-1)
    elif k in ("geomean", "geometric"):
        q = np.exp(np.mean(np.log(d), axis=-1))
    elif k in ("harmmean", "harmonic"):
        q = n / np.sum(1.0 / d, axis=-1)
    elif k == "lukasiewicz_repo":
        q = np.maximum(np.sum(d, axis=-1) - n - 1.0, 0.0)
    elif k in ("lukasiewicz", "tl"):
        q = np.maximum(np.sum(d, axis=-1) - (n - 1.0), 0.0)
    elif k in ("hamacher", "thp"):
        s = np.sum(d, axis=-1)
        p = np.prod(d, axis=-1)
        q = np.where(np.abs(s - p) > EPS, p / (s - p), 0.0)
    elif k == "odiv":
        q = (np.prod(d, axis=-1) + np.min(d, axis=-1)) / float(n)
    else:
        raise ValueError(f"unknown SWAFED mode: {mode}")
    return np.clip(q, float(q_min), float(q_max))


def swafed_tail_capacities(X: np.ndarray, qmap: np.ndarray) -> np.ndarray:
    """Power measure tail values m(A_i)=(|A_i|/n)^q(x)."""
    x = np.asarray(X)
    n = x.shape[-1]
    q = np.asarray(qmap, dtype=float)
    if q.shape != x.shape[:-1]:
        raise ValueError(f"qmap shape {q.shape} incompatible with X {x.shape}")
    sizes = np.arange(n, 0, -1, dtype=float) / float(n)
    return np.power(sizes.reshape((1,) * q.ndim + (n,)), q[..., None])


def aggregate_swafed_descriptor_tensor(
    X: np.ndarray,
    img: np.ndarray,
    mode: str = "mean",
    family: str = "cf1f2",
    F1: str = "CL",
    F2: str = "CL",
    window: int = 3,
) -> np.ndarray:
    """Use image-local SWAFED q while aggregating the current MFI descriptors."""
    x, _order, xs = _ordered(X)
    m = swafed_tail_capacities(x, swafed_q_map(img, window=window, mode=mode))
    prev = np.concatenate([np.zeros_like(xs[..., :1]), xs[..., :-1]], axis=-1)
    fam = str(family).lower()
    if fam == "choquet":
        return np.sum((xs - prev) * m, axis=-1)
    if fam == "cf":
        return np.clip(np.sum(FUNCTIONS[F1](xs - prev, m), axis=-1), 0.0, 1.0)
    if fam == "cc":
        return np.clip(np.sum(FUNCTIONS[F1](xs, m) - FUNCTIONS[F1](prev, m), axis=-1), 0.0, 1.0)
    if fam == "cf1f2":
        if xs.shape[-1] == 1:
            return xs[..., 0]
        z = xs[..., 0] + np.sum(
            FUNCTIONS[F1](xs[..., 1:], m[..., 1:]) -
            FUNCTIONS[F2](xs[..., :-1], m[..., 1:]), axis=-1)
        return np.clip(z, 0.0, 1.0)
    raise ValueError(f"unknown SWAFED aggregation family: {family}")


def choquet_inspired(
    X: np.ndarray,
    weight_function: str = "mean",
    temperature: float = 4.0,
) -> np.ndarray:
    """Input-dependent Choquet-inspired aggregation.

    Implements the structural idea Gamma_F = x_(1) + sum delta_i F(x_without_pair),
    where F is symmetric/increasing for the standard candidates below.
    """
    _x, _order, xs = _ordered(X)
    n = xs.shape[-1]
    if n <= 2:
        return np.mean(xs, axis=-1)
    z = xs[..., 0].copy()
    k = str(weight_function).lower()
    for i in range(n - 1):
        keep = [j for j in range(n) if j not in (i, i + 1)]
        rest = xs[..., keep]
        if k == "mean":
            w = np.mean(rest, axis=-1)
        elif k == "max":
            w = np.max(rest, axis=-1)
        elif k == "geomean":
            w = np.exp(np.mean(np.log(np.maximum(rest, EPS)), axis=-1))
        elif k == "softmaxmean":
            a = np.exp(float(temperature) * (rest - np.max(rest, axis=-1, keepdims=True)))
            a /= np.maximum(np.sum(a, axis=-1, keepdims=True), EPS)
            w = np.sum(a * rest, axis=-1)
        else:
            raise ValueError(f"unknown Choquet-inspired weight function: {weight_function}")
        z += (xs[..., i + 1] - xs[..., i]) * np.clip(w, 0.0, 1.0)
    return np.clip(z, 0.0, 1.0)


def partitioned_choquet_inspired(
    X: np.ndarray,
    partitions: Sequence[Sequence[int]],
    within: str = "mean",
    between: str = "geomean",
) -> np.ndarray:
    """Two-level partition-conditioned input-dependent aggregation.

    Features inside a fixed partition share a block weight; block summaries are
    then aggregated through a second Choquet-inspired stage.  This follows the
    2026 partition-dependent-weight research direction while remaining a simple
    CPU-testable candidate.
    """
    x = np.clip(np.asarray(X, float), 0.0, 1.0)
    blocks = []
    for block in partitions:
        ids = [int(i) for i in block if 0 <= int(i) < x.shape[-1]]
        if not ids:
            continue
        xb = x[..., ids]
        if within == "mean":
            blocks.append(np.mean(xb, axis=-1))
        elif within == "max":
            blocks.append(np.max(xb, axis=-1))
        elif within == "geomean":
            blocks.append(np.exp(np.mean(np.log(np.maximum(xb, EPS)), axis=-1)))
        else:
            blocks.append(choquet_inspired(xb, within))
    if not blocks:
        raise ValueError("no valid partitions")
    b = np.stack(blocks, axis=-1)
    if b.shape[-1] == 1:
        return b[..., 0]
    return choquet_inspired(b, between)


def regularized_pair_capacity(
    singleton_weights: Sequence[float],
    interactions: Optional[np.ndarray] = None,
    shrinkage: float = 0.75,
) -> Dict[str, Any]:
    """Low-complexity interaction capacity with regularized pair terms.

    This is a practical 2-additive/k-interaction surrogate: interactions are
    shrunk toward zero before constructing a normalized monotone candidate.
    Negative pair coefficients are allowed only as far as monotonicity survives;
    otherwise they are progressively shrunk.
    """
    w = np.maximum(np.asarray(singleton_weights, float), 0.0)
    w /= max(float(w.sum()), EPS)
    n = len(w)
    P = np.zeros((n, n), float) if interactions is None else np.asarray(interactions, float).copy()
    if P.shape != (n, n):
        raise ValueError("interactions must be n x n")
    P = 0.5 * (P + P.T)
    np.fill_diagonal(P, 0.0)
    P *= float(1.0 - np.clip(shrinkage, 0.0, 1.0))

    # Reduce pair magnitude until all one-element marginal increments are nonnegative.
    scale = 1.0
    table = None
    for _ in range(20):
        table = capacity_table_2additive(w, P * scale)
        ok = True
        for mask in range(1 << n):
            for i in range(n):
                if not (mask & (1 << i)) and table[mask | (1 << i)] + 1e-10 < table[mask]:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            break
        scale *= 0.7
    if table is None:
        table = capacity_table_2additive(w, np.zeros_like(P))
    table = np.clip(table, 0.0, 1.0)
    table[-1] = 1.0
    return {
        "kind": "capacity",
        "capacity_table": table.tolist(),
        "meta": {
            "family": "regularized_pair_capacity",
            "singleton_weights": w.tolist(),
            "interaction_scale": float(scale),
            "shrinkage": float(shrinkage),
        },
    }
