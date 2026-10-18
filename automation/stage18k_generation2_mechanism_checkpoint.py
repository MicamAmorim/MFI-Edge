from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-18j PMI cue."""

from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage18k_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "18k-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage18j_decision": (
            "The fixed image-internal PMI dependency-deficit cue passed the official "
            "BSDS500-validation axis but missed the conjunctive UDED aggregate-F1 "
            "margin. UDED aggregate F1/precision/recall and mean fold F1 changed by "
            "+0.000534/+0.002268/-0.002507/+0.000636, with 9/15 fold wins and "
            "15/15 eligibility. Official BSDS500-validation ODS/OIS/AP improved by "
            "+0.005537/+0.002090/+0.009347. The compact controller remains incumbent."
        ),
        "requested_work": [
            "Use live primary literature and completed joint development evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for the repeated BSDS-positive/UDED-submargin pattern without relaxing margins, fitting dataset identity, or combining rejected cues.",
            "Prefer a bounded mechanism distinct from image-internal PMI/co-occurrence dependency and all earlier closed families.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism.",
        ],
        "forbidden": [
            "Do not tune or extend Stage 18j's intensity, pair, co-occurrence, smoothing, pseudocount, density, PMI, deficit, calibration, eligibility, or integration choices.",
            "Do not advance to color, variance-feature, KDE, learned-affinity, multiscale, graph/spectral, OWT/UCM, approximate-PMI forest, half-disc, patchwise, conditional-PMI, or detector-fusion variants from the Stage 18j result.",
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
    print("STAGE18K_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
