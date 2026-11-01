from __future__ import annotations

"""Stage 24 train-only aggregation and residual/error suppression primitives."""

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
from scipy.special import expit

EPS = 1e-6


@dataclass
class MembershipModel:
    midpoint: np.ndarray
    scale: np.ndarray

    def to_dict(self) -> dict:
        return {"midpoint": self.midpoint.tolist(), "scale": self.scale.tolist()}


@dataclass
class LogisticModel:
    beta: np.ndarray
    mean: np.ndarray | None = None
    scale: np.ndarray | None = None

    def to_dict(self) -> dict:
        d = {"beta": self.beta.tolist()}
        if self.mean is not None:
            d["mean"] = self.mean.tolist()
        if self.scale is not None:
            d["scale"] = self.scale.tolist()
        return d


def _stack_pixels(cue_sets: Sequence[Sequence[np.ndarray]], indices: Sequence[int]) -> np.ndarray:
    return np.concatenate([
        np.stack([np.asarray(cue_sets[c][int(i)], float) for c in range(len(cue_sets))], axis=-1).reshape(-1, len(cue_sets))
        for i in indices
    ], axis=0)


def _stack_gt(gts: Sequence[np.ndarray], indices: Sequence[int]) -> np.ndarray:
    return np.concatenate([np.asarray(gts[int(i)], bool).ravel() for i in indices]).astype(float)


def fit_membership(cue_sets, gts, indices) -> MembershipModel:
    """Robust cue normalization fitted only on exact native-GT labels."""
    x = _stack_pixels(cue_sets, indices)
    y = _stack_gt(gts, indices).astype(bool)
    midpoint, scale = [], []
    for j in range(x.shape[1]):
        col = x[:, j]
        pos, neg = col[y], col[~y]
        mid = 0.5 * (float(np.median(pos)) + float(np.median(neg))) if pos.size and neg.size else float(np.median(col))
        q25, q75 = np.quantile(col, [0.25, 0.75])
        s = max(float(q75 - q25), 0.05 * max(float(np.ptp(col)), 1.0), 1e-4)
        midpoint.append(mid); scale.append(s)
    return MembershipModel(np.asarray(midpoint, float), np.asarray(scale, float))


def apply_membership(cues: Sequence[np.ndarray], model: MembershipModel) -> np.ndarray:
    x = np.stack([np.asarray(c, float) for c in cues], axis=-1)
    z = np.clip((x - model.midpoint) / np.maximum(model.scale, EPS), -20.0, 20.0)
    return np.asarray(expit(z), dtype=np.float32)


def _balanced_sample(x: np.ndarray, y: np.ndarray, n: int, seed: int):
    yb = np.asarray(y, bool)
    pos, neg = np.flatnonzero(yb), np.flatnonzero(~yb)
    if pos.size == 0 or neg.size == 0:
        take = np.arange(min(len(y), n)); return x[take], y[take].astype(float)
    per = min(pos.size, neg.size, max(1, n // 2))
    rng = np.random.default_rng(seed)
    idx = np.concatenate([rng.choice(pos, per, replace=False), rng.choice(neg, per, replace=False)])
    rng.shuffle(idx)
    return x[idx], y[idx].astype(float)


def _fit_logistic(x: np.ndarray, y: np.ndarray, *, nonnegative: bool, ridge: float = 1e-3) -> LogisticModel:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 2 or y.ndim != 1 or len(x) != len(y):
        raise ValueError("invalid logistic inputs")

    def objective(beta):
        z = beta[0] + x @ beta[1:]
        loss = np.logaddexp(0.0, z) - y * z
        p = expit(z)
        grad = np.empty_like(beta)
        grad[0] = np.mean(p - y)
        grad[1:] = (x.T @ (p - y)) / len(y) + ridge * beta[1:]
        value = float(np.mean(loss) + 0.5 * ridge * np.dot(beta[1:], beta[1:]))
        return value, grad

    bounds = [(None, None)] + ([(0.0, None)] if nonnegative else [(None, None)]) * x.shape[1]
    result = minimize(lambda b: objective(b)[0], np.zeros(x.shape[1] + 1), jac=lambda b: objective(b)[1],
                      method="L-BFGS-B", bounds=bounds, options={"maxiter": 400, "ftol": 1e-10})
    if not result.success or not np.all(np.isfinite(result.x)):
        raise RuntimeError(f"logistic fit failed: {result.message}")
    return LogisticModel(np.asarray(result.x, float))


def fit_nonnegative_fusion(cue_sets, gts, indices, membership, *, max_samples=30000, seed=20261101):
    xs, ys = [], []
    for i in indices:
        i = int(i)
        m = apply_membership([cue_sets[c][i] for c in range(len(cue_sets))], membership)
        xs.append(m.reshape(-1, m.shape[-1])); ys.append(np.asarray(gts[i], bool).ravel())
    x, y = _balanced_sample(np.concatenate(xs), np.concatenate(ys), max_samples, seed)
    return _fit_logistic(x, y, nonnegative=True)


def apply_nonnegative_fusion(membership_map, model):
    m = np.asarray(membership_map, float)
    return np.asarray(expit(model.beta[0] + m @ model.beta[1:]), dtype=np.float32)


def aggregate_memberships(m, kind, logistic=None):
    if kind == "equal_mean": out = np.mean(m, axis=-1)
    elif kind == "minimum": out = np.min(m, axis=-1)
    elif kind == "maximum": out = np.max(m, axis=-1)
    elif kind == "median": out = np.median(m, axis=-1)
    elif kind == "nonnegative_logistic":
        if logistic is None: raise ValueError("logistic model required")
        out = apply_nonnegative_fusion(m, logistic)
    else: raise KeyError(kind)
    return np.asarray(np.clip(out, 0.0, 1.0), dtype=np.float32)


def residual_features(fusion, membership_map):
    f, m = np.asarray(fusion, np.float32), np.asarray(membership_map, np.float32)
    local = gaussian_filter(f, 1.0)
    local_sq = gaussian_filter(f * f, 1.0)
    std = np.sqrt(np.maximum(local_sq - local * local, 0.0))
    cue_min, cue_max, cue_mean = np.min(m, -1), np.max(m, -1), np.mean(m, -1)
    return np.stack([f, local, std, np.abs(f-local), cue_min, cue_max, cue_mean, cue_max-cue_min], axis=-1).astype(np.float32)


def fit_residual_gate(fusions, memberships, gts, indices, *, max_samples=40000, seed=20261101):
    x = np.concatenate([residual_features(fusions[int(i)], memberships[int(i)]).reshape(-1, 8) for i in indices])
    y = np.concatenate([np.asarray(gts[int(i)], bool).ravel() for i in indices])
    x, y = _balanced_sample(x, y, max_samples, seed)
    mean, scale = np.mean(x, 0), np.std(x, 0)
    scale = np.where(scale < 1e-6, 1.0, scale)
    model = _fit_logistic((x - mean) / scale, y, nonnegative=False)
    model.mean, model.scale = mean, scale
    return model


def gate_probability(fusion, membership_map, model):
    if model.mean is None or model.scale is None: raise ValueError("gate model lacks standardization")
    x = residual_features(fusion, membership_map)
    z = (x - model.mean) / np.maximum(model.scale, EPS)
    return np.asarray(np.clip(expit(model.beta[0] + z @ model.beta[1:]), 0, 1), dtype=np.float32)


def apply_suppressor(fusion, membership_map, *, kind, parameter=1.0, gate_model=None):
    f, m, p = np.asarray(fusion, np.float32), np.asarray(membership_map, np.float32), float(parameter)
    if kind == "identity": out = f
    elif kind == "local_coherence": out = f * np.power(np.clip(gaussian_filter(f, 1.0), EPS, 1.0), p)
    elif kind == "disagreement": out = f * np.exp(-p * (np.max(m, -1) - np.min(m, -1)))
    elif kind == "compress": out = np.power(np.clip(f, 0, 1), max(p, EPS))
    elif kind == "learned_gate":
        if gate_model is None: raise ValueError("gate model required")
        out = f * np.power(np.clip(gate_probability(f, m, gate_model), EPS, 1.0), p)
    else: raise KeyError(kind)
    return np.asarray(np.clip(out, 0, 1), dtype=np.float32)


def model_hash(*models) -> str:
    payload = [m.to_dict() if hasattr(m, "to_dict") else m for m in models]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
