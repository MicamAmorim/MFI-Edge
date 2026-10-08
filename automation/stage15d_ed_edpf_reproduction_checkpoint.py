from __future__ import annotations

"""Planning checkpoint for the Stage-15d Edge Drawing / EDPF audit."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15d_ed_edpf_reproduction_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "15d-edge-drawing-edpf-reproduction-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage15c_status": (
            "VCM closed as fidelity-unresolved: public primary material does not "
            "fix enough output-affecting details for an exact or faithful run, so "
            "no surrogate was executed or scored"
        ),
        "requested_work": [
            "Use live primary-source research on Topal and Akinlar's Edge Drawing (DOI 10.1016/j.jvcir.2012.05.004), Akinlar and Topal's EDPF (DOI 10.1142/S0218001412550026), and the official ED_Lib repository.",
            "Verify the official repository lineage, immutable commit, license, build requirements, published detector variants, fixed/default parameters, and whether the selected EDPF path is strictly untrained or author-fixed.",
            "Recover the author-designated scalar edge-map convention and distinguish Edge Drawing chain construction from EDPF chain-level Helmholtz false-detection control; Stage 14t's connected-component surrogate is not equivalent.",
            "Resolve native-resolution BSDS500-validation export semantics and metric compatibility without using BSDS500 test, UDED held-out, or BIPEDv2 test feedback.",
            "Prefer exact author code. Register exactly one executable fidelity-labeled reproduction, or one deterministic dependency/build preflight if an exact run is not yet justified.",
            "For an image experiment, emit per-image maps, runtime and provenance records, an official BSDS500-validation manifest, and best_method_preview.png using predeclared sorted positions 1, 50, and 100.",
            "Update the Stage-15 literature ledger and bibliography matrix with every source that materially determines implementation or protocol."
        ],
        "forbidden": [
            "Do not modify MFI architecture before Stage 15p.",
            "Do not tune Edge Drawing or EDPF parameters from BSDS validation or protected results.",
            "Do not treat Stage 14t as a reproduction or falsification of full EDPF.",
            "Do not use BSDS500 test, BIPEDv2 test, or UDED held-out feedback.",
            "Do not represent the local Windows evaluator as reference-verified or use the fixed-seed diagnostic matcher for dataset scoring."
        ],
        "official_eval_manifest_omission": (
            "Justified: literature/provenance planning only; no detector maps are generated."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15D_ED_EDPF_REPRODUCTION_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
