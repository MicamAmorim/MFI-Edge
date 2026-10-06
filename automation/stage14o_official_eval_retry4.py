from __future__ import annotations

"""Prepare the fourth attachment-only retry for Stage 14o official evaluation.

The third retry reached the pinned Berkeley per-image evaluator, but MATLAB
R2023a could not parse chained cell/field indexing in that source.  The wrapper
now creates a run-local syntax-only compatibility mirror without editing the
vendored benchmark.  The controller performs the actual frozen export and
evaluation after this script exits; repeated CV and candidate parameters are
unchanged.
"""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage14o_official_eval_retry4"
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
        "experiment_id": "stage14o_official_eval_retry4",
        "source_experiment": "stage14o_interval_capacity_uncertainty",
        "scope": "official BSDS500-validation attachment only",
        "scientific_candidate_changed": False,
        "repeated_cv_rerun": False,
        "vendor_source_changed": False,
        "repair": "run-local MATLAB R2023a syntax compatibility mirror with explicit groundTruth load and cell access",
        "manifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "visual_preview": str(PREVIEW.relative_to(ROOT)).replace("\\", "/"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14O_OFFICIAL_EVAL_RETRY4_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
