from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-17h fractal context."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage17i_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "17i-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage17h_decision": (
            "The fixed local fractional-Brownian scaling membership failed the "
            "conjunctive rule. UDED aggregate F1/precision/recall and mean fold F1 "
            "changed by +0.000164/+0.000385/-0.000232/+0.000073, with 11/15 fold "
            "wins and 15/15 eligible folds. Official BSDS500-validation ODS/OIS/AP "
            "changed by +0.001978/+0.000972/+0.011064. The aggregate-F1 and ODS "
            "margins failed, closing this fixed realization to outcome-driven tuning."
        ),
        "requested_work": [
            "Use live primary literature and completed Stage-14 through Stage-17 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for Stage 17h's stable but submargin UDED and BSDS gains without altering its fractal contract or advancing related fractal variants.",
            "Prefer a bounded mechanism distinct from local stochastic scaling, photometric invariants, GMRF surprise, local ranks, tensors, spectral graphs, forests, detector fusion, conditioning, structural gating, persistence, profiles/self-similarity, marginal normalization, aggregation replacement, and localizer replacement.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune Stage 17h or advance to alternative lags, supports, directions, fractal estimators, multifractal spectra, wavelet/color fractals, multiscale variants, or learned fractal models from this result.",
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
    print("STAGE17I_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
