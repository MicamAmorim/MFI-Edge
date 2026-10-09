from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-16l chain cue."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage16m_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "16m-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage16l_decision": (
            "The fixed exact-EDPF chain-support membership failed the conjunctive "
            "rule. On UDED it changed aggregate F1/precision/recall and mean fold "
            "F1 by -0.000191/-0.000244/-0.000090/-0.000013, won 8/15 F1 "
            "comparisons, and won only 3/15 largest-component coverage comparisons, "
            "despite eligibility in 15/15 folds and a positive mean coverage delta "
            "of +0.000030. Official BSDS500-validation ODS/OIS/AP improved by "
            "+0.013847/+0.005044/+0.014949. The fixed realization is rejected and "
            "its parameters and integration are closed to tuning."
        ),
        "requested_work": [
            "Use live primary literature and completed Stage-14 through Stage-16 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for the repeated pattern of substantial BSDS benefit without UDED support, including Stage 16l's fully eligible but non-incremental chain cue, without fitting dataset identity or weakening the cross-dataset rule.",
            "Prefer a bounded evidence representation distinct from failed detector averaging, response/component gating, image conditioning, connected-threshold persistence, local profile fitting, and exact EDPF-chain context.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune EDPF parameters, alignment dilation, eligibility, membership weighting, Choquet context, gate, localizer, or threshold grid from Stage-16l outcomes.",
            "Do not tune failed Stage-16b fusion, Stage-16d stability, Stage-16f rolling-guidance, Stage-16h persistence, or Stage-16j profile families from their outcomes.",
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
    print("STAGE16M_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
