from __future__ import annotations

"""Diagnose the frozen Stage-15a Berkeley fixture mismatch without scoring data."""

from pathlib import Path
import csv
import hashlib
import json


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "results" / "local_dev" / "stage15a_protocol_audit"
FIXTURE = (
    ROOT
    / "evaluation"
    / "bsds_official"
    / "vendor"
    / "BSDS500"
    / "bench"
    / "data"
)
OUT = ROOT / "results" / "automation" / "stage15a_fixture_diagnostic"
TABLES = ("eval_bdry.txt", "eval_bdry_img.txt", "eval_bdry_thr.txt")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _numeric_rows(path: Path) -> list[list[float]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append([float(value) for value in line.split()])
    return rows


def main() -> int:
    summary_path = AUDIT / "summary.json"
    if not summary_path.exists():
        raise RuntimeError("Stage-15a audit summary is missing")
    audit = json.loads(summary_path.read_text(encoding="utf-8"))
    reference = audit.get("reference_reproduction", {})

    comparisons = []
    for name in TABLES:
        expected_path = FIXTURE / "test_2" / name
        observed_path = AUDIT / "reference_eval" / name
        if not expected_path.exists() or not observed_path.exists():
            raise RuntimeError(f"missing fixture comparison table: {name}")
        expected = _numeric_rows(expected_path)
        observed = _numeric_rows(observed_path)
        if len(expected) != len(observed):
            raise RuntimeError(f"row-count mismatch for {name}")
        deltas = [
            abs(left - right)
            for expected_row, observed_row in zip(expected, observed)
            for left, right in zip(expected_row, observed_row)
        ]
        comparisons.append(
            {
                "table": name,
                "expected_sha256": _sha256(expected_path),
                "observed_sha256": _sha256(observed_path),
                "rows": len(expected),
                "max_abs_numeric_delta": max(deltas, default=0.0),
                "mean_abs_numeric_delta": sum(deltas) / len(deltas) if deltas else 0.0,
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "fixture_table_deltas.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparisons[0]))
        writer.writeheader()
        writer.writerows(comparisons)

    summary = {
        "stage": "15a-fixture-diagnostic",
        "role": "evaluator_diagnostic",
        "architecture_changed": False,
        "protected_split_used": False,
        "detector_predictions_generated": False,
        "reference_fixture_passed_original_tolerance": bool(reference.get("passed", False)),
        "registered_tolerance": reference.get("tolerance"),
        "metric_absolute_error": reference.get("absolute_error"),
        "comparisons": comparisons,
        "source_hashes_sha256": audit.get("evaluator", {}).get(
            "source_hashes_sha256", {}
        ),
        "diagnostic_scope": (
            "Quantify exact shipped-table versus locally regenerated-table drift and "
            "preserve input/source hashes before deciding whether the mismatch is a "
            "Windows MEX/platform compatibility effect or an evaluator-path defect."
        ),
        "decision_rule": (
            "Do not relax the preregistered 1e-4 tolerance and do not run the full "
            "validation attachment until the fixture discrepancy has a documented, "
            "source-supported explanation or a faithful evaluator repair."
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15A_FIXTURE_DIAGNOSTIC_READY", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
