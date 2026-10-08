from __future__ import annotations

"""Rebuild the pinned Berkeley matcher source and retest its five-image fixture."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "evaluation" / "bsds_official" / "config.json"
HELPERS = ROOT / "evaluation" / "bsds_official" / "matlab"
COMPAT = HELPERS / "stage15a_win_compat"
DEFAULT_OUT = ROOT / "results" / "automation" / "stage15a_source_matcher_rebuild"


def _q(path: Path) -> str:
    return str(path.resolve()).replace("'", "''").replace("\\", "/")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> np.ndarray:
    return np.atleast_2d(np.loadtxt(path, dtype=float))


def _matlab(matlab: Path, expression: str, prefdir: Path) -> dict:
    env = os.environ.copy()
    env["MATLAB_PREFDIR"] = str(prefdir.resolve())
    result = subprocess.run(
        [str(matlab), "-batch", expression],
        cwd=str(ROOT),
        env=env,
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out

    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    matlab = Path(cfg["matlab_executable"])
    bsds = ROOT / cfg["sources"]["bsds500"]["vendor_dir"]
    source = bsds / "bench" / "source"
    benchmark = bsds / "bench" / "benchmarks"
    fixture = bsds / "bench" / "data"
    shipped = fixture / "test_2"

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    build_dir = out / "matcher"
    build_dir.mkdir()
    prefdir = out / "matlab_prefs"
    prefdir.mkdir()

    processes = []
    processes.append(
        _matlab(
            matlab,
            f"addpath('{_q(HELPERS)}');stage15a_build_source_matcher("
            f"'{_q(source)}','{_q(build_dir)}','{_q(COMPAT)}');",
            prefdir,
        )
    )

    run_dirs = []
    for index in (1, 2):
        run_dir = out / f"rebuilt_run{index}"
        run_dirs.append(run_dir)
        processes.append(
            _matlab(
                matlab,
                f"addpath('{_q(HELPERS)}');stage15a_eval_fixture_with_matcher("
                f"'{_q(build_dir)}','{_q(benchmark)}','{_q(fixture / 'png')}',"
                f"'{_q(fixture / 'groundTruth')}','{_q(run_dir)}');",
                prefdir,
            )
        )

    table_names = ("eval_bdry.txt", "eval_bdry_img.txt", "eval_bdry_thr.txt")
    rows = []
    for name in table_names:
        first = _load(run_dirs[0] / name)
        second = _load(run_dirs[1] / name)
        expected = _load(shipped / name)
        if not (first.shape == second.shape == expected.shape):
            raise RuntimeError(f"shape mismatch for {name}")
        rows.append(
            {
                "table": name,
                "rebuilt_repeat_max_abs_delta": float(np.max(np.abs(first - second))),
                "rebuilt_vs_shipped_max_abs_delta": float(np.max(np.abs(first - expected))),
                "rebuilt_run1_sha256": _sha256(run_dirs[0] / name),
                "rebuilt_run2_sha256": _sha256(run_dirs[1] / name),
                "shipped_sha256": _sha256(shipped / name),
            }
        )

    with (out / "aggregate_rebuild_deltas.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    mex_path = build_dir / "correspondPixels.mexw64"
    summary = {
        "stage": "15a-source-matcher-rebuild",
        "role": "evaluator_diagnostic",
        "architecture_changed": False,
        "protected_split_used": False,
        "detector_predictions_generated": False,
        "full_validation_scored": False,
        "registered_tolerance_changed": False,
        "source_commit": cfg["sources"]["bsds500"]["commit"],
        "source_sha256": {
            name: _sha256(source / name)
            for name in (
                "correspondPixels.cc",
                "csa.cc",
                "kofn.cc",
                "match.cc",
                "Exception.cc",
                "Matrix.cc",
                "Random.cc",
                "String.cc",
                "Timer.cc",
            )
        },
        "windows_compile_compatibility_headers": {
            str(path.relative_to(ROOT)).replace("\\", "/"): _sha256(path)
            for path in sorted(COMPAT.rglob("*.h"))
        },
        "windows_compile_compatibility_scope": (
            "Forced-include typedef/API/legacy-macro shims plus POSIX timing and "
            "IEEE-754 declarations required by MSVC; vendored matcher sources are "
            "byte-unchanged and the assignment/matching algorithm is unmodified."
        ),
        "rebuilt_mex_sha256": _sha256(mex_path),
        "build_metadata": (build_dir / "build_metadata.txt").read_text(
            encoding="utf-8"
        ).splitlines(),
        "aggregate_tables": rows,
        "processes": processes,
        "decision_rule": (
            "Keep the registered 1e-4 tolerance. If the source-pinned rebuilt matcher "
            "is repeatable and all shipped aggregate tables agree within tolerance, use "
            "that locally built binary for the frozen Stage-15a retry with recorded build "
            "provenance. Otherwise Stage 15a remains open and the mismatch is classified "
            "as unresolved platform/source behavior rather than a detector result."
        ),
        "official_eval_manifest_omission": (
            "Justified: this is a five-image evaluator fixture/build diagnostic, emits no "
            "detector maps, and does not score BSDS validation."
        ),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15A_SOURCE_MATCHER_REBUILD_READY", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
