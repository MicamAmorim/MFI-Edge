from __future__ import annotations

"""Fixture-only equivalence test for two pinned Berkeley evaluator paths."""

from pathlib import Path
import csv
import hashlib
import json
import shutil
import subprocess

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "evaluation" / "bsds_official" / "config.json"
PRIOR = ROOT / "results" / "local_dev" / "stage15a_protocol_audit" / "reference_eval"
OUT = ROOT / "results" / "automation" / "stage15a_evaluator_path_equivalence"
MATLAB_HELPERS = ROOT / "evaluation" / "bsds_official" / "matlab"


def _q(path: Path) -> str:
    return str(path.resolve()).replace("'", "''").replace("\\", "/")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_table(path: Path) -> np.ndarray:
    return np.atleast_2d(np.loadtxt(path, dtype=float))


def _run_matlab(matlab: Path, expression: str) -> dict:
    result = subprocess.run(
        [str(matlab), "-batch", expression],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        timeout=30 * 60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"MATLAB diagnostic failed ({result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return {
        "returncode": result.returncode,
        "stdout_tail": "\n".join(result.stdout.splitlines()[-20:]),
    }


def _git_blob(repo: Path, relative_path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", f"HEAD:{relative_path}"],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def main() -> int:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    matlab = Path(cfg["matlab_executable"])
    bsds = ROOT / cfg["sources"]["bsds500"]["vendor_dir"]
    pdollar = ROOT / cfg["sources"]["pdollar_edges"]["vendor_dir"]
    benchmark = bsds / "bench" / "benchmarks"
    fixture = bsds / "bench" / "data"
    shipped = fixture / "test_2"

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    expression_base = (
        f"addpath('{_q(MATLAB_HELPERS)}');"
        "stage15a_compare_eval_paths("
        f"'{_q(pdollar)}','{_q(benchmark)}','{_q(fixture / 'images')}',"
        f"'{_q(fixture / 'groundTruth')}',{{out}});"
    )
    process_meta = []
    run_dirs = []
    for index in (1, 2):
        run_dir = OUT / f"pdollar_run{index}"
        run_dirs.append(run_dir)
        expression = expression_base.replace("{out}", f"'{_q(run_dir)}'")
        process_meta.append(_run_matlab(matlab, expression))

    table_names = ("eval_bdry.txt", "eval_bdry_img.txt", "eval_bdry_thr.txt")
    rows = []
    for name in table_names:
        wrapper = _load_table(PRIOR / name)
        first = _load_table(run_dirs[0] / name)
        second = _load_table(run_dirs[1] / name)
        expected = _load_table(shipped / name)
        if not (wrapper.shape == first.shape == second.shape == expected.shape):
            raise RuntimeError(f"shape mismatch for {name}")
        rows.append(
            {
                "table": name,
                "wrapper_vs_pdollar_max_abs_delta": float(np.max(np.abs(wrapper - first))),
                "pdollar_repeat_max_abs_delta": float(np.max(np.abs(first - second))),
                "pdollar_vs_shipped_max_abs_delta": float(np.max(np.abs(first - expected))),
                "wrapper_sha256": _sha256(PRIOR / name),
                "pdollar_run1_sha256": _sha256(run_dirs[0] / name),
                "pdollar_run2_sha256": _sha256(run_dirs[1] / name),
                "shipped_sha256": _sha256(shipped / name),
            }
        )

    image_ids = sorted(path.stem for path in (fixture / "images").glob("*.jpg"))
    raw_rows = []
    for image_id in image_ids:
        wrapper_path = PRIOR / f"{image_id}_ev1.txt"
        first_path = run_dirs[0] / f"{image_id}_ev1.txt"
        second_path = run_dirs[1] / f"{image_id}_ev1.txt"
        wrapper = _load_table(wrapper_path)
        first = _load_table(first_path)
        second = _load_table(second_path)
        raw_rows.append(
            {
                "image_id": image_id,
                "wrapper_vs_pdollar_max_abs_delta": float(np.max(np.abs(wrapper - first))),
                "pdollar_repeat_max_abs_delta": float(np.max(np.abs(first - second))),
                "wrapper_sha256": _sha256(wrapper_path),
                "pdollar_run1_sha256": _sha256(first_path),
                "pdollar_run2_sha256": _sha256(second_path),
            }
        )

    with (OUT / "aggregate_path_deltas.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (OUT / "per_image_raw_path_deltas.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(raw_rows[0]))
        writer.writeheader()
        writer.writerows(raw_rows)

    bsds_linux_mex = benchmark / "correspondPixels.mexa64"
    pdollar_linux_mex = pdollar / "private" / "correspondPixels.mexa64"
    pdollar_windows_mex = pdollar / "private" / "correspondPixels.mexw64"
    summary = {
        "stage": "15a-evaluator-path-equivalence",
        "role": "evaluator_diagnostic",
        "architecture_changed": False,
        "protected_split_used": False,
        "detector_predictions_generated": False,
        "full_validation_scored": False,
        "registered_tolerance_changed": False,
        "comparison": {
            "paths": [
                "repository syntax-compatible pinned evaluation_bdry_image",
                "Piotr Dollar edgesEvalImg documented as BSDS-compatible",
            ],
            "same_windows_matcher": True,
            "fresh_matlab_process_repetition": True,
            "aggregate_tables": rows,
            "raw_image_tables": raw_rows,
        },
        "binary_provenance": {
            "bsds_linux_mex_sha256": _sha256(bsds_linux_mex),
            "pdollar_linux_mex_sha256": _sha256(pdollar_linux_mex),
            "linux_mex_bytes_identical": bsds_linux_mex.read_bytes() == pdollar_linux_mex.read_bytes(),
            "pdollar_windows_mex_sha256": _sha256(pdollar_windows_mex),
            "bsds_linux_mex_git_blob": _git_blob(bsds, "bench/benchmarks/correspondPixels.mexa64"),
            "pdollar_linux_mex_git_blob": _git_blob(pdollar, "private/correspondPixels.mexa64"),
            "pdollar_windows_mex_git_blob": _git_blob(pdollar, "private/correspondPixels.mexw64"),
        },
        "processes": process_meta,
        "decision_rule": (
            "Do not relax the 1e-4 fixture tolerance. Exact wrapper/pdollar and repeat "
            "agreement rules out repository compatibility-transform, aggregation, and "
            "nondeterminism defects, isolating the remaining mismatch to compiled/platform "
            "or historical fixture-generation provenance. Otherwise repair the divergent path."
        ),
        "official_eval_manifest_omission": (
            "Justified: this is a five-image evaluator fixture equivalence test, generates "
            "no detector maps, and deliberately does not score BSDS validation."
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15A_EVALUATOR_PATH_EQUIVALENCE_READY", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
