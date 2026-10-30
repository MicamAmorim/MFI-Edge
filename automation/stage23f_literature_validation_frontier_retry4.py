from __future__ import annotations

"""Resume only the still-missing Stage-23F Berkeley match tables.

Retry 3 stopped before evaluator work because the checkpoint-preserving runner
could not resolve its sibling base module. This retry uses the repaired runner,
preserves all complete and partial tables, and computes only missing matches.
"""

from pathlib import Path
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "local_dev" / "stage23f_literature_validation_frontier"
MANIFEST = SOURCE / "official_eval_manifest.json"
PREVIEW = SOURCE / "best_method_preview.png"
OFFICIAL = ROOT / "results" / "official_eval" / "stage23f_literature_validation_frontier"
OUT = ROOT / "results" / "automation" / "stage23f_literature_validation_frontier_retry4"
EVALUATOR = ROOT / "evaluation" / "bsds_official" / "run_official_bsds_resume.py"
CONFIG = ROOT / "evaluation" / "bsds_official" / "config.json"

PAIRS = (
    ("pair_03", "stage23f_pair_03_minimum_conjunction", "stage23f_pair_03_equal_arithmetic_mean"),
    ("pair_04", "stage23f_pair_04_nonnegative_logistic_additive", "stage23f_pair_04_equal_arithmetic_mean"),
    ("triple_04", "stage23f_triple_04_median_owa", "stage23f_triple_04_equal_arithmetic_mean"),
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    for required in (MANIFEST, PREVIEW, EVALUATOR, CONFIG):
        if not required.exists():
            raise FileNotFoundError(required)

    frozen_root = SOURCE / "frozen_maps"
    manifest = _load(MANIFEST)
    methods = [str(item["name"]) for item in manifest["methods"]]
    if len(methods) != 6 or len(set(methods)) != 6:
        raise RuntimeError("Stage-23F manifest no longer contains exactly six methods")
    for method in methods:
        pngs = sorted((frozen_root / method).glob("*.png"))
        if len(pngs) != 100 or any(path.stat().st_size <= 0 for path in pngs):
            raise RuntimeError(f"incomplete frozen Stage-23F map set: {method}")

    repository_python = ROOT / ".venv" / "Scripts" / "python.exe"
    evaluator_python = repository_python if repository_python.exists() else Path(sys.executable)
    command = [
        str(evaluator_python), str(EVALUATOR),
        "--manifest", str(MANIFEST),
        "--experiment-id", "stage23f_literature_validation_frontier",
        "--out", str(OFFICIAL),
        "--config", str(CONFIG),
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"resumable Stage-23F official evaluation failed: {completed.returncode}")

    official_summary = _load(OFFICIAL / "summary.json")
    if official_summary.get("status") != "completed":
        raise RuntimeError("Stage-23F official summary is not complete")
    results = official_summary["methods"]

    relationships = []
    for set_id, primary_name, control_name in PAIRS:
        primary = results[primary_name]
        control = results[control_name]
        deltas = {
            "delta_ODS": float(primary["ODS"]) - float(control["ODS"]),
            "delta_OIS": float(primary["OIS"]) - float(control["OIS"]),
            "delta_AP": float(primary["AP"]) - float(control["AP"]),
        }
        relationships.append({
            "set_id": set_id,
            "primary": primary_name,
            "matched_equal_mean": control_name,
            **deltas,
            "jointly_transferable": bool(
                deltas["delta_ODS"] >= 0.002
                and deltas["delta_OIS"] >= 0.0
                and deltas["delta_AP"] >= 0.0
            ),
        })

    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "completed",
        "experiment_id": "stage23f_literature_validation_frontier_retry4",
        "source_experiment": "stage23f_literature_validation_frontier",
        "scope": "attachment-only resumable official BSDS500-validation evaluation",
        "descriptor_computation": 0,
        "aggregated_map_computation": 0,
        "frozen_predictions_changed": False,
        "manifest_changed": False,
        "incumbent_changed": False,
        "reference_reproduction_verified": False,
        "checkpoint_preserving_evaluator": True,
        "relationships": relationships,
        "official_summary": str((OFFICIAL / "summary.json").relative_to(ROOT)).replace("\\", "/"),
        "visual_preview": str(PREVIEW.relative_to(ROOT)).replace("\\", "/"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE23F_OFFICIAL_ATTACHMENT_RETRY4_COMPLETED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
