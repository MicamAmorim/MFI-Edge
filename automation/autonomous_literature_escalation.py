from __future__ import annotations

"""Repeatable autonomous research/literature escalation checkpoint.

This checkpoint performs no fitting and inspects no protected external-test
labels. It exists so the controller can keep the scientific loop moving when a
completed development experiment has no obvious immediate successor.
"""

from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "autonomous_literature_escalation"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "autonomous-literature-escalation",
        "role": "literature_escalation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scientific_context_files": [
            "automation/SCIENTIFIC_CONTEXT.md",
            "automation/research_goal.json",
            "automation/CODEX_POLICY.md",
            "docs/paper/EXPERIMENT_HISTORY.md",
            "docs/paper/BIBLIOGRAPHY_MATRIX.md",
            "docs/paper/SOTA_TARGETS.md",
            "ROADMAP.md",
        ],
        "requested_work": [
            "Read the persistent scientific context and current experiment history before proposing anything.",
            "Use live web search and high reasoning to inspect current primary literature and official benchmark sources relevant to the present failure mode and the generalized non-neural SOTA objective.",
            "Refresh docs/paper/SOTA_TARGETS.md when current neural SOTA or benchmark protocol information is material to the next decision.",
            "Identify a small set of mechanistically distinct non-neural hypotheses; avoid merely micro-tuning a recently failed family.",
            "Choose and preregister exactly one next minimal falsification experiment, or a bounded hypothesis-led search when a single point test would be uninformative.",
            "The next experiment must use development-authorized data only and must emit deterministic qualitative preview artifacts when image-based.",
            "Update automation/SCIENTIFIC_CONTEXT.md if the high-level scientific state changes.",
        ],
        "forbidden": [
            "Do not use BSDS500 test, BIPEDv2 test, UDED held-out, or any inspected final/test result to choose the next architecture or parameters.",
            "Do not add neural networks or pretrained neural features to the final inference path.",
            "Do not stop merely because the previous hypothesis failed or the next mechanism is uncertain.",
            "Do not declare goal_reached from a single development metric or an incomparable literature number.",
        ],
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("AUTONOMOUS_LITERATURE_ESCALATION_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
