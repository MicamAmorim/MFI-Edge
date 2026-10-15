from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-17f photometric context."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage17g_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "17g-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage17f_decision": (
            "The fixed sigma-1 shadow-shading photometric quasi-invariant context "
            "passed the official BSDS500-validation axis but failed the registered "
            "UDED aggregate-F1 margin and fold-win requirements. UDED aggregate "
            "F1/precision/recall and mean fold F1 changed by "
            "+0.000756/+0.000826/+0.000594/+0.000509, with 7/15 fold wins and "
            "12/15 eligible folds. Official ODS/OIS/AP changed by "
            "+0.003855/+0.002520/+0.008468. The conjunctive rule rejects the "
            "fixed realization and closes photometric variants to outcome-driven tuning."
        ),
        "requested_work": [
            "Use live primary literature and completed Stage-14 through Stage-17 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for Stage 17f's BSDS-positive but UDED-submargin result without altering its photometric contract or advancing related invariant variants.",
            "Prefer a bounded mechanism distinct from photometric/color invariants, local GMRF surprise, local ranks, scalar structure tensors, spectral globalization, forests, detector fusion, conditioning, structural gating, persistence, local profiles/self-similarity, marginal normalization, aggregation replacement, and finite-scale localizer replacement.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune Stage 17f or advance to specular, hue, alternative-color-space, multiscale, illuminant-estimated, color-localizer, or learned photometric variants from this result.",
            "Do not tune earlier failed Stage-14 through Stage-17 mechanism families from their outcomes.",
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
    print("STAGE17G_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
