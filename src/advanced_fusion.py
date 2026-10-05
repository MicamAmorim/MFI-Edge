from __future__ import annotations

import json
from typing import Dict, Iterable, List, Tuple

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata


def tied_percentile(score):
    """Tie-preserving empirical percentile map in [0,1]."""
    x = np.asarray(score, dtype=float)
    flat = np.nan_to_num(x, nan=-np.inf).ravel()
    if flat.size <= 1:
        return np.zeros_like(x, dtype=float)
    ranks = rankdata(flat, method="average") - 1.0
    return (ranks / max(flat.size - 1, 1)).reshape(x.shape)


def _component_support(seeds, corridor):
    seeds = np.asarray(seeds, dtype=bool)
    corridor = np.asarray(corridor, dtype=bool)
    if not np.any(seeds) or not np.any(corridor):
        return np.zeros_like(corridor, dtype=bool)
    labels, nlab = ndi.label(corridor, structure=np.ones((3, 3), dtype=bool))
    if nlab == 0:
        return np.zeros_like(corridor, dtype=bool)
    touched = np.unique(labels[seeds])
    touched = touched[touched > 0]
    if touched.size == 0:
        return np.zeros_like(corridor, dtype=bool)
    keep = np.zeros(nlab + 1, dtype=bool)
    keep[touched] = True
    return keep[labels]


def geodesic_link_score(detector_score, confidence, seed_q=0.90, corridor_q=0.65,
                        bonus=0.50, outside=0.15):
    """Connectivity-aware continuous score.

    Seeds require strong joint detector/MFI evidence. A permissive corridor is
    formed from detector-rank OR MFI evidence, dilated by one pixel to bridge
    tiny gaps. Only connected components touching a seed receive the full
    linked score. This is a proposal/linking prior, not a posterior probability.
    """
    s = np.asarray(detector_score, dtype=float)
    c = np.clip(np.asarray(confidence, dtype=float), 0.0, 1.0)
    sr = tied_percentile(s)

    joint = 0.70 * sr + 0.30 * c
    seeds = joint >= float(seed_q)
    corridor = (sr >= float(corridor_q)) | (c >= min(0.95, float(corridor_q) + 0.10))
    corridor = ndi.binary_dilation(corridor, iterations=1)
    support = _component_support(seeds, corridor)

    linked = np.maximum(sr, 0.65 * c)
    inside_score = linked * (1.0 + float(bonus) * c)
    outside_score = float(outside) * sr
    return np.where(support, inside_score, outside_score)


def fuse_advanced(detector_score, confidence, strategy, params):
    """Fuse a detector score with MFI confidence into a continuous score."""
    s = np.asarray(detector_score, dtype=float)
    c = np.clip(np.asarray(confidence, dtype=float), 0.0, 1.0)

    if strategy.startswith("soft_"):
        eps = float(params["eps"])
        gamma = float(params["gamma"])
        return s * (eps + (1.0 - eps) * np.power(c, gamma))

    if strategy.startswith("residual_"):
        lam = float(params["lambda"])
        return s * np.clip(1.0 + lam * (c - 0.5), 0.05, None)

    if strategy.startswith("adaptive_exp_"):
        alpha = float(params["alpha"])
        # Thresholding this score at tau is equivalent to using the spatially
        # varying detector threshold tau*exp(-alpha*(c-0.5)).
        return s * np.exp(alpha * (c - 0.5))

    if strategy.startswith("proposal_"):
        q = float(params["q"])
        outside = float(params["outside"])
        roi = c >= q
        return s * (outside + (1.0 - outside) * roi.astype(float))

    if strategy.startswith("rank_"):
        alpha = float(params["alpha"])
        sr = tied_percentile(s)
        return (1.0 - alpha) * sr + alpha * c

    if strategy.startswith("geodesic_"):
        return geodesic_link_score(
            s, c,
            seed_q=float(params["seed_q"]),
            corridor_q=float(params["corridor_q"]),
            bonus=float(params["bonus"]),
            outside=float(params.get("outside", 0.15)),
        )

    raise ValueError(f"Unknown advanced fusion strategy: {strategy}")


def advanced_fusion_specs(synthetic_roi_q=0.50):
    """Return the Stage-7 fusion grid.

    The grid is deliberately broad but finite so every deployable fuzzy-measure
    variant can be crossed with the same fusion families on UDED.
    """
    out = []

    for eps in (0.10, 0.25, 0.50):
        for gamma in (0.5, 1.0, 2.0):
            out.append((
                f"soft_e{eps:.2f}_g{gamma:g}",
                {"eps": eps, "gamma": gamma},
            ))

    for lam in (0.10, 0.25, 0.50, 1.00):
        out.append((f"residual_l{lam:.2f}", {"lambda": lam}))

    for alpha in (0.25, 0.50, 1.00, 1.50, 2.00):
        out.append((f"adaptive_exp_a{alpha:.2f}", {"alpha": alpha}))

    qvals = sorted({
        round(float(synthetic_roi_q), 2),
        0.45, 0.55, 0.65, 0.75,
    })
    for q in qvals:
        for outside in (0.00, 0.25):
            out.append((
                f"proposal_q{q:.2f}_o{outside:.2f}",
                {"q": q, "outside": outside},
            ))

    for alpha in (0.10, 0.25, 0.50, 0.75, 1.00):
        out.append((f"rank_a{alpha:.2f}", {"alpha": alpha}))

    for seed_q in (0.85, 0.92):
        for corridor_q in (0.55, 0.65, 0.75):
            for bonus in (0.25, 0.50):
                out.append((
                    f"geodesic_s{seed_q:.2f}_c{corridor_q:.2f}_b{bonus:.2f}",
                    {
                        "seed_q": seed_q,
                        "corridor_q": corridor_q,
                        "bonus": bonus,
                        "outside": 0.15,
                    },
                ))

    return out
