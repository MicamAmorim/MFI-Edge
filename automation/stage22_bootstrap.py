from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "automation" / "experiments.json"
CTX = ROOT / "automation" / "SCIENTIFIC_CONTEXT.md"
ROADMAP = ROOT / "ROADMAP.md"

EXP_ID = "stage22a_thesis_legacy_protocol_certification"
ENTRY = {
    "description": "Stage 22A exact thesis-legacy protocol certification: verify Drive-derived source hashes and synthetic MATLAB getBoundaries + ejBCM-F microcases without reading any dataset or scoring a detector.",
    "runner": "python",
    "path": "automation/stage22a_thesis_legacy_protocol_certification.py",
    "args": [],
    "role": "stage22_thesis_legacy_protocol_certification",
    "feedback_policy": "source_hash_and_synthetic_microcases_only_no_dataset_read_no_detector_scoring_no_promotion_finite_stage22_program",
    "one_shot": True,
    "result_files": [
        "results/automation/stage22a_thesis_legacy_protocol_certification/summary.json",
        "results/automation/stage22a_thesis_legacy_protocol_certification/matlab_microcases.json"
    ]
}

MARKER = "## Stage 22 activation - finite causal resolution and thesis-legacy program"
TEXT = f'''\n\n{MARKER}\n\nThe user explicitly starts the bounded Stage-22 program defined in `docs/paper/STAGE22_RESEARCH_PROGRAM.md`. It supersedes the Stage-21 synthesis stop. The hard scientific budget is five stages (22A-22E), with no sixth experiment, replacement candidate, post-hoc tuning loop, or automatic literature escalation after closure. Stage 22A is the registered next action. Compact distorted-Choquet MFI remains incumbent. Thesis-legacy, Berkeley-0.025, and Estrada-Jepson-0.025 tracks are descriptive/non-promotional and separate from standard Berkeley 0.0075.\n'''


def append_once(path: Path):
    txt = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if MARKER not in txt:
        path.write_text(txt.rstrip() + TEXT + "\n", encoding="utf-8")


def main():
    exps = json.loads(EXP.read_text(encoding="utf-8"))
    if EXP_ID not in exps:
        exps[EXP_ID] = ENTRY
        EXP.write_text(json.dumps(exps, indent=2) + "\n", encoding="utf-8")
    append_once(CTX)
    append_once(ROADMAP)
    print(f"STAGE22_BOOTSTRAP_READY: {EXP_ID}")
    print("Next: .\\run_research_autopilot.bat --reset-state")


if __name__ == "__main__":
    main()
