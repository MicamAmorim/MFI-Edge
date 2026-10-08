from __future__ import annotations

"""Planning checkpoint for the Stage-15e CO/SCO reproduction audit."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15e_co_sco_reproduction_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "15e-co-sco-reproduction-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage15d_status": (
            "exact author-code grayscale EDPF completed on BSDS500 validation "
            "with ODS/OIS/AP 0.548048/0.548596/0.000000; retained as a "
            "strictly-untrained binary-output baseline, not an MFI component"
        ),
        "requested_work": [
            "Use live primary-source research on Yang et al. (2013), Efficient Color Boundary Detection with Color-Opponent Mechanisms, DOI 10.1109/CVPR.2013.362, and the associated CO implementation.",
            "Audit the primary SCO paper (DOI 10.1109/TIP.2015.2425538) and official or author-designated code to resolve the exact relationship between CO, double opponency, sparseness, and contextual processing.",
            "Establish immutable code provenance, license or redistribution constraints, fixed published variants and parameters, training class, dependencies, scalar output convention, and native-resolution execution path for each reproducible method.",
            "Recover the reported dataset split, evaluator, thresholding, NMS/thinning, and annotation protocol; keep literature metrics separate from the common BSDS500-validation reproduction.",
            "Choose exactly one next action: an exact fidelity-labeled reproduction when the public contract is complete, or a deterministic source/dependency/fidelity preflight when it is not.",
            "For an image experiment, emit per-image maps, runtimes and provenance, an official BSDS500-validation manifest, and best_method_preview.png using predeclared sorted positions 1, 50, and 100.",
            "Update the Stage-15 literature ledger and bibliography matrix with every source that materially determines implementation or protocol."
        ],
        "forbidden": [
            "Do not modify MFI architecture before Stage 15p.",
            "Do not tune CO/SCO parameters or choose variants from BSDS validation or protected results.",
            "Do not use BSDS500 test, BIPEDv2 test, or UDED held-out feedback.",
            "Do not conflate color opponency, contextual sparseness, and learned combination stages without source evidence.",
            "Do not represent the local Windows evaluator as reference-verified or use the fixed-seed diagnostic matcher for dataset scoring."
        ],
        "official_eval_manifest_omission": (
            "Justified: literature/provenance planning only; no detector maps are generated."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15E_CO_SCO_REPRODUCTION_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
