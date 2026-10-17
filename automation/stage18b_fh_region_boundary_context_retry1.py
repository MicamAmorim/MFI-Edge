from __future__ import annotations

"""Harness-only retry for the unchanged Stage 18b FH experiment."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
RUNNER = ROOT / "run_stage18b_fh_region_boundary_context.py"
OUT = ROOT / "results" / "local_dev" / "stage18b_fh_region_boundary_context_retry1"


def main() -> int:
    if not PYTHON.exists():
        raise RuntimeError(f"repository virtual environment missing: {PYTHON}")
    command = [str(PYTHON), str(RUNNER), "--out", str(OUT), *sys.argv[1:]]
    return int(subprocess.run(command, cwd=ROOT, check=False).returncode)


if __name__ == "__main__":
    raise SystemExit(main())
