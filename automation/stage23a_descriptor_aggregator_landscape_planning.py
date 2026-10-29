from __future__ import annotations

"""Stage 23A bootstrap: literature census and landscape planning checkpoint.

This stage deliberately performs no fitting and reads no benchmark/test labels.
Its role is to trigger the high-reasoning/live-web research agent with the new
Stage-23 agenda before any descriptor cache or factorial experiment is built.
"""

from datetime import datetime, timezone
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage23a_descriptor_aggregator_landscape_planning"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "completed",
        "experiment_id": "stage23a_descriptor_aggregator_landscape_planning",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scientific_stage": "23A",
        "dataset_access": "none",
        "detector_scoring": False,
        "active_agenda": "docs/paper/STAGE23_EVIDENCE_AGGREGATION_CAMPAIGN.md",
        "active_policy": "automation/STAGE23_POLICY.md",
        "active_registry": "automation/stage23_experiments.json",
        "cache_root": "cache/local_dev/stage23",
        "requested_work": [
            "Read the completed Stage-22 synthesis and the Stage-23 campaign/policy/context before proposing experiments.",
            "Use primary literature, official author repositories, and official benchmark documentation to build the Stage-23 descriptor census, aggregator census, protocol matrix, and detector target map.",
            "Map descriptor/evidence families actually used by strong non-neural edge/boundary methods, plus mechanistically distinct evidence families that are scientifically relevant but absent from the current MFI pipeline.",
            "Map representative aggregation families with distinct mathematical behavior; include simple controls and do not assume Choquet is best.",
            "Record exact validation/test split, metric, tolerance, annotation treatment, preprocessing/postprocessing, training class, code availability, and implementation fidelity for literature comparisons.",
            "Update docs/paper/STAGE23_LITERATURE_LEDGER.md for every source that materially drives the shortlist or protocol design.",
            "Preregister a bounded first descriptor/aggregator shortlist; do not open an unrestricted combinatorial search.",
            "Design Stage 23B as a cache-infrastructure certification before any large descriptor extraction. The cache must enforce extract-once/reuse-everywhere semantics with provenance hashes and fail-closed corruption handling.",
            "Register exactly one next Stage-23 experiment in automation/stage23_experiments.json and return that id.",
        ],
        "forbidden": [
            "Do not run UDED/BSDS/BIPED scoring in Stage 23A.",
            "Do not reopen Stage 22 or tune the rejected Stage-22E calibration.",
            "Do not select descriptors or aggregators from protected/test outcomes.",
            "Do not register a giant powerset search before complementarity/redundancy analysis.",
            "Do not recompute existing reusable descriptor maps in later stages when an exact valid Stage-23 cache artifact exists.",
        ],
        "expected_repository_outputs": [
            "docs/paper/STAGE23_DESCRIPTOR_CENSUS.md",
            "docs/paper/STAGE23_AGGREGATOR_CENSUS.md",
            "docs/paper/STAGE23_PROTOCOL_MATRIX.md",
            "docs/paper/STAGE23_LITERATURE_LEDGER.md",
            "one registered Stage-23B cache-certification experiment",
        ],
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE23A_DESCRIPTOR_AGGREGATOR_LANDSCAPE_PLANNING_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
