from __future__ import annotations

"""Resumable BSDS500 official evaluator.

This runner is intentionally checkpoint-first. It preserves every valid nonempty
per-image Berkeley match table and every complete per-method summary across
process restarts. A retry therefore continues only the missing work instead of
re-evaluating methods that are already complete.

The scientific computation remains unchanged: frozen prediction maps are passed
to the same pinned Berkeley matcher and the same MATLAB collection routine used
by ``run_official_bsds.py``.
"""

from pathlib import Path
import argparse
import hashlib
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import run_official_bsds as base


IDENTITY_FILE = "resume_identity.json"
SUMMARY_KEYS = ("ODS", "OIS", "AP")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _prediction_file(pred_dir: Path, image_id: str) -> Path:
    for suffix in (".png", ".mat"):
        candidate = pred_dir / f"{image_id}{suffix}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"missing frozen prediction for {image_id} in {pred_dir}")


def _prediction_fingerprint(pred_dir: Path, image_ids: list[str]) -> str:
    h = hashlib.sha256()
    for image_id in image_ids:
        path = _prediction_file(pred_dir, image_id)
        h.update(image_id.encode("utf-8"))
        h.update(b"\0")
        h.update(path.name.encode("utf-8"))
        h.update(b"\0")
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
    return h.hexdigest()


def _identity(
    *,
    method_name: str,
    pred_dir: Path,
    image_ids: list[str],
    split: str,
    cfg: dict,
) -> dict:
    sources = cfg["sources"]
    return {
        "schema_version": 1,
        "method": method_name,
        "split": split,
        "n_images": len(image_ids),
        "nthresh": int(cfg.get("nthresh", 99)),
        "max_dist": float(cfg.get("max_dist", 0.0075)),
        "thinpb": bool(cfg.get("thinpb", True)),
        "bsds500_commit": str(sources["bsds500"]["commit"]),
        "pdollar_edges_commit": str(sources["pdollar_edges"]["commit"]),
        "prediction_sha256": _prediction_fingerprint(pred_dir, image_ids),
    }


def _nonempty_tables(out_dir: Path, image_ids: list[str]) -> list[str]:
    return [
        image_id
        for image_id in image_ids
        if (out_dir / f"{image_id}_ev1.txt").exists()
        and (out_dir / f"{image_id}_ev1.txt").stat().st_size > 0
    ]


def _valid_summary(path: Path) -> bool:
    if not path.exists() or path.stat().st_size <= 0:
        return False
    try:
        data = _load(path)
    except Exception:
        return False
    return all(key in data for key in SUMMARY_KEYS)


def _ensure_identity(out_dir: Path, identity: dict, existing_count: int) -> None:
    identity_path = out_dir / IDENTITY_FILE
    if identity_path.exists():
        return

    # Stage 23F produced partial tables before the cross-retry identity file was
    # introduced. They live in the same frozen experiment directory and are
    # adopted once under the current exact prediction/config fingerprint.
    payload = dict(identity)
    payload["adopted_existing_nonempty_tables"] = int(existing_count)
    identity_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _check_identity(out_dir: Path, identity: dict) -> None:
    identity_path = out_dir / IDENTITY_FILE
    recorded = _load(identity_path)
    comparable = dict(recorded)
    comparable.pop("adopted_existing_nonempty_tables", None)
    if comparable != identity:
        raise RuntimeError(
            "refusing to resume Berkeley tables with mismatched provenance: "
            f"{identity_path}"
        )


def _evaluate_one_resume(
    matlab: Path,
    *,
    method_name: str,
    split: str,
    benchmark_dir: Path,
    image_dir: Path,
    gt_dir: Path,
    pred_dir: Path,
    out_dir: Path,
    cfg: dict,
) -> tuple[dict, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    image_ids = sorted(path.stem for path in image_dir.glob("*.jpg"))
    if not image_ids:
        raise RuntimeError(f"no BSDS images found in {image_dir}")

    identity = _identity(
        method_name=method_name,
        pred_dir=pred_dir,
        image_ids=image_ids,
        split=split,
        cfg=cfg,
    )
    existing = _nonempty_tables(out_dir, image_ids)
    _ensure_identity(out_dir, identity, len(existing))
    _check_identity(out_dir, identity)

    summary_path = out_dir / "official_summary.json"
    if len(existing) == len(image_ids) and _valid_summary(summary_path):
        print(
            f"BSDS_RESUME_SKIP_COMPLETE {method_name} tables={len(existing)}/{len(image_ids)}",
            flush=True,
        )
        return _load(summary_path), "reused_complete"

    # A stale aggregate summary must never hide missing per-image tables. The
    # aggregate is cheap and deterministic, so only it may be regenerated.
    if summary_path.exists() and len(existing) != len(image_ids):
        summary_path.unlink()

    nthresh = int(cfg.get("nthresh", 99))
    max_dist = float(cfg.get("max_dist", 0.0075))
    thinpb = 1 if bool(cfg.get("thinpb", True)) else 0
    expr_base = (
        f"addpath('{base._matlab_quote(base.MATLAB_WRAPPER_DIR)}');"
        "evaluate_bsds_official("
        f"'{base._matlab_quote(benchmark_dir)}',"
        f"'{base._matlab_quote(image_dir)}',"
        f"'{base._matlab_quote(gt_dir)}',"
        f"'{base._matlab_quote(pred_dir)}',"
        f"'{base._matlab_quote(out_dir)}',"
        f"{nthresh},{max_dist:.12g},{thinpb}"
    )

    existing_set = set(existing)
    missing = [image_id for image_id in image_ids if image_id not in existing_set]
    if missing:
        print(
            f"BSDS_RESUME_CONTINUE {method_name} tables={len(existing)}/{len(image_ids)} "
            f"missing={len(missing)}",
            flush=True,
        )

    eval_runs = []
    while missing:
        before = len(missing)
        proc = base._run(
            [str(matlab), "-batch", expr_base + ",'evaluate');"],
            timeout=4 * 60 * 60,
            check=False,
        )
        eval_runs.append(proc)
        completed_ids = set(_nonempty_tables(out_dir, image_ids))
        missing = [image_id for image_id in image_ids if image_id not in completed_ids]
        if not missing:
            break
        if len(missing) >= before:
            raise RuntimeError(
                "MATLAB native matching made no resumable progress; "
                f"method={method_name}, returncode={proc.returncode}, "
                f"missing={missing[:10]}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            )

    complete = _nonempty_tables(out_dir, image_ids)
    if len(complete) != len(image_ids):
        raise RuntimeError(
            f"incomplete resumable Berkeley table set for {method_name}: "
            f"{len(complete)}/{len(image_ids)}"
        )

    # If matching was already complete but collection had not run before the
    # interruption, jump directly to the deterministic aggregation step.
    collect = base._run(
        [str(matlab), "-batch", expr_base + ",'collect');"],
        timeout=4 * 60 * 60,
    )
    if not _valid_summary(summary_path):
        raise RuntimeError(
            f"Berkeley collection did not create a valid summary for {method_name}\n"
            f"COLLECT STDOUT:\n{collect.stdout}\nCOLLECT STDERR:\n{collect.stderr}"
        )

    result = _load(summary_path)
    result["resume_existing_tables_before"] = int(len(existing))
    result["resume_matching_processes"] = int(len(eval_runs))
    result["resume_mode"] = True
    print(
        f"BSDS_RESUME_METHOD_DONE {method_name} tables={len(complete)}/{len(image_ids)}",
        flush=True,
    )
    return result, "resumed" if existing else "computed"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default=str(base.DEFAULT_CONFIG))
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = base.ROOT / cfg_path
    cfg = base._load_json(cfg_path)

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = base.ROOT / manifest_path
    manifest = base._load_json(manifest_path)
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

    matlab = base._matlab_executable(cfg)
    bsds_root, benchmark_dir = base._ensure_benchmark_sources(cfg, split)
    image_dir = bsds_root / "BSDS500" / "data" / "images" / split
    gt_dir = bsds_root / "BSDS500" / "data" / "groundTruth" / split

    methods: list[dict] = []
    export_meta: dict[str, dict] = {}
    if bool(manifest.get("include_incumbent", True)) and bool(
        cfg.get("incumbent", {}).get("enabled", True)
    ):
        pred, meta = base._incumbent_predictions(
            cfg, image_dir=image_dir, gt_dir=gt_dir, split=split
        )
        methods.append({"name": "incumbent_compact_positive_choquet", "pred_dir": pred})
        export_meta["incumbent_compact_positive_choquet"] = meta

    for method in manifest.get("methods", []):
        pred, meta = base._export_method(
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
        out = base.ROOT / out
    out.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict] = {}
    resume_status: dict[str, str] = {}
    for method in methods:
        name = str(method["name"])
        method_out = out / "matlab" / base._safe_name(name)
        print(f"BSDS_OFFICIAL_EVAL {name} split={split}", flush=True)
        result, status = _evaluate_one_resume(
            matlab,
            method_name=name,
            split=split,
            benchmark_dir=benchmark_dir,
            image_dir=image_dir,
            gt_dir=gt_dir,
            pred_dir=Path(method["pred_dir"]),
            out_dir=method_out,
            cfg=cfg,
        )
        results[name] = result
        resume_status[name] = status

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
            "protected_document_only" if is_protected else "development_official_metric"
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
            "windows_correspondPixels_source_commit": str(src["pdollar_edges"]["commit"]),
            "reference_reproduction_verified": bool(
                cfg.get("reference_reproduction_verified", False)
            ),
            "resume_across_process_restarts": True,
        },
        "methods": results,
        "resume_status": resume_status,
        "comparisons_vs_incumbent": comparisons,
        "export": export_meta,
        "manifest": str(manifest_path.relative_to(base.ROOT)).replace("\\", "/")
        if base.ROOT.resolve() in manifest_path.resolve().parents
        else str(manifest_path),
        "final_claim_guard": (
            "Development metrics are decision-capable on train/val, but a final "
            "SOTA claim still requires an independently verified reference "
            "reproduction and the project's protected multi-benchmark gate."
        ),
    }
    base._save_json(out / "summary.json", summary)
    print("BSDS_OFFICIAL_RESUMABLE_EVALUATION_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
