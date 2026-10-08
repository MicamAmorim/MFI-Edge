from __future__ import annotations

"""Repeatable autonomous Stage-15 research/literature checkpoint.

This checkpoint performs no fitting and inspects no protected external-test
labels. During Stage 15 it exists to keep the reproduction/diagnostic campaign
moving without falling back into open-ended mechanism invention.
"""

from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "autonomous_literature_escalation"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "stage15-autonomous-literature-escalation",
        "role": "literature_escalation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "active_research_generation": "stage15_reproduction_diagnosis_then_redesign",
        "scientific_context_files": [
            "automation/SCIENTIFIC_CONTEXT.md",
            "automation/research_goal.json",
            "automation/CODEX_POLICY.md",
            "docs/paper/STAGE15_RESEARCH_PROGRAM.md",
            "docs/paper/NONTRAINED_EDGE_METHODS_REVIEW_1986_2026.md",
            "docs/paper/STAGE15_LITERATURE_LEDGER.md",
            "docs/paper/AGENT_GENERATION_V14_SNAPSHOT.md",
            "docs/paper/EXPERIMENT_HISTORY.md",
            "docs/paper/BIBLIOGRAPHY_MATRIX.md",
            "docs/paper/SOTA_TARGETS.md",
            "ROADMAP.md",
        ],
        "requested_work": [
            "Read the Stage-15 research program, transition review, literature ledger, Stage-14 snapshot, persistent scientific context, and experiment history before proposing anything.",
            "Use live web search and high reasoning to verify primary papers, official author code, benchmark protocols, training status, and reproduction requirements relevant to the next Stage-15 step.",
            "Until Stage 15o is scientifically closed, prioritize protocol audit, exact/faithful reproduction, and error/complementarity diagnosis. Do not invent or promote a new MFI architecture during Stages 15a-15o.",
            "Follow the Stage-15 ordering unless a hard reproducibility dependency requires a documented reordering. The first new campaign action should be Stage 15a protocol/evaluator audit planning.",
            "For every paper/code/protocol that materially drives a decision, update docs/paper/STAGE15_LITERATURE_LEDGER.md in the same repository change that preregisters the experiment. Record DOI/official URL, source type, training class, protocol evidence, implementation fidelity, and decision role.",
            "Synchronize docs/paper/BIBLIOGRAPHY_MATRIX.md whenever a newly verified source belongs in the future manuscript; never leave decision-driving literature only in transient prompts/logs.",
            "Prefer primary peer-reviewed papers, official author repositories, and official benchmark sources. Mark secondary sources as such and do not use them alone to establish headline metrics or training status.",
            "Treat literature headline metrics as incomparable unless the evaluation protocol is matched. Preserve literature-reported and repository-re-evaluated numbers separately.",
            "Prefer exact author code or a faithful reproduction. If only a surrogate is feasible, label the missing elements explicitly and do not claim to have reproduced the original method.",
            "Refresh docs/paper/SOTA_TARGETS.md when the current frontier or benchmark protocol materially affects the decision.",
            "Register exactly one next Stage-15 experiment or bounded research step at a time, with deterministic qualitative outputs for image experiments and per-image outputs when needed for later Stage-15 complementarity analysis.",
            "Update automation/SCIENTIFIC_CONTEXT.md when the high-level scientific state changes, while preserving the Stage-14 lineage and negative results.",
        ],
        "forbidden": [
            "Do not use BSDS500 test, BIPEDv2 test, UDED held-out, or any inspected final/test result to choose architecture, parameters, experiment priority, or routing.",
            "Do not add neural networks, pretrained neural features, learned edge classifiers, or supervised boundary weights to the final non-neural inference path.",
            "Do not resume the Stage-14 pattern of mechanism invention before the Stage-15 reproduction/diagnostic campaign justifies it.",
            "Do not micro-tune a reproduced method after seeing its result.",
            "Do not treat Stage 14t as a reproduction or falsification of EDPF; the chain-first EDPF mechanism remains a distinct Stage-15 reproduction target.",
            "Do not declare a literature method SOTA from an unmatched or ambiguous F/F1/ODS number.",
            "Do not discard failed reproductions or negative results from the future-paper record.",
        ],
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15_AUTONOMOUS_LITERATURE_ESCALATION_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
