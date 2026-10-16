from __future__ import annotations

"""Fixed Frei-Chen edge-subspace occupancy for Stage 17t.

Frei and Chen (IEEE Transactions on Computers, 1977) describe every 3x3
image patch in an orthonormal basis whose first four vectors span an edge
subspace, the next four span a line subspace, and the ninth is the average
component.  Stage 17t uses only the bounded cosine of the angle between a
patch and its edge-subspace projection.  It is a context cue, not a complete
reproduction of the paper's sequential binary boundary detector.
"""

import numpy as np
from scipy import ndimage as ndi


SUPPORT_SIZE = 3
EPSILON = 1.0e-15
SQRT2 = float(np.sqrt(2.0))


# Published Frei-Chen orthonormal basis.  The explicit normalizers matter:
# the original criterion is an angle/projection ratio in nine-dimensional
# patch space, so unnormalized masks would change the result.
FREI_CHEN_BASIS = np.asarray(
    [
        [[-1, -SQRT2, -1], [0, 0, 0], [1, SQRT2, 1]],
        [[1, 0, -1], [SQRT2, 0, -SQRT2], [1, 0, -1]],
        [[0, -1, SQRT2], [1, 0, -1], [-SQRT2, 1, 0]],
        [[SQRT2, -1, 0], [-1, 0, 1], [0, 1, -SQRT2]],
        [[0, 1, 0], [-1, 0, -1], [0, 1, 0]],
        [[-1, 0, 1], [0, 0, 0], [1, 0, -1]],
        [[1, -2, 1], [-2, 4, -2], [1, -2, 1]],
        [[-2, 1, -2], [1, 4, 1], [-2, 1, -2]],
        [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
    ],
    dtype=np.float64,
)
FREI_CHEN_BASIS[:4] /= np.sqrt(8.0)
FREI_CHEN_BASIS[4:6] /= 2.0
FREI_CHEN_BASIS[6:8] /= 6.0
FREI_CHEN_BASIS[8] /= 3.0


def _gray01(image: np.ndarray) -> np.ndarray:
    x = np.asarray(image, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("Frei-Chen context expects a two-dimensional image")
    if not np.all(np.isfinite(x)):
        raise ValueError("Frei-Chen context received non-finite input")
    if x.size and float(np.max(x)) > 1.5:
        x = x / 255.0
    return np.clip(x, 0.0, 1.0)


def frei_chen_edge_subspace_evidence(
    image: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return the fixed edge-subspace projection fraction in ``[0, 1]``.

    With normalized basis responses ``r_i``, the evidence is

    ``sqrt(sum_{i=1..4} r_i^2 / sum_{i=1..9} r_i^2)``.

    This is ``cos(theta_edge)`` in the paper.  A zero-energy patch receives
    zero rather than an undefined angle.  Reflection is the fixed finite-
    raster convention; there is no threshold or per-image normalization.
    """

    x = _gray01(image)
    responses = np.stack(
        [ndi.correlate(x, mask, mode="reflect") for mask in FREI_CHEN_BASIS],
        axis=-1,
    )
    squared = responses * responses
    edge_energy = np.sum(squared[..., :4], axis=-1)
    line_energy = np.sum(squared[..., 4:8], axis=-1)
    average_energy = squared[..., 8]
    total_energy = edge_energy + line_energy + average_energy
    evidence = np.sqrt(
        np.divide(
            edge_energy,
            total_energy,
            out=np.zeros_like(edge_energy),
            where=total_energy > EPSILON,
        )
    )
    evidence = np.clip(evidence, 0.0, 1.0).astype(np.float32)
    if not np.all(np.isfinite(evidence)):
        raise RuntimeError("non-finite Frei-Chen edge-subspace evidence")

    diagnostics = {
        "evidence_mean": float(np.mean(evidence)),
        "evidence_q90": float(np.quantile(evidence, 0.9)),
        "max_evidence": float(np.max(evidence)),
        "active_fraction": float(np.mean(evidence > 0.0)),
        "edge_energy_mean": float(np.mean(edge_energy)),
        "line_energy_mean": float(np.mean(line_energy)),
        "average_energy_mean": float(np.mean(average_energy)),
    }
    return evidence, diagnostics


def synthetic_contract() -> dict[str, float | bool]:
    size = 65
    center = size // 2
    flat = np.zeros((size, size), dtype=np.float64)
    step = np.zeros((size, size), dtype=np.float64)
    step[:, center:] = 1.0
    line = np.zeros((size, size), dtype=np.float64)
    line[:, center] = 1.0
    checker = (np.indices((size, size)).sum(axis=0) % 2).astype(np.float64)
    rng = np.random.default_rng(17018)
    noise = np.clip(0.5 + 0.001 * rng.standard_normal((size, size)), 0.0, 1.0)
    basis_edge = np.full((size, size), 0.5, dtype=np.float64)
    basis_line = np.full((size, size), 0.5, dtype=np.float64)
    basis_edge[center - 1 : center + 2, center - 1 : center + 2] += (
        0.25 * FREI_CHEN_BASIS[0]
    )
    basis_line[center - 1 : center + 2, center - 1 : center + 2] += (
        0.25 * FREI_CHEN_BASIS[4]
    )

    flat_map, _ = frei_chen_edge_subspace_evidence(flat)
    step_map, _ = frei_chen_edge_subspace_evidence(step)
    line_map, _ = frei_chen_edge_subspace_evidence(line)
    checker_map, _ = frei_chen_edge_subspace_evidence(checker)
    noise_map, _ = frei_chen_edge_subspace_evidence(noise)
    basis_edge_map, _ = frei_chen_edge_subspace_evidence(basis_edge)
    basis_line_map, _ = frei_chen_edge_subspace_evidence(basis_line)
    repeat, _ = frei_chen_edge_subspace_evidence(step)
    scaled, _ = frei_chen_edge_subspace_evidence(0.5 * step)

    gram = FREI_CHEN_BASIS.reshape(9, 9) @ FREI_CHEN_BASIS.reshape(9, 9).T
    orthonormal_max_abs_error = float(np.max(np.abs(gram - np.eye(9))))
    band = np.s_[:, center - 1 : center + 2]
    step_band_mean = float(np.mean(step_map[band]))
    line_band_mean = float(np.mean(line_map[band]))
    checker_mean = float(np.mean(checker_map[2:-2, 2:-2]))
    noise_mean = float(np.mean(noise_map[2:-2, 2:-2]))
    basis_edge_center = float(basis_edge_map[center, center])
    basis_line_center = float(basis_line_map[center, center])
    return {
        "finite": bool(
            all(
                np.all(np.isfinite(value))
                for value in (flat_map, step_map, line_map, checker_map)
            )
        ),
        "bounded": bool(float(np.min(step_map)) >= 0.0 and float(np.max(step_map)) <= 1.0),
        "flat_max": float(np.max(np.abs(flat_map))),
        "repeat_max_abs_delta": float(np.max(np.abs(step_map - repeat))),
        "positive_scale_max_abs_delta": float(np.max(np.abs(step_map - scaled))),
        "orthonormal_max_abs_error": orthonormal_max_abs_error,
        "step_band_mean": step_band_mean,
        "line_band_mean": line_band_mean,
        "checker_mean": checker_mean,
        "noise_mean": noise_mean,
        "basis_edge_center": basis_edge_center,
        "basis_line_center": basis_line_center,
        "basis_edge_exceeds_line": bool(basis_edge_center > basis_line_center),
        "step_exceeds_checker": bool(step_band_mean > checker_mean),
        "step_exceeds_noise": bool(step_band_mean > noise_mean),
        "support_size": SUPPORT_SIZE,
    }
