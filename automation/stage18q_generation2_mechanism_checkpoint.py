from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-18p median OWA context."""

from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage18q_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "18q-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage18p_decision": (
            "The fixed five-input median OWA failed both development axes. UDED "
            "aggregate F1/precision/recall and mean fold F1 changed by "
            "-0.001998/-0.001055/-0.003541/-0.001747, with 1/15 fold wins. "
            "Official BSDS500-validation ODS/OIS/AP changed by "
            "+0.000666/-0.000988/-0.012906. The compact Choquet controller remains incumbent."
        ),
        "requested_work": [
            "Use live primary literature and completed joint development evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for the failure of fixed majority/order-statistic aggregation and the broader pattern of small or dataset-asymmetric cue gains without relaxing promotion margins.",
            "Prefer a bounded mechanism distinct from OWA/order-statistic aggregation, Sugeno aggregation, and all earlier closed families.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism.",
        ],
        "forbidden": [
            "Do not tune or extend Stage 18p's OWA vector, quantifier, order statistic, trimming, weighting, capacity, mixture, calibration, gate, localizer, or thresholds.",
            "Do not advance to adaptive, weighted, learned, spatial, image-conditioned, or cue-selected OWA variants from the Stage 18p result.",
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
    print("STAGE18Q_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
