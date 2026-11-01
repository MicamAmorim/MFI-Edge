from __future__ import annotations

"""Harness-only Stage-23G9 retry with an accessible MSVC runtime path."""

from pathlib import Path
import os
import runpy


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "automation" / "stage23g9_qfrd_overlap_clean_materialization.py"
VC_RUNTIME = Path(
    r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE"
)
REQUIRED_RUNTIME_FILES = (
    "msvcp140.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll",
)


def main() -> int:
    missing = [name for name in REQUIRED_RUNTIME_FILES if not (VC_RUNTIME / name).is_file()]
    if missing:
        raise RuntimeError(
            "Stage-23G9 retry cannot locate the installed x64 MSVC runtime: "
            + ", ".join(missing)
        )
    # Retain the handle for the delegated process. This changes only Windows
    # DLL resolution; the Python environment and QFrD path remain unchanged.
    runtime_handle = os.add_dll_directory(str(VC_RUNTIME))
    try:
        runpy.run_path(str(BASE), run_name="__main__")
    finally:
        runtime_handle.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
