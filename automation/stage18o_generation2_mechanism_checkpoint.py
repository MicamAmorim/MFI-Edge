from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-18n facet-break cue."""

from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage18o_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "18o-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage18n_decision": (
            "The fixed sloped-facet structural-break cue failed both development axes. "
            "UDED aggregate F1/precision/recall and mean fold F1 changed by "
            "-0.000162/-0.000171/-0.000138/-0.000130, with 1/15 fold wins and "
            "2/15 eligibility. Official BSDS500-validation ODS/OIS/AP changed by "
            "-0.000021/+0.000078/+0.000098. The compact controller remains incumbent."
        ),
        "requested_work": [
            "Use live primary literature and completed joint development evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for weak cue eligibility and repeated isolated-membership failures without relaxing margins, fitting dataset identity, or combining rejected cues.",
            "Prefer a bounded mechanism distinct from sloped-facet regression, local surface-model comparison, and all earlier closed families.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism.",
        ],
        "forbidden": [
            "Do not tune or extend Stage 18n's neighborhoods, offsets, axes, plane model, regression statistic, residual tolerance, bounding map, calibration, eligibility, or integration choices.",
            "Do not advance to robust, higher-order, adaptive-window, adaptive-orientation, alternative-test, segmented, multiscale, color, or learned facet variants from the Stage 18n result.",
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
    print("STAGE18O_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
