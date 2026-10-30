from __future__ import annotations

"""Harness-only legacy regression-tree API repair for Stage 23G2."""

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "stage23g2_pmi_exact_runtime_preflight_retry3"


def _load_base_module():
    path = ROOT / "automation" / "stage23g2_pmi_exact_runtime_preflight.py"
    spec = importlib.util.spec_from_file_location("stage23g2_pmi_preflight_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the frozen Stage-23G2 preflight")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    base = _load_base_module()
    base.EXPERIMENT_ID = EXPERIMENT_ID
    base.OUT = ROOT / "results" / "automation" / EXPERIMENT_ID
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

    # Unchanged getLocalPairs.m expects this deterministic image-size cache
    # destination beside Code. It is harness-owned because empty directories
    # were not copied into the sparse persistent build surface.
    cache_dir = base.BUILD_CODE_ROOT.parent / "caches" / "ii_jj_caches"
    cache_dir.mkdir(parents=True, exist_ok=True)

    original_write_harness = base._write_matlab_harness

    def write_harness_with_tree_compatibility() -> Path:
        harness = original_write_harness()
        compatibility_root = base.OUT / "matlab_compatibility"
        tree_adapter = compatibility_root / "classregtree.m"
        tree_adapter.write_text(
            """classdef classregtree
    properties (SetAccess = private)
        Model
    end
    methods
        function obj = classregtree(X, y, varargin)
            method = 'regression';
            minleaf = 1;
            nvartosample = 'all';
            for k = 1:2:numel(varargin)
                key = lower(char(varargin{k}));
                value = varargin{k+1};
                switch key
                    case 'method'
                        method = lower(char(value));
                    case 'minleaf'
                        minleaf = value;
                    case 'nvartosample'
                        nvartosample = value;
                    case 'prune'
                        assert(strcmpi(char(value), 'off'));
                    otherwise
                        error('classregtree_compat:unsupportedOption', ...
                            'Unsupported legacy classregtree option: %s', key);
                end
            end
            assert(strcmp(method, 'regression'));
            obj.Model = fitrtree(X, y, ...
                'MinLeafSize', minleaf, ...
                'NumVariablesToSample', nvartosample);
        end
        function y = eval(obj, X)
            y = predict(obj.Model, X);
        end
    end
end
""",
            encoding="utf-8",
        )
        return harness

    base._write_matlab_harness = write_harness_with_tree_compatibility
    return_code = int(base.main())

    summary_path = base.OUT / "summary.json"
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        adapter_path = base.OUT / "matlab_compatibility" / "classregtree.m"
        runtime = summary.setdefault("runtime_compatibility", {})
        runtime["legacy_tree_api"] = "classregtree/eval"
        runtime["tree_implementation"] = (
            "run-local classdef adapter to fitrtree/predict preserving the unchanged "
            "author method=regression, nvartosample, minleaf, and prune=off call contract"
        )
        runtime["tree_adapter_sha256"] = (
            _sha256(adapter_path) if adapter_path.is_file() else None
        )
        runtime["tree_adapter_scope"] = (
            "compile_test approximate-PMI compatibility path; the registered "
            "MS_algorithm_from_paper path sets approximate_PMI=false"
        )
        artifacts = summary.setdefault("artifacts", [])
        rel = str(adapter_path.relative_to(ROOT)).replace("\\", "/")
        if rel not in artifacts:
            artifacts.append(rel)
        summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
