from __future__ import annotations

"""Live-literature checkpoint after the failed Stage-16b fixed expert mean."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage16c_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "16c-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage16b_decision": (
            "The fixed equal SED/MFI mean failed its preregistered conjunctive rule. "
            "It improved UDED aggregate F1 over compact MFI, but missed the precision "
            "and fold-win conditions; on BSDS500 validation it remained below exact "
            "SED on ODS, OIS, and AP. The weight and fusion family are closed to "
            "outcome-driven tuning."
        ),
        "requested_work": [
            "Use live primary literature and the completed Stage-15/16 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before any candidate result is inspected.",
            "Account for Stage 16b's asymmetric result: SED is weak on UDED but strongest on BSDS, while the equal mean modestly helps UDED yet dilutes SED on BSDS.",
            "Prefer a mechanism that can be implemented without redistributing unlicensed dependencies and without making exact SED part of the final required inference path unless provenance permits it.",
            "Register one minimal falsification or one bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update the literature ledger, bibliography matrix, history, roadmap, and preregistration when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune SED/MFI fusion weights, normalizations, nonlinear means, routers, or constituent parameters from Stage 16b outcomes.",
            "Do not revive the failed Stage-15p cross-texture integration or micro-tune failed Stage-14 mechanisms without an independently justified distinct hypothesis.",
            "Do not use UDED held-out, BSDS500 test, BIPEDv2 test, or any protected/external result for selection.",
            "Do not use dataset identity, ground truth, oracle winners, or validation method labels at inference.",
            "Do not claim the Windows Berkeley matcher is reference-verified or use the fixed-seed diagnostic matcher for dataset scoring.",
            "Do not change the compact Choquet-gated Scharr+NMS incumbent until a new candidate passes its preregistered joint rule."
        ],
        "official_eval_manifest_omission": (
            "Required and justified: this event is literature/mechanism planning only "
            "and does not generate detector maps or image-benchmark outputs."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE16C_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
