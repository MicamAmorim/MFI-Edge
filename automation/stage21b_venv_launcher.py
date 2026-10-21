from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
raise SystemExit(subprocess.call([str(PYTHON), str(ROOT / "automation" / "stage21b_three_protocol_retrospective.py"), *sys.argv[1:]], cwd=ROOT))
