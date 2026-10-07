from __future__ import annotations

"""Independent BSDS500 official MATLAB evaluation module.

The detector pipeline remains Python. This module:
1. bootstraps pinned official/compatible benchmark sources locally;
2. obtains the requested BSDS split without collapsing human annotations;
3. exports frozen soft edge maps (incumbent plus optional candidate methods);
4. calls MATLAB R2023a/another configured MATLAB in batch mode;
5. parses official boundaryBench-style ODS/OIS/AP into JSON for the agent.

By default BSDS500 validation is development feedback and BSDS500 test is
protected. Protected splits require an explicit manifest opt-in and are always
marked no-tuning.
"""

from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = MODULE_DIR / "config.json"
MATLAB_WRAPPER_DIR = MODULE_DIR / "matlab"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _run(
    cmd: list[str],
    *,
    cwd: Path = ROOT,
    timeout: float | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    p = subprocess.run(
        [str(x) for x in cmd],
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if check and p.returncode != 0:
        raise RuntimeError(
            f"command failed ({p.returncode}): {cmd!r}\n"
            f"STDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
        )
    return p


def _repo_path(value: str) -> Path:
    p = (ROOT / str(value)).resolve()
    if ROOT.resolve() not in p.parents and p != ROOT.resolve():
        raise ValueError(f"path escapes repository: {value}")
    return p


def _matlab_executable(cfg: dict) -> Path:
    candidates: list[Path] = []
    env = os.environ.get("MATLAB_EXE")
    if env:
        candidates.append(Path(env))
    configured = str(cfg.get("matlab_executable", "")).strip()
    if configured:
        candidates.append(Path(configured))

    found = shutil.which("matlab") or shutil.which("matlab.exe")
    if found:
        candidates.append(Path(found))

    if os.name == "nt":
        base = Path(r"C:\Program Files\MATLAB")
        if base.exists():
            candidates.extend(
                sorted(
                    base.glob(r"R20*\bin\matlab.exe"),
                    reverse=True,
                )
            )

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "MATLAB executable not found. Set MATLAB_EXE or edit "
        "evaluation/bsds_official/config.json."
    )


def _git_head(path: Path) -> str:
    return _run(["git", "-C", str(path), "rev-parse", "HEAD"]).stdout.strip()


def _ensure_sparse_checkout(
    repo_url: str,
    commit: str,
    dest: Path,
    sparse_paths: list[str],
) -> None:
    if not (dest / ".git").exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        _run(
            [
                "git", "clone", "--filter=blob:none", "--no-checkout",
                repo_url, str(dest),
            ],
            timeout=600,
        )
        _run(["git", "-C", str(dest), "sparse-checkout", "init", "--cone"])

    _run(
        ["git", "-C", str(dest), "sparse-checkout", "set", *sparse_paths],
        timeout=300,
    )

    # Fetching a SHA directly prevents the local benchmark from drifting when
    # upstream master changes. Repeating this on later runs is cheap and also
    # repairs an interrupted vendor checkout.
    _run(
        ["git", "-C", str(dest), "fetch", "--depth", "1", "origin", commit],
        timeout=600,
    )
    _run(
        ["git", "-C", str(dest), "checkout", "--detach", commit],
        timeout=300,
    )

    head = _git_head(dest)
    if head != commit:
        raise RuntimeError(
            f"pinned source mismatch for {dest}: expected {commit}, got {head}"
        )


def _ensure_benchmark_sources(cfg: dict, split: str) -> tuple[Path, Path]:
    sources = cfg["sources"]
    bs = sources["bsds500"]
    pd = sources["pdollar_edges"]

    bs_dest = _repo_path(bs["vendor_dir"])
    _ensure_sparse_checkout(
        str(bs["repository"]),
        str(bs["commit"]),
        bs_dest,
        [
            "bench",
            f"BSDS500/data/images/{split}",
            f"BSDS500/data/groundTruth/{split}",
        ],
    )

    pd_dest = _repo_path(pd["vendor_dir"])
    _ensure_sparse_checkout(
        str(pd["repository"]),
        str(pd["commit"]),
        pd_dest,
        ["private"],
    )

    benchmark_dir = bs_dest / "bench" / "benchmarks"
    if os.name == "nt":
        mex_src = pd_dest / "private" / "correspondPixels.mexw64"
        mex_dst = benchmark_dir / "correspondPixels.mexw64"
        if not mex_src.exists():
            raise FileNotFoundError(
                f"pinned Windows correspondPixels MEX missing: {mex_src}"
            )
        if not mex_dst.exists() or mex_dst.stat().st_size != mex_src.stat().st_size:
            shutil.copy2(mex_src, mex_dst)

    return bs_dest, benchmark_dir


def _safe_name(value: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._")
    return s or "method"


def _replace_args(
    values: list[Any],
    *,
    image_dir: Path,
    gt_dir: Path,
    output_dir: Path,
    split: str,
) -> list[str]:
    replacements = {
        "{image_dir}": str(image_dir),
        "{ground_truth_dir}": str(gt_dir),
        "{output_dir}": str(output_dir),
        "{split}": split,
    }
    out: list[str] = []
    for value in values:
        text = str(value)
        for key, repl in replacements.items():
            text = text.replace(key, repl)
        if any(ch in text for ch in "\n\r"):
            raise ValueError(f"unsafe export argument: {text!r}")
        out.append(text)
    return out


def _prediction_complete(pred_dir: Path, image_dir: Path) -> bool:
    ids = sorted(p.stem for p in image_dir.glob("*.jpg"))
    return bool(ids) and all((pred_dir / f"{iid}.png").exists() for iid in ids)


def _validate_predictions(pred_dir: Path, image_dir: Path) -> None:
    ids = sorted(p.stem for p in image_dir.glob("*.jpg"))
    missing = [iid for iid in ids if not (pred_dir / f"{iid}.png").exists()]
    if missing:
        raise RuntimeError(
            f"prediction directory {pred_dir} is missing {len(missing)} "
            f"BSDS maps; first missing ids: {missing[:10]}"
        )


def _export_method(
    method: dict,
    *,
    exp_id: str,
    image_dir: Path,
    gt_dir: Path,
    split: str,
) -> tuple[Path, dict]:
    name = _safe_name(method["name"])
    if method.get("prediction_dir"):
        pred_dir = _repo_path(str(method["prediction_dir"]))
        _validate_predictions(pred_dir, image_dir)
        return pred_dir, {"source": "prediction_dir"}

    export = method.get("export")
    if not isinstance(export, dict):
        raise ValueError(
            f"method {name!r} needs prediction_dir or export specification"
        )
    script = _repo_path(str(export["script"]))
    if script.suffix.lower() != ".py":
        raise ValueError("official-eval export scripts must be repository-local Python")
    if not script.exists():
        raise FileNotFoundError(script)

    pred_dir = (
        ROOT
        / "automation"
        / "runtime"
        / "official_eval_cache"
        / "experiments"
        / _safe_name(exp_id)
        / name
        / split
    )
    if _prediction_complete(pred_dir, image_dir):
        return pred_dir, {"source": "export_cache", "script": str(script.relative_to(ROOT))}

    pred_dir.mkdir(parents=True, exist_ok=True)
    args = _replace_args(
        list(export.get("args", [])),
        image_dir=image_dir,
        gt_dir=gt_dir,
        output_dir=pred_dir,
        split=split,
    )
    p = _run(
        [sys.executable, str(script), *args],
        timeout=float(export.get("timeout_minutes", 180)) * 60.0,
    )
    _validate_predictions(pred_dir, image_dir)
    return pred_dir, {
        "source": "export_script",
        "script": str(script.relative_to(ROOT)).replace("\\", "/"),
        "stdout_tail": "\n".join((p.stdout or "").splitlines()[-30:]),
    }


def _incumbent_predictions(
    cfg: dict,
    *,
    image_dir: Path,
    gt_dir: Path,
    split: str,
) -> tuple[Path, dict]:
    inc = cfg.get("incumbent", {})
    exporter = _repo_path(str(inc["exporter"]))
    source = exporter.read_bytes() + json.dumps(
        {
            "split": split,
            "png_bit_depth": cfg.get("png_bit_depth", 8),
        },
        sort_keys=True,
    ).encode("utf-8")
    fingerprint = hashlib.sha256(source).hexdigest()[:16]
    cache_base = _repo_path(str(inc["cache_dir"]))
    pred_dir = cache_base / split / fingerprint
    if _prediction_complete(pred_dir, image_dir):
        return pred_dir, {
            "source": "incumbent_cache",
            "fingerprint": fingerprint,
        }

    pred_dir.mkdir(parents=True, exist_ok=True)
    p = _run(
        [
            sys.executable,
            str(exporter),
            "--image-dir", str(image_dir),
            "--output-dir", str(pred_dir),
            "--split", split,
        ],
        timeout=4 * 60 * 60,
    )
    _validate_predictions(pred_dir, image_dir)
    return pred_dir, {
        "source": "incumbent_exporter",
        "fingerprint": fingerprint,
        "stdout_tail": "\n".join((p.stdout or "").splitlines()[-30:]),
    }


def _matlab_quote(path: Path | str) -> str:
    return str(path).replace("'", "''").replace("\\", "/")


def _evaluate_one(
    matlab: Path,
    *,
    benchmark_dir: Path,
    image_dir: Path,
    gt_dir: Path,
    pred_dir: Path,
    out_dir: Path,
    cfg: dict,
) -> dict:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    nthresh = int(cfg.get("nthresh", 99))
    max_dist = float(cfg.get("max_dist", 0.0075))
    thinpb = 1 if bool(cfg.get("thinpb", True)) else 0

    expr_base = (
        f"addpath('{_matlab_quote(MATLAB_WRAPPER_DIR)}');"
        "evaluate_bsds_official("
        f"'{_matlab_quote(benchmark_dir)}',"
        f"'{_matlab_quote(image_dir)}',"
        f"'{_matlab_quote(gt_dir)}',"
        f"'{_matlab_quote(pred_dir)}',"
        f"'{_matlab_quote(out_dir)}',"
        f"{nthresh},{max_dist:.12g},{thinpb}"
    )
    # Keep the native correspondPixels MEX lifecycle separate from the
    # allocation-heavy pure-MATLAB aggregation.  On Windows/R2023a the pinned
    # MEX can leave latent heap state that is detected only after all 100 image
    # files have been written, causing a false evaluator failure during
    # collection or process teardown.  This process boundary changes no score
    # computation and leaves the pinned sources untouched.
    expected_ids = sorted(path.stem for path in image_dir.glob("*.jpg"))
    eval_runs: list[subprocess.CompletedProcess] = []
    missing_eval = list(expected_ids)
    # The pinned Windows MEX intermittently terminates MATLAB with heap
    # corruption after it has successfully written a prefix of per-image
    # results. Resume those immutable results in fresh MATLAB processes rather
    # than discarding valid work or changing the matcher. The MATLAB wrapper
    # skips only nonempty result files, so each image is still matched exactly
    # once by the original Berkeley implementation.
    for _ in range(len(expected_ids) + 1):
        before = len(missing_eval)
        p_eval = _run(
            [str(matlab), "-batch", expr_base + ",'evaluate');"],
            timeout=4 * 60 * 60,
            check=False,
        )
        eval_runs.append(p_eval)
        missing_eval = [
            image_id
            for image_id in expected_ids
            if not (out_dir / f"{image_id}_ev1.txt").exists()
            or (out_dir / f"{image_id}_ev1.txt").stat().st_size == 0
        ]
        if not missing_eval:
            break
        if len(missing_eval) >= before:
            raise RuntimeError(
                "MATLAB native matching made no resumable progress; "
                f"returncode={p_eval.returncode}, missing={missing_eval[:10]}\n"
                f"STDOUT:\n{p_eval.stdout}\nSTDERR:\n{p_eval.stderr}"
            )
    if missing_eval:
        p_eval = eval_runs[-1]
        raise RuntimeError(
            "MATLAB native matching did not produce a complete evaluation set; "
            f"attempts={len(eval_runs)}, returncode={p_eval.returncode}, "
            f"missing={missing_eval[:10]}\nSTDOUT:\n{p_eval.stdout}\n"
            f"STDERR:\n{p_eval.stderr}"
        )
    p_collect = _run(
        [str(matlab), "-batch", expr_base + ",'collect');"],
        timeout=4 * 60 * 60,
    )
    summary_path = out_dir / "official_summary.json"
    if not summary_path.exists():
        raise RuntimeError(
            "MATLAB evaluator returned successfully but did not create "
            f"{summary_path}\nEVAL STDOUT:\n{p_eval.stdout}\n"
            f"EVAL STDERR:\n{p_eval.stderr}\nCOLLECT STDOUT:\n{p_collect.stdout}\n"
            f"COLLECT STDERR:\n{p_collect.stderr}"
        )
    result = _load_json(summary_path)
    result["matlab_evaluate_returncode"] = int(eval_runs[-1].returncode)
    result["matlab_evaluate_processes"] = len(eval_runs)
    result["matlab_evaluate_stdout_tail"] = "\n".join(
        (eval_runs[-1].stdout or "").splitlines()[-30:]
    )
    result["matlab_collect_stdout_tail"] = "\n".join(
        (p_collect.stdout or "").splitlines()[-30:]
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path
    cfg = _load_json(cfg_path)

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    manifest = _load_json(manifest_path)
    split = str(manifest.get("split") or cfg.get("development_split", "val"))

    protected = {str(x) for x in cfg.get("protected_splits", ["test"])}
    feedback_allowed = {
        str(x) for x in cfg.get("feedback_allowed_splits", ["train", "val"])
    }
    is_protected = split in protected
    if is_protected and not bool(manifest.get("allow_protected", False)):
        raise RuntimeError(
            f"split {split!r} is protected. Automatic official evaluation "
            "will not run it without explicit allow_protected=true."
        )

    matlab = _matlab_executable(cfg)
    bsds_root, benchmark_dir = _ensure_benchmark_sources(cfg, split)
    image_dir = bsds_root / "BSDS500" / "data" / "images" / split
    gt_dir = bsds_root / "BSDS500" / "data" / "groundTruth" / split
    if not image_dir.exists() or not gt_dir.exists():
        raise FileNotFoundError(
            f"BSDS split not available after bootstrap: {image_dir} / {gt_dir}"
        )

    methods: list[dict] = []
    export_meta: dict[str, dict] = {}

    if bool(manifest.get("include_incumbent", True)) and bool(
        cfg.get("incumbent", {}).get("enabled", True)
    ):
        pred, meta = _incumbent_predictions(
            cfg, image_dir=image_dir, gt_dir=gt_dir, split=split
        )
        methods.append({"name": "incumbent_compact_positive_choquet", "pred_dir": pred})
        export_meta["incumbent_compact_positive_choquet"] = meta

    for method in manifest.get("methods", []):
        pred, meta = _export_method(
            method,
            exp_id=args.experiment_id,
            image_dir=image_dir,
            gt_dir=gt_dir,
            split=split,
        )
        name = str(method["name"])
        methods.append({"name": name, "pred_dir": pred})
        export_meta[name] = meta

    if not methods:
        raise RuntimeError("official evaluation manifest contains no methods")

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict] = {}
    for method in methods:
        name = str(method["name"])
        method_out = out / "matlab" / _safe_name(name)
        print(f"BSDS_OFFICIAL_EVAL {name} split={split}", flush=True)
        results[name] = _evaluate_one(
            matlab,
            benchmark_dir=benchmark_dir,
            image_dir=image_dir,
            gt_dir=gt_dir,
            pred_dir=Path(method["pred_dir"]),
            out_dir=method_out,
            cfg=cfg,
        )

    incumbent_name = "incumbent_compact_positive_choquet"
    inc = results.get(incumbent_name)
    comparisons: dict[str, dict] = {}
    if inc:
        for name, value in results.items():
            if name == incumbent_name:
                continue
            comparisons[name] = {
                "delta_ODS": float(value["ODS"]) - float(inc["ODS"]),
                "delta_OIS": float(value["OIS"]) - float(inc["OIS"]),
                "delta_AP": float(value["AP"]) - float(inc["AP"]),
            }

    src = cfg["sources"]
    summary = {
        "status": "completed",
        "experiment_id": args.experiment_id,
        "dataset": "BSDS500",
        "split": split,
        "dataset_role": (
            "protected_document_only"
            if is_protected
            else "development_official_metric"
        ),
        "feedback_allowed": bool(split in feedback_allowed and not is_protected),
        "metric_policy": (
            "Agent may use these metrics for development decisions."
            if split in feedback_allowed and not is_protected
            else "Agent may document these metrics but must not tune from them."
        ),
        "evaluator": {
            "family": "original Berkeley BSDS boundary benchmark",
            "matlab": str(matlab),
            "nthresh": int(cfg.get("nthresh", 99)),
            "max_dist": float(cfg.get("max_dist", 0.0075)),
            "thinpb": bool(cfg.get("thinpb", True)),
            "multi_annotator": True,
            "bsds500_commit": str(src["bsds500"]["commit"]),
            "windows_correspondPixels_source_commit": str(
                src["pdollar_edges"]["commit"]
            ),
            "reference_reproduction_verified": bool(
                cfg.get("reference_reproduction_verified", False)
            ),
        },
        "methods": results,
        "comparisons_vs_incumbent": comparisons,
        "export": export_meta,
        "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/")
        if ROOT.resolve() in manifest_path.resolve().parents
        else str(manifest_path),
        "final_claim_guard": (
            "Development metrics are decision-capable on train/val, but a final "
            "SOTA claim still requires an independently verified reference "
            "reproduction and the project's protected multi-benchmark gate."
        ),
    }
    _save_json(out / "summary.json", summary)
    print("BSDS_OFFICIAL_EVALUATION_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
