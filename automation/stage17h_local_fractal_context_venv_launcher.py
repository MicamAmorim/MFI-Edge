from __future__ import annotations

"""Repository-local launcher selecting the established project environment."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
RUNNER = ROOT / "run_stage17h_local_fractal_context.py"


def main() -> int:
    if not PYTHON.exists():
        raise RuntimeError(f"repository virtual environment missing: {PYTHON}")
    command = [str(PYTHON), str(RUNNER), *sys.argv[1:]]
    return int(subprocess.run(command, cwd=ROOT, check=False).returncode)


if __name__ == "__main__":
    raise SystemExit(main())
