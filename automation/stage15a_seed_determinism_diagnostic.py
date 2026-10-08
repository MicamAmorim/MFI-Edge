from __future__ import annotations

"""Test whether the pinned matcher's clock-seeded RNG causes fixture drift."""

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
DEFAULT_OUT = ROOT / "results" / "automation" / "stage15a_seed_determinism_diagnostic"
FIXED_SEED = 1


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
        [str(matlab), "-batch", expression], cwd=str(ROOT), env=env,
        text=True, encoding="utf-8", errors="replace", capture_output=True,
        check=False, timeout=30 * 60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"MATLAB diagnostic failed ({result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return {"returncode": result.returncode,
            "stdout_tail": "\n".join(result.stdout.splitlines()[-20:])}


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
    controlled_source = out / "controlled_source"
    shutil.copytree(source, controlled_source)
    random_cc = controlled_source / "Random.cc"
    original_random_hash = _sha256(source / "Random.cc")
    source_text = random_cc.read_text(encoding="utf-8")
    old = "Random::Random ()\n{\n    reseed (0);\n}"
    new = f"Random::Random ()\n{{\n    reseed ({FIXED_SEED});\n}}"
    if source_text.count(old) != 1:
        raise RuntimeError("Pinned Random.cc no longer matches the audited seed transform")
    random_cc.write_text(source_text.replace(old, new), encoding="utf-8", newline="")

    build_dir = out / "matcher"
    build_dir.mkdir()
    prefdir = out / "matlab_prefs"
    prefdir.mkdir()
    processes = [_matlab(
        matlab,
        f"addpath('{_q(HELPERS)}');stage15a_build_source_matcher("
        f"'{_q(controlled_source)}','{_q(build_dir)}','{_q(COMPAT)}');",
        prefdir,
    )]
    run_dirs = []
    for index in (1, 2):
        run_dir = out / f"fixed_seed_run{index}"
        run_dirs.append(run_dir)
        processes.append(_matlab(
            matlab,
            f"addpath('{_q(HELPERS)}');stage15a_eval_fixture_with_matcher("
            f"'{_q(build_dir)}','{_q(benchmark)}','{_q(fixture / 'png')}',"
            f"'{_q(fixture / 'groundTruth')}','{_q(run_dir)}');",
            prefdir,
        ))

    rows = []
    for name in ("eval_bdry.txt", "eval_bdry_img.txt", "eval_bdry_thr.txt"):
        first = _load(run_dirs[0] / name)
        second = _load(run_dirs[1] / name)
        expected = _load(shipped / name)
        if not (first.shape == second.shape == expected.shape):
            raise RuntimeError(f"shape mismatch for {name}")
        rows.append({
            "table": name,
            "fixed_seed_repeat_max_abs_delta": float(np.max(np.abs(first - second))),
            "fixed_seed_vs_shipped_max_abs_delta": float(np.max(np.abs(first - expected))),
            "fixed_seed_run1_sha256": _sha256(run_dirs[0] / name),
            "fixed_seed_run2_sha256": _sha256(run_dirs[1] / name),
            "shipped_sha256": _sha256(shipped / name),
        })
    with (out / "fixed_seed_deltas.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "stage": "15a-seed-determinism-diagnostic",
        "role": "evaluator_diagnostic",
        "architecture_changed": False,
        "protected_split_used": False,
        "detector_predictions_generated": False,
        "full_validation_scored": False,
        "registered_tolerance_changed": False,
        "official_evaluator_modified": False,
        "diagnostic_only_controlled_source_copy": True,
        "fixed_seed": FIXED_SEED,
        "seed_choice_preregistered": True,
        "source_commit": cfg["sources"]["bsds500"]["commit"],
        "original_random_cc_sha256": original_random_hash,
        "controlled_random_cc_sha256": _sha256(random_cc),
        "controlled_transform": "In the run-local source copy only, replace the global Random default constructor's clock request reseed(0) with reseed(1).",
        "aggregate_tables": rows,
        "processes": processes,
        "decision_rule": "If every fixed-seed repeat delta is exactly zero, classify clock-seeded random sampling as the cause of fresh-process fixture drift. Close Stage 15a without reference-reproduction verification because the unmodified official path failed the registered 1e-4 criterion; the controlled binary is diagnostic only and must not score datasets. Otherwise retain unresolved platform/source behavior and do not proceed.",
        "official_eval_manifest_omission": "Justified: this is a five-image evaluator RNG diagnostic using shipped maps; it generates no detector maps and scores no BSDS validation images.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15A_SEED_DETERMINISM_DIAGNOSTIC_READY", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
