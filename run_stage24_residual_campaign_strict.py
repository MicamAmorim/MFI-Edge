from __future__ import annotations

"""Strict Stage-24 entry point.

Hardens the base Stage-24 runner so every aggregator/suppressor threshold used
for scientific selection is chosen with the same canonical one-to-one matcher.
It also records the official-Berkeley reference-reproduction guard after the
campaign.  The BSDS exporter remains the frozen, GT-blind base exporter.
"""

from pathlib import Path
import json
import sys
import numpy as np

import run_stage24_residual_campaign as base
from src.stage24_integrity import deterministic_seed, select_threshold
from src.stage24_residual import (
    aggregate_memberships,
    apply_membership,
    apply_suppressor,
    fit_membership,
    fit_nonnegative_fusion,
    fit_residual_gate,
)


def strict_screen_recipe(pair_maps, gts, train, seed):
    membership = fit_membership(pair_maps, gts, train)
    memberships = [
        apply_membership([pair_maps[0][i], pair_maps[1][i]], membership)
        for i in range(len(gts))
    ]
    logistic = fit_nonnegative_fusion(
        pair_maps,
        gts,
        train,
        membership,
        seed=deterministic_seed(seed, "fusion"),
    )
    train_gts = [gts[int(i)] for i in train]

    aggregate_candidates = []
    for aggregator in (
        "equal_mean",
        "minimum",
        "maximum",
        "median",
        "nonnegative_logistic",
    ):
        scores = [aggregate_memberships(m, aggregator, logistic) for m in memberships]
        train_scores = [scores[int(i)] for i in train]
        selected = select_threshold(
            train_scores,
            train_gts,
            count=41,
            tolerance_ratio=base.TOL,
        )
        aggregate_candidates.append(
            ((float(selected["F1"]), float(selected["precision"]), aggregator), aggregator, scores)
        )
    _, aggregator, base_scores = max(aggregate_candidates, key=lambda x: x[0])

    gate = fit_residual_gate(
        base_scores,
        memberships,
        gts,
        train,
        seed=deterministic_seed(seed, "gate"),
    )
    suppressor_candidates = []
    for kind, parameter in (
        ("identity", 1.0),
        ("local_coherence", 2.0),
        ("local_coherence", 4.0),
        ("disagreement", 0.5),
        ("disagreement", 1.0),
        ("compress", 1.5),
        ("learned_gate", 0.5),
        ("learned_gate", 1.0),
        ("learned_gate", 2.0),
    ):
        scores = [
            apply_suppressor(
                base_scores[i],
                memberships[i],
                kind=kind,
                parameter=parameter,
                gate_model=gate,
            )
            for i in range(len(gts))
        ]
        train_scores = [scores[int(i)] for i in train]
        selected = select_threshold(
            train_scores,
            train_gts,
            count=41,
            tolerance_ratio=base.TOL,
        )
        suppressor_candidates.append(
            (
                (
                    float(selected["F1"]),
                    float(selected["precision"]),
                    kind,
                    -float(parameter),
                ),
                kind,
                float(parameter),
                float(selected["threshold"]),
            )
        )
    _, kind, parameter, threshold = max(suppressor_candidates, key=lambda x: x[0])

    # Recompute the selected candidate's canonical train metrics for provenance.
    final_scores = []
    for i in range(len(gts)):
        fusion = aggregate_memberships(memberships[i], aggregator, logistic)
        final_scores.append(
            apply_suppressor(
                fusion,
                memberships[i],
                kind=kind,
                parameter=parameter,
                gate_model=gate,
            )
        )
    train_selected = select_threshold(
        [final_scores[int(i)] for i in train],
        train_gts,
        count=41,
        tolerance_ratio=base.TOL,
    )
    recipe = {
        "aggregator": aggregator,
        "suppressor": kind,
        "parameter": parameter,
        "threshold": float(train_selected["threshold"]),
        "train_F1": float(train_selected["F1"]),
        "train_precision": float(train_selected["precision"]),
        "train_recall": float(train_selected["recall"]),
        "threshold_contract": "canonical_one_to_one_matcher_only",
    }
    return recipe, membership, logistic, gate


def _find_reference_verified(obj) -> bool:
    if isinstance(obj, dict):
        if obj.get("reference_reproduction_verified") is True:
            return True
        return any(_find_reference_verified(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_find_reference_verified(v) for v in obj)
    return False


def _record_final_claim_guard() -> None:
    summary_path = base.OUT_DEFAULT / "summary.json"
    if not summary_path.is_file():
        return
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    official = summary.get("official_evaluation")
    verified = _find_reference_verified(official)
    completed = isinstance(official, dict) and official.get("status") == "completed"
    summary["final_claim_guard"] = {
        "official_evaluation_completed": bool(completed),
        "reference_reproduction_verified": bool(verified),
        "final_claim_eligible": bool(completed and verified),
        "rule": (
            "BSDS validation can be reported as development evidence when completed, "
            "but final benchmark/SOTA claims remain blocked until the pinned official "
            "Berkeley path has reproduced its registered reference output."
        ),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str), encoding="utf-8")


def main() -> int:
    base.screen_recipe = strict_screen_recipe
    rc = base.main()
    if "--export-bsds" not in sys.argv:
        _record_final_claim_guard()
    return int(rc)


if __name__ == "__main__":
    raise SystemExit(main())
