from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    python = ROOT / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = ROOT / ".venv" / "bin" / "python"
    if not python.exists():
        raise RuntimeError(f"repository virtual environment missing: {python}")
    return int(subprocess.run(
        [str(python), str(ROOT / "run_stage23g10_qfrd_fh_gap_diagnosis.py")],
        cwd=ROOT, check=False,
    ).returncode)


if __name__ == "__main__":
    raise SystemExit(main())
