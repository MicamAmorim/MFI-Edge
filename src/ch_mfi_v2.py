from __future__ import annotations

"""CH-MFI v2: second-wave local research architecture.

The v1 architecture remains untouched in `src/ch_mfi.py`.  This module adds the
experimental operator families requested after the literature review while
preserving the bilateral context/localization philosophy.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np

from .advanced_fusion import tied_percentile
from .advanced_fuzzy_v2 import (
    aggregate_swafed_descriptor_tensor,
    choquet_inspired,
    d_choquet_family,
    partitioned_choquet_inspired,
)
from .ch_mfi import CHMFIConfig, CHMFIResult, distorted_probability_capacity
from .context_maps import ContextMaps, analyze_context, regime_soft_weights
from .dynamic_localizer import LocalizerResult, dynamic_localizer, oriented_nms
from .hybrid import percentile_confidence
from .pipeline import aggregate_features, empirical_surprisal, precompute_multiscale_features
from .shapley_gating import apply_descriptor_gate, apply_spatial_gate, regime_gate, soft_gate_from_importance

EPS = 1e-9


@dataclass
class CHMFIv2Config(CHMFIConfig):
    """Superset of CHMFIConfig used only on the local-development branch."""

    aggregation_variant: str = "standard"
    # standard | swafed | dcf | dcc | dxc | choquet_inspired | partitioned
    rdf: str = "abs"
    swafed_mode: str = "mean"
    swafed_window: int = 3
    inspired_weight_function: str = "mean"
    partition_within: str = "mean"
    partition_between: str = "geomean"
    partitions: Optional[Tuple[Tuple[int, ...], ...]] = None
    # Optional scale-specific capacity specs, keyed by scale as string/int.
    scale_specific_measures: Optional[Dict[str, Dict[str, Any]]] = None
    architecture_label: str = "CH-MFI-v2"


def _measure_for_scale(cfg: CHMFIv2Config, scale: int):
    if not cfg.scale_specific_measures:
        return cfg.within_measure
    m = cfg.scale_specific_measures
    return m.get(str(scale), m.get(scale, cfg.within_measure))


def _apply_descriptor_gating(X, cfg: CHMFIv2Config, spatial_gate):
    Xin = np.asarray(X, dtype=float)
    if spatial_gate is not None:
        return apply_spatial_gate(Xin, spatial_gate)
    if cfg.descriptor_importance is not None:
        gate = soft_gate_from_importance(
            cfg.descriptor_importance,
            cfg.shapley_threshold,
            cfg.shapley_temperature,
            cfg.gate_floor,
        )
        return apply_descriptor_gate(Xin, gate)
    return Xin


def _aggregate_scale(X, w: int, image: np.ndarray, ctx: ContextMaps, cfg: CHMFIv2Config, spatial_gate):
    Xin = _apply_descriptor_gating(X, cfg, spatial_gate)
    measure = _measure_for_scale(cfg, int(w))
    mctx = {
        "heterogeneity": ctx.heterogeneity,
        "blur": ctx.blur,
        "texture": ctx.texture,
        "noise": ctx.noise,
        "coherence": ctx.coherence,
    }
    variant = str(cfg.aggregation_variant).lower()

    if variant == "swafed":
        raw = aggregate_swafed_descriptor_tensor(
            Xin, image,
            mode=cfg.swafed_mode,
            family=cfg.family.lower(),
            F1=cfg.F1,
            F2=cfg.F2,
            window=cfg.swafed_window,
        )
    elif variant in ("dcf", "dcc", "dxc", "dchoquet"):
        raw = d_choquet_family(
            Xin,
            measure,
            mode=variant,
            F=cfg.F1,
            rdf=cfg.rdf,
            context=mctx,
            scale=int(w),
        )
    elif variant == "choquet_inspired":
        raw = choquet_inspired(Xin, cfg.inspired_weight_function)
    elif variant == "partitioned":
        parts = cfg.partitions
        if parts is None:
            # Default partition follows current descriptor semantics approximately:
            # first-order/curvature, oriented contrast, texture/frequency.
            n = Xin.shape[-1]
            if n >= 8:
                parts = ((0, 1, 2, 3), (4, 5, 6), (7,))
            else:
                cut = max(1, n // 2)
                parts = (tuple(range(cut)), tuple(range(cut, n)))
        raw = partitioned_choquet_inspired(
            Xin, parts,
            within=cfg.partition_within,
            between=cfg.partition_between,
        )
    elif variant == "standard":
        if cfg.operator_mode == "conditional":
            rw = regime_soft_weights(ctx)
            experts = {
                "clean": aggregate_features(Xin, "CF1F2", F1="CL", F2="CL", measure_spec=measure, measure_context=mctx, scale=int(w)),
                "texture": aggregate_features(Xin, "CF1F2", F1="TM", F2="TM", measure_spec=measure, measure_context=mctx, scale=int(w)),
                "blur": aggregate_features(Xin, "CF1F2", F1="TP", F2="TL", measure_spec=measure, measure_context=mctx, scale=int(w)),
                "noise": aggregate_features(Xin, "CF1F2", F1="TM", F2="FNA", measure_spec=measure, measure_context=mctx, scale=int(w)),
            }
            raw = sum(np.asarray(rw[k], float) * np.asarray(experts[k], float) for k in experts)
        else:
            raw = aggregate_features(
                Xin,
                family=cfg.family,
                F1=cfg.F1,
                F2=cfg.F2,
                q=0.1,
                measure_spec=measure,
                measure_context=mctx,
                scale=int(w),
            )
    else:
        raise ValueError(f"unknown aggregation_variant: {cfg.aggregation_variant}")

    bits = empirical_surprisal(np.asarray(raw, float))
    return np.asarray(percentile_confidence(bits), np.float32)


def _aggregate_stack(stack: np.ndarray, measure_spec: Mapping[str, Any]):
    return np.asarray(
        aggregate_features(stack, family="CF1F2", F1="CL", F2="CL", measure_spec=measure_spec),
        np.float32,
    )


def _uncertainty(stack):
    x = np.clip(np.asarray(stack, float), 0.0, 1.0)
    var = tied_percentile(np.var(x, axis=-1))
    p = x / np.maximum(np.sum(x, axis=-1, keepdims=True), EPS)
    ent = -np.sum(np.where(p > 0, p * np.log(p + EPS), 0.0), axis=-1)
    ent /= np.log(max(x.shape[-1], 2))
    return np.asarray(np.clip(0.55 * var + 0.45 * ent, 0.0, 1.0), np.float32)


def run_ch_mfi_v2(
    img: np.ndarray,
    cfg: CHMFIv2Config,
    precomputed=None,
    context: Optional[ContextMaps] = None,
) -> CHMFIResult:
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

    scale_maps = {}
    for w, X, _hetero in pre:
        scale_maps[int(w)] = _aggregate_scale(X, int(w), img, ctx, cfg, spatial_gate)

    ordered = [scale_maps[int(s)] for s in cfg.scales]
    full_stack = np.stack(ordered, axis=-1)
    uncertainty = _uncertainty(full_stack)

    g = float(np.clip(cfg.granularity, 0.0, 1.0))
    if cfg.hierarchy == "global_local" and len(cfg.scales) >= 4:
        coarse_scales = [s for s in cfg.scales if int(s) >= 13]
        fine_scales = [s for s in cfg.scales if int(s) < 13]
        coarse_stack = np.stack([scale_maps[int(s)] for s in coarse_scales], axis=-1)
        fine_stack = np.stack([scale_maps[int(s)] for s in fine_scales], axis=-1)
        coarse = _aggregate_stack(
            coarse_stack,
            distorted_probability_capacity(np.ones(coarse_stack.shape[-1]), gamma=0.85),
        )
        fine = _aggregate_stack(
            fine_stack,
            distorted_probability_capacity(np.ones(fine_stack.shape[-1]), gamma=0.85),
        )
        top = np.stack([(1.0 - 0.65 * g) * coarse, (0.35 + 0.65 * g) * fine], axis=-1)
        top_spec = cfg.scale_measure or distorted_probability_capacity([1.0 - g + 1e-3, g + 1e-3], gamma=0.85)
        mfi = _aggregate_stack(top, top_spec)
    else:
        scale_spec = cfg.scale_measure or distorted_probability_capacity(np.ones(full_stack.shape[-1]), gamma=0.85)
        mfi = _aggregate_stack(full_stack, scale_spec)
        cut = max(1, full_stack.shape[-1] // 2)
        coarse = np.mean(full_stack[..., :cut], axis=-1)
        fine = np.mean(full_stack[..., cut:], axis=-1)

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
