from __future__ import annotations

"""Repeatable Stage-23 literature/mechanism research checkpoint.

No fitting, benchmark scoring, or protected split access occurs here. The
controller invokes Codex after this checkpoint with the Stage-23 agenda and
high-reasoning/live-web research mode.
"""

from datetime import datetime, timezone
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage23_literature_escalation"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "completed",
        "experiment_id": "stage23_literature_escalation",
        "role": "literature_escalation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_access": "none",
        "detector_scoring": False,
        "requested_work": [
            "Read docs/paper/STAGE23_EVIDENCE_AGGREGATION_CAMPAIGN.md, automation/STAGE23_POLICY.md, automation/STAGE23_CONTEXT.md, and the latest Stage-23 results before proposing anything.",
            "Use primary literature and official code/benchmark sources to resolve the current scientific uncertainty.",
            "Preserve extract-once/cache-first semantics for all reusable descriptor and transform maps.",
            "Keep literature-reported metrics separate from local matched-protocol re-evaluations.",
            "Register exactly one next experiment in automation/stage23_experiments.json unless the agenda explicitly authorizes a bounded batch.",
        ],
        "forbidden": [
            "No protected/test feedback may drive architecture or experiment selection.",
            "Do not reopen Stage 22 or tune rejected Stage-22 mechanisms.",
            "Do not bypass the complementarity-first ordering with an unrestricted descriptor powerset search.",
        ],
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE23_LITERATURE_ESCALATION_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
