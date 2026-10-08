from __future__ import annotations

"""Harness-only dependency/checkout repair for the frozen Stage-15i preflight."""

import importlib.util
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
AUTHOR_ROOT = ROOT / "external" / "QFrD_stage15i_retry1"
AUTHOR_REPOSITORY = "https://github.com/renhu9120/QFrD.git"
AUTHOR_COMMIT = "8dcc8d846e6dcbe1bc4b931b89f1c814f5f9a245"
OUT = ROOT / "results" / "automation" / "stage15i_qfrd_runtime_preflight_retry1"
TORCH_REQUIREMENTS = ("torch==2.9.0", "torchvision==0.24.0")


def _run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd or ROOT), check=False, text=True)


def _prepare_clean_checkout() -> None:
    """Use a fresh ignored checkout; never overwrite the incomplete first clone."""
    if not AUTHOR_ROOT.exists():
        AUTHOR_ROOT.parent.mkdir(parents=True, exist_ok=True)
        clone = _run(
            ["git", "-c", "safe.directory=*", "clone", "--no-checkout", AUTHOR_REPOSITORY, str(AUTHOR_ROOT)]
        )
        if clone.returncode != 0:
            raise RuntimeError(f"author clone failed with exit code {clone.returncode}")
        checkout = _run(
            ["git", "-c", "safe.directory=*", "checkout", "--detach", AUTHOR_COMMIT],
            cwd=AUTHOR_ROOT,
        )
        if checkout.returncode != 0:
            raise RuntimeError(f"author checkout failed with exit code {checkout.returncode}")


def _repair_runtime() -> None:
    missing = [name for name in ("torch", "torchvision") if importlib.util.find_spec(name) is None]
    if not missing:
        return
    install = _run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--index-url",
            "https://download.pytorch.org/whl/cpu",
            *TORCH_REQUIREMENTS,
        ]
    )
    if install.returncode != 0:
        raise RuntimeError(f"pinned CPU runtime installation failed with exit code {install.returncode}")


def _load_base_module():
    path = ROOT / "automation" / "stage15i_qfrd_runtime_preflight.py"
    spec = importlib.util.spec_from_file_location("stage15i_qfrd_runtime_preflight_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the frozen Stage-15i preflight harness")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    _prepare_clean_checkout()
    _repair_runtime()
    base = _load_base_module()
    base.AUTHOR_ROOT = AUTHOR_ROOT
    base.OUT = OUT
    return int(base.main())


if __name__ == "__main__":
    raise SystemExit(main())
