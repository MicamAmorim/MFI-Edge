from __future__ import annotations

"""Live-literature checkpoint after the Stage-15 diagnostic program."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage16a_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "16a-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage15o_decision": (
            "The registered Stage-15p gate failed. Cross-boundary texture contrast "
            "improved BSDS500-validation image-blocked AUC/AP but reduced both metrics "
            "on UDED selection and was positive in only two of five UDED folds."
        ),
        "requested_work": [
            "Use live primary literature and the completed Stage-15 evidence to select exactly one interpretable non-neural generation-2 mechanism for a bounded preregistered development experiment.",
            "Treat UDED selection and BSDS500 validation as joint development axes; require a pre-result conjunctive promotion rule and preserve leakage-free fitting where fitting is used.",
            "Prefer structural or contextual mechanisms supported across Stage 15, including fixed chain support, surround/sparseness, or a fixed expert combination, but do not assume any named family is selected before the literature audit.",
            "Explicitly distinguish cross-boundary texture contrast, which failed the cross-dataset Stage-15p gate, from any mechanistically different proposal.",
            "Account for the Stage-15 findings that SED is the strongest matched non-trained reference, structural fragmentation differs sharply across UDED and BSDS, and frozen methods retain limited spatial complementarity.",
            "Register one minimal falsification or one bounded hypothesis-led search, with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update the literature ledger, bibliography matrix, history, roadmap, and preregistration when sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not register Stage 15p or integrate the tested cross-boundary texture cue after its conjunctive gate failure.",
            "Do not tune from UDED held-out, BSDS500 test, BIPEDv2 test, or any other protected/external result.",
            "Do not fit a dataset-identity router or use ground truth, oracle winners, or validation method labels at inference.",
            "Do not micro-tune failed Stage-14 mechanisms or reproduced Stage-15 baselines from their benchmark outcomes.",
            "Do not claim that the local Windows Berkeley matcher is reference-verified or use the fixed-seed diagnostic matcher for dataset scoring.",
            "Do not change the incumbent until the new experiment passes its preregistered joint promotion rule."
        ],
        "official_eval_manifest_omission": (
            "Required and justified: this event is literature/mechanism planning only and "
            "does not generate detector maps or image-benchmark outputs."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE16A_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
