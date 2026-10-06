from __future__ import annotations

"""Stage 14e — research checkpoint for a controlled RDF robustness protocol.

This checkpoint performs no fitting and does not inspect external-test labels.
It exists because Stage 14d retained the five-feature compact positive bank but
stopped before an RDF comparison: the corruption protocol was under-specified.
The following Codex research step must use literature plus repository evidence to
specify one minimal, fair, development-only robustness experiment and register
exactly that next experiment.
"""

from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage14e_rdf_protocol_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "14e-rdf-robustness-protocol-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scientific_context": [
            "Stage 14b did not support spatially aligned negative evidence as a development advantage.",
            "Stage 14c retained a compact five-feature positive bank as noninferior to the fold-trained full bank on UDED selection repeated CV.",
            "Stage 14d showed that removing gabor4_scale_persistence degraded development performance, so the five-feature compact bank is provisionally retained.",
            "Stage 10 previously screened d-CF/d-CC/d-XC broadly and did not find a better inner-CV family than the standard family; a new RDF experiment must therefore test a mechanistically narrower robustness hypothesis rather than repeat a broad operator sweep.",
            "BSDS500 test, BIPEDv2 test, and UDED held-out are already inspected and forbidden as optimization signals.",
        ],
        "requested_work": [
            "Read automation/research_goal.json, automation/CODEX_POLICY.md, ROADMAP.md, docs/paper/EXPERIMENT_HISTORY.md, docs/paper/BIBLIOGRAPHY_MATRIX.md, synthetic_v2.py, the compact Stage-14 bank runner, and the implemented RDF/d-Choquet modules.",
            "Use live web search and prioritize primary literature on restricted dissimilarity functions, d-Choquet/d-CF/d-XC/d-CC aggregation, fuzzy edge fusion, and robustness to noise/blur/texture.",
            "Specify a controlled synthetic development protocol using only predeclared corruption families/severities. The protocol must separate clean-reference performance from corruption degradation and must not use external datasets to choose corruptions or parameters.",
            "Keep the five-feature compact positive signature, Scharr+NMS localizer, gate, and threshold-selection procedure fixed unless the RDF operator itself mathematically requires a narrowly documented representation change.",
            "Prefer one standard-Choquet control versus one literature-justified RDF operator/RDF pair as the first falsification test, not a broad grid. If literature does not justify a unique RDF choice, define a tiny preregistered pilot on synthetic validation only whose sole purpose is operator selection, followed by a separately registered confirmation experiment.",
            "Report metrics stratified by corruption family and severity, including absolute F1 and degradation from the clean/control condition. Predeclare the primary robustness criterion before implementation.",
            "Implement the smallest safe runner needed, register exactly one next experiment in automation/experiments.json, update relevant docs/paper records, and return that experiment id.",
        ],
        "protocol_constraints": {
            "development_data_allowed": [
                "datasets/sintetics/benchmark_v2/validation",
                "UDED selection only when repeated leakage-free CV is required"
            ],
            "forbidden_feedback": ["UDED held-out", "BSDS500 test", "BIPEDv2 test"],
            "fixed_architecture_elements": [
                "five-feature compact positive bank",
                "Scharr+NMS localizer",
                "context gate unless the RDF test is purely at the context-aggregation layer"
            ],
            "one_change_rule": "The primary comparison should change the aggregation/dissimilarity mechanism, not multiple architecture components simultaneously."
        },
        "paper_sync": [
            "Record materially used literature in docs/paper/BIBLIOGRAPHY_MATRIX.md.",
            "Record the preregistered protocol and rationale in docs/paper/EXPERIMENT_HISTORY.md.",
            "Update docs/paper/ARCHITECTURE_MAP.md only if the proposed RDF path changes the retained architecture.",
            "Update docs/paper/PAPER_WRITING_PLAN.md only if the manuscript claims/protocol narrative changes materially."
        ],
        "forbidden": [
            "No broad Stage-10-style RDF sweep as the first test.",
            "No choosing corruptions, RDFs, thresholds, or hyperparameters from BSDS/BIPED/UDED-heldout behavior.",
            "No modification of protected Stage-12 lineage files; add Stage-14 code instead or request human review.",
            "No mixture-of-experts work until development-only complementarity is demonstrated."
        ],
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE14E_RDF_PROTOCOL_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
