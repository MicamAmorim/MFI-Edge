from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-18b FH cue."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage18c_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "18c-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage18b_decision": (
            "The fixed FH adaptive-region boundary cue failed the conjunctive "
            "promotion rule. UDED aggregate F1/precision/recall and mean fold "
            "F1 changed by -0.000307/-0.000632/+0.000277/-0.000248, with 6/15 "
            "fold wins and 14/15 eligibility. Official BSDS500-validation "
            "ODS/OIS/AP improved by +0.002858/+0.002241/+0.009290, but the "
            "UDED failures reject the candidate. The compact controller remains "
            "incumbent."
        ),
        "requested_work": [
            "Use live primary literature and completed joint development evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for the repeated BSDS-positive/UDED-weak or negative context pattern without relaxing margins, fitting dataset identity, or combining rejected cues.",
            "Prefer a bounded mechanism distinct from FH region partition boundaries and all earlier closed cue, graph, region, structural, conditioning, aggregation, fusion, and localizer families.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune or extend Stage 18b Gaussian smoothing, graph scale, connectivity, weights, minimum-size processing, boundary rasterization, region selection, color, feature-space graphs, hierarchy, calibration, eligibility, or integration.",
            "Do not tune or combine earlier failed Stage-14 through Stage-18 mechanism families from their outcomes.",
            "Do not use UDED held-out, BSDS500 test, BIPEDv2 test, or any protected or external result for selection.",
            "Do not use dataset identity, ground truth, oracle winners, or validation method labels at inference.",
            "Do not claim the Windows Berkeley matcher is reference-verified or use the fixed-seed diagnostic matcher for dataset scoring.",
            "Do not change the compact Choquet-gated median-conditioned Scharr+NMS incumbent until a candidate passes its preregistered joint rule."
        ],
        "official_eval_manifest_omission": (
            "Required and justified: this event is literature/mechanism planning only "
            "and does not generate detector maps or image-benchmark outputs."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE18C_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
