from __future__ import annotations

"""Prepare an attachment-only retry for Stage 14u official evaluation.

The frozen UDED experiment completed, but MATLAB native matching exited with
Windows heap corruption. The controller performs the frozen export and
official evaluation after this script exits; CV, predictions, candidate
parameters, and vendor sources are unchanged.
"""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage14u_official_eval_retry"
MANIFEST = ROOT / "results" / "local_dev" / "stage14u_yager_evidential_ignorance" / "official_eval_manifest.json"
PREVIEW = ROOT / "results" / "local_dev" / "stage14u_yager_evidential_ignorance" / "best_method_preview.png"


def main() -> int:
    if not MANIFEST.exists():
        raise FileNotFoundError(MANIFEST)
    if not PREVIEW.exists():
        raise FileNotFoundError(PREVIEW)

    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "ready_for_official_eval_retry",
        "experiment_id": "stage14u_official_eval_retry",
        "source_experiment": "stage14u_yager_evidential_ignorance",
        "scope": "official BSDS500-validation attachment only",
        "scientific_candidate_changed": False,
        "repeated_cv_rerun": False,
        "vendor_source_changed": False,
        "predictions_changed": False,
        "repair": "retry frozen matching after intermittent Windows MATLAB heap corruption",
        "manifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "visual_preview": str(PREVIEW.relative_to(ROOT)).replace("\\", "/"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14U_OFFICIAL_EVAL_RETRY_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
