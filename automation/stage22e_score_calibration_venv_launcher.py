from __future__ import annotations

"""Run the single Stage-22E calibration candidate in the repository environment."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
RUNNER = ROOT / "run_stage22e_score_calibration.py"


def main() -> int:
    if not PYTHON.exists():
        raise RuntimeError(f"repository Python is missing: {PYTHON}")
    return subprocess.call([str(PYTHON), str(RUNNER), *sys.argv[1:]], cwd=str(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
