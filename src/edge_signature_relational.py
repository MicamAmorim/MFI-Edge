from __future__ import annotations

"""Generic cross-scale relations for Stage 11c/12.

These features are image-derived and GT-free at inference.  GT is only used by
analysis scripts to decide which relations are worth keeping.  The module wraps
Stage-11's signature tensor without changing the historical implementation.
"""

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .edge_signature import EPS, GROUPS, SignatureSamples, population_masks, signature_tensor


def _entropy01(z: np.ndarray) -> np.ndarray:
    p = z / np.maximum(np.sum(z, axis=-1, keepdims=True), EPS)
    h = -np.sum(p * np.log(np.maximum(p, EPS)), axis=-1)
    den = np.log(max(z.shape[-1], 2))
    return np.clip(h / den, 0.0, 1.0)


def relational_signature_tensor(item: Mapping[str, object], feature_names: Sequence[str]):
    """Return Stage-11 features plus scale-relational properties for every descriptor."""
    base, names = signature_tensor(item, feature_names)
    pre = item["features"]
    scales = np.asarray([int(x[0]) for x in pre], dtype=float)
    arrays = [np.asarray(x[1], np.float32) for x in pre]
    stack = np.stack(arrays, axis=-2)  # H,W,scale,descriptor

    cols = [base]
    extra_names: list[str] = []
    extra_cols: list[np.ndarray] = []

    coarse_idx = np.flatnonzero(scales >= 13)
    fine_idx = np.flatnonzero(scales < 13)
    # 0=coarsest, 1=finest.  This is a generic ordinal scale coordinate.
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


def extract_relational_samples(items, feature_names, max_samples_per_group=2500, seed=20261005):
    Xs, gs, counts = [], [], []
    final_names = None
    for ii, item in enumerate(items):
        tensor, names = relational_signature_tensor(item, feature_names)
        if final_names is None:
            final_names = names
        elif names != final_names:
            raise RuntimeError("relational signature feature names changed across images")
        masks = population_masks(item)
        flat = tensor.reshape(-1, tensor.shape[-1])
        row = {"id": str(item["id"])}
        for gi, group in enumerate(GROUPS):
            ids = np.flatnonzero(np.asarray(masks[group], bool).ravel())
            if ids.size > int(max_samples_per_group):
                rng = np.random.default_rng(int(seed) + 1009 * ii + 97 * gi)
                ids = rng.choice(ids, size=int(max_samples_per_group), replace=False)
            row[group] = int(ids.size)
            if ids.size:
                Xs.append(flat[ids].astype(np.float32, copy=False))
                gs.append(np.full(ids.size, gi, dtype=np.int8))
        counts.append(row)
    if not Xs:
        raise RuntimeError("no relational signature samples extracted")
    return SignatureSamples(
        X=np.concatenate(Xs, axis=0),
        groups=np.concatenate(gs, axis=0),
        feature_names=list(final_names or []),
        counts_per_image=counts,
    )


def signature_map_from_spec(item, feature_names, spec):
    """Evaluate a frozen analytical signature specification over every pixel."""
    tensor, names = relational_signature_tensor(item, feature_names)
    index = {n: i for i, n in enumerate(names)}
    score = np.zeros(tensor.shape[:2], dtype=np.float32)
    for row in spec:
        x = np.asarray(tensor[..., index[str(row["feature"])]], float)
        z = float(row["direction"]) * (x - float(row["midpoint"])) / max(float(row["scale"]), EPS)
        mu = 1.0 / (1.0 + np.exp(-np.clip(z, -20.0, 20.0)))
        score += float(row["weight"]) * mu.astype(np.float32)
    return np.clip(score, 0.0, 1.0)
