from __future__ import annotations

"""Launch Stage 16v with the repository Python environment."""

from pathlib import Path
import hashlib
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
RUNNER = ROOT / "run_stage16v_structured_forest.py"
EDGES_DIR = ROOT / "evaluation" / "bsds_official" / "vendor" / "pdollar_edges"
MODEL_RELATIVE = Path("models") / "forest" / "modelBsds.mat"
MODEL_SHA256 = "9b0f2af485516c89549d4050a7d29fe789c315a4632d16cf29a07796b54c1a6b"


def materialize_model() -> None:
    """Restore the pinned tracked model omitted by the vendor sparse checkout."""
    model_path = EDGES_DIR / MODEL_RELATIVE
    if not model_path.is_file():
        model_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = model_path.with_suffix(".mat.stage16v.tmp")
        trust = f"safe.directory={EDGES_DIR.resolve().as_posix()}"
        with temporary.open("wb") as handle:
            subprocess.run(
                [
                    "git", "-c", trust, "-C", str(EDGES_DIR), "show",
                    f"HEAD:{MODEL_RELATIVE.as_posix()}",
                ],
                cwd=str(ROOT), stdout=handle, check=True,
            )
        temporary.replace(model_path)
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    if digest != MODEL_SHA256:
        raise RuntimeError(
            f"pinned model hash mismatch: expected {MODEL_SHA256}, found {digest}"
        )


def main() -> int:
    if not VENV_PYTHON.is_file():
        print(f"ERROR: repository Python environment not found at {VENV_PYTHON}")
        return 2
    materialize_model()
    completed = subprocess.run(
        [str(VENV_PYTHON), str(RUNNER), *sys.argv[1:]],
        cwd=str(ROOT),
        check=False,
    )
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
