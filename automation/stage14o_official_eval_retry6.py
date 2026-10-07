from __future__ import annotations

"""Prepare the sixth attachment-only retry for Stage 14o official evaluation.

The fifth retry completed per-image matching and read all 100 incumbent result
files before Windows reported native heap corruption.  The evaluator now runs
native matching and pure-MATLAB aggregation in separate MATLAB processes.  The
controller performs the frozen export and evaluation after this script exits;
CV, vendor sources, cached predictions, and candidate parameters are unchanged.
"""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage14o_official_eval_retry6"
MANIFEST = ROOT / "results" / "local_dev" / "stage14o_interval_capacity_uncertainty" / "official_eval_manifest.json"
PREVIEW = ROOT / "results" / "local_dev" / "stage14o_interval_capacity_uncertainty" / "best_method_preview.png"


def main() -> int:
    if not MANIFEST.exists():
        raise FileNotFoundError(MANIFEST)
    if not PREVIEW.exists():
        raise FileNotFoundError(PREVIEW)

    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "ready_for_official_eval_retry",
        "experiment_id": "stage14o_official_eval_retry6",
        "source_experiment": "stage14o_interval_capacity_uncertainty",
        "scope": "official BSDS500-validation attachment only",
        "scientific_candidate_changed": False,
        "repeated_cv_rerun": False,
        "vendor_source_changed": False,
        "predictions_changed": False,
        "repair": "isolate native per-image matching from pure-MATLAB aggregation in fresh MATLAB processes",
        "manifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "visual_preview": str(PREVIEW.relative_to(ROOT)).replace("\\", "/"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14O_OFFICIAL_EVAL_RETRY6_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
