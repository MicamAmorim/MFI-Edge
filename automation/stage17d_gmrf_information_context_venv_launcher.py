from __future__ import annotations

"""Launch Stage 17d with the repository Python environment."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
RUNNER = ROOT / "run_stage17d_gmrf_information_context.py"


def main() -> int:
    if not VENV_PYTHON.is_file():
        print(f"ERROR: repository Python environment not found at {VENV_PYTHON}")
        return 2
    completed = subprocess.run(
        [str(VENV_PYTHON), str(RUNNER), *sys.argv[1:]],
        cwd=str(ROOT),
        check=False,
    )
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
