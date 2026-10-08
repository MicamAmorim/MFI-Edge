from __future__ import annotations

"""Planning checkpoint for the Stage-15g texture-gradient reproduction audit."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15g_texture_surround_reproduction_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "15g-texture-gradient-surround-reproduction-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage15f_status": (
            "exact author-code Compass completed on BSDS500 validation; versus the "
            "unchanged MFI incumbent it changed ODS/OIS/AP by approximately "
            "+0.08542/+0.07709/-0.01594 and remains an external baseline"
        ),
        "requested_work": [
            "Use live primary-source research on Yang, Peng and Wu, Edge Detection Using Texture Gradients and Surround Modulation, Signal, Image and Video Processing 2025, DOI 10.1007/s11760-025-04339-6.",
            "Locate and audit author or official code, supplements, data, and primary methodological clarifications before considering an independent implementation.",
            "Resolve immutable provenance, license constraints, training class, fixed parameters, texture-gradient construction, surround-modulation equations, scale/orientation handling, output conventions, and postprocessing.",
            "Recover every reported split and metric protocol and keep literature numbers separate from a common BSDS500-validation reproduction.",
            "Choose exactly one next action: an exact fidelity-labeled reproduction if the public contract is complete, a faithful fixed reimplementation only if every output-affecting choice is primary-source-resolved, or a deterministic fidelity preflight if it is not.",
            "For an image experiment, emit per-image maps, runtimes and provenance, an official BSDS500-validation manifest, and best_method_preview.png using predeclared sorted positions 1, 50, and 100.",
            "Update the Stage-15 literature ledger and bibliography matrix with every source that materially determines implementation or protocol."
        ],
        "forbidden": [
            "Do not modify MFI architecture before Stage 15p.",
            "Do not tune texture, surround, scale, orientation, fusion, or postprocessing parameters from BSDS validation or protected results.",
            "Do not use BSDS500 test, BIPEDv2 test, or UDED held-out feedback.",
            "Do not treat Stage 14l or Stage 15f as a reproduction or falsification of the Stage-15g method.",
            "Do not invent missing output-affecting parameters or represent a surrogate as exact or faithful.",
            "Do not represent the local Windows evaluator as reference-verified or use the fixed-seed diagnostic matcher for dataset scoring."
        ],
        "official_eval_manifest_omission": (
            "Justified: literature/provenance planning only; no detector maps are generated."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15G_TEXTURE_SURROUND_REPRODUCTION_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
