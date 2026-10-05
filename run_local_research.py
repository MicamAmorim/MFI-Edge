from __future__ import annotations

"""Stable entrypoint for the local CH-MFI research benchmark.

This wrapper keeps compatibility between the local runner and Stage-7 bootstrap
field names while the exploratory benchmark evolves independently.
"""

import benchmark_local_ch_mfi as bench
from benchmark_uded_stage7 import bootstrap_delta as _bootstrap_delta


def _bootstrap_compat(candidate_counts, baseline_counts, n_boot=5000, seed=20261004):
    r = _bootstrap_delta(baseline_counts, candidate_counts, n_boot=n_boot, seed=seed)
    return {
        "ci_low": r["delta_F1_ci95_low"],
        "ci_high": r["delta_F1_ci95_high"],
        "p_positive": r["p_delta_gt_0"],
        **r,
    }


bench.bootstrap_delta = _bootstrap_compat


if __name__ == "__main__":
    bench.main()
