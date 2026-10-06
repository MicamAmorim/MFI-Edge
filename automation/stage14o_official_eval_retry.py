from __future__ import annotations

"""Prepare an attachment-only retry for the Stage-14o official evaluation.

The controller's default-on official-evaluation hook performs the actual
export and MATLAB evaluation after this script exits. This runner deliberately
does not rerun Stage-14o repeated CV or alter its frozen candidate.
"""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage14o_official_eval_retry"
MANIFEST = (
    ROOT
    / "results"
    / "local_dev"
    / "stage14o_interval_capacity_uncertainty"
    / "official_eval_manifest.json"
)
PREVIEW = (
    ROOT
    / "results"
    / "local_dev"
    / "stage14o_interval_capacity_uncertainty"
    / "best_method_preview.png"
)


def main() -> int:
    if not MANIFEST.exists():
        raise FileNotFoundError(MANIFEST)
    if not PREVIEW.exists():
        raise FileNotFoundError(PREVIEW)

    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "ready_for_official_eval_retry",
        "experiment_id": "stage14o_official_eval_retry",
        "source_experiment": "stage14o_interval_capacity_uncertainty",
        "scope": "official BSDS500-validation attachment only",
        "scientific_candidate_changed": False,
        "repeated_cv_rerun": False,
        "manifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "visual_preview": str(PREVIEW.relative_to(ROOT)).replace("\\", "/"),
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("STAGE14O_OFFICIAL_EVAL_RETRY_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
