from __future__ import annotations

"""Live-literature checkpoint after the failed Stage-16f RGF localizer."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage16g_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "16g-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage16f_decision": (
            "The fixed rolling-guidance localizer failed the conjunctive rule. "
            "It improved official BSDS500-validation ODS/OIS/AP by "
            "+0.035113/+0.028126/+0.009010, but reduced UDED aggregate F1, "
            "precision, recall, and mean fold F1 by "
            "0.103203/0.038523/0.195051/0.102773 and won 0/15 folds. "
            "The fixed RGF realization and neighboring parameters are closed "
            "to outcome-driven tuning."
        ),
        "requested_work": [
            "Use live primary literature and the completed Stage-14 through Stage-16 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting any candidate result.",
            "Explicitly account for the repeated BSDS-positive/UDED-negative localizer pattern and the Stage-16f recall collapse without fitting a dataset-identity router.",
            "Prefer a bounded mechanism that preserves the incumbent localizer's UDED recall while addressing a documented error mode through a distinct evidence source or representation.",
            "Register one minimal falsification or one bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update the literature ledger, bibliography matrix, history, roadmap, and preregistration when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune rolling-guidance spatial/range sigma, iterations, support, color handling, conditioning order, localizer fusion, context, gate, or threshold grid from Stage-16f outcomes.",
            "Do not tune Stage-16b fusion or Stage-16d stability-gate families from their outcomes.",
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
    print("STAGE16G_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
