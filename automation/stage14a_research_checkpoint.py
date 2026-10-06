from __future__ import annotations

"""Stage 14a — literature-guided planning checkpoint for a new development cycle.

This checkpoint performs no fitting and does not inspect external-test labels.
It writes a compact planning event so the on-demand Codex step can research the
implemented mechanism families, choose one minimal development-only falsification
experiment, register it, and stop before any external-test reuse.
"""

from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage14a_research_checkpoint"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "14a-literature-guided-development-checkpoint",
        "role": "research_planning",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scientific_context": [
            "Stage 13 external-transfer work is complete for the current frozen generation.",
            "BSDS500 test and BIPEDv2 test are already inspected external tests and must not be used for Stage-14 optimization or experiment prioritization.",
            "A human has authorized a new development cycle using synthetic development data and UDED selection repeated leakage-free CV only.",
            "The repository already contains d-Choquet/d-CF/d-XC/d-CC RDF operators, positive-only, separable bi-capacity, ratio-control, contextual routing, and multiscale signature machinery.",
        ],
        "requested_work": [
            "Read automation/research_goal.json, automation/CODEX_POLICY.md, ROADMAP.md, docs/paper/EXPERIMENT_HISTORY.md, docs/paper/BIBLIOGRAPHY_MATRIX.md, and the relevant implemented fuzzy modules.",
            "When live web search is available, check current primary literature for RDF/d-Choquet edge aggregation, contextual/nonadditive routing, compact capacities, and interpretable mixture-of-experts ideas relevant to this architecture.",
            "Formulate about three mechanistically distinct Stage-14 hypotheses without using BSDS/BIPED outcomes as the optimization signal.",
            "Prefer pruning/ablation before combination. Do not build a large ensemble unless development-only evidence first demonstrates complementarity.",
            "Choose exactly one minimal falsification experiment on allowed development data, implement its runner if needed, register it in automation/experiments.json, and return its exact experiment id.",
            "Use repeated leakage-free CV when architecture or thresholds are compared; keep UDED held-out unused.",
        ],
        "candidate_mechanisms": [
            "RDF-based d-Choquet/d-CF/d-XC/d-CC on the multiscale signature, especially under blur/noise/texture/scale heterogeneity.",
            "Development-only ablation of relative positive-vs-negative contextual control versus positive-only and separable bi-capacity controls.",
            "Small interpretable conditional expert routing only if prior development ablations show complementary regime-specific benefit.",
        ],
        "forbidden": [
            "No fitting, ranking, threshold selection, architecture choice, or hyperparameter tuning from BSDS500 test or BIPEDv2 test.",
            "No optimization on UDED held-out.",
            "No broad brute-force sweep as the first Stage-14 experiment.",
            "No modification of protected Stage-12 lineage files; create new Stage-14 scripts/modules instead or request human review.",
        ],
    }
    path = OUT / "summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE14A_RESEARCH_CHECKPOINT_READY")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
