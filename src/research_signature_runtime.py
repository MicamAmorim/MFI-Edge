from __future__ import annotations

"""Inference-only Stage-11/12 signature maps used by the WebUI.

This module contains no GT-dependent fitting logic. It mirrors the image-derived
signature and cross-scale relations used by the active research lineage so a
separate WebUI worktree can run frozen research artifacts from mfi-edge-local-dev.
"""

from typing import Mapping, Sequence

import numpy as np
from scipy import ndimage as ndi

from .features import gray_float, robust01

EPS = 1e-9


def _sample_along(g: np.ndarray, nx: np.ndarray, ny: np.ndarray, radius: float):
    yy, xx = np.mgrid[: g.shape[0], : g.shape[1]]
    plus = ndi.map_coordinates(g, [yy + radius * ny, xx + radius * nx], order=1, mode="reflect")
    minus = ndi.map_coordinates(g, [yy - radius * ny, xx - radius * nx], order=1, mode="reflect")
    return plus, minus


def structural_signature_maps(image: np.ndarray, scales: Sequence[int]):
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
    pre = item["features"]
    scales = [int(x[0]) for x in pre]
    arrays = [np.asarray(x[1], np.float32) for x in pre]
    stack = np.stack(arrays, axis=-2)
    names: list[str] = []
    cols: list[np.ndarray] = []

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


def _entropy01(z: np.ndarray) -> np.ndarray:
    p = z / np.maximum(np.sum(z, axis=-1, keepdims=True), EPS)
    h = -np.sum(p * np.log(np.maximum(p, EPS)), axis=-1)
    den = np.log(max(z.shape[-1], 2))
    return np.clip(h / den, 0.0, 1.0)


def relational_signature_tensor(item: Mapping[str, object], feature_names: Sequence[str]):
    base, names = signature_tensor(item, feature_names)
    pre = item["features"]
    scales = np.asarray([int(x[0]) for x in pre], dtype=float)
    arrays = [np.asarray(x[1], np.float32) for x in pre]
    stack = np.stack(arrays, axis=-2)

    cols = [base]
    extra_names: list[str] = []
    extra_cols: list[np.ndarray] = []

    coarse_idx = np.flatnonzero(scales >= 13)
    fine_idx = np.flatnonzero(scales < 13)
    fineness = np.linspace(0.0, 1.0, len(scales), dtype=np.float32)

    for di, name in enumerate(feature_names):
        z = np.asarray(stack[..., :, di], np.float32)
        fine = np.mean(z[..., fine_idx], axis=-1)
        coarse = np.mean(z[..., coarse_idx], axis=-1)
        zmax = np.max(z, axis=-1)
        zmean = np.mean(z, axis=-1)
        total = np.sum(z, axis=-1)

        balance = fine / np.maximum(fine + coarse, EPS)
        delta01 = np.clip(0.5 + 0.5 * (fine - coarse), 0.0, 1.0)
        persistence = np.clip(zmean / np.maximum(zmax, EPS), 0.0, 1.0)
        entropy = _entropy01(z)
        centroid = np.sum(z * fineness.reshape((1, 1, -1)), axis=-1) / np.maximum(total, EPS)
        peak_idx = np.argmax(z, axis=-1)
        peak_fineness = fineness[peak_idx]

        rels = {
            f"{name}_fine_coarse_balance": balance,
            f"{name}_fine_coarse_delta01": delta01,
            f"{name}_scale_persistence": persistence,
            f"{name}_scale_entropy": entropy,
            f"{name}_scale_centroid": centroid,
            f"{name}_peak_fineness": peak_fineness,
        }
        for n, v in rels.items():
            extra_names.append(n)
            extra_cols.append(np.asarray(v, np.float32))

    if extra_cols:
        cols.append(np.stack(extra_cols, axis=-1))
    out = np.concatenate(cols, axis=-1).astype(np.float32)
    out = np.nan_to_num(out, nan=0.0, posinf=1.0, neginf=0.0)
    return out, list(names) + extra_names
