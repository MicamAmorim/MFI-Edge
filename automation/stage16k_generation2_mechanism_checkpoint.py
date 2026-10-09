from __future__ import annotations

"""Live-literature checkpoint after the rejected Stage-16j profile cue."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage16k_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "16k-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage16j_decision": (
            "The fixed step-profile context cue failed the conjunctive rule. "
            "On UDED it changed aggregate F1/precision/recall and mean fold F1 "
            "by +0.001584/-0.000072/+0.004412/+0.001563, won 12/15 folds, "
            "and was eligible in 14/15 folds, but missed the required +0.002 "
            "aggregate-F1 margin. On official BSDS500 validation it changed "
            "ODS/OIS/AP by -0.001980/-0.001964/+0.001585. The fixed profile "
            "realization and neighboring parameters are closed to tuning."
        ),
        "requested_work": [
            "Use live primary literature and completed Stage-14 through Stage-16 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting candidate results.",
            "Account for the rejection of a locally discriminative and UDED-stable profile cue that did not transfer jointly to BSDS, without relaxing margins or fitting dataset identity.",
            "Prefer a bounded evidence source or representation distinct from failed detector averaging, response/component gating, image conditioning, connected-threshold persistence, and local step-profile fitting.",
            "Register one minimal falsification or bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update literature and paper records when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune profile extent, offsets, template widths, interpolation, eligibility, calibration, context, gate, localizer, or threshold grid from Stage-16j outcomes.",
            "Do not tune failed Stage-16b fusion, Stage-16d stability, Stage-16f rolling-guidance, or Stage-16h persistence families from their outcomes.",
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
    print("STAGE16K_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
