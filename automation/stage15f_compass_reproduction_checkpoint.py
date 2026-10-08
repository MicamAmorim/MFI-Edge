from __future__ import annotations

"""Planning checkpoint for the Stage-15f Compass reproduction audit."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15f_compass_reproduction_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "15f-compass-reproduction-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage15e_status": (
            "exact author-code CO and SCO completed on BSDS500 validation; "
            "SCO improved ODS/OIS/AP over paired CO by approximately "
            "0.02066/0.01708/0.04317 and both remain external baselines"
        ),
        "requested_work": [
            "Use live primary-source research on Ruzon and Tomasi, Color Edge Detection with the Compass Operator, CVPR 1999, DOI 10.1109/CVPR.1999.784624.",
            "Locate and audit author or official code, supplements, and later primary clarifications before considering an independent implementation.",
            "Resolve immutable code provenance, license or redistribution constraints, training class, fixed parameters, color space, half-disc geometry, distribution-distance definition, orientation aggregation, output normalization, and postprocessing.",
            "Recover the reported dataset split and metric protocol and keep literature numbers separate from a common BSDS500-validation reproduction.",
            "Choose exactly one next action: an exact fidelity-labeled reproduction if the public contract is complete, a faithful fixed reimplementation only if every output-affecting choice is primary-source-resolved, or a deterministic fidelity preflight if it is not.",
            "For an image experiment, emit per-image maps, runtimes and provenance, an official BSDS500-validation manifest, and best_method_preview.png using predeclared sorted positions 1, 50, and 100.",
            "Update the Stage-15 literature ledger and bibliography matrix with every source that materially determines implementation or protocol."
        ],
        "forbidden": [
            "Do not modify MFI architecture before Stage 15p.",
            "Do not tune Compass parameters or choose variants from BSDS validation or protected results.",
            "Do not use BSDS500 test, BIPEDv2 test, or UDED held-out feedback.",
            "Do not treat the failed Stage-14l fixed LBP feature as a test of the Compass distribution-gradient method.",
            "Do not invent missing output-affecting parameters or represent a surrogate as an exact reproduction.",
            "Do not represent the local Windows evaluator as reference-verified or use the fixed-seed diagnostic matcher for dataset scoring."
        ],
        "official_eval_manifest_omission": (
            "Justified: literature/provenance planning only; no detector maps are generated."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15F_COMPASS_REPRODUCTION_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
