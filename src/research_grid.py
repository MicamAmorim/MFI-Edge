from __future__ import annotations

from dataclasses import replace
from itertools import product
from pathlib import Path
from typing import List
import json
import os

import numpy as np

from .ch_mfi import CHMFIConfig, distorted_probability_capacity


def _base_measures(n_features: int):
    n = int(n_features)
    uniform = np.ones(n, dtype=float) / max(n, 1)
    out = [
        ("power_q0.2", {"kind": "power", "q": 0.2}),
        ("power_q1.0", {"kind": "power", "q": 1.0}),
        ("power_q1.5", {"kind": "power", "q": 1.5}),
        ("additive_uniform", {"kind": "additive", "weights": uniform.tolist()}),
        ("local_add_evidence", {"kind": "local_additive", "mode": "evidence", "gamma": 1.0}),
        ("local_add_reliability", {"kind": "local_additive", "mode": "reliability", "window": 5}),
    ]
    for gamma in (0.55, 0.85, 1.20, 1.60):
        out.append((f"distprob_g{gamma:.2f}", distorted_probability_capacity(uniform, gamma=gamma)))
    return out


def smoke_grid(n_features: int) -> List[CHMFIConfig]:
    """Small sanity grid intended to finish in minutes."""
    measures = _base_measures(n_features)
    cfgs = []
    for name, measure in measures[:5]:
        cfgs.append(CHMFIConfig(
            name=f"smoke_{name}_bilateral",
            within_measure=measure,
            hierarchy="global_local",
            operator_mode="fixed",
            controller="bilateral_exp",
            localizer_mode="adaptive",
            granularity=0.50,
        ))
        cfgs.append(CHMFIConfig(
            name=f"smoke_{name}_conditional",
            within_measure=measure,
            hierarchy="global_local",
            operator_mode="conditional",
            controller="bilateral_exp",
            localizer_mode="adaptive",
            granularity=0.50,
        ))
    cfgs.append(CHMFIConfig(name="control_dynamic_localizer", controller="localizer_only"))
    cfgs.append(CHMFIConfig(name="control_mfi_only", controller="mfi_only"))
    return cfgs


def standard_grid(n_features: int) -> List[CHMFIConfig]:
    """Balanced grid for a Ryzen 7 / 32 GB workstation.

    It intentionally keeps every architecture family alive rather than eliminating
    variants early. Expect roughly 250 candidates with the current defaults.
    """
    cfgs: List[CHMFIConfig] = []
    for mname, measure in _base_measures(n_features):
        for hierarchy, op_mode, gran, controller in product(
            ("flat", "global_local"),
            ("fixed", "conditional"),
            (0.25, 0.50, 0.75),
            ("bilateral_exp", "soft"),
        ):
            cfgs.append(CHMFIConfig(
                name=f"{mname}__{hierarchy}__{op_mode}__g{gran:.2f}__{controller}",
                within_measure=measure,
                hierarchy=hierarchy,
                operator_mode=op_mode,
                granularity=gran,
                controller=controller,
                localizer_mode="adaptive",
                alpha=0.75,
                beta_uncertainty=0.50,
                eps=0.25,
                gamma=1.0,
            ))

    # Restricted-dissimilarity family: kept separate so it is easy to diagnose.
    for mname, measure in _base_measures(n_features)[:4]:
        for d in ("abs", "sqrt", "quadratic", "sin"):
            for gran in (0.25, 0.50, 0.75):
                cfgs.append(CHMFIConfig(
                    name=f"dCF_{d}__{mname}__g{gran:.2f}",
                    within_measure=measure,
                    dissimilarity=d,
                    hierarchy="global_local",
                    granularity=gran,
                    controller="bilateral_exp",
                    localizer_mode="adaptive",
                ))

    # Controls and architecture ablations.
    cfgs.extend([
        CHMFIConfig(name="control_localizer_adaptive", controller="localizer_only", localizer_mode="adaptive"),
        CHMFIConfig(name="control_localizer_uniform", controller="localizer_only", localizer_mode="uniform"),
        CHMFIConfig(name="control_mfi_only", controller="mfi_only"),
        CHMFIConfig(name="control_flat_fixed", hierarchy="flat", operator_mode="fixed"),
    ])
    return cfgs


def wide_grid(n_features: int) -> List[CHMFIConfig]:
    """Larger exploratory grid; suitable for long overnight CPU runs."""
    base = standard_grid(n_features)
    cfgs = list(base)
    measures = _base_measures(n_features)
    for mname, measure in measures:
        for hierarchy, op_mode, gran, controller, alpha, beta in product(
            ("flat", "global_local"),
            ("fixed", "conditional"),
            (0.0, 0.25, 0.50, 0.75, 1.0),
            ("bilateral_exp", "soft"),
            (0.35, 0.75, 1.20),
            (0.0, 0.35, 0.70),
        ):
            cfgs.append(CHMFIConfig(
                name=f"wide_{mname}__{hierarchy}__{op_mode}__g{gran:.2f}__{controller}__a{alpha:.2f}__b{beta:.2f}",
                within_measure=measure,
                hierarchy=hierarchy,
                operator_mode=op_mode,
                granularity=gran,
                controller=controller,
                localizer_mode="adaptive",
                alpha=alpha,
                beta_uncertainty=beta,
                eps=0.25,
                gamma=1.0,
            ))
    uniq = {}
    for c in cfgs:
        uniq.setdefault(c.name, c)
    return list(uniq.values())


def _append_shapley_variants(cfgs: List[CHMFIConfig], n_features: int) -> List[CHMFIConfig]:
    """Append Shapley-gated variants when MFI_SHAPLEY_FILE points to a learned file."""
    raw = os.environ.get("MFI_SHAPLEY_FILE", "").strip()
    if not raw:
        return cfgs
    path = Path(raw)
    if not path.exists():
        print(f"WARNING: MFI_SHAPLEY_FILE not found: {path}", flush=True)
        return cfgs
    payload = json.loads(path.read_text(encoding="utf-8"))
    importance = payload.get("normalized_positive_shapley")
    if not isinstance(importance, list) or len(importance) != int(n_features):
        print("WARNING: Shapley file feature count does not match current descriptors", flush=True)
        return cfgs

    additions: List[CHMFIConfig] = []
    # Apply learned gates to a focused but diverse slice; originals remain in the competition.
    candidates = [
        c for c in cfgs
        if c.controller in ("bilateral_exp", "soft")
        and c.hierarchy == "global_local"
        and c.operator_mode in ("fixed", "conditional")
        and c.dissimilarity is None
    ][:24]
    for c in candidates:
        additions.append(replace(
            c,
            name=f"shapley__{c.name}",
            descriptor_importance=list(map(float, importance)),
            shapley_threshold=0.05,
            shapley_temperature=0.04,
            gate_floor=0.05,
        ))
    return cfgs + additions


def build_grid(preset: str, n_features: int) -> List[CHMFIConfig]:
    p = str(preset).lower()
    if p == "smoke":
        cfgs = smoke_grid(n_features)
    elif p == "standard":
        cfgs = standard_grid(n_features)
    elif p == "wide":
        cfgs = wide_grid(n_features)
    else:
        raise ValueError("preset must be smoke, standard, or wide")
    return _append_shapley_variants(cfgs, n_features)
