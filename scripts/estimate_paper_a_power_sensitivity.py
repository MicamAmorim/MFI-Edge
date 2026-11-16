#!/usr/bin/env python3
"""Pre-freeze approximate power sensitivity for H1/H2. NO dataset/GT/F1 read.

Normal Fisher-z heuristic for rank-rho magnitude; NOT a formal Spearman
permutation or domain-blocked power simulation. Assumes n independent scenes,
one-sided alpha .025 for each of two Holm-controlled primary tests.
Exploratory rhos are deliberately excluded from assumptions.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist

NORMAL = NormalDist()


def approx_power(n: int, rho: float, alpha: float = 0.025) -> float:
    if n < 8 or not (0 <= rho < 1) or not (0 < alpha < 0.05):
        raise ValueError("Require n >= 8, 0 <= |rho| < 1 and 0 < alpha < .05")
    z = math.atanh(rho) * math.sqrt(n - 3)
    return NORMAL.cdf(z - NORMAL.inv_cdf(1 - alpha))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", nargs="+", type=int, default=[120, 150, 180, 200])
    parser.add_argument("--rho", nargs="+", type=float,
                        default=[0.15, 0.20, 0.25, 0.30, 0.35, 0.40])
    parser.add_argument("--target-power", type=float, default=0.80)
    parser.add_argument("--alpha", type=float, default=0.025)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 0 < args.target_power < 1:
        parser.error("--target-power must be within (0,1)")
    if any(n < 8 for n in args.n) or any(not 0 <= r < 1 for r in args.rho):
        parser.error("N must be >=8 and rho must be in [0,1)")
    grid = [
        {
            "independent_groups": n,
            "assumed_abs_rho": rho,
            "approx_one_sided_power": round(approx_power(n, rho, args.alpha), 4),
        }
        for n in sorted(set(args.n))
        for rho in sorted(set(args.rho))
    ]
    required = {
        str(rho): next(
            (n for n in range(8, 1001)
             if approx_power(n, rho, args.alpha) >= args.target_power),
            None,
        )
        for rho in sorted(set(args.rho))
    }
    report = {
        "status": "APPROXIMATE_POWER_SCREEN_NOT_FINAL_POWER_ANALYSIS",
        "method": "Fisher-z normal heuristic for assumed magnitude of Spearman rho",
        "family": ["H1_negative_Spearman", "H2_positive_Spearman"],
        "conservative_alpha_per_test": args.alpha,
        "holm_fwer_target": 0.05,
        "target_power": args.target_power,
        "required_n_approx_by_assumed_abs_rho": required,
        "grid": grid,
        "tentative_total_n": 150,
        "sample_unit": "independent original scene/capture group, never repeated frame or fold",
        "max_multicue_capture_groups_after_4113_hold": 95,
        "biped_train_images_not_independence_certified": 198,
        "assumptions_from_exploratory_rho": False,
        "confirmatory_GT_H5_F1_or_images_opened": False,
        "required_next_step": (
            "Design-matched Spearman simulation with domain-blocked permutation, "
            "heterogeneity and scene-level sampling before freeze"
        ),
        "caveats": [
            "Uses Pearson Fisher-z approximation applied to rank rho, not exact Spearman sampling",
            "Does not model within-domain differences, ties, cluster dependence or Holm joint power",
            "The exploratory magnitude (~0.8) is selection-biased and MUST NOT be used for power",
            "The result is only a screening grid; no cohort selection or freeze authorized"
        ],
    }
    if args.output:
        out = args.output.expanduser().resolve()
        if not out.parent.is_dir():
            parser.error("Output parent directory must exist")
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
