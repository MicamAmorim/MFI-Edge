from __future__ import annotations

"""Live-literature checkpoint after the failed Stage-16d stability gate."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage16e_generation2_mechanism_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "16e-generation2-mechanism-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage16d_decision": (
            "The fixed stable-region-boundary support gate failed its conjunctive "
            "rule on both development axes. It reduced UDED aggregate and mean-fold "
            "F1, precision, and recall with only 4/15 fold wins, and reduced official "
            "BSDS500-validation ODS, OIS, and AP. The component-tree surrogate and "
            "its stability/gate parameters are closed to outcome-driven tuning."
        ),
        "requested_work": [
            "Use live primary literature and the completed Stage-14 through Stage-16 evidence to select exactly one mechanistically distinct, interpretable, non-neural generation-2 falsification.",
            "Treat UDED selection and BSDS500 validation as joint development axes and preregister a conjunctive promotion rule before inspecting any candidate result.",
            "Account for the failure of both detector-level fixed averaging and response-derived stable-region attenuation without revisiting their parameters.",
            "Prefer a bounded mechanism that addresses a documented incumbent error mode and is distinct from failed component support, endpoint linking, NFA attenuation, localizer replacement, and SED/MFI averaging.",
            "Register one minimal falsification or one bounded hypothesis-led search with a repository-local runner, deterministic best_method_preview.png, and an official BSDS500-validation manifest.",
            "Update the literature ledger, bibliography matrix, history, roadmap, and preregistration when primary sources materially determine the selected mechanism."
        ],
        "forbidden": [
            "Do not tune Stage-16d quantization, connectivity, area, level delta, chamfer distance, fragment length, gate exponent, floor, or threshold grid from its outcomes.",
            "Do not tune Stage-16b fusion weights, normalizations, nonlinear means, routers, or constituent parameters.",
            "Do not revive the failed Stage-15p cross-texture integration or micro-tune failed Stage-14 mechanisms without an independently justified distinct hypothesis.",
            "Do not use UDED held-out, BSDS500 test, BIPEDv2 test, or any protected/external result for selection.",
            "Do not use dataset identity, ground truth, oracle winners, or validation method labels at inference.",
            "Do not claim the Windows Berkeley matcher is reference-verified or use the fixed-seed diagnostic matcher for dataset scoring.",
            "Do not change the compact Choquet-gated Scharr+NMS incumbent until a candidate passes its preregistered joint rule."
        ],
        "official_eval_manifest_omission": (
            "Required and justified: this event is literature/mechanism planning only "
            "and does not generate detector maps or image-benchmark outputs."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE16E_GENERATION2_MECHANISM_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
