from __future__ import annotations

"""Planning checkpoint for the Stage-15h adaptive-surround reproduction audit."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15h_adaptive_surround_reproduction_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "15h-adaptive-surround-reproduction-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage15g_status": (
            "closed fidelity-unresolved after a dataset-free contract audit found no "
            "article-specific code and unresolved output-affecting conflicts across "
            "the related patent and BESD repository; no detector was scored"
        ),
        "requested_work": [
            "Use live primary-source research on Zhang et al., Contour detection model inspired by V1 surround modulation, Signal, Image and Video Processing, DOI 10.1007/s11760-024-03634-y.",
            "Locate and audit author or official code, supplements, data, and primary methodological clarifications before considering an independent implementation.",
            "Resolve immutable provenance, license constraints, training class, fixed parameters, image-internal scale adaptation, surround geometry and weighting, orientation/channel fusion, output conventions, and postprocessing.",
            "Recover every reported dataset split and metric protocol; do not assume the reported average optimal F-score is Berkeley ODS or directly comparable to the repository evaluator.",
            "Choose exactly one next action: an exact fidelity-labeled reproduction if author code is available, a faithful fixed reimplementation only if every output-affecting choice is primary-source-resolved, or a deterministic dataset-free fidelity preflight if the public contract is incomplete.",
            "For an image experiment, emit per-image maps, runtimes and provenance, an official BSDS500-validation manifest, and best_method_preview.png using predeclared sorted positions 1, 50, and 100.",
            "Update the Stage-15 literature ledger and bibliography matrix with every source that materially determines implementation or protocol."
        ],
        "forbidden": [
            "Do not modify MFI architecture before Stage 15p.",
            "Do not tune surround, adaptation, scale, orientation, fusion, or postprocessing parameters from BSDS validation or protected results.",
            "Do not use BSDS500 test, BIPEDv2 test, or UDED held-out feedback.",
            "Do not infer Stage-15h implementation choices from the failed Stage-15g contract or combine non-equivalent related implementations into a surrogate.",
            "Do not represent the local Windows evaluator as reference-verified or use the fixed-seed diagnostic matcher for dataset scoring."
        ],
        "official_eval_manifest_omission": (
            "Required and justified: literature/provenance planning only; no detector "
            "maps or dataset outputs are generated."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15H_ADAPTIVE_SURROUND_REPRODUCTION_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
