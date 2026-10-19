from __future__ import annotations

"""User-directed transition from open-ended cue search to bounded GT-guided analysis."""

from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage19a_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "19a-gt-guided-transition-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "user_directed_program": True,
        "authoritative_policy": "automation/STAGE19_GT_GUIDED_POLICY.md",
        "authoritative_preregistration": "docs/paper/STAGE19_GT_GUIDED_PROGRAM.md",
        "stage18z_decision": (
            "The fixed fold-fitted ICA response-concentration cue was ineligible in "
            "all 15 UDED folds and failed the BSDS500-validation ODS condition. "
            "The compact Choquet-gated Scharr+NMS controller remains incumbent."
        ),
        "direction_change": (
            "The user explicitly redirects the project away from open-ended one-cue-at-a-time "
            "Generation-2 escalation and into a finite GT-guided descriptor/aggregation study. "
            "This bounded program supersedes the generic fallback-to-another-mechanism behavior "
            "until Stage 19-20 is completed or the user explicitly changes it."
        ),
        "hard_budget": {
            "stage19_analysis_experiments": 3,
            "stage20_candidate_experiments_max": 4,
            "total_scientific_experiments_max": 7,
            "planning_checkpoints_not_counted": ["19A", "19E"],
            "after_four_stage20_failures": "stop_and_synthesize_no_automatic_literature_escalation",
            "after_stage20_promotion": "freeze_candidate_and_stop_queue_for_confirmation_planning",
        },
        "required_sequence": [
            "Stage 19B: GT/descriptor atlas and univariate relevance (experiment 1/3).",
            "Stage 19C: redundancy, conditional complementarity, pairwise interactions, cross-dataset stability (experiment 2/3).",
            "Stage 19D: compare exactly three interpretable aggregation families on a shortlist of at most six descriptors (experiment 3/3).",
            "Stage 19E: synthesis checkpoint; freeze an ordered queue of at most four Stage-20 candidates before any Stage-20 BSDS-val result is inspected.",
            "Stage 20A-20D: execute only the frozen queue; no candidate replacement or fifth candidate after outcomes are known.",
        ],
        "dataset_firewall": [
            "Stage 19B-19D may use BSDS500 train, preserving all individual human annotations.",
            "Stage 19B-19D must not read BSDS500 validation; reserve it for Stage-20 official development evaluation.",
            "Stage 19 may use UDED selection only as development, excluding all known BSDS-origin overlaps from GT-guided fitting/analysis and recording the overlap-clean manifest.",
            "All train/test resampling is grouped by image; random pixel splitting across train/test is forbidden.",
            "UDED held-out, BSDS500 test, BIPEDv2 test, and protected/external data are forbidden for Stage-19 selection or fitting.",
        ],
        "requested_work": [
            "Read automation/STAGE19_GT_GUIDED_POLICY.md and docs/paper/STAGE19_GT_GUIDED_PROGRAM.md before editing anything.",
            "Treat those files as authoritative for this user-directed bounded phase when they conflict with generic open-ended escalation guidance.",
            "Update ROADMAP.md, automation/SCIENTIFIC_CONTEXT.md, and docs/paper/EXPERIMENT_HISTORY.md to record the direction change without rewriting historical outcomes.",
            "Register exactly one next experiment: Stage 19B descriptor relevance atlas, following the frozen 12-cue pool and dataset firewall in the authoritative policy.",
            "Stage 19B must be analysis-only: no detector promotion, no BSDS-validation read, no architecture change, and no new descriptor invention.",
            "Ensure the Stage-19B runner emits machine-readable descriptor statistics, the overlap-clean dataset manifest, image-grouped uncertainty summaries, and deterministic qualitative visualizations.",
        ],
        "forbidden": [
            "Do not register another open-ended literature/mechanism escalation at this checkpoint.",
            "Do not add a thirteenth descriptor to the Stage-19 frozen pool after GT-guided results are inspected.",
            "Do not read BSDS500 validation during Stage 19B-19D.",
            "Do not use protected/final data or same-photo BSDS overlaps in UDED GT-guided fitting.",
            "Do not promote or alter the incumbent during Stage 19B-19D.",
            "Do not relax the finite budget or create a fifth Stage-20 candidate.",
            "Do not use fixed-seed diagnostic Berkeley matching for dataset scoring.",
        ],
        "official_eval_manifest_omission": (
            "Required and justified: Stage 19A is a transition/planning checkpoint and "
            "does not generate detector maps or benchmark scores."
        ),
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE19A_GT_GUIDED_TRANSITION_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
