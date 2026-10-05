from __future__ import annotations

"""Stable entrypoint for the local CH-MFI research benchmark.

This wrapper keeps compatibility between the local runner and Stage-7 helper
function signatures while the exploratory benchmark evolves independently.
"""

import benchmark_local_ch_mfi as bench
from benchmark_uded_stage7 import (
    bootstrap_delta as _bootstrap_delta,
    tolerance_error_map as _tolerance_error_map,
)


def _bootstrap_compat(candidate_counts, baseline_counts, n_boot=5000, seed=20261004):
    r = _bootstrap_delta(baseline_counts, candidate_counts, n_boot=n_boot, seed=seed)
    return {
        "ci_low": r["delta_F1_ci95_low"],
        "ci_high": r["delta_F1_ci95_high"],
        "p_positive": r["p_delta_gt_0"],
        **r,
    }


def _tolerance_compat(pred, gt, tol):
    return _tolerance_error_map(gt, pred, tol)


bench.bootstrap_delta = _bootstrap_compat
bench.tolerance_error_map = _tolerance_compat


if __name__ == "__main__":
    bench.main()
