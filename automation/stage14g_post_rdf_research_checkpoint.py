from __future__ import annotations

"""Stage 14g — literature-guided checkpoint after Stage 14f RDF falsification.

This checkpoint performs no fitting and does not inspect external-test labels.
It asks Codex to reassess the next mechanistically distinct development-only
hypothesis after the isolated d-CC/FBPC/absolute-RDF test failed promotion.
"""

from datetime import datetime, timezone
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage14g_post_rdf_research_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "14g-post-rdf-literature-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scientific_context": [
            "Stage 14b did not support spatially aligned negative evidence over an image-mean negative control.",
            "Stage 14c retained a compact five-feature positive bank with no meaningful development loss versus the full bank.",
            "Stage 14d showed gabor4_scale_persistence is not safely removable from that compact bank.",
            "Stage 14f tested one isolated RDF hypothesis: d-CC with FBPC and absolute RDF versus the retained standard positive distorted-Choquet control under paired synthetic corruption.",
            "Stage 14f failed its authoritative preregistered promotion rule: mean absolute corrupted-F1 advantage -0.00191, clean delta -0.00280, zero corruption families with positive mean absolute advantage.",
            "The protocol precedence issue is resolved in docs/paper/STAGE14F_PROTOCOL_RESOLUTION.md; do not treat the superseded history criterion as an active competing preregistration.",
        ],
        "requested_work": [
            "Read automation/research_goal.json, automation/CODEX_POLICY.md, ROADMAP.md, docs/paper/EXPERIMENT_HISTORY.md, docs/paper/STAGE14F_PREREGISTRATION.md, docs/paper/STAGE14F_PROTOCOL_RESOLUTION.md, docs/paper/BIBLIOGRAPHY_MATRIX.md, and only the implementation modules needed for candidate hypotheses.",
            "Use live web search and primary literature to compare a small set of mechanistically distinct next directions.",
            "Do not micro-tune d-CC/FBPC/absolute RDF after its failed preregistered test. The whole RDF family is not disproven, but any further RDF test must be mechanistically distinct and literature-justified rather than a parameter sweep.",
            "Consider whether development evidence now justifies a complementarity/error-regime analysis before any mixture-of-experts, or whether another compact aggregation/context mechanism has a stronger literature-backed falsification test.",
            "Choose exactly one minimal development-only experiment. Use UDED selection repeated leakage-free CV and/or synthetic development data as appropriate; never use UDED held-out, BSDS500 test, or BIPEDv2 test to choose the experiment or parameters.",
            "Register exactly one next experiment only if it is sufficiently specified; otherwise return requires_human=true with the unresolved methodological choice.",
            "Synchronize relevant docs/paper records according to CODEX_POLICY.md.",
        ],
        "forbidden": [
            "No promotion or tuning from external-test outcomes.",
            "No broad RDF/operator/RDF-function brute-force screen as the immediate next step.",
            "No mixture/ensemble before development-only complementarity is explicitly measured.",
            "No rewriting protected Stage-12 lineage files.",
        ],
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE14G_POST_RDF_RESEARCH_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
