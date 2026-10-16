from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-17r recurrence cue."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage17s_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "17s-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage17r_decision": (
            "The fixed directional patch-recurrence membership was eligible in "
            "15/15 UDED folds and won 14/15, but aggregate F1 improved only "
            "+0.001396 versus the required +0.002. Official BSDS500-validation "
            "ODS/OIS/AP changed by +0.001872/+0.000782/+0.003748; ODS also missed "
            "its required +0.002 margin. The conjunctive rule rejects the cue."
        ),
        "requested_work": [
            "Use live primary literature and completed Stage-14 through Stage-17 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for stable but submargin gains without relaxing either registered margin or fitting dataset identity.",
            "Prefer a bounded mechanism distinct from patch recurrence, robust outliers, topological sensitivity, surround isolation, entropy, fractal scaling, photometric invariants, GMRF surprise, ranks, tensors, graphs, forests, fusion, conditioning, structural gating, persistence, profiles, marginal normalization, aggregation replacement, and localizer replacement.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune Stage 17r or advance to alternative patch/search geometry, bands, directions, match counts, similarity, multiscale/color/learned patches, full decomposition, smoothing, restoration, or integration variants from this result.",
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
    print("STAGE17S_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
