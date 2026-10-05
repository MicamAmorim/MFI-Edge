from __future__ import annotations

from dataclasses import replace
from itertools import product
from pathlib import Path
from typing import List, Optional
import json
import os

import numpy as np

from .ch_mfi import distorted_probability_capacity
from .ch_mfi_v2 import CHMFIv2Config
from .advanced_fuzzy_v2 import regularized_pair_capacity


def _base_measures(n):
    u = np.ones(int(n), float) / max(int(n), 1)
    return [
        ("power_q0.2", {"kind":"power", "q":0.2}),
        ("power_q1.0", {"kind":"power", "q":1.0}),
        ("power_q1.5", {"kind":"power", "q":1.5}),
        ("additive_uniform", {"kind":"additive", "weights":u.tolist()}),
        ("local_evidence", {"kind":"local_additive", "mode":"evidence", "gamma":1.0}),
        ("local_reliability", {"kind":"local_additive", "mode":"reliability", "window":5}),
        ("distprob_g055", distorted_probability_capacity(u, gamma=0.55)),
        ("distprob_g085", distorted_probability_capacity(u, gamma=0.85)),
        ("distprob_g120", distorted_probability_capacity(u, gamma=1.20)),
        ("distprob_g160", distorted_probability_capacity(u, gamma=1.60)),
    ]


def _load_regime_shapley(path: Optional[str]):
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    out = {}
    for k, v in d.get("regimes", {}).items():
        out[k] = v["normalized_positive_shapley"]
    return out or None


def _load_scale_bank(path: Optional[str], family: str = "regularized_pair"):
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    out = {}
    for scale, row in d.get("scales", {}).items():
        out[str(scale)] = row[family]
    return out or None


def smoke_grid(n_features: int, regime_file=None, scale_file=None) -> List[CHMFIv2Config]:
    u = np.ones(n_features) / n_features
    cfgs = [
        CHMFIv2Config(name="v2_control_standard", aggregation_variant="standard", within_measure={"kind":"power","q":0.2}),
        CHMFIv2Config(name="v2_swafed_mean", aggregation_variant="swafed", swafed_mode="mean"),
        CHMFIv2Config(name="v2_dcf_abs", aggregation_variant="dcf", rdf="abs"),
        CHMFIv2Config(name="v2_dcc_abs", aggregation_variant="dcc", rdf="abs"),
        CHMFIv2Config(name="v2_dxc_abs", aggregation_variant="dxc", rdf="abs"),
        CHMFIv2Config(name="v2_choquet_inspired", aggregation_variant="choquet_inspired", inspired_weight_function="mean"),
        CHMFIv2Config(name="v2_partitioned", aggregation_variant="partitioned"),
        CHMFIv2Config(name="v2_pair_regularized", aggregation_variant="standard", within_measure=regularized_pair_capacity(u, shrinkage=0.8)),
    ]
    rs = _load_regime_shapley(regime_file)
    if rs:
        cfgs.append(CHMFIv2Config(name="v2_regime_shapley", regime_importance=rs, operator_mode="conditional"))
    sb = _load_scale_bank(scale_file)
    if sb:
        cfgs.append(CHMFIv2Config(name="v2_scale_capacity_bank", scale_specific_measures=sb))
    return cfgs


def standard_grid(n_features: int, regime_file=None, scale_file=None) -> List[CHMFIv2Config]:
    cfgs: List[CHMFIv2Config] = []
    measures = _base_measures(n_features)

    # Core contextual/hierarchical competition.
    for mname, measure in measures:
        for hierarchy, opmode, gran, controller in product(
            ("flat", "global_local"),
            ("fixed", "conditional"),
            (0.25, 0.50, 0.75),
            ("bilateral_exp", "soft"),
        ):
            cfgs.append(CHMFIv2Config(
                name=f"v2_std__{mname}__{hierarchy}__{opmode}__g{gran:.2f}__{controller}",
                aggregation_variant="standard",
                within_measure=measure,
                hierarchy=hierarchy,
                operator_mode=opmode,
                granularity=gran,
                controller=controller,
                localizer_mode="adaptive",
            ))

    # SWAFED-faithful q(x) from the image neighbourhood, not descriptor-vector proxy.
    for mode, gran, controller in product(
        ("mean", "geomean", "harmmean", "hamacher", "odiv", "max", "min", "prod", "lukasiewicz", "lukasiewicz_repo"),
        (0.25, 0.50, 0.75),
        ("bilateral_exp", "soft"),
    ):
        cfgs.append(CHMFIv2Config(
            name=f"v2_swafed__{mode}__g{gran:.2f}__{controller}",
            aggregation_variant="swafed", swafed_mode=mode, granularity=gran,
            controller=controller, hierarchy="global_local", localizer_mode="adaptive",
        ))

    # Published restricted-dissimilarity families.
    for variant, rdf, mitem, gran in product(
        ("dcf", "dcc", "dxc"),
        ("abs", "square", "sqrt", "x2", "sqrt2"),
        measures[:4],
        (0.25, 0.50, 0.75),
    ):
        mname, measure = mitem
        cfgs.append(CHMFIv2Config(
            name=f"v2_{variant}__{rdf}__{mname}__g{gran:.2f}",
            aggregation_variant=variant, rdf=rdf, within_measure=measure,
            hierarchy="global_local", granularity=gran, controller="bilateral_exp",
        ))

    # Choquet-inspired and partition-dependent families.
    for wf, gran in product(("mean", "max", "geomean", "softmaxmean"), (0.25,0.50,0.75)):
        cfgs.append(CHMFIv2Config(
            name=f"v2_choquet_inspired__{wf}__g{gran:.2f}",
            aggregation_variant="choquet_inspired", inspired_weight_function=wf,
            granularity=gran, controller="bilateral_exp",
        ))
    for within, between, gran in product(("mean","max","geomean"), ("mean","geomean"), (0.25,0.50,0.75)):
        cfgs.append(CHMFIv2Config(
            name=f"v2_partitioned__{within}_{between}__g{gran:.2f}",
            aggregation_variant="partitioned", partition_within=within,
            partition_between=between, granularity=gran, controller="bilateral_exp",
        ))

    # Regularized low-complexity interaction controls.
    u = np.ones(n_features, float) / n_features
    for shrink, gran in product((0.50,0.75,0.90), (0.25,0.50,0.75)):
        cfgs.append(CHMFIv2Config(
            name=f"v2_regularized_pair__s{shrink:.2f}__g{gran:.2f}",
            aggregation_variant="standard",
            within_measure=regularized_pair_capacity(u, shrinkage=shrink),
            granularity=gran,
        ))

    # Learned banks are optional and appended rather than replacing controls.
    regime = _load_regime_shapley(regime_file)
    if regime:
        for gran in (0.25,0.50,0.75):
            cfgs.append(CHMFIv2Config(
                name=f"v2_regime_shapley__g{gran:.2f}",
                aggregation_variant="standard", operator_mode="conditional",
                regime_importance=regime, granularity=gran,
            ))

    for fam in ("additive", "distorted_gamma0.85", "regularized_pair"):
        bank = _load_scale_bank(scale_file, fam)
        if bank:
            for gran in (0.25,0.50,0.75):
                cfgs.append(CHMFIv2Config(
                    name=f"v2_scale_bank__{fam}__g{gran:.2f}",
                    aggregation_variant="standard", scale_specific_measures=bank,
                    granularity=gran,
                ))

    # Stable unique names.
    uniq = {}
    for c in cfgs:
        uniq.setdefault(c.name, c)
    return list(uniq.values())


def wide_grid(n_features: int, regime_file=None, scale_file=None) -> List[CHMFIv2Config]:
    base = standard_grid(n_features, regime_file, scale_file)
    cfgs = list(base)
    # Expand the most promising families without deleting anything from standard.
    for c in base:
        if c.aggregation_variant in ("standard", "swafed", "dcf", "dcc", "dxc"):
            for alpha, beta in product((0.35,0.75,1.20), (0.0,0.35,0.70)):
                cfgs.append(replace(
                    c,
                    name=f"wide__{c.name}__a{alpha:.2f}__b{beta:.2f}",
                    alpha=alpha,
                    beta_uncertainty=beta,
                ))
    uniq = {}
    for c in cfgs:
        uniq.setdefault(c.name, c)
    return list(uniq.values())


def build_grid(preset: str, n_features: int, regime_file=None, scale_file=None):
    p = str(preset).lower()
    if p == "smoke":
        return smoke_grid(n_features, regime_file, scale_file)
    if p == "standard":
        return standard_grid(n_features, regime_file, scale_file)
    if p == "wide":
        return wide_grid(n_features, regime_file, scale_file)
    raise ValueError("preset must be smoke, standard, or wide")
