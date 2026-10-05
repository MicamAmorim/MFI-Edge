from __future__ import annotations

"""Edge-signature discovery utilities.

This module is intentionally diagnostic.  Ground truth is used only to discover
which image-derived properties distinguish true boundaries from difficult
non-boundaries.  The eventual detector must compute the same properties from an
unlabelled image; GT is never an inference-time input.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np
from scipy import ndimage as ndi
from scipy.optimize import minimize

from .features import gray_float, robust01

EPS = 1e-9
GROUPS = ("edge", "near_edge", "texture", "background")


@dataclass
class SignatureSamples:
    X: np.ndarray
    groups: np.ndarray
    feature_names: List[str]
    counts_per_image: List[Dict[str, object]]


def _sample_along(g: np.ndarray, nx: np.ndarray, ny: np.ndarray, radius: float):
    yy, xx = np.mgrid[: g.shape[0], : g.shape[1]]
    plus = ndi.map_coordinates(g, [yy + radius * ny, xx + radius * nx], order=1, mode="reflect")
    minus = ndi.map_coordinates(g, [yy - radius * ny, xx - radius * nx], order=1, mode="reflect")
    return plus, minus


def structural_signature_maps(image: np.ndarray, scales: Sequence[int]) -> Dict[str, np.ndarray]:
    """Compute edge-structure properties that are not tied to a specific fuzzy model."""
    g = gray_float(image)
    angle_cs = []
    angle_sn = []
    angle_w = []
    raw_grads = []
    for scale in scales:
        sigma = max(0.8, float(scale) / 12.0)
        gs = ndi.gaussian_filter(g, sigma=sigma, mode="reflect")
        gx = ndi.sobel(gs, axis=1, mode="reflect")
        gy = ndi.sobel(gs, axis=0, mode="reflect")
        mag = np.hypot(gx, gy)
        theta = np.arctan2(gy, gx)
        raw_grads.append(robust01(mag))
        angle_cs.append(mag * np.cos(2.0 * theta))
        angle_sn.append(mag * np.sin(2.0 * theta))
        angle_w.append(mag)

    den = np.sum(np.stack(angle_w, axis=-1), axis=-1) + EPS
    c = np.sum(np.stack(angle_cs, axis=-1), axis=-1) / den
    s = np.sum(np.stack(angle_sn, axis=-1), axis=-1) / den
    orientation_consistency = np.clip(np.hypot(c, s), 0.0, 1.0)

    # Geometry at a compact reference scale. Double-radius agreement rewards a
    # stable step instead of a single noisy contrast peak.
    gs = ndi.gaussian_filter(g, sigma=1.2, mode="reflect")
    gx = ndi.sobel(gs, axis=1, mode="reflect")
    gy = ndi.sobel(gs, axis=0, mode="reflect")
    mag = np.hypot(gx, gy) + EPS
    nx, ny = gx / mag, gy / mag
    tx, ty = -ny, nx

    p1, m1 = _sample_along(gs, nx, ny, 1.5)
    p2, m2 = _sample_along(gs, nx, ny, 3.0)
    tp1, tm1 = _sample_along(gs, tx, ty, 1.5)
    tp2, tm2 = _sample_along(gs, tx, ty, 3.0)
    c1, c2 = np.abs(p1 - m1), np.abs(p2 - m2)
    tc1, tc2 = np.abs(tp1 - tm1), np.abs(tp2 - tm2)
    nc = 0.5 * (c1 + c2)
    tc = 0.5 * (tc1 + tc2)
    normal_tangent_ratio = np.clip(nc / (nc + tc + EPS), 0.0, 1.0)
    step_consistency = np.clip(1.0 - np.abs(c1 - c2) / (c1 + c2 + EPS), 0.0, 1.0)
    step_likeness = robust01(nc) * normal_tangent_ratio * step_consistency

    grad_stack = np.stack(raw_grads, axis=-1)
    grad_max = np.max(grad_stack, axis=-1)
    scale_persistence = np.mean(grad_stack, axis=-1) / np.maximum(grad_max, EPS)

    return {
        "orientation_consistency": orientation_consistency.astype(np.float32),
        "normal_tangent_ratio": normal_tangent_ratio.astype(np.float32),
        "step_consistency": step_consistency.astype(np.float32),
        "step_likeness": np.asarray(step_likeness, np.float32),
        "gradient_scale_persistence": np.clip(scale_persistence, 0.0, 1.0).astype(np.float32),
    }


def signature_tensor(item: Mapping[str, object], feature_names: Sequence[str]):
    """Return HxWxF signature tensor and semantic feature names for one prepared item."""
    pre = item["features"]
    scales = [int(x[0]) for x in pre]
    arrays = [np.asarray(x[1], np.float32) for x in pre]
    stack = np.stack(arrays, axis=-2)  # H,W,scale,descriptor
    names: List[str] = []
    cols: List[np.ndarray] = []

    # Preserve scale-resolved evidence so the analysis can discover scale-specific
    # behavior instead of assuming a hierarchy in advance.
    for si, scale in enumerate(scales):
        for di, name in enumerate(feature_names):
            names.append(f"{name}_s{scale}")
            cols.append(stack[..., si, di])

    for di, name in enumerate(feature_names):
        z = stack[..., :, di]
        names.extend([f"{name}_mean", f"{name}_max", f"{name}_std"])
        cols.extend([np.mean(z, axis=-1), np.max(z, axis=-1), np.std(z, axis=-1)])

    index = {str(n): i for i, n in enumerate(feature_names)}
    if "normal_contrast" in index and "normal_minus_tangent" in index:
        nc = stack[..., :, index["normal_contrast"]]
        nmt = stack[..., :, index["normal_minus_tangent"]]
        dom = np.mean(nmt / np.maximum(nc, EPS), axis=-1)
        names.append("descriptor_normal_dominance")
        cols.append(np.clip(dom, 0.0, 1.0))

    # Coarse/fine balance is symmetric around 0.5 and therefore easier to use as
    # a fuzzy membership later than an unbounded ratio.
    if "grad" in index:
        gi = index["grad"]
        coarse_idx = [i for i, s in enumerate(scales) if s >= 13]
        fine_idx = [i for i, s in enumerate(scales) if s < 13]
        coarse = np.mean(stack[..., coarse_idx, gi], axis=-1)
        fine = np.mean(stack[..., fine_idx, gi], axis=-1)
        balance = fine / (fine + coarse + EPS)
        names.append("fine_vs_coarse_gradient")
        cols.append(np.clip(balance, 0.0, 1.0))

    structural = structural_signature_maps(np.asarray(item["pre_img"]), scales)
    for name, value in structural.items():
        names.append(name)
        cols.append(value)

    # Composite hypothesis: a true edge should be directional, persistent and
    # step-like.  This is *not* assumed to be optimal; Stage 11 explicitly tests it.
    if all(k in structural for k in ("orientation_consistency", "normal_tangent_ratio", "gradient_scale_persistence")):
        composite = (
            structural["orientation_consistency"]
            * structural["normal_tangent_ratio"]
            * structural["gradient_scale_persistence"]
        ) ** (1.0 / 3.0)
        names.append("structural_edge_consensus")
        cols.append(composite)

    tensor = np.stack(cols, axis=-1).astype(np.float32)
    tensor = np.nan_to_num(tensor, nan=0.0, posinf=1.0, neginf=0.0)
    return tensor, names


def population_masks(item: Mapping[str, object], near_radius: int = 2, far_radius: int = 4,
                     texture_quantile: float = 0.85, background_quantile: float = 0.35):
    """Build edge, near-edge, high-gradient texture and easy-background populations."""
    gt = np.asarray(item["gt"], bool)
    edge = gt.copy()
    near_outer = ndi.binary_dilation(gt, iterations=max(int(near_radius), 1))
    near = near_outer & ~gt
    far = ~ndi.binary_dilation(gt, iterations=max(int(far_radius), int(near_radius) + 1))

    # Use the finest gradient descriptor only to define difficult negatives.  It is
    # a sampling device, not a feature-selection target.
    pre = item["features"]
    fine = min(pre, key=lambda x: int(x[0]))
    grad = np.asarray(fine[1], float)[..., 0]
    fv = grad[far]
    if fv.size:
        tq = float(np.quantile(fv, texture_quantile))
        bq = float(np.quantile(fv, background_quantile))
    else:
        tq, bq = 1.0, 0.0
    texture = far & (grad >= tq)
    background = far & (grad <= bq)
    return {"edge": edge, "near_edge": near, "texture": texture, "background": background}


def _sample_mask(mask: np.ndarray, max_samples: int, rng: np.random.Generator):
    ids = np.flatnonzero(np.asarray(mask, bool).ravel())
    if ids.size > int(max_samples):
        ids = rng.choice(ids, size=int(max_samples), replace=False)
    return np.asarray(ids, dtype=np.int64)


def extract_signature_samples(items: Sequence[Mapping[str, object]], feature_names: Sequence[str],
                              max_samples_per_group: int = 2500, seed: int = 20261005) -> SignatureSamples:
    Xs, gs = [], []
    counts: List[Dict[str, object]] = []
    final_names: List[str] | None = None
    for ii, item in enumerate(items):
        tensor, names = signature_tensor(item, feature_names)
        if final_names is None:
            final_names = names
        elif names != final_names:
            raise RuntimeError("signature feature names changed across images")
        masks = population_masks(item)
        row: Dict[str, object] = {"id": str(item["id"])}
        flat = tensor.reshape(-1, tensor.shape[-1])
        for gi, group in enumerate(GROUPS):
            rng = np.random.default_rng(int(seed) + 1009 * ii + 97 * gi)
            ids = _sample_mask(masks[group], max_samples_per_group, rng)
            row[group] = int(ids.size)
            if ids.size:
                Xs.append(flat[ids].astype(np.float32, copy=False))
                gs.append(np.full(ids.size, gi, dtype=np.int8))
        counts.append(row)
    if not Xs:
        raise RuntimeError("no signature samples were extracted")
    return SignatureSamples(
        X=np.concatenate(Xs, axis=0),
        groups=np.concatenate(gs, axis=0),
        feature_names=list(final_names or []),
        counts_per_image=counts,
    )


def binary_auc(score: np.ndarray, target: np.ndarray) -> float:
    s = np.asarray(score, float).ravel()
    y = np.asarray(target, bool).ravel()
    finite = np.isfinite(s)
    s, y = s[finite], y[finite]
    np1, nn = int(y.sum()), int((~y).sum())
    if np1 == 0 or nn == 0:
        return 0.5
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(s) + 1, dtype=float)
    u = float(ranks[y].sum() - np1 * (np1 + 1) / 2.0)
    return float(np.clip(u / (np1 * nn), 0.0, 1.0))


def average_precision_binary(score: np.ndarray, target: np.ndarray) -> float:
    s = np.asarray(score, float).ravel()
    y = np.asarray(target, bool).ravel()
    finite = np.isfinite(s)
    s, y = s[finite], y[finite]
    npos = int(y.sum())
    if npos == 0:
        return 0.0
    order = np.argsort(-s, kind="mergesort")
    ys = y[order].astype(float)
    precision = np.cumsum(ys) / np.arange(1, len(ys) + 1)
    return float(np.sum(precision * ys) / npos)


def mutual_information_binary(score: np.ndarray, target: np.ndarray, bins: int = 16) -> float:
    s = np.asarray(score, float).ravel()
    y = np.asarray(target, bool).ravel().astype(int)
    finite = np.isfinite(s)
    s, y = s[finite], y[finite]
    if len(s) < 20 or len(np.unique(y)) < 2:
        return 0.0
    edges = np.unique(np.quantile(s, np.linspace(0, 1, int(bins) + 1)))
    if len(edges) <= 2:
        return 0.0
    xb = np.clip(np.digitize(s, edges[1:-1], right=False), 0, len(edges) - 2)
    joint = np.zeros((len(edges) - 1, 2), dtype=float)
    np.add.at(joint, (xb, y), 1.0)
    joint /= max(joint.sum(), 1.0)
    px = joint.sum(axis=1, keepdims=True)
    py = joint.sum(axis=0, keepdims=True)
    expected = px @ py
    nz = joint > 0
    return float(np.sum(joint[nz] * np.log((joint[nz] + EPS) / (expected[nz] + EPS))))


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return 0.0
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    pooled = np.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / max(len(a) + len(b) - 2, 1))
    return float((np.mean(a) - np.mean(b)) / max(pooled, EPS))


def pair_summary(samples: SignatureSamples, negative_group: str) -> List[Dict[str, float | str]]:
    if negative_group not in GROUPS or negative_group == "edge":
        raise ValueError(negative_group)
    edge_code, neg_code = GROUPS.index("edge"), GROUPS.index(negative_group)
    keep = (samples.groups == edge_code) | (samples.groups == neg_code)
    y = samples.groups[keep] == edge_code
    X = samples.X[keep]
    rows: List[Dict[str, float | str]] = []
    for j, name in enumerate(samples.feature_names):
        s = X[:, j]
        auc = binary_auc(s, y)
        direction = 1.0 if auc >= 0.5 else -1.0
        oriented = direction * s
        rows.append({
            "feature": name,
            "negative_group": negative_group,
            "auc_raw": float(auc),
            "auc_separation": float(max(auc, 1.0 - auc)),
            "direction": float(direction),
            "ap_oriented": average_precision_binary(oriented, y),
            "mutual_information": mutual_information_binary(s, y),
            "cohens_d": cohens_d(s[y], s[~y]),
            "edge_mean": float(np.mean(s[y])),
            "edge_median": float(np.median(s[y])),
            "negative_mean": float(np.mean(s[~y])),
            "negative_median": float(np.median(s[~y])),
        })
    return rows


def feature_group_statistics(samples: SignatureSamples) -> List[Dict[str, float | str]]:
    rows: List[Dict[str, float | str]] = []
    for gi, group in enumerate(GROUPS):
        x = samples.X[samples.groups == gi]
        if not len(x):
            continue
        for j, name in enumerate(samples.feature_names):
            v = x[:, j]
            rows.append({
                "group": group, "feature": name, "n": int(len(v)),
                "mean": float(np.mean(v)), "std": float(np.std(v)),
                "q10": float(np.quantile(v, 0.10)), "q25": float(np.quantile(v, 0.25)),
                "median": float(np.median(v)), "q75": float(np.quantile(v, 0.75)),
                "q90": float(np.quantile(v, 0.90)),
            })
    return rows


def correlation_matrix(samples: SignatureSamples, hard_negative_groups=("near_edge", "texture")) -> np.ndarray:
    codes = [GROUPS.index("edge")] + [GROUPS.index(x) for x in hard_negative_groups]
    keep = np.isin(samples.groups, codes)
    return np.nan_to_num(np.corrcoef(samples.X[keep], rowvar=False), nan=0.0)


def select_candidate_signature(samples: SignatureSamples, texture_rows: Sequence[Mapping[str, object]],
                               near_rows: Sequence[Mapping[str, object]], max_features: int = 8,
                               max_abs_corr: float = 0.92):
    by_t = {str(r["feature"]): r for r in texture_rows}
    by_n = {str(r["feature"]): r for r in near_rows}
    ranked = []
    for name in samples.feature_names:
        t, n = by_t[name], by_n[name]
        direction_agrees = float(t["direction"]) == float(n["direction"])
        robustness = 0.65 * float(t["auc_separation"]) + 0.35 * float(n["auc_separation"])
        if not direction_agrees:
            robustness *= 0.75
        ranked.append((robustness, name, t, n))
    ranked.sort(reverse=True, key=lambda z: z[0])

    corr = correlation_matrix(samples)
    idx = {name: i for i, name in enumerate(samples.feature_names)}
    chosen = []
    for robustness, name, t, n in ranked:
        j = idx[name]
        if any(abs(float(corr[j, idx[c["feature"]]])) > float(max_abs_corr) for c in chosen):
            continue
        edge_vals = samples.X[samples.groups == GROUPS.index("edge"), j]
        hard_vals = samples.X[np.isin(samples.groups, [GROUPS.index("near_edge"), GROUPS.index("texture")]), j]
        edge_med = float(np.median(edge_vals))
        hard_med = float(np.median(hard_vals))
        direction = 1.0 if edge_med >= hard_med else -1.0
        q25, q75 = np.quantile(np.concatenate([edge_vals, hard_vals]), [0.25, 0.75])
        scale = float(max(q75 - q25, 0.05))
        chosen.append({
            "feature": name,
            "weight": float(robustness),
            "direction": direction,
            "midpoint": float(0.5 * (edge_med + hard_med)),
            "scale": scale,
            "edge_median": edge_med,
            "hard_negative_median": hard_med,
            "texture_auc": float(t["auc_separation"]),
            "near_auc": float(n["auc_separation"]),
        })
        if len(chosen) >= int(max_features):
            break
    total = sum(float(x["weight"]) for x in chosen) or 1.0
    for x in chosen:
        x["weight"] = float(x["weight"]) / total
    return chosen


def analytical_signature_score(X: np.ndarray, feature_names: Sequence[str], spec: Sequence[Mapping[str, object]]) -> np.ndarray:
    index = {str(n): i for i, n in enumerate(feature_names)}
    out = np.zeros(len(X), dtype=float)
    for row in spec:
        x = np.asarray(X[:, index[str(row["feature"])]], float)
        z = float(row["direction"]) * (x - float(row["midpoint"])) / max(float(row["scale"]), EPS)
        membership = 1.0 / (1.0 + np.exp(-np.clip(z, -20.0, 20.0)))
        out += float(row["weight"]) * membership
    return np.asarray(out, np.float32)


def diagnostic_metrics(samples: SignatureSamples, score: np.ndarray, negative_groups=("near_edge", "texture")):
    edge_code = GROUPS.index("edge")
    neg_codes = [GROUPS.index(x) for x in negative_groups]
    keep = (samples.groups == edge_code) | np.isin(samples.groups, neg_codes)
    y = samples.groups[keep] == edge_code
    s = np.asarray(score)[keep]
    auc = binary_auc(s, y)
    if auc < 0.5:
        s = -s
        auc = 1.0 - auc
    return {"auc": float(auc), "ap": average_precision_binary(s, y), "n": int(len(s)), "n_edge": int(y.sum())}


def fit_logistic_diagnostic(train: SignatureSamples, negative_groups=("near_edge", "texture"), l2: float = 1.0):
    """Small diagnostic upper bound; never treated as the proposed detector."""
    edge_code = GROUPS.index("edge")
    neg_codes = [GROUPS.index(x) for x in negative_groups]
    keep = (train.groups == edge_code) | np.isin(train.groups, neg_codes)
    X = np.asarray(train.X[keep], float)
    y = (train.groups[keep] == edge_code).astype(float)
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd < 1e-6] = 1.0
    Z = (X - mu) / sd

    # Class balancing makes the diagnostic insensitive to sample-count choices.
    pos = max(float(y.sum()), 1.0)
    neg = max(float((1.0 - y).sum()), 1.0)
    sw = np.where(y > 0.5, 0.5 / pos, 0.5 / neg)

    def fun(theta):
        w, b = theta[:-1], theta[-1]
        z = np.clip(Z @ w + b, -30.0, 30.0)
        p = 1.0 / (1.0 + np.exp(-z))
        loss = -np.sum(sw * (y * np.log(p + EPS) + (1.0 - y) * np.log(1.0 - p + EPS)))
        reg = 0.5 * float(l2) * float(np.dot(w, w)) / max(len(w), 1)
        return float(loss + reg)

    init = np.zeros(Z.shape[1] + 1, dtype=float)
    opt = minimize(fun, init, method="L-BFGS-B", options={"maxiter": 250, "ftol": 1e-9})
    return {"weights": opt.x[:-1], "bias": float(opt.x[-1]), "mean": mu, "std": sd,
            "success": bool(opt.success), "message": str(opt.message), "objective": float(opt.fun)}


def logistic_score(samples: SignatureSamples, model: Mapping[str, object]) -> np.ndarray:
    X = np.asarray(samples.X, float)
    Z = (X - np.asarray(model["mean"], float)) / np.asarray(model["std"], float)
    z = np.clip(Z @ np.asarray(model["weights"], float) + float(model["bias"]), -30.0, 30.0)
    return (1.0 / (1.0 + np.exp(-z))).astype(np.float32)
