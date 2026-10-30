from __future__ import annotations

"""Planning-only Stage-23G strong-detector intervention checkpoint.

The controller routes this completed marker to high-reasoning/live-literature
analysis.  This runner deliberately reads and scores no dataset.
"""

from datetime import datetime, timezone
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage23g_gap_guided_detector_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "completed",
        "experiment_id": "stage23g_gap_guided_detector_checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_access": "none",
        "detector_scoring": False,
        "stage23f_transfer_result": "no_primary_jointly_transferable",
        "requested_work": [
            "Use high reasoning and live primary-source/official-code research.",
            "Read the complete Stage-23C--F landscape and preserve every negative transfer result.",
            "Select exactly one strong non-neural detector target with a matched development protocol and reproducible baseline.",
            "Inventory the target's existing evidence families and identify one missing family supported by the cached complementarity map.",
            "Choose any aggregation prospectively from the Stage-23E/F behavioral evidence; do not call a failed Stage-23F relationship validated.",
            "Register exactly one bounded next action, beginning with baseline materialization/gap diagnosis if that evidence is not already complete.",
        ],
        "forbidden": [
            "No protected/test result may choose the target, evidence, aggregation, parameters, or experiment priority.",
            "Do not backfill the Stage-23F frontier or tune its failed cells.",
            "Do not promote a raw landscape cell or alter compact MFI at this checkpoint.",
            "Do not recompute any exact valid Stage-23 cache artifact.",
        ],
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE23G_GAP_GUIDED_DETECTOR_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
