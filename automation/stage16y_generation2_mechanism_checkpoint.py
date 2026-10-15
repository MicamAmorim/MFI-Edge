from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-16x spectral context."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage16y_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "16y-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage16x_decision": (
            "The fixed spectral-globalization membership failed the conjunctive rule. "
            "On UDED it changed aggregate F1/precision/recall and mean fold F1 by "
            "-0.000430/-0.000190/-0.000826/-0.000364 and won 6/15 folds. "
            "Official BSDS500-validation ODS/OIS/AP changed by "
            "+0.001975/+0.001748/+0.011216; ODS narrowly missed the registered "
            "+0.002 margin. The bounded spectral surrogate is rejected and closed to tuning."
        ),
        "requested_work": [
            "Use live primary literature and completed Stage-14 through Stage-16 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for the recurring BSDS-positive/UDED-weak pattern without fitting dataset identity or relaxing the cross-dataset rule.",
            "Prefer a bounded mechanism distinct from spectral graph globalization, forests, detector fusion, conditioning, structural gating, connected-threshold persistence, local profile or self-similarity cues, marginal normalization, aggregation replacement, and finite-scale localizer replacement.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune Stage-16x or advance to exact or learned gPb from this result.",
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
    print("STAGE16Y_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
