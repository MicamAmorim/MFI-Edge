from __future__ import annotations

"""Planning checkpoint for the Stage-15c vector co-occurrence audit."""

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15c_vcm_reproduction_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "15c-vector-cooccurrence-morphology-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "protected_split_used": False,
        "stage15b_status": (
            "exact author-code SED completed on BSDS500 validation with "
            "ODS/OIS/AP 0.678546/0.709152/0.712814; retained as an external "
            "strictly-untrained baseline, not an MFI component"
        ),
        "requested_work": [
            "Use live primary-source research on Lu et al. (2021), Vector co-occurrence morphological edge detection for colour image, DOI 10.1049/ipr2.12290.",
            "Establish author-code or supplementary-material availability, the exact published algorithm and fixed parameters, training classification, input colour space, output-map convention, and BSDS split/evaluator protocol.",
            "Audit whether the paper's reported high values are Berkeley ODS/OIS/AP under a comparable threshold and matching policy; preserve incompatible literature numbers separately.",
            "Prefer exact author code. If unavailable, enumerate all missing implementation details and label any proposed implementation faithful or surrogate before execution.",
            "Register exactly one executable Stage-15c reproduction, or one deterministic dependency/fidelity preflight when exact reproduction cannot yet be justified.",
            "For an image experiment, provide native-resolution per-image outputs, an official BSDS500-validation manifest, runtime/provenance records, and deterministic best_method_preview.png from predeclared positions.",
            "Update the Stage-15 literature ledger and bibliography matrix with every source that materially determines implementation or protocol."
        ],
        "forbidden": [
            "Do not modify MFI architecture before Stage 15p.",
            "Do not tune vector-morphology parameters from BSDS validation or any protected result.",
            "Do not use BSDS500 test, BIPEDv2 test, or UDED held-out feedback.",
            "Do not treat a proxy metric or paper headline as Berkeley ODS/OIS/AP without protocol verification.",
            "Do not represent the local Windows evaluator as reference-verified or use the fixed-seed diagnostic matcher for dataset scoring."
        ],
        "official_eval_manifest_omission": (
            "Justified: literature/provenance planning only; no detector maps are generated."
        )
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15C_VCM_REPRODUCTION_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
