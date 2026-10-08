from __future__ import annotations

"""Planning checkpoint for the Stage-15j high-number protocol audit."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15j_high_number_protocol_audit_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "15j-high-number-protocol-audit-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage15i_status": (
            "exact pinned-author QFrD completed on BSDS500 validation at fixed defaults; "
            "local ODS/OIS/AP were 0.587261/0.618621/0.583650, all above the unchanged "
            "MFI incumbent, but the result is a reproduction baseline and the local "
            "matcher remains stochastic/reference-uncertified"
        ),
        "requested_work": [
            "Use live primary-source research to audit recent non-trained edge papers with unusually high reported F/F1 values.",
            "Prioritize claims already named in the Stage-15 program and bibliography, then add only directly relevant primary papers or official author repositories.",
            "For each candidate resolve dataset split, ODS versus per-image or average-optimal F, threshold selection scope, matcher/tolerance, annotation handling, thinning/NMS, resizing, and output multiplicity.",
            "Classify each method as strictly untrained, parameter-fixed but author-tuned, weakly data-calibrated, trained classical, neural, or unresolved.",
            "Keep literature headline metrics separate from the repository's common BSDS500-validation results and do not infer equivalence from metric labels alone.",
            "Select exactly one next action: an immutable exact-code reproduction checkpoint, a deterministic fidelity preflight, or closure of Stage 15j with the transition to Stage 15k if no additional method has a reproducible matched contract.",
            "Update STAGE15_LITERATURE_LEDGER.md, BIBLIOGRAPHY_MATRIX.md, SOTA_TARGETS.md when frontier evidence changes, and the protocol matrix/history with source-qualified conclusions."
        ],
        "forbidden": [
            "Do not modify MFI architecture before Stage 15p.",
            "Do not tune QFrD, any reproduced baseline, or any paper parameter from BSDS validation or protected results.",
            "Do not read or score BSDS500 test, BIPEDv2 test, or UDED held-out.",
            "Do not accept a headline F/F1 number as Berkeley ODS without primary-source protocol evidence.",
            "Do not register a surrogate when output-affecting choices remain unresolved.",
            "Do not represent the local Windows evaluator as reference-verified or use the fixed-seed diagnostic matcher for dataset scoring."
        ],
        "official_eval_manifest_omission": (
            "Required and justified: literature/protocol research only; no detector maps "
            "or image-benchmark outputs are generated."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15J_HIGH_NUMBER_PROTOCOL_AUDIT_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
