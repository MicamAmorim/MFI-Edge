from __future__ import annotations

"""Convex pairwise-ranking fit for a monotone 2-additive capacity."""

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, minimize

from .fuzzy_measures import capacity_table_2additive, interaction_matrix, shapley_values, validate_capacity_table
from .measure_learning import _pair_index, _two_additive_design, _two_additive_monotonicity


def learn_pairwise_2additive(
    uded_pairs: tuple[np.ndarray, np.ndarray],
    bsds_pairs: tuple[np.ndarray, np.ndarray],
    *,
    ridge: float = 1.0e-4,
    maxiter: int = 700,
) -> dict:
    """Fit one normalized monotone capacity from two equally weighted domains.

    Each pair is ``(higher_target_membership, lower_target_membership)``.  The
    two mean logistic ranking losses receive equal weight, so the 200-image
    BSDS-train source cannot numerically swamp the small UDED source.
    """

    domains = []
    n = None
    pairs = None
    for higher, lower in (uded_pairs, bsds_pairs):
        higher = np.asarray(higher, dtype=float)
        lower = np.asarray(lower, dtype=float)
        if higher.ndim != 2 or lower.shape != higher.shape or len(higher) == 0:
            raise ValueError("each ranking domain needs nonempty aligned 2-D pair arrays")
        design_hi, current_pairs = _two_additive_design(np.clip(higher, 0.0, 1.0))
        design_lo, _ = _two_additive_design(np.clip(lower, 0.0, 1.0))
        if n is None:
            n = higher.shape[1]
            pairs = current_pairs
        elif higher.shape[1] != n or current_pairs != pairs:
            raise ValueError("ranking domains disagree on descriptor dimension")
        domains.append(design_hi - design_lo)

    assert n is not None and pairs is not None
    p = n + len(pairs)
    _, pair_to_idx = _pair_index(n)
    monotonicity = _two_additive_monotonicity(n, pairs, pair_to_idx)
    initial = np.zeros(p, dtype=float)
    initial[:n] = 1.0 / n

    def objective(z: np.ndarray) -> tuple[float, np.ndarray]:
        loss = 0.0
        gradient = np.zeros_like(z)
        for design in domains:
            margin = design @ z
            loss += 0.5 * float(np.mean(np.logaddexp(0.0, -margin)))
            inverse = -1.0 / (1.0 + np.exp(np.clip(margin, -40.0, 40.0)))
            gradient += 0.5 * (design.T @ inverse) / len(design)
        loss += 0.5 * ridge * float(z[n:] @ z[n:])
        gradient[n:] += ridge * z[n:]
        return loss, gradient

    result = minimize(
        objective,
        initial,
        jac=True,
        method="SLSQP",
        bounds=Bounds(np.r_[np.zeros(n), -np.ones(p - n)], np.ones(p)),
        constraints=[
            LinearConstraint(np.ones((1, p)), 1.0, 1.0),
            LinearConstraint(monotonicity, 0.0, np.inf),
        ],
        options={"maxiter": int(maxiter), "ftol": 1.0e-9, "disp": False},
    )
    z = np.asarray(result.x if result.success else initial, dtype=float)
    pair_matrix = np.zeros((n, n), dtype=float)
    for offset, (i, j) in enumerate(pairs):
        pair_matrix[i, j] = pair_matrix[j, i] = z[n + offset]
    table = capacity_table_2additive(z[:n], pair_matrix)
    if not validate_capacity_table(table, tol=5.0e-6):
        raise RuntimeError("pairwise capacity fit violated monotonicity")
    return {
        "kind": "two_additive_pairwise_consensus",
        "singletons": z[:n].tolist(),
        "pairs": pair_matrix.tolist(),
        "capacity_table": table.tolist(),
        "fit_success": bool(result.success),
        "fit_message": str(result.message),
        "objective": float(result.fun),
        "uded_pairs": int(len(domains[0])),
        "bsds_pairs": int(len(domains[1])),
        "shapley": shapley_values(table).tolist(),
        "interaction": interaction_matrix(table).tolist(),
    }
