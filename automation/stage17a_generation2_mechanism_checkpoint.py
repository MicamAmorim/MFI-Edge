from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-16z tensor context."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage17a_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "17a-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage16z_decision": (
            "The fixed scalar structure-tensor membership passed the complete UDED gate: "
            "aggregate F1/precision/recall and mean fold F1 changed by "
            "+0.003263/+0.002639/+0.004184/+0.002705, with 14/15 fold wins, "
            "15/15 eligible folds, and exact support preservation. Official BSDS500-"
            "validation ODS/OIS/AP changed by +0.001414/+0.000628/+0.010279; ODS missed "
            "the preregistered +0.002 margin. The conjunctive rule rejects the fixed "
            "realization and closes it to tuning."
        ),
        "requested_work": [
            "Use live primary literature and completed Stage-14 through Stage-16 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for Stage 16z's UDED-positive but submargin-BSDS result and the broader recurring BSDS-positive/UDED-weak pattern without fitting dataset identity or relaxing the cross-dataset rule.",
            "Prefer a bounded mechanism distinct from scalar structure-tensor context, spectral graph globalization, forests, detector fusion, conditioning, structural gating, connected-threshold persistence, local profile or self-similarity cues, marginal normalization, aggregation replacement, and finite-scale localizer replacement.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune Stage 16z or advance to color, multiscale, normalized-coherence, or coherence-enhancing-diffusion variants from this result.",
            "Do not tune earlier failed Stage-14 through Stage-16 mechanism families from their outcomes.",
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
    print("STAGE17A_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
