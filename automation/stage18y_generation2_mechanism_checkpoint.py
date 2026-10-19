from __future__ import annotations

"""Live-literature checkpoint after rejected Stage-18x Teager energy."""

from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage18y_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "18y-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage18x_decision": (
            "The fixed dual-stencil Teager-energy cue improved UDED aggregate F1 "
            "by only +0.000813, won 3/15 folds, and was eligible in 3/15 folds. "
            "BSDS500-validation ODS/OIS/AP changed by "
            "+0.000002/+0.000867/+0.000088, missing the required ODS margin. "
            "The compact Choquet controller remains incumbent."
        ),
        "requested_work": [
            "Use live primary literature and completed joint development evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for repeated weak or ineligible isolated context additions without relaxing promotion margins or combining rejected cues.",
            "Prefer a bounded mechanism distinct from nonlinear energy, relative variation, calibration, aggregation, and all earlier closed families.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism.",
        ],
        "forbidden": [
            "Do not tune or extend Stage 18x stencils, boundary handling, rectification, consensus, normalization, calibration, eligibility, integration, energy operators, demodulation, contrast enhancement, or higher-order variants.",
            "Do not combine Teager-energy evidence with rejected cues or alter the retained feature bank, singleton weights, capacity, aggregation, gate, localizer, or thresholds from the Stage 18x result.",
            "Do not tune or combine earlier failed Stage-14 through Stage-18 mechanism families from their outcomes.",
            "Do not use UDED held-out, BSDS500 test, BIPEDv2 test, or any protected or external result for selection.",
            "Do not use dataset identity, ground truth, oracle winners, or validation method labels at inference.",
            "Do not claim the Windows Berkeley matcher is reference-verified or use the fixed-seed diagnostic matcher for dataset scoring.",
            "Do not change the compact Choquet-gated median-conditioned Scharr+NMS incumbent until a candidate passes its preregistered joint rule.",
        ],
        "official_eval_manifest_omission": (
            "Required and justified: this event is literature/mechanism planning only "
            "and does not generate detector maps or image-benchmark outputs."
        ),
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE18Y_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
