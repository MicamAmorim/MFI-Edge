from __future__ import annotations

"""Cheap checkpoint that asks the on-demand Codex step to plan the next valid stage.

This script does no model fitting and does not inspect external-test labels. It only
writes a compact protocol-planning event for the controller. The Codex analysis
that follows may use live web search when supported by the local CLI, inspect the
paper record, and prepare exactly one scientifically valid next experiment.
"""

from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage13b_protocol_research"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "13b-protocol-research",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scientific_context": [
            "Stage 13a BSDS500 test was already run once with frozen Stage-12d candidates.",
            "BSDS500 test feedback must not tune descriptors, thresholds, hyperparameters, or architecture.",
            "The next evidence should be an independent frozen replication (preferably BIPED) and/or publication-grade official Berkeley evaluation.",
        ],
        "requested_work": [
            "Inspect ROADMAP.md, automation/research_goal.json, docs/paper and Stage-13a documentation.",
            "Use current academic/primary sources when web search is available; prioritize the official DexiNed/BIPED source and Berkeley BSDS benchmark resources.",
            "Define the exact BIPED version/layout/protocol and a reproducible way to obtain or validate the dataset without using BSDS test feedback for tuning.",
            "Define how the official Berkeley boundary benchmark will be run or reproduced from exported score maps.",
            "Implement the smallest safe next runner, add it to automation/experiments.json, run only quick smoke/syntax checks, and return that experiment id.",
            "If a required dataset/tool cannot be obtained safely without a human action, register a deterministic preflight/download-validation experiment rather than inventing a path.",
        ],
        "forbidden": [
            "No re-fitting or re-ranking on BSDS500 test.",
            "No new architecture chosen from BSDS500 test behavior.",
            "No broad brute-force sweep.",
        ],
        "preferred_next_sequence": [
            "BIPED frozen replication",
            "official Berkeley evaluation of frozen score maps",
            "only then decide whether to close the current model generation or open a new development cycle",
        ],
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("RESEARCH_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
