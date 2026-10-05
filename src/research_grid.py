from __future__ import annotations

from itertools import product
from typing import List

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
    variants early. Expect roughly 100-200 candidates depending on feature count.
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
    # Stable unique-by-name preserving first occurrence.
    uniq = {}
    for c in cfgs:
        uniq.setdefault(c.name, c)
    return list(uniq.values())


def build_grid(preset: str, n_features: int) -> List[CHMFIConfig]:
    p = str(preset).lower()
    if p == "smoke":
        return smoke_grid(n_features)
    if p == "standard":
        return standard_grid(n_features)
    if p == "wide":
        return wide_grid(n_features)
    raise ValueError("preset must be smoke, standard, or wide")
