from __future__ import annotations

"""Prepare the resumable attachment-only Stage-14u official-eval retry."""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage14u_official_eval_retry2"
SOURCE = ROOT / "results" / "local_dev" / "stage14u_yager_evidential_ignorance"
MANIFEST = SOURCE / "official_eval_manifest.json"
PREVIEW = SOURCE / "best_method_preview.png"


def main() -> int:
    for required in (MANIFEST, PREVIEW):
        if not required.exists():
            raise FileNotFoundError(required)
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "ready_for_official_eval_retry",
        "experiment_id": "stage14u_official_eval_retry2",
        "source_experiment": "stage14u_yager_evidential_ignorance",
        "scope": "official BSDS500-validation attachment only",
        "scientific_candidate_changed": False,
        "repeated_cv_rerun": False,
        "vendor_source_changed": False,
        "predictions_changed": False,
        "repair": (
            "resume completed per-image Berkeley matches across fresh MATLAB "
            "processes after intermittent Windows heap corruption"
        ),
        "manifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "visual_preview": str(PREVIEW.relative_to(ROOT)).replace("\\", "/"),
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("STAGE14U_OFFICIAL_EVAL_RETRY2_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
