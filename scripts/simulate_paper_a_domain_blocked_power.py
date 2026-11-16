#!/usr/bin/env python3
"""Synthetic pre-freeze power study for a CANDIDATE within-domain H1/H2 test.

No research image/map/GT/F1/data files are opened. For n untied independent
scene groups, the conditional within-domain rank-permutation null distribution
is invariant to actual rank ordering, so a reusable Monte Carlo reference is
valid. This is NOT an implemented/frozen change to protocol.json.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import numpy as np

SCENARIOS = {
    "null_with_domain_shift": (0.0, 0.0, 1.2),
    "homogeneous_rho_020": (0.20, 0.20, 0.4),
    "homogeneous_rho_025": (0.25, 0.25, 0.4),
    "homogeneous_rho_030": (0.30, 0.30, 0.4),
    "heterogeneous_rho_030_010": (0.30, 0.10, 0.8),
    "sign_reversal_rho_025_minus010": (0.25, -0.10, 0.8),
}
DESIGNS = ((75, 75), (90, 90), (105, 95), (125, 95), (145, 95))


def ranks_z(x):
    n = len(x)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(n, dtype=np.float64)
    ranks[order] = np.arange(1, n + 1, dtype=np.float64)
    ranks -= (n + 1) / 2
    return ranks / math.sqrt(n * (n + 1) / 12)


def pooled_within_domain(x1, y1, x2, y2, n1):
    n = len(x1)
    t1 = t2 = 0.0
    for start, end in ((0, n1), (n1, n)):
        t1 -= float(np.dot(ranks_z(x1[start:end]), ranks_z(y1[start:end])))
        t2 += float(np.dot(ranks_z(x2[start:end]), ranks_z(y2[start:end])))
    return t1 / (n - 2), t2 / (n - 2)


def null_distribution(n1, n2, nperm, rng):
    if min(n1, n2) < 10 or nperm < 1000:
        raise ValueError("Require >=10 scene groups/domain and >=1000 null draws")
    groups = []
    for n in (n1, n2):
        r = np.arange(n, dtype=np.float64) - (n - 1) / 2
        groups.append(r / math.sqrt(n * (n + 1) / 12))
    values = np.empty(nperm, dtype=float)
    for i in range(nperm):
        values[i] = (
            np.dot(groups[0], rng.permutation(groups[0]))
            + np.dot(groups[1], rng.permutation(groups[1]))
        ) / (n1 + n2 - 2)
    values.sort()
    return values


def directed_p(t, null_sorted):
    index = int(np.searchsorted(null_sorted, t, side="left"))
    return (len(null_sorted) - index + 1) / (len(null_sorted) + 1)


def holm_two(p1, p2, alpha=0.05):
    low, high = (0, 1) if p1 <= p2 else (1, 0)
    p = [p1, p2]
    adjusted = [0., 0.]
    adjusted[low] = min(1., 2 * p[low])
    adjusted[high] = min(1., max(adjusted[low], p[high]))
    return (adjusted[0] < alpha, adjusted[1] < alpha)


def synthetic_sample(n1, n2, rho_a, rho_b, shift, rng):
    n = n1 + n2
    z = rng.standard_normal((n, 4))
    x1 = z[:, 0]
    x2 = 0.4 * z[:, 0] + math.sqrt(1 - 0.4**2) * z[:, 1]
    e1 = z[:, 2]
    e2 = 0.4 * z[:, 2] + math.sqrt(1 - 0.4**2) * z[:, 3]
    rho = np.r_[np.repeat(rho_a, n1), np.repeat(rho_b, n2)]
    # Gaussian-copula Pearson correlation corresponding to intended Spearman.
    pearson = 2 * np.sin(np.pi * rho / 6)
    y1 = -pearson * x1 + np.sqrt(1 - pearson**2) * e1
    y2 = pearson * x2 + np.sqrt(1 - pearson**2) * e2
    groups = np.r_[np.repeat(-.5, n1), np.repeat(.5, n2)]
    return (x1 + shift * groups, y1 - shift * groups,
            x2 + shift * groups, y2 + shift * groups)


def simulate_design(n1, n2, reps, nperm, seed):
    rng = np.random.default_rng(np.random.SeedSequence([seed, n1, n2]))
    null = null_distribution(n1, n2, nperm, rng)
    results = []
    for label, (ra, rb, shift) in SCENARIOS.items():
        hits = np.zeros(4, dtype=int)
        sums = np.zeros(2)
        for _ in range(reps):
            observations = synthetic_sample(n1, n2, ra, rb, shift, rng)
            t1, t2 = pooled_within_domain(*observations, n1)
            p1, p2 = directed_p(t1, null), directed_p(t2, null)
            h1, h2 = holm_two(p1, p2)
            hits += (int(h1), int(h2), int(h1 and h2), int(h1 or h2))
            sums += (t1, t2)
        results.append({
            "BIPED_n": n1, "MultiCue_n": n2, "total_n": n1 + n2,
            "scenario": label, "assumed_abs_spearman_rho": {"BIPED": ra, "MultiCue": rb},
            "between_domain_shift": shift,
            "power_H1": round(float(hits[0] / reps), 4),
            "power_H2": round(float(hits[1] / reps), 4),
            "power_both": round(float(hits[2] / reps), 4),
            "probability_any_rejection": round(float(hits[3] / reps), 4),
            "mean_oriented_rho": [round(float(x / reps), 4) for x in sums],
            "max_binomial_MC_SE": round(0.5 / math.sqrt(reps), 4),
        })
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicates", type=int, default=1000)
    parser.add_argument("--null-permutations", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261115)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.replicates < 100 or args.null_permutations < 1000:
        parser.error("At least 100 replicates and 1000 null permutations required")
    rows = []
    for na, nb in DESIGNS:
        rows.extend(simulate_design(na, nb, args.replicates,
                                    args.null_permutations, args.seed))
        print(f"Design {na}+{nb} complete; {len(SCENARIOS)} synthetic scenarios",
              flush=True)
    report = {
        "status": "SYNTHETIC_DOMAIN_BLOCKED_POWER_CANDIDATE_NOT_FROZEN",
        "statistic_proposal": "weighted mean within-domain Spearman rho, weights n_d-1",
        "alternatives": {"H1": "negative", "H2": "positive"},
        "test": "domain-blocked permutation null, one-sided p, Holm for two hypotheses",
        "null_generation": "reusable exact continuous-rank permutation structure",
        "per_design_null_draws": args.null_permutations,
        "simulation_replicates_per_scenario": args.replicates,
        "random_seed": args.seed,
        "assumed_effects_are_not_estimated_from_exploratory_data": True,
        "BIPED_candidates_not_independence_certified": 198,
        "MultiCue_max_candidate_capture_groups_after_4113_hold": 95,
        "primary_statistic_NOT_YET_FROZEN": True,
        "research_images_maps_GT_H5_F1_opened": False,
        "results": rows,
        "limitations": [
            "Synthetic Gaussian-copula observations, assumed effect sizes",
            "No image/scene dependence between groups, no ties or missing values",
            "No observed data, no true effect estimate, no real cohort selection",
            "A rank-pool within-domain statistic is proposed, not yet preregistered",
            "Null distribution reuse assumes continuous independent within-domain ranks",
            "Full confirmatory inference still requires locked 100000 permutations",
            "Group identity, evaluator/GT, calibration and sampling remain gates before freeze",
        ],
    }
    if args.output:
        path = args.output.expanduser().resolve()
        if not path.parent.is_dir():
            parser.error("Output parent directory must exist")
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    compact = {k: v for k, v in report.items() if k != "results"}
    compact["result_rows"] = len(rows)
    compact["N150_results"] = rows[:len(SCENARIOS)]
    print(json.dumps(compact, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
