from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    windows = ROOT / ".venv" / "Scripts" / "python.exe"
    python = windows if windows.exists() else ROOT / ".venv" / "bin" / "python"
    if not python.exists():
        raise RuntimeError(f"repository virtual environment missing: {python}")
    return int(subprocess.run(
        [str(python), str(ROOT / "run_stage23d_cached_complementarity_map.py"), *sys.argv[1:]],
        cwd=ROOT, check=False,
    ).returncode)


if __name__ == "__main__":
    raise SystemExit(main())
