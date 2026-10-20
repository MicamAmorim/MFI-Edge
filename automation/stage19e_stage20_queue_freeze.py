from __future__ import annotations

"""Planning-only checkpoint that freezes the finite Stage-20 candidate queue."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage19e_stage20_queue_freeze"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "19e-stage20-queue-freeze",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "authoritative_policy": "automation/STAGE19_GT_GUIDED_POLICY.md",
        "stage19d_result": {
            "recommended_family": "monotone_2additive_choquet",
            "weaker_domain_balanced_logloss": 0.5406465191267359,
            "weaker_domain_auc": 0.8220243551913964,
            "transfer_collapse": False,
            "interpretation": (
                "The constrained monotone 2-additive Choquet family led the fixed "
                "three-family comparison on the preregistered weaker-domain rule. "
                "Stage 19D remains identification evidence and did not promote a detector."
            ),
        },
        "required_work": [
            "Synthesize only the completed Stage 19B, 19C, and 19D development artifacts.",
            "Identify descriptors and interactions supported by the preregistered shared-development rules.",
            "Freeze an ordered queue of no more than four Stage-20 candidates before executing Stage 20A or reading any candidate BSDS500-validation result.",
            "Preregister every queued candidate's exact architecture, fitting and calibration, UDED repeated-CV protocol, BSDS500-validation exporter/evaluator, deterministic preview, runtime outputs, and numerical promotion thresholds.",
            "Register Stage 20A only after the complete queue and every candidate protocol are committed together.",
        ],
        "queue_constraints": {
            "maximum_candidates": 4,
            "family_priority": "monotone_2additive_choquet",
            "additive_logistic_status": "transfer_collapsed_under_preregistered_rule",
            "no_replacement_after_outcome": True,
            "no_fifth_candidate": True,
            "stop_after_queue_failure": "synthesize_and_stop_without_literature_escalation",
            "stop_after_pass": "freeze_promoted_generation_for_confirmation_planning",
        },
        "dataset_firewall": [
            "Use only Stage-19 development evidence to define the queue.",
            "Do not read BSDS500 validation while freezing the queue.",
            "Stage 20 uses UDED-selection leakage-free repeated CV and the unchanged official BSDS500-validation attachment.",
            "UDED held-out, BSDS500 test, BIPEDv2 test, and other protected outcomes cannot shape the queue.",
        ],
        "forbidden": [
            "Do not promote the Stage-19D family directly from probabilistic atlas metrics.",
            "Do not add an aggregation family or descriptor unsupported by Stage 19.",
            "Do not tune or replace a queued candidate after a Stage-20 outcome.",
            "Do not relax the conjunctive cross-dataset rule or use dataset identity.",
            "Do not fall back to open-ended literature escalation if the frozen queue fails.",
        ],
        "official_eval_manifest_omission": (
            "Required and justified: Stage 19E is a synthesis/preregistration checkpoint; "
            "it generates no detector map and reads no benchmark image or ground truth."
        ),
        "visual_preview_omission": (
            "Required and justified: Stage 19E is non-image planning. Every queued Stage-20 "
            "candidate must independently emit best_method_preview.png."
        ),
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE19E_QUEUE_FREEZE_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
