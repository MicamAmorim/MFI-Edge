from __future__ import annotations

"""Harness-only legacy-MATLAB compatibility retry for Stage 23G2."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_base_module():
    path = ROOT / "automation" / "stage23g2_pmi_exact_runtime_preflight.py"
    spec = importlib.util.spec_from_file_location("stage23g2_pmi_preflight_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the frozen Stage-23G2 preflight")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    base = _load_base_module()
    base.EXPERIMENT_ID = "stage23g2_pmi_exact_runtime_preflight_retry1"
    base.OUT = ROOT / "results" / "automation" / base.EXPERIMENT_ID
    base.BUILD_CODE_ROOT = (
        ROOT
        / "results"
        / "automation"
        / "stage23g2_pmi_exact_runtime_preflight"
        / f"build_worktree_{base.AUTHOR_COMMIT[:12]}"
        / "Code"
    )
    if not base.BUILD_CODE_ROOT.is_dir():
        raise RuntimeError("the provenance-verified Stage-23G2 build surface is missing")
    return int(base.main())


if __name__ == "__main__":
    raise SystemExit(main())
