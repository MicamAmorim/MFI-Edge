from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence

import numpy as np
from scipy import ndimage as ndi
from scipy.optimize import Bounds, LinearConstraint, minimize

from .fuzzy_measures import (
    EPS,
    capacity_table_2additive,
    capacity_table_additive,
    capacity_table_sugeno,
    interaction_matrix,
    shapley_values,
    validate_capacity_table,
)


def balanced_sample(X, y, max_samples=20000, seed=0):
    X = np.asarray(X, dtype=float).reshape(-1, np.asarray(X).shape[-1])
    y = np.asarray(y, dtype=float).reshape(-1)
    valid = np.isfinite(X).all(axis=1) & np.isfinite(y)
    X, y = X[valid], y[valid]
    pos = np.flatnonzero(y >= 0.5)
    neg = np.flatnonzero(y < 0.5)
    rng = np.random.default_rng(seed)
    each = min(len(pos), len(neg), max_samples // 2)
    if each <= 0:
        idx = rng.choice(len(y), size=min(len(y), max_samples), replace=False)
    else:
        idx = np.concatenate([
            rng.choice(pos, size=each, replace=False),
            rng.choice(neg, size=each, replace=False),
        ])
        rng.shuffle(idx)
    return np.clip(X[idx], 0.0, 1.0), y[idx]


def pool_balanced_samples(feature_maps, targets, max_samples=30000, seed=0):
    rng = np.random.default_rng(seed)
    xs, ys = [], []
    per = max(500, int(max_samples / max(len(feature_maps), 1)))
    for k, (X, y) in enumerate(zip(feature_maps, targets)):
        a, b = balanced_sample(X, y, max_samples=per, seed=int(rng.integers(0, 2**31 - 1)))
        xs.append(a); ys.append(b)
    X = np.concatenate(xs, axis=0)
    y = np.concatenate(ys, axis=0)
    if len(y) > max_samples:
        idx = rng.choice(len(y), size=max_samples, replace=False)
        X, y = X[idx], y[idx]
    return X, y


def feature_reliability_weights(X, y, floor=0.02):
    X = np.asarray(X, dtype=float); y = np.asarray(y, dtype=float) >= 0.5
    if y.sum() == 0 or (~y).sum() == 0:
        return np.ones(X.shape[-1]) / X.shape[-1]
    mp, mn = X[y].mean(0), X[~y].mean(0)
    sp = X[y].std(0); sn = X[~y].std(0)
    effect = np.maximum(mp - mn, 0.0) / (0.5 * (sp + sn) + 0.05)
    effect = np.maximum(effect, floor)
    return effect / effect.sum()


def learn_additive(X, y, ridge=1e-4):
    X = np.asarray(X, float); y = np.asarray(y, float)
    n = X.shape[1]
    init = feature_reliability_weights(X, y)

    def fun(w):
        r = X @ w - y
        return 0.5 * np.mean(r * r) + 0.5 * ridge * np.sum((w - 1.0 / n) ** 2)

    def jac(w):
        r = X @ w - y
        return (X.T @ r) / len(y) + ridge * (w - 1.0 / n)

    res = minimize(
        fun, init, jac=jac, method="SLSQP",
        bounds=Bounds(np.zeros(n), np.ones(n)),
        constraints=[LinearConstraint(np.ones((1, n)), 1.0, 1.0)],
        options={"maxiter": 500, "ftol": 1e-10, "disp": False},
    )
    w = res.x if res.success else init
    w = np.clip(w, 0.0, None); w /= max(w.sum(), EPS)
    return {"kind": "additive", "weights": w.tolist(), "capacity_table": capacity_table_additive(w).tolist(), "fit_success": bool(res.success)}


def _pair_index(n):
    pairs = list(combinations(range(n), 2))
    return pairs, {p: n + k for k, p in enumerate(pairs)}


def _two_additive_design(X):
    X = np.asarray(X, float)
    n = X.shape[1]
    pairs, _ = _pair_index(n)
    cols = [X]
    if pairs:
        cols.append(np.column_stack([np.minimum(X[:, i], X[:, j]) for i, j in pairs]))
    return np.column_stack(cols), pairs


def _two_additive_monotonicity(n, pairs, pair_to_idx):
    p = n + len(pairs)
    rows = []
    # Necessary and sufficient monotonicity constraints for 2-additive capacities:
    # m_i + sum_{j in T} m_ij >= 0 for every i and T subset of N\{i}.
    for i in range(n):
        others = [j for j in range(n) if j != i]
        for mask in range(1 << len(others)):
            row = np.zeros(p, dtype=float); row[i] = 1.0
            for k, j in enumerate(others):
                if mask & (1 << k):
                    key = (min(i, j), max(i, j))
                    row[pair_to_idx[key]] += 1.0
            rows.append(row)
    return np.asarray(rows)


def learn_2additive(X, y, ridge=1e-4, maxiter=700):
    X = np.asarray(X, float); y = np.asarray(y, float)
    D, pairs = _two_additive_design(X)
    n = X.shape[1]; p = D.shape[1]
    pairs2, pair_to_idx = _pair_index(n)
    assert pairs == pairs2
    init = np.zeros(p, dtype=float)
    init[:n] = feature_reliability_weights(X, y)
    Amono = _two_additive_monotonicity(n, pairs, pair_to_idx)

    def fun(z):
        r = D @ z - y
        return 0.5 * np.mean(r * r) + 0.5 * ridge * np.sum(z[n:] ** 2)

    def jac(z):
        r = D @ z - y
        g = (D.T @ r) / len(y)
        g[n:] += ridge * z[n:]
        return g

    constraints = [
        LinearConstraint(np.ones((1, p)), 1.0, 1.0),
        LinearConstraint(Amono, 0.0, np.inf),
    ]
    lo = np.concatenate([np.zeros(n), -np.ones(p - n)])
    hi = np.ones(p)
    res = minimize(
        fun, init, jac=jac, method="SLSQP", bounds=Bounds(lo, hi), constraints=constraints,
        options={"maxiter": int(maxiter), "ftol": 1e-9, "disp": False},
    )
    z = res.x if res.success else init
    singles = z[:n]
    pairmat = np.zeros((n, n), dtype=float)
    for k, (i, j) in enumerate(pairs):
        pairmat[i, j] = pairmat[j, i] = z[n + k]
    table = capacity_table_2additive(singles, pairmat)
    if not validate_capacity_table(table, tol=5e-6):
        # Safe fallback: retain learned singleton importance and positive pair synergies only.
        pairmat = np.maximum(pairmat, 0.0)
        table = capacity_table_2additive(np.maximum(singles, 0.0), pairmat)
    return {
        "kind": "two_additive",
        "singletons": np.asarray(singles).tolist(),
        "pairs": pairmat.tolist(),
        "capacity_table": table.tolist(),
        "fit_success": bool(res.success),
        "shapley": shapley_values(table).tolist(),
        "interaction": interaction_matrix(table).tolist(),
    }


def _choquet_linear_design(X):
    X = np.asarray(X, float)
    n = X.shape[1]; full = (1 << n) - 1
    order = np.argsort(X, axis=1, kind="stable")
    xs = np.take_along_axis(X, order, axis=1)
    prev = np.column_stack([np.zeros(len(X)), xs[:, :-1]])
    delta = xs - prev
    masks = np.zeros_like(order, dtype=np.int64)
    cur = np.zeros(len(X), dtype=np.int64)
    for i in range(n - 1, -1, -1):
        cur |= (np.int64(1) << order[:, i])
        masks[:, i] = cur
    A = np.zeros((len(X), full - 1), dtype=float)  # masks 1..full-1
    base = np.zeros(len(X), dtype=float)
    for i in range(n):
        mi = masks[:, i]
        di = delta[:, i]
        is_full = mi == full
        base[is_full] += di[is_full]
        rows = np.flatnonzero(~is_full)
        if len(rows):
            A[rows, mi[rows] - 1] += di[rows]
    return A, base


def _full_capacity_monotonicity(n):
    full = (1 << n) - 1
    p = full - 1
    rows = []
    for mask in range(1, full):
        for i in range(n):
            if mask & (1 << i):
                continue
            sup = mask | (1 << i)
            if sup == full:
                continue  # upper bound mu(mask)<=1 already covers this edge
            row = np.zeros(p, dtype=float)
            row[sup - 1] = 1.0
            row[mask - 1] = -1.0
            rows.append(row)
    return np.asarray(rows)


def learn_full_capacity(X, y, ridge=5e-4, prior_q=0.1, maxiter=350):
    """Learn all 2^n-2 free capacity values with monotonicity constraints.

    Intended for n<=8 in exploratory experiments. The training objective uses the
    classical Choquet integral because it is linear in capacity values; the learned
    capacity can then also be transferred to CF/CC/CF1F2 variants.
    """
    X = np.asarray(X, float); y = np.asarray(y, float)
    n = X.shape[1]
    if n > 8:
        raise ValueError("full capacity learning is intentionally limited to n<=8")
    full = (1 << n) - 1
    A, base = _choquet_linear_design(X)
    prior = np.zeros(full - 1, dtype=float)
    for mask in range(1, full):
        prior[mask - 1] = (mask.bit_count() / n) ** float(prior_q)
    Amono = _full_capacity_monotonicity(n)

    def fun(z):
        r = base + A @ z - y
        return 0.5 * np.mean(r * r) + 0.5 * ridge * np.mean((z - prior) ** 2)

    def jac(z):
        r = base + A @ z - y
        return (A.T @ r) / len(y) + (ridge / len(z)) * (z - prior)

    constraints = [] if Amono.size == 0 else [LinearConstraint(Amono, 0.0, np.inf)]
    res = minimize(
        fun, prior, jac=jac, method="SLSQP",
        bounds=Bounds(np.zeros(full - 1), np.ones(full - 1)), constraints=constraints,
        options={"maxiter": int(maxiter), "ftol": 1e-8, "disp": False},
    )
    z = res.x if res.success else prior
    table = np.zeros(1 << n, dtype=float)
    table[1:full] = z; table[full] = 1.0
    return {
        "kind": "full_capacity",
        "capacity_table": table.tolist(),
        "fit_success": bool(res.success),
        "shapley": shapley_values(table).tolist(),
        "interaction": interaction_matrix(table).tolist(),
    }


def learned_sugeno_from_reliability(X, y, target_sum=0.7):
    w = feature_reliability_weights(X, y)
    g = np.clip(w * float(target_sum), 1e-5, 0.95)
    table = capacity_table_sugeno(g)
    return {
        "kind": "sugeno_lambda",
        "densities": g.tolist(),
        "target_sum": float(target_sum),
        "capacity_table": table.tolist(),
        "shapley": shapley_values(table).tolist(),
        "interaction": interaction_matrix(table).tolist(),
    }


def context_vector(img):
    """Training-free global context descriptors for routing context-specific capacities."""
    x = np.asarray(img, dtype=float)
    if x.ndim == 3:
        x = x[..., :3].mean(axis=2)
    if x.max() > 1:
        x = x / 255.0
    med = ndi.median_filter(x, size=3, mode="reflect")
    hp = x - ndi.gaussian_filter(x, 1.0, mode="reflect")
    noise_mad = 1.4826 * np.median(np.abs(hp - np.median(hp)))
    impulse = np.mean(np.abs(x - med) > 0.20)
    lap = ndi.laplace(ndi.gaussian_filter(x, 0.6, mode="reflect"), mode="reflect")
    sharpness = np.var(lap)
    gx = ndi.sobel(x, axis=1, mode="reflect"); gy = ndi.sobel(x, axis=0, mode="reflect")
    grad = np.hypot(gx, gy)
    texture = np.median(ndi.uniform_filter((x - ndi.uniform_filter(x, 7)) ** 2, 7)) ** 0.5
    contrast = np.percentile(x, 95) - np.percentile(x, 5)
    return np.asarray([noise_mad, impulse, sharpness, np.mean(grad), texture, contrast], dtype=float)


def fit_context_centroids(images, labels):
    V = np.vstack([context_vector(im) for im in images])
    labels = np.asarray(labels)
    mean = V.mean(0); std = V.std(0) + 1e-8
    Z = (V - mean) / std
    centroids = {str(lab): Z[labels == lab].mean(0).tolist() for lab in np.unique(labels)}
    return {"mean": mean.tolist(), "std": std.tolist(), "centroids": centroids}


def predict_context(img, model):
    v = (context_vector(img) - np.asarray(model["mean"])) / np.asarray(model["std"])
    best, bestd = None, np.inf
    for lab, c in model["centroids"].items():
        d = float(np.sum((v - np.asarray(c)) ** 2))
        if d < bestd:
            best, bestd = lab, d
    return best
