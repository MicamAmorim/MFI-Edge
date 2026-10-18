from __future__ import annotations

"""Repository-local launcher selecting the established project environment."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
RUNNER = ROOT / "run_stage18t_isotonic_membership_calibration.py"


def main() -> int:
    if not PYTHON.exists():
        raise RuntimeError(f"repository virtual environment missing: {PYTHON}")
    return int(subprocess.run([str(PYTHON), str(RUNNER), *sys.argv[1:]], cwd=ROOT, check=False).returncode)


if __name__ == "__main__":
    raise SystemExit(main())
