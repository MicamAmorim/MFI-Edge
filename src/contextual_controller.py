from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from src.advanced_fusion import tied_percentile, _component_support


def _gray01(img):
    x = np.asarray(img, dtype=float)
    if x.ndim == 3:
        x = x[..., :3]
        x = 0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]
    if x.size == 0:
        return x
    mx = float(np.nanmax(x))
    if mx > 1.0:
        x = x / 255.0
    return np.clip(np.nan_to_num(x), 0.0, 1.0)


def local_heterogeneity(img, sigma=1.0, window=5):
    """Robust local heterogeneity map in [0,1].

    It combines local standard deviation and gradient magnitude, then converts
    the result to a tie-preserving within-image percentile. The map is a
    contextual descriptor, not a probability.
    """
    x = _gray01(img)
    if x.size == 0:
        return np.zeros_like(x, dtype=float)
    sm = ndi.gaussian_filter(x, sigma=float(sigma))
    size = max(3, int(window) | 1)
    m1 = ndi.uniform_filter(sm, size=size, mode="reflect")
    m2 = ndi.uniform_filter(sm * sm, size=size, mode="reflect")
    std = np.sqrt(np.maximum(m2 - m1 * m1, 0.0))
    gx = ndi.sobel(sm, axis=1, mode="reflect")
    gy = ndi.sobel(sm, axis=0, mode="reflect")
    grad = np.hypot(gx, gy)
    return tied_percentile(0.65 * tied_percentile(std) + 0.35 * tied_percentile(grad))


def contextual_confidence(confidence, heterogeneity, beta=0.5, interaction=0.0):
    """Reweight MFI confidence by local heterogeneity without hard rejection."""
    c = np.clip(np.asarray(confidence, dtype=float), 0.0, 1.0)
    h = np.clip(np.asarray(heterogeneity, dtype=float), 0.0, 1.0)
    z = c - float(beta) * (h - 0.5) + float(interaction) * 4.0 * (c - 0.5) * (h - 0.5)
    return np.clip(z, 0.0, 1.0)


def contextual_score(detector_score, confidence, heterogeneity, strategy, params):
    """Context-aware detector/MFI controller.

    Unlike Stage 7's direct score fusion, these controllers explicitly model
    local heterogeneity. High-texture regions can receive a stricter effective
    threshold unless MFI evidence is simultaneously strong.
    """
    s = np.asarray(detector_score, dtype=float)
    c = np.clip(np.asarray(confidence, dtype=float), 0.0, 1.0)
    h = np.clip(np.asarray(heterogeneity, dtype=float), 0.0, 1.0)

    if strategy == "ctx_residual":
        lam = float(params["lambda"])
        beta = float(params["beta"])
        eta = float(params.get("interaction", 0.0))
        gain = 1.0 + lam * (c - 0.5) - beta * (h - 0.5)
        gain += eta * 4.0 * (c - 0.5) * (h - 0.5)
        return s * np.clip(gain, 0.05, 3.0)

    if strategy == "ctx_exp":
        alpha = float(params["alpha"])
        beta = float(params["beta"])
        eta = float(params.get("interaction", 0.0))
        z = alpha * (c - 0.5) - beta * (h - 0.5)
        z += eta * 4.0 * (c - 0.5) * (h - 0.5)
        return s * np.exp(np.clip(z, -2.5, 2.5))

    if strategy == "ctx_soft":
        eps = float(params["eps"])
        gamma = float(params["gamma"])
        beta = float(params["beta"])
        gate = eps + (1.0 - eps) * np.power(c, gamma)
        texture = np.exp(-beta * (h - 0.5))
        return s * gate * texture

    if strategy == "ctx_hysteresis":
        seed_q = float(params["seed_q"])
        corridor_q = float(params["corridor_q"])
        beta = float(params["beta"])
        mfi_weight = float(params["mfi_weight"])
        outside = float(params.get("outside", 0.10))

        sr = tied_percentile(s)
        joint = (1.0 - mfi_weight) * sr + mfi_weight * c - 0.10 * beta * h
        seeds = joint >= seed_q

        # Texture raises the local corridor requirement; strong MFI lowers it.
        local_q = corridor_q + beta * 0.20 * (h - 0.5) - 0.15 * (c - 0.5)
        local_q = np.clip(local_q, 0.25, 0.90)
        corridor = sr >= local_q
        corridor |= (c >= min(0.95, corridor_q + 0.20)) & (h <= 0.85)
        corridor = ndi.binary_dilation(corridor, iterations=1)
        support = _component_support(seeds, corridor)

        inside = np.maximum(sr, 0.55 * c) * (1.0 + 0.35 * c)
        return np.where(support, inside, outside * sr)

    raise ValueError(f"Unknown contextual strategy: {strategy}")


def single_controller_specs():
    """Exploratory Stage-8 single-measure controller grid."""
    out = []
    for lam in (0.15, 0.25, 0.50, 0.75):
        for beta in (0.0, 0.25, 0.50):
            for eta in (0.0, 0.25):
                out.append(("ctx_residual", {"lambda": lam, "beta": beta, "interaction": eta}))

    for alpha in (0.25, 0.50, 0.75, 1.00):
        for beta in (0.0, 0.25, 0.50):
            for eta in (0.0, 0.25):
                out.append(("ctx_exp", {"alpha": alpha, "beta": beta, "interaction": eta}))

    for eps in (0.25, 0.50):
        for gamma in (0.5, 1.0, 2.0):
            for beta in (0.0, 0.50):
                out.append(("ctx_soft", {"eps": eps, "gamma": gamma, "beta": beta}))

    for seed_q in (0.85, 0.90):
        for corridor_q in (0.45, 0.55, 0.65):
            for beta in (0.0, 0.25):
                for mw in (0.25, 0.50):
                    out.append(("ctx_hysteresis", {
                        "seed_q": seed_q, "corridor_q": corridor_q,
                        "beta": beta, "mfi_weight": mw, "outside": 0.10,
                    }))
    return out


def route_confidences(conf_a, conf_b, heterogeneity, pivot=0.5, sharpness=8.0,
                      high_heterogeneity_uses_b=True):
    a = np.clip(np.asarray(conf_a, dtype=float), 0.0, 1.0)
    b = np.clip(np.asarray(conf_b, dtype=float), 0.0, 1.0)
    h = np.clip(np.asarray(heterogeneity, dtype=float), 0.0, 1.0)
    z = np.clip(float(sharpness) * (h - float(pivot)), -20.0, 20.0)
    w = 1.0 / (1.0 + np.exp(-z))
    if not high_heterogeneity_uses_b:
        w = 1.0 - w
    return (1.0 - w) * a + w * b


def router_specs():
    """Grid for local mixture-of-measures routing by heterogeneity."""
    out = []
    for pivot in (0.40, 0.50, 0.60):
        for sharp in (4.0, 8.0):
            for lam in (0.25, 0.50):
                out.append({
                    "pivot": pivot, "sharpness": sharp,
                    "controller": "ctx_residual",
                    "controller_params": {"lambda": lam, "beta": 0.25, "interaction": 0.25},
                })
    return out
