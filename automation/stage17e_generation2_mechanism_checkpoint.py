from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-17d GMRF context."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage17e_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "17e-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage17d_decision": (
            "The fixed isotropic-pairwise GMRF Fisher-information context was "
            "eligible in all 15 UDED folds but missed the registered UDED F1 "
            "and precision conditions: aggregate F1/precision/recall and mean "
            "fold F1 changed by +0.000719/-0.000108/+0.002133/+0.000715, with "
            "10/15 fold wins. Official BSDS500-validation ODS/OIS/AP changed "
            "by +0.000312/-0.002259/-0.003687. The conjunctive rule rejects "
            "the fixed realization and closes GMRF variants to outcome-driven tuning."
        ),
        "requested_work": [
            "Use live primary literature and completed Stage-14 through Stage-17 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for Stage 17d's weak UDED recall gain but failed precision/F1 margin and negative BSDS OIS/AP without altering its GMRF contract or advancing related random-field variants.",
            "Prefer a bounded mechanism distinct from local GMRF surprise, local nonparametric ranks, scalar structure tensors, spectral graph globalization, forests, detector fusion, conditioning, structural gating, connected-threshold persistence, local profiles/self-similarity, marginal normalization, aggregation replacement, and finite-scale localizer replacement.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune Stage 17d or advance to multiscale, anisotropic, color, mixture, altered-neighbourhood, altered-estimator, or learned random-field variants from this result.",
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
    print("STAGE17E_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
