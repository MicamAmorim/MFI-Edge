from __future__ import annotations

"""Image-internal pointwise-mutual-information boundary context.

This is a bounded, equation-level surrogate of the affinity principle in
Isola et al. (ECCV 2014).  It deliberately stops before the paper's spectral
globalization: low PMI across a centered local pair becomes positive context
for the repository's unchanged localizer.
"""

import numpy as np


N_LEVELS = 256
JOINT_EXPONENT = 1.25
PSEUDOCOUNT = 1.0
PAIR_OFFSETS = ((0, 1), (1, 0), (1, 1), (1, -1))


def _quantize(image: np.ndarray) -> np.ndarray:
    return np.rint(np.clip(image, 0.0, 1.0) * (N_LEVELS - 1)).astype(np.uint8)


def pmi_dependency_context(image: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Return bounded evidence for weak statistical association across a pixel."""

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("PMI context requires one finite grayscale raster")
    if float(np.min(values)) < 0.0 or float(np.max(values)) > 1.0:
        raise ValueError("PMI context expects values in [0,1]")

    levels = _quantize(values)
    padded = np.pad(levels, 1, mode="reflect")
    height, width = levels.shape
    pair_fields: list[tuple[np.ndarray, np.ndarray]] = []
    joint_counts = np.full((N_LEVELS, N_LEVELS), PSEUDOCOUNT, dtype=np.float64)

    for dy, dx in PAIR_OFFSETS:
        a = padded[1 - dy : 1 - dy + height, 1 - dx : 1 - dx + width]
        b = padded[1 + dy : 1 + dy + height, 1 + dx : 1 + dx + width]
        pair_fields.append((a, b))
        np.add.at(joint_counts, (a.ravel(), b.ravel()), 1.0)
        np.add.at(joint_counts, (b.ravel(), a.ravel()), 1.0)

    joint_mass = joint_counts / float(np.sum(joint_counts))
    # Convert discrete masses to unit-interval density estimates before applying
    # the paper's rho exponent.  This preserves the dimensional convention of
    # the continuous KDE formulation; applying rho directly to masses would
    # make the score depend spuriously on the number of gray levels.
    joint = joint_mass * float(N_LEVELS * N_LEVELS)
    marginal = np.sum(joint_mass, axis=1) * float(N_LEVELS)
    evidence = np.zeros((height, width), dtype=np.float64)
    deficit_sum = 0.0
    for a, b in pair_fields:
        p_joint = joint[a, b]
        p_independent = marginal[a] * marginal[b]
        pmi = np.log(np.power(p_joint, JOINT_EXPONENT) / p_independent)
        deficit = np.maximum(-pmi, 0.0)
        deficit_sum += float(np.mean(deficit))
        evidence = np.maximum(evidence, 1.0 - np.exp(-deficit))

    cue = np.clip(evidence, 0.0, 1.0).astype(np.float32)
    return cue, {
        "cue_mean": float(np.mean(cue)),
        "cue_q90": float(np.quantile(cue, 0.9)),
        "cue_max": float(np.max(cue)),
        "positive_fraction": float(np.mean(cue > 0.0)),
        "mean_pair_deficit": float(deficit_sum / len(pair_fields)),
        "occupied_joint_bins": float(np.count_nonzero(joint_counts > PSEUDOCOUNT)),
    }


def synthetic_contract() -> dict[str, object]:
    size = 96
    flat = np.full((size, size), 0.25, dtype=np.float64)
    step = flat.copy()
    step[:, size // 2 :] = 0.75
    yy, xx = np.indices((size, size))
    checker = np.where(((yy // 2) + (xx // 2)) % 2 == 0, 0.25, 0.75)
    rng = np.random.default_rng(18010)
    noise = np.clip(0.25 + rng.normal(0.0, 0.01, (size, size)), 0.0, 1.0)

    flat_map, _ = pmi_dependency_context(flat)
    step_map, _ = pmi_dependency_context(step)
    repeat_map, _ = pmi_dependency_context(step)
    checker_map, _ = pmi_dependency_context(checker)
    noise_map, _ = pmi_dependency_context(noise)
    relabeled = np.where(step < 0.5, 0.10, 0.90)
    relabeled_map, _ = pmi_dependency_context(relabeled)

    band = np.zeros_like(step_map, dtype=bool)
    band[:, size // 2 - 1 : size // 2 + 2] = True
    step_band_mean = float(np.mean(step_map[band]))
    step_off_mean = float(np.mean(step_map[~band]))
    checker_mean = float(np.mean(checker_map))
    noise_mean = float(np.mean(noise_map))
    maps = (flat_map, step_map, checker_map, noise_map, relabeled_map)
    return {
        "finite": bool(all(np.all(np.isfinite(value)) for value in maps)),
        "bounded": bool(all(float(np.min(value)) >= 0.0 and float(np.max(value)) <= 1.0 for value in maps)),
        "flat_max": float(np.max(flat_map)),
        "step_band_mean": step_band_mean,
        "step_off_mean": step_off_mean,
        "checker_mean": checker_mean,
        "noise_mean": noise_mean,
        "step_localized": bool(step_band_mean > step_off_mean),
        "step_exceeds_checker": bool(step_band_mean > checker_mean),
        "step_exceeds_noise": bool(step_band_mean > noise_mean),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat_map))),
        "label_reassignment_max_abs_delta": float(np.max(np.abs(step_map - relabeled_map))),
    }
