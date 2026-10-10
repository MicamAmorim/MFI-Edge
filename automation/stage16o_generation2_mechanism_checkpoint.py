from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-16n SUSAN cue."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage16o_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "16o-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage16n_decision": (
            "The fixed initial SUSAN/USAN local-self-similarity membership failed "
            "the conjunctive rule. On UDED it changed aggregate F1/precision/recall "
            "and mean fold F1 by +0.000302/-0.000463/+0.001628/+0.000185, won "
            "7/15 fold-F1 comparisons, and was eligible in 15/15 folds. Official "
            "BSDS500-validation ODS/OIS/AP improved by +0.004674/+0.002200/+0.006049. "
            "The fixed realization is rejected because the UDED aggregate-F1 margin "
            "and fold-win conditions failed; its parameters and integration are closed "
            "to tuning."
        ),
        "requested_work": [
            "Use live primary literature and completed Stage-14 through Stage-16 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for the recurring BSDS-positive/UDED-weak-or-negative pattern without fitting dataset identity, relaxing the cross-dataset rule, or using protected feedback.",
            "Prefer a bounded mechanism distinct from failed detector averaging, conditioning, component/region/chain gating, connected-threshold persistence, local profile fitting, and centre-referenced SUSAN context.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune the SUSAN mask, brightness threshold, exponent, geometric threshold, boundary handling, eligibility, calibration, Choquet integration, gate, localizer, or threshold grid from Stage-16n outcomes.",
            "Do not tune failed Stage-16b fusion, Stage-16d stability, Stage-16f rolling guidance, Stage-16h persistence, Stage-16j profile, or Stage-16l EDPF-chain integrations.",
            "Do not revive Stage-15p cross-texture integration or micro-tune failed Stage-14 mechanisms without an independently justified distinct hypothesis.",
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
    print("STAGE16O_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
