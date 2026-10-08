from __future__ import annotations

"""Planning checkpoint for the Stage-15i modern fractional reference audit."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15i_fractional_reference_reproduction_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "15i-fractional-reference-reproduction-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage15h_status": (
            "closed fidelity-unresolved after a dataset-free contract audit confirmed "
            "that public primary material does not specify a complete executable "
            "adaptive-surround detector; no detector or benchmark was run"
        ),
        "requested_work": [
            "Use live primary-source research on Fractional Dirac Operators for Edge Detection, Fractal and Fractional 2026, DOI 10.3390/fractalfract10060412.",
            "Locate and audit article-specific author code, supplements, immutable provenance, license terms, and any official implementation or data archive.",
            "Resolve training class, fixed published operator definitions and parameters, color/channel treatment, boundary conditions, scalar output construction, normalization, thresholding, thinning, and postprocessing.",
            "Recover the exact BSDS split and ODS/OIS/AP evaluator contract and keep reported paper metrics separate from any common BSDS500-validation reproduction.",
            "Explicitly compare the target method's Dirac construction with the fixed half-order spectral Riesz realization falsified in Stage 14s; this checkpoint is a reference audit and cannot reopen fractional-order or implementation tuning.",
            "Choose exactly one next action: exact fidelity-labeled reproduction if author code and a complete fixed contract exist, faithful fixed reimplementation only if every output-affecting choice is primary-source-resolved, or deterministic dataset-free fidelity preflight otherwise.",
            "For an image experiment, preserve per-image maps, runtimes and provenance, emit an official BSDS500-validation manifest, and write best_method_preview.png using predeclared sorted positions 1, 50, and 100.",
            "Update the Stage-15 literature ledger and bibliography matrix with every source that materially determines implementation or protocol."
        ],
        "forbidden": [
            "Do not modify MFI architecture before Stage 15p.",
            "Do not tune fractional order, masks, boundary handling, normalization, channel fusion, thresholding, or postprocessing from BSDS validation or protected results.",
            "Do not use BSDS500 test, BIPEDv2 test, or UDED held-out feedback.",
            "Do not treat Stage 14s as a reproduction or universal falsification of the target Fractional Dirac method.",
            "Do not invent missing output-affecting parameters or label a repository-specific surrogate exact or faithful.",
            "Do not represent the local Windows evaluator as reference-verified or use the fixed-seed diagnostic matcher for dataset scoring."
        ],
        "official_eval_manifest_omission": (
            "Required and justified: literature/provenance planning only; no detector "
            "maps or dataset outputs are generated."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15I_FRACTIONAL_REFERENCE_REPRODUCTION_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
