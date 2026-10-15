from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-16t scale localizer."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage16u_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "16u-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage16t_decision": (
            "The fixed gamma-normalized sigma-1/2/4 scale-selected localizer "
            "failed the conjunctive rule. On UDED it changed aggregate "
            "F1/precision/recall and mean fold F1 by "
            "-0.019452/+0.001642/-0.053267/-0.020488 and won 2/15 folds. "
            "Official BSDS500-validation ODS/OIS/AP changed by "
            "+0.003808/+0.000911/-0.010464. The realization is rejected and "
            "closed to scale-space or localizer tuning."
        ),
        "requested_work": [
            "Use live primary literature and completed Stage-14 through Stage-16 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for the recurring BSDS-positive/UDED-negative pattern without fitting dataset identity, relaxing the cross-dataset rule, or using protected feedback.",
            "Prefer a bounded mechanism distinct from failed cue additions, detector fusion, conditioning, component/region/chain gating, connected-threshold persistence, local profile fitting, local self-similarity, marginal normalization, qualitative aggregation, and fixed finite-scale localizer replacement.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune Stage-16t scales, gamma normalization, Gaussian derivative discretization, endpoint or tie handling, NMS, response mapping, conditioning, localizer fusion, context, gate, or thresholds.",
            "Do not tune earlier failed Stage-14 through Stage-16 mechanism families from their outcomes.",
            "Do not revive Stage-15p cross-texture integration without an independently justified distinct hypothesis.",
            "Do not use UDED held-out, BSDS500 test, BIPEDv2 test, or any protected/external result for selection.",
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
    print("STAGE16U_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
