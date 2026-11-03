from __future__ import annotations
"""Controlled aggregation, suppression and thinning for Paper A recertification.

Scientific scores stay float32. GT is never resized. Binary thinning is only a
UDED diagnostic; official BSDS uses the pinned Berkeley thinpb procedure.
"""
from itertools import combinations
import hashlib
import json

import numpy as np
from scipy.optimize import minimize, nnls
from scipy.ndimage import gaussian_filter
from scipy.special import expit
from skimage.morphology import thin

from src.postprocess import gradient_orientation, non_maximum_suppression
from src.stage24_integrity import (
    one_to_one_boundary_counts, canonical_threshold_candidates, aggregate_counts,
)
from src.stage24_residual import (
    apply_membership, fit_membership, fit_nonnegative_fusion,
    apply_nonnegative_fusion, fit_residual_gate, apply_suppressor,
)

AGGREGATORS = (
    "equal_mean", "minimum", "maximum", "median", "product",
    "lukasiewicz",
    "weighted_mean", "nonnegative_logistic",
    "owa_centered", "owa_median", "owa_optimistic", "owa_pessimistic", "owa_learned",
    "choquet_additive", "choquet_positive_2add", "choquet_signed_2add",
    "choquet_distorted_055", "choquet_generalized_055", "choquet_generalized_150",
    "sugeno_additive", "sugeno_positive_2add",
)
THINNING = ("raw", "nms_image", "binary_thin_diagnostic")
CALIBRATION_MODES = ("legacy_sigmoid", "zero_anchored")
SUPPRESSORS = (
    ("identity", 1.0), ("disagreement", 0.5), ("disagreement", 1.0),
    ("local_coherence", 2.0), ("local_coherence", 4.0), ("compress", 1.5),
    ("learned_gate", 0.5), ("learned_gate", 1.0), ("learned_gate", 2.0),
)
SEED = 20261104


def deterministic_seed(*parts):
    return int.from_bytes(
        hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:4], "little"
    ) & 0x7fffffff


def _sample_training(maps, gts, indices, limit=12000, seed=SEED):
    """Balanced, deterministic, exact-GT supervised sampling; train indices only."""
    x = np.concatenate([np.asarray(maps[int(i)], np.float32).reshape(-1, maps[0].shape[-1])
                        for i in indices], axis=0)
    y = np.concatenate([np.asarray(gts[int(i)], bool).ravel()
                        for i in indices])
    pos, neg = np.flatnonzero(y), np.flatnonzero(~y)
    if not len(pos) or not len(neg):
        raise ValueError("Cannot fit an aggregation capacity without both GT classes")
    rng = np.random.default_rng(seed)
    n = min(len(pos), len(neg), limit // 2)
    ix = np.r_[rng.choice(pos, n, replace=False), rng.choice(neg, n, replace=False)]
    rng.shuffle(ix)
    return x[ix].astype(np.float64), y[ix].astype(np.float64)


def simplex_fit(x, y):
    """Nonnegative L2 coefficients, simplex projection; no validation labels."""
    w, _ = nnls(np.asarray(x, float), np.asarray(y, float))
    if w.sum() <= 1e-10:
        w = np.ones(x.shape[1])
    return np.asarray(w / w.sum(), float)


def _pair_features(x):
    return np.stack([np.minimum(x[..., i], x[..., j])
                     for i, j in combinations(range(x.shape[-1]), 2)], axis=-1)


def capacity_coefficients(x, y, signed=False):
    """Möbius 2-additive capacity. Signed variant enforces every monotonic increment."""
    n = x.shape[-1]
    if n not in (2, 3):
        raise ValueError("Capacity learning restricted to pairs or triples")
    features = np.concatenate([x, _pair_features(x)], axis=1)
    w0 = simplex_fit(features, y)
    if not signed:
        return w0

    pairs = tuple(combinations(range(n), 2))
    linear = []
    for i in range(n):
        others = [j for j in range(n) if i != j]
        for k in range(len(others) + 1):
            for sub in combinations(others, k):
                row = np.zeros(n + len(pairs))
                row[i] = 1.
                for j in sub:
                    row[n + pairs.index(tuple(sorted((i, j))))] = 1.
                linear.append(row)
    constraints = [{"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0),
                    "jac": lambda w: np.ones_like(w)}]
    constraints.extend({"type": "ineq", "fun": lambda w, row=row: float(row @ w),
                        "jac": lambda w, row=row: row} for row in linear)
    objective = lambda w: float(np.mean((features @ w - y) ** 2) + 1e-4 * (w @ w))
    jac = lambda w: (2 * features.T @ (features @ w - y) / len(y) + 2e-4*w)
    result = minimize(objective, w0, jac=jac, constraints=constraints,
                      method="SLSQP", options={"maxiter": 250, "ftol": 1e-9})
    if not result.success or abs(float(result.x.sum()) - 1) > 1e-5:
        raise RuntimeError("Signed capacity optimization failed: " + result.message)
    if min(float(row @ result.x) for row in linear) < -1e-5:
        raise RuntimeError("Learned signed capacity is not monotone")
    return np.asarray(result.x, float)


def capacity_from_mobius(coef, n):
    values = np.zeros(1 << n, dtype=float)
    pairs = tuple(combinations(range(n), 2))
    for mask in range(1, 1 << n):
        values[mask] = sum(coef[i] for i in range(n) if mask & (1 << i))
        values[mask] += sum(coef[n + k] for k, (i, j) in enumerate(pairs)
                            if (mask & (1 << i)) and (mask & (1 << j)))
    if abs(values[-1] - 1) > 1e-4:
        raise RuntimeError("Capacity is not normalized")
    for mask in range(1 << n):
        for i in range(n):
            if not mask & (1 << i) and values[mask | (1 << i)] < values[mask] - 1e-5:
                raise RuntimeError("Capacity is not monotone")
    return values


def choquet(x, cap):
    n = x.shape[-1]
    order = np.argsort(x, axis=-1)
    sorted_x = np.take_along_axis(x, order, axis=-1)
    out = np.zeros(x.shape[:-1], dtype=float)
    previous = np.zeros_like(out)
    for j in range(n):
        masks = np.zeros(x.shape[:-1], np.int32)
        for k in range(j, n):
            masks |= 1 << order[..., k]
        value = sorted_x[..., j]
        out += (value - previous) * cap[masks]
        previous = value
    return out


def sugeno(x, cap):
    n = x.shape[-1]
    out = np.zeros(x.shape[:-1], dtype=float)
    for mask in range(1, 1 << n):
        mins = np.min(x[..., [i for i in range(n) if mask & (1 << i)]], axis=-1)
        out = np.maximum(out, np.minimum(mins, cap[mask]))
    return out


def fit_aggregator(name, memberships, gts, train, seed=SEED):
    if name not in AGGREGATORS:
        raise ValueError(name)
    n = memberships[0].shape[-1]
    state = {"family": name, "n_inputs": n}
    if name == "nonnegative_logistic":
        # The caller supplies the memberships as normalized evidence maps.
        x, y = _sample_training(memberships, gts, train, seed=seed)
        from src.stage24_residual import _fit_logistic
        state["logistic"] = _fit_logistic(x, y, nonnegative=True).to_dict()
    elif name in ("weighted_mean", "owa_learned", "choquet_additive",
                  "choquet_positive_2add", "choquet_signed_2add",
                  "sugeno_additive", "sugeno_positive_2add",
                  "choquet_generalized_055", "choquet_generalized_150"):
        x, y = _sample_training(memberships, gts, train, seed=seed)
        if name == "owa_learned":
            weights = simplex_fit(np.sort(x, axis=1)[:, ::-1], y)
            state["weights"] = weights.tolist()
        elif name in ("choquet_positive_2add", "sugeno_positive_2add",
                      "choquet_generalized_055", "choquet_generalized_150",
                      "choquet_signed_2add"):
            signed = name == "choquet_signed_2add"
            if name.startswith("choquet_generalized"):
                gamma = 0.55 if name.endswith("055") else 1.5
                x = x ** gamma
            co = capacity_coefficients(x, y, signed=signed)
            state["capacity"] = capacity_from_mobius(co, n).tolist()
            state["mobius"] = co.tolist()
        else:
            weights = simplex_fit(x, y)
            state["weights"] = weights.tolist()
    return state


def apply_aggregator(membership, state):
    m = np.asarray(membership, dtype=float)
    n = m.shape[-1]
    if n != state["n_inputs"]:
        raise ValueError("Aggregation arity mismatch")
    kind = state["family"]
    if kind == "equal_mean": out = np.mean(m, axis=-1)
    elif kind == "minimum": out = np.min(m, axis=-1)
    elif kind == "maximum": out = np.max(m, axis=-1)
    elif kind == "median": out = np.median(m, axis=-1)
    elif kind == "product": out = np.prod(m, axis=-1)
    elif kind == "lukasiewicz": out = lukasiewicz_tnorm(m)
    elif kind in ("weighted_mean", "choquet_additive"):
        out = np.tensordot(m, np.asarray(state["weights"]), axes=([-1], [0]))
    elif kind == "nonnegative_logistic":
        from src.stage24_residual import LogisticModel
        out = apply_nonnegative_fusion(m, LogisticModel(np.asarray(state["logistic"]["beta"])))
    elif kind.startswith("owa_"):
        if kind == "owa_optimistic": weights = np.array([1.0] + [0.] * (n-1))
        elif kind == "owa_pessimistic": weights = np.array([0.] * (n-1) + [1.])
        elif kind == "owa_centered": weights = np.ones(n) / n
        elif kind == "owa_median":
            weights = np.zeros(n)
            if n % 2: weights[n//2] = 1.
            else: weights[n//2-1:n//2+1] = .5
        else: weights = np.asarray(state["weights"])
        out = np.tensordot(np.sort(m, axis=-1)[..., ::-1], weights, axes=([-1], [0]))
    elif kind == "choquet_distorted_055":
        cap = np.asarray([(int(mask).bit_count() / n) ** .55 for mask in range(1 << n)])
        out = choquet(m, cap)
    elif kind.startswith("choquet_"):
        if kind.startswith("choquet_generalized"):
            gamma = .55 if kind.endswith("055") else 1.5
            out = np.maximum(choquet(m ** gamma, np.asarray(state["capacity"])), 0) ** (1 / gamma)
        else:
            out = choquet(m, np.asarray(state["capacity"]))
    elif kind.startswith("sugeno_"):
        if kind == "sugeno_additive":
            weights = np.asarray(state["weights"])
            cap = np.array([sum(weights[i] for i in range(n) if mask & (1<<i))
                            for mask in range(1 << n)])
        else:
            cap = np.asarray(state["capacity"])
        out = sugeno(m, cap)
    else:
        raise KeyError(kind)
    out = np.asarray(out, np.float32)
    if not np.isfinite(out).all():
        raise RuntimeError("Nonfinite aggregator result")
    return np.clip(out, 0, 1)


def calibrate_memberships(membership_map, model, mode="legacy_sigmoid"):
    """Train-fitted calibration with exact zero-evidence baseline anchored to zero.

    'legacy_sigmoid' reproduces Stage24 sigmoid memberships.
    'zero_anchored' removes the fitted sigmoid response to a zero descriptor.
    This is monotone and nonnegative; it does NOT assert probability calibration.
    """
    m = np.asarray(membership_map, dtype=np.float32)
    if mode == "legacy_sigmoid":
        return m
    if mode != "zero_anchored":
        raise ValueError("Unknown membership calibration: " + str(mode))
    midpoint = np.asarray(model.midpoint, dtype=float)
    scale = np.maximum(np.asarray(model.scale, dtype=float), 1e-6)
    baseline = expit(-midpoint / scale)
    out = (np.asarray(m, dtype=float) - baseline) / np.maximum(1.0 - baseline, 1e-9)
    return np.asarray(np.clip(out, 0.0, 1.0), dtype=np.float32)


def score_distribution_diagnostics(score, image_id, label):
    """Auditable score concentration, quantization and saturation diagnostics."""
    s = np.asarray(score, dtype=float).ravel()
    s = s[np.isfinite(s)]
    if len(s) == 0:
        raise ValueError("Empty score map")
    levels = np.unique(np.rint(np.clip(s, 0, 1) * 255).astype(np.uint8))
    qs = np.quantile(s, [.01,.05,.25,.50,.75,.95,.99])
    return {"image_id": image_id, "label": label, "count": len(s),
            "fraction_exact_zero": float(np.mean(s <= 1e-7)),
            "fraction_near_half_001": float(np.mean(np.abs(s-.5) <= .01)),
            "q01": float(qs[0]), "q05": float(qs[1]), "q25": float(qs[2]),
            "median": float(qs[3]), "q75": float(qs[4]), "q95": float(qs[5]),
            "q99": float(qs[6]), "p95_p05_span": float(qs[5]-qs[1]),
            "distinct_quantized_8bit_levels": int(len(levels)),
            "raw_distinct_float_levels": int(len(np.unique(s)))}


def quantile_mapping_fit(scores, n=256):
    """Fit strictly monotone global score remapping on UDED only.

    A monotone mapping does not change the ranking before export; the fixed
    Berkeley 99-threshold grid and 8-bit quantization may change its AP.
    """
    all_scores = np.concatenate([np.asarray(s,float).ravel() for s in scores])
    if not np.isfinite(all_scores).all():
        raise ValueError("Nonfinite UDED scores in quantile mapping")
    quantiles = np.quantile(all_scores, np.linspace(0,1,int(n)))
    values, first_indices = np.unique(quantiles, return_index=True)
    if values.size < 3:
        raise ValueError("Degenerate quantile mapping")
    ranks = first_indices/(len(quantiles)-1)
    return {"score_values": values.tolist(), "mapped_quantiles": ranks.tolist(),
            "fitted_on": "UDED_selection_only"}


def quantile_mapping_apply(score, calibration):
    x = np.asarray(score,dtype=np.float32)
    vals = np.asarray(calibration["score_values"], float)
    ranks = np.asarray(calibration["mapped_quantiles"], float)
    return np.asarray(np.interp(x, vals, ranks, left=0., right=1.),dtype=np.float32)


def lukasiewicz_tnorm(membership_map):
    """Canonical n-ary Łukasiewicz conjunction: max(0, sum(x_i)-n+1)."""
    m=np.asarray(membership_map,float)
    return np.asarray(np.maximum(0.0,np.sum(m,axis=-1)-m.shape[-1]+1.0),np.float32)


def thin_score(score, mode, image):
    """Float-map geometry. Berkeley thinning is not approximated here."""
    s = np.asarray(score, np.float32)
    if mode == "raw" or mode == "binary_thin_diagnostic":
        return s
    if mode != "nms_image":
        raise ValueError(mode)
    ori = gradient_orientation(image, sigma=1.0)
    if ori.shape != s.shape:
        raise ValueError("NMS image/score geometry mismatch")
    return np.asarray(non_maximum_suppression(s, ori), np.float32)


def binary_map(thinned_score, threshold, mode):
    binary = np.asarray(thinned_score) >= float(threshold)
    if mode == "binary_thin_diagnostic":
        return thin(binary)
    return binary


def evaluate_at(scores, gts, images, threshold, mode, tolerance=0.0075):
    counts = [one_to_one_boundary_counts(
        binary_map(thin_score(s, mode, im), threshold, mode), gt,
        tolerance_ratio=tolerance,
    ) for s, gt, im in zip(scores, gts, images)]
    return aggregate_counts(counts), counts


def choose_threshold(scores, gts, images, mode, count=21):
    processed = [thin_score(s, mode, im) for s, im in zip(scores, images)]
    thresholds = canonical_threshold_candidates(processed, count=count)
    # Avoid a zero threshold classifying the entire image as positive.
    thresholds = [float(t) for t in thresholds if t > 1e-7]
    if not thresholds:
        thresholds = [0.5]
    best = None
    for t in thresholds:
        vals = [one_to_one_boundary_counts(binary_map(p, t, mode), g)
                for p, g in zip(processed, gts)]
        c = aggregate_counts(vals)
        key = (c.f1, c.precision, c.recall, t)
        if best is None or key > best[0]:
            best = (key, c, t)
    _, c, t = best
    return float(t), c


def serialize_model(pair, membership, agg, suppression, mode, gate=None,
                    calibration_mode="legacy_sigmoid"):
    return {
        "descriptors": list(pair), "membership": membership.to_dict(),
        "aggregator": agg, "suppression": list(suppression),
        "thinning": mode, "gate": gate.to_dict() if gate is not None else None,
        "calibration_mode": calibration_mode,
        "GT": "native",
    }


def inference_recipe(cues, model, image):
    from src.stage24_residual import MembershipModel, LogisticModel
    mem = model["membership"]
    membership = apply_membership(cues, MembershipModel(
        np.asarray(mem["midpoint"]), np.asarray(mem["scale"])))
    membership = calibrate_memberships(membership, MembershipModel(
        np.asarray(mem["midpoint"]), np.asarray(mem["scale"])),
        model.get("calibration_mode","legacy_sigmoid"))
    base = apply_aggregator(membership, model["aggregator"])
    gate = model.get("gate")
    gate_obj = None if gate is None else LogisticModel(np.asarray(gate["beta"]),
                    np.asarray(gate["mean"]), np.asarray(gate["scale"]))
    name, strength = model["suppression"]
    output = apply_suppressor(base, membership, kind=name,
                              parameter=strength, gate_model=gate_obj)
    return thin_score(output, model["thinning"], image)
