from __future__ import annotations

"""Planning checkpoint for the exact Stage-15b SED reproduction."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15b_sed_reproduction_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "15b-sed-reproduction-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage15a_status": (
            "closed_without_reference_verification; clock-seeded matcher sampling "
            "caused fresh-process drift; controlled matcher is diagnostic-only"
        ),
        "requested_work": [
            "Use live primary-source research to verify the exact SED method, published parameters, training status, author code availability, and BSDS protocol.",
            "Start from Akbarinia and Parraga, IJCV 2018, DOI 10.1007/s11263-017-1035-5; prefer official author code and archived supplementary material over secondary implementations.",
            "Classify the planned implementation as exact author code, faithful reimplementation, or surrogate, and state every missing element before execution.",
            "Preregister one fixed published SED variant without outcome-driven tuning and preserve literature-reported metrics separately from repository re-evaluation.",
            "Account explicitly for Stage 15a: the unmodified official Windows matcher is stochastic and not reference-certified; never use the seed-controlled diagnostic binary for dataset scoring.",
            "Register exactly one executable Stage-15b reproduction or a deterministic dependency preflight if exact reproduction is not yet possible.",
            "For an image experiment, provide an official BSDS500-validation manifest, per-image outputs, and deterministic best_method_preview.png with predeclared examples and panel order.",
            "Update the Stage-15 literature ledger and bibliography matrix for every source that materially determines the implementation or protocol.",
        ],
        "forbidden": [
            "Do not modify MFI architecture before Stage 15p.",
            "Do not tune SED parameters after seeing BSDS validation or any protected result.",
            "Do not use BSDS500 test, BIPEDv2 test, or UDED held-out feedback.",
            "Do not represent the local official evaluator as reference-verified.",
            "Do not score any dataset with the fixed-seed diagnostic matcher.",
        ],
        "official_eval_manifest_omission": (
            "Justified: literature/provenance planning only; no detector maps are generated."
        ),
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15B_SED_REPRODUCTION_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
