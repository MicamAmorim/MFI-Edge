from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np

from .advanced_fusion import tied_percentile
from .context_maps import ContextMaps, analyze_context, regime_soft_weights
from .dynamic_localizer import LocalizerResult, dynamic_localizer, oriented_nms
from .fuzzy_measures import tail_capacities
from .hybrid import percentile_confidence
from .operators import FUNCTIONS
from .pipeline import aggregate_features, empirical_surprisal, precompute_multiscale_features
from .shapley_gating import (
    apply_descriptor_gate,
    apply_spatial_gate,
    regime_gate,
    soft_gate_from_importance,
)

EPS = 1e-9
DEFAULT_SCALES = (25, 13, 7, 5, 3)


def distorted_probability_capacity(
    weights: Sequence[float],
    gamma: float = 1.0,
    distortion: str = "power",
) -> Dict[str, Any]:
    """Build m(A)=g(sum_{i in A} p_i) as a full capacity table.

    This gives a compact/interpretable bridge between additive weights and an
    unrestricted capacity. `power` uses g(t)=t**gamma; `sqrt-logit` is an
    exploratory smooth distortion with the same boundary conditions.
    """
    p = np.maximum(np.asarray(weights, dtype=float), 0.0)
    if p.ndim != 1 or p.size == 0:
        raise ValueError("weights must be a non-empty 1D sequence")
    p = p / max(float(p.sum()), EPS)
    n = p.size
    table = np.zeros(1 << n, dtype=float)
    for mask in range(1, 1 << n):
        s = float(sum(p[i] for i in range(n) if mask & (1 << i)))
        if distortion == "power":
            z = np.power(np.clip(s, 0.0, 1.0), float(gamma))
        elif distortion == "sqrt-logit":
            # Smooth S-shaped family controlled by gamma; normalized on [0,1].
            a = max(float(gamma), 1e-3)
            u = np.power(max(s, EPS), a)
            v = np.power(max(1.0 - s, EPS), a)
            z = u / max(u + v, EPS)
        else:
            raise ValueError(f"unknown distortion: {distortion}")
        table[mask] = float(np.clip(z, 0.0, 1.0))
    table[-1] = 1.0
    return {
        "kind": "capacity",
        "capacity_table": table.tolist(),
        "meta": {"family": "distorted_probability", "weights": p.tolist(), "gamma": float(gamma), "distortion": distortion},
    }


def restricted_dissimilarity(a: np.ndarray, b: np.ndarray, kind: str = "abs") -> np.ndarray:
    """Bounded restricted dissimilarities for exploratory d-Choquet variants.

    These implement a generic restricted-dissimilarity family; they should not be
    labelled a bit-exact reproduction of a particular paper unless its exact D is
    selected and verified separately.
    """
    d = np.abs(np.asarray(a, float) - np.asarray(b, float))
    if kind == "abs":
        return np.clip(d, 0.0, 1.0)
    if kind == "sqrt":
        return np.sqrt(np.clip(d, 0.0, 1.0))
    if kind == "quadratic":
        return np.square(np.clip(d, 0.0, 1.0))
    if kind == "sin":
        return np.sin(0.5 * np.pi * np.clip(d, 0.0, 1.0))
    raise ValueError(f"unknown restricted dissimilarity: {kind}")


def dissimilarity_cf_integral(
    X: np.ndarray,
    measure_spec: Mapping[str, Any],
    F: str = "CL",
    dissimilarity: str = "abs",
    context: Optional[Mapping[str, Any]] = None,
    scale: Optional[int] = None,
) -> np.ndarray:
    """Exploratory d-CF integral using D(x_i,x_{i-1}) in place of increments."""
    x = np.clip(np.asarray(X, dtype=float), 0.0, 1.0)
    order = np.argsort(x, axis=-1, kind="stable")
    xs = np.take_along_axis(x, order, axis=-1)
    prev = np.concatenate([np.zeros_like(xs[..., :1]), xs[..., :-1]], axis=-1)
    m = tail_capacities(x, measure_spec, context=context, scale=scale)
    delta = restricted_dissimilarity(xs, prev, dissimilarity)
    return np.clip(np.sum(FUNCTIONS[F](delta, m), axis=-1), 0.0, 1.0)


@dataclass
class CHMFIConfig:
    name: str = "ch_mfi_default"
    scales: Tuple[int, ...] = DEFAULT_SCALES
    feature_mode: str = "oriented"
    hierarchy: str = "global_local"  # flat | global_local
    within_measure: Dict[str, Any] = field(default_factory=lambda: {"kind": "power", "q": 0.2})
    scale_measure: Optional[Dict[str, Any]] = None
    operator_mode: str = "fixed"  # fixed | conditional
    family: str = "CF1F2"
    F1: str = "CL"
    F2: str = "CL"
    dissimilarity: Optional[str] = None
    descriptor_importance: Optional[Sequence[float]] = None
    regime_importance: Optional[Dict[str, Sequence[float]]] = None
    shapley_threshold: float = 0.05
    shapley_temperature: float = 0.04
    gate_floor: float = 0.05
    granularity: float = 0.50
    localizer_mode: str = "adaptive"  # adaptive | uniform
    controller: str = "bilateral_exp"  # bilateral_exp | soft | mfi_only | localizer_only
    alpha: float = 0.75
    beta_uncertainty: float = 0.50
    eps: float = 0.25
    gamma: float = 1.0
    nms: bool = True


@dataclass
class CHMFIResult:
    score: np.ndarray
    mfi: np.ndarray
    uncertainty: np.ndarray
    scale_confidences: Dict[int, np.ndarray]
    coarse: np.ndarray
    fine: np.ndarray
    localizer: np.ndarray
    localizer_bank: Dict[str, np.ndarray]
    context: ContextMaps
    descriptor_gate: Optional[np.ndarray]


def _default_scale_measure(n: int, granularity: float = 0.5) -> Dict[str, Any]:
    # Fine scales receive more prior mass as granularity approaches 1.
    if n == 2:
        w = [1.0 - float(granularity), float(granularity)]
    else:
        w = np.ones(n, dtype=float)
    return distorted_probability_capacity(w, gamma=0.85)


def _aggregate_one_scale(
    X: np.ndarray,
    w: int,
    ctx: ContextMaps,
    cfg: CHMFIConfig,
    spatial_gate: Optional[np.ndarray],
) -> np.ndarray:
    Xin = np.asarray(X, dtype=float)
    if spatial_gate is not None:
        Xin = apply_spatial_gate(Xin, spatial_gate)
    elif cfg.descriptor_importance is not None:
        gate = soft_gate_from_importance(
            cfg.descriptor_importance,
            cfg.shapley_threshold,
            cfg.shapley_temperature,
            cfg.gate_floor,
        )
        Xin = apply_descriptor_gate(Xin, gate)

    mctx = {
        "heterogeneity": ctx.heterogeneity,
        "blur": ctx.blur,
        "texture": ctx.texture,
        "noise": ctx.noise,
        "coherence": ctx.coherence,
    }

    if cfg.dissimilarity:
        raw = dissimilarity_cf_integral(
            Xin,
            cfg.within_measure,
            F=cfg.F1,
            dissimilarity=cfg.dissimilarity,
            context=mctx,
            scale=int(w),
        )
    elif cfg.operator_mode == "conditional":
        rw = regime_soft_weights(ctx)
        # Each expert is deliberately interpretable and already implemented in
        # the operator library. The output is a soft conditional aggregation.
        experts = {
            "clean": aggregate_features(Xin, "CF1F2", F1="CL", F2="CL", measure_spec=cfg.within_measure, measure_context=mctx, scale=int(w)),
            "texture": aggregate_features(Xin, "CF1F2", F1="TM", F2="TM", measure_spec=cfg.within_measure, measure_context=mctx, scale=int(w)),
            "blur": aggregate_features(Xin, "CF1F2", F1="TP", F2="TL", measure_spec=cfg.within_measure, measure_context=mctx, scale=int(w)),
            "noise": aggregate_features(Xin, "CF1F2", F1="TM", F2="FNA", measure_spec=cfg.within_measure, measure_context=mctx, scale=int(w)),
        }
        raw = sum(np.asarray(rw[k], float) * np.asarray(experts[k], float) for k in experts)
    else:
        raw = aggregate_features(
            Xin,
            family=cfg.family,
            F1=cfg.F1,
            F2=cfg.F2,
            q=0.1,
            measure_spec=cfg.within_measure,
            measure_context=mctx,
            scale=int(w),
        )

    bits = empirical_surprisal(raw)
    return np.asarray(percentile_confidence(bits), np.float32)


def _aggregate_scale_stack(stack: np.ndarray, measure_spec: Mapping[str, Any]) -> np.ndarray:
    return np.asarray(
        aggregate_features(stack, family="CF1F2", F1="CL", F2="CL", measure_spec=measure_spec),
        np.float32,
    )


def _scale_uncertainty(stack: np.ndarray) -> np.ndarray:
    x = np.clip(np.asarray(stack, float), 0.0, 1.0)
    var = tied_percentile(np.var(x, axis=-1))
    p = x / np.maximum(np.sum(x, axis=-1, keepdims=True), EPS)
    ent = -np.sum(np.where(p > 0, p * np.log(p + EPS), 0.0), axis=-1)
    ent /= np.log(max(x.shape[-1], 2))
    return np.asarray(np.clip(0.55 * var + 0.45 * ent, 0.0, 1.0), np.float32)


def run_ch_mfi(
    img: np.ndarray,
    cfg: CHMFIConfig,
    precomputed=None,
    context: Optional[ContextMaps] = None,
) -> CHMFIResult:
    """Run the Contextual-Hierarchical MFI research architecture.

    The MFI branch supplies context/evidence; the spatial localizer remains the
    source of precise edge location. This intentionally tests the bilateral
    architecture suggested by the UDED generalization results.
    """
    ctx = context or analyze_context(img)
    pre = precomputed
    if pre is None:
        pre, _ = precompute_multiscale_features(img, cfg.scales, feature_mode=cfg.feature_mode)

    spatial_gate = None
    if cfg.regime_importance:
        spatial_gate = regime_gate(
            regime_soft_weights(ctx),
            cfg.regime_importance,
            cfg.shapley_threshold,
            cfg.shapley_temperature,
            cfg.gate_floor,
        )

    scale_maps: Dict[int, np.ndarray] = {}
    for w, X, _hetero in pre:
        scale_maps[int(w)] = _aggregate_one_scale(X, int(w), ctx, cfg, spatial_gate)

    ordered = [scale_maps[int(s)] for s in cfg.scales]
    full_stack = np.stack(ordered, axis=-1)
    uncertainty = _scale_uncertainty(full_stack)

    g = float(np.clip(cfg.granularity, 0.0, 1.0))
    if cfg.hierarchy == "global_local" and len(cfg.scales) >= 4:
        coarse_scales = [s for s in cfg.scales if int(s) >= 13]
        fine_scales = [s for s in cfg.scales if int(s) < 13]
        coarse_stack = np.stack([scale_maps[int(s)] for s in coarse_scales], axis=-1)
        fine_stack = np.stack([scale_maps[int(s)] for s in fine_scales], axis=-1)
        coarse = _aggregate_scale_stack(coarse_stack, distorted_probability_capacity(np.ones(coarse_stack.shape[-1]), gamma=0.85))
        fine = _aggregate_scale_stack(fine_stack, distorted_probability_capacity(np.ones(fine_stack.shape[-1]), gamma=0.85))
        top = np.stack([(1.0 - 0.65 * g) * coarse, (0.35 + 0.65 * g) * fine], axis=-1)
        top_spec = cfg.scale_measure or _default_scale_measure(2, g)
        mfi = _aggregate_scale_stack(top, top_spec)
    else:
        scale_spec = cfg.scale_measure or distorted_probability_capacity(np.ones(full_stack.shape[-1]), gamma=0.85)
        mfi = _aggregate_scale_stack(full_stack, scale_spec)
        coarse = np.mean(full_stack[..., : max(1, full_stack.shape[-1] // 2)], axis=-1)
        fine = np.mean(full_stack[..., max(1, full_stack.shape[-1] // 2):], axis=-1)

    mfi = np.asarray(percentile_confidence(mfi), np.float32)
    loc: LocalizerResult = dynamic_localizer(img, ctx, mode=cfg.localizer_mode)
    localizer = oriented_nms(loc.fused) if cfg.nms else loc.fused

    if cfg.controller == "bilateral_exp":
        z = float(cfg.alpha) * (mfi - 0.5) - float(cfg.beta_uncertainty) * uncertainty
        score = np.asarray(localizer, float) * np.exp(np.clip(z, -2.5, 2.5))
    elif cfg.controller == "soft":
        gate = float(cfg.eps) + (1.0 - float(cfg.eps)) * np.power(mfi, float(cfg.gamma))
        score = np.asarray(localizer, float) * gate * np.exp(-float(cfg.beta_uncertainty) * uncertainty)
    elif cfg.controller == "mfi_only":
        score = mfi
    elif cfg.controller == "localizer_only":
        score = localizer
    else:
        raise ValueError(f"unknown controller: {cfg.controller}")

    return CHMFIResult(
        score=np.asarray(score, np.float32),
        mfi=mfi,
        uncertainty=uncertainty,
        scale_confidences=scale_maps,
        coarse=np.asarray(coarse, np.float32),
        fine=np.asarray(fine, np.float32),
        localizer=np.asarray(localizer, np.float32),
        localizer_bank=loc.bank,
        context=ctx,
        descriptor_gate=spatial_gate,
    )
