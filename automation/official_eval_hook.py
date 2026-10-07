from __future__ import annotations

"""Optional official-evaluation hook for the autonomous research controller.

This module is deliberately outside the detector pipeline. It runs after a
registered image experiment has produced its normal outputs and before Codex
analyzes the event. Failures are recorded as evaluator metadata and, under the
default policy, do not invalidate the underlying experiment.

A candidate opts in by emitting `official_eval_manifest.json` next to its
primary result. The manifest describes how to export a frozen soft boundary map
for a development split. BSDS500 test is protected and never becomes an
optimization signal.
"""

from pathlib import Path
import hashlib
import json
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "results" / "official_eval"

SKIP_ROLES = {
    "research_planning",
    "literature_escalation",
    "dataset_preflight",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _sha256(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _candidate_manifest(exp_id: str, spec: dict, config: dict) -> Path | None:
    official = config.get("official_evaluation", {})
    filename = str(
        spec.get("official_eval_manifest")
        or official.get("manifest_filename")
        or "official_eval_manifest.json"
    )

    explicit = spec.get("official_eval_manifest")
    if explicit:
        p = ROOT / str(explicit)
        return p if p.exists() else None

    for raw in spec.get("result_files", []):
        p = ROOT / str(raw)
        if p.name.lower() == "summary.json":
            candidate = p.parent / filename
            if candidate.exists():
                return candidate
    for raw in spec.get("result_files", []):
        p = ROOT / str(raw)
        candidate = p.parent / filename
        if candidate.exists():
            return candidate

    for base in (
        ROOT / "results" / "local_dev" / exp_id,
        ROOT / "results" / "external" / exp_id,
    ):
        p = base / filename
        if p.exists():
            return p
    return None


def _module_path(config: dict) -> Path:
    rel = str(
        config.get("official_evaluation", {}).get(
            "module", "evaluation/bsds_official/run_official_bsds.py"
        )
    )
    p = (ROOT / rel).resolve()
    if ROOT.resolve() not in p.parents:
        raise RuntimeError(f"official evaluator module escapes repository: {rel}")
    if not p.exists():
        raise FileNotFoundError(p)
    return p


def _summary_path(exp_id: str) -> Path:
    return RESULT_ROOT / exp_id / "summary.json"


def _same_completed(summary_path: Path, manifest_hash: str | None) -> bool:
    if not summary_path.exists():
        return False
    try:
        old = _load_json(summary_path)
    except Exception:
        return False
    terminal = {"completed", "evaluator_failed", "evaluator_timeout"}
    return (
        old.get("status") in terminal
        and old.get("manifest_sha256") == manifest_hash
    )


def maybe_run(exp_id: str, spec: dict, config: dict) -> dict | None:
    official = config.get("official_evaluation", {})
    if not bool(official.get("enabled", False)):
        return None
    if not bool(official.get("run_before_codex", True)):
        return None

    role = str(spec.get("role", "development"))
    if role in SKIP_ROLES:
        return None

    out_summary = _summary_path(exp_id)
    manifest = _candidate_manifest(exp_id, spec, config)
    manifest_hash = _sha256(manifest)

    if _same_completed(out_summary, manifest_hash):
        return _load_json(out_summary)

    if manifest is None:
        result = {
            "status": "manifest_missing",
            "experiment_id": exp_id,
            "role": role,
            "message": (
                "No official_eval_manifest.json was emitted by this experiment. "
                "The normal experiment remains valid; future image-based "
                "development experiments must emit the manifest so official "
                "BSDS development metrics can be attached before Codex decides."
            ),
            "manifest_sha256": None,
        }
        _save_json(out_summary, result)
        return result

    module = _module_path(config)
    eval_cfg = ROOT / str(
        official.get("config", "evaluation/bsds_official/config.json")
    )
    cmd = [
        sys.executable,
        str(module),
        "--manifest",
        str(manifest),
        "--experiment-id",
        exp_id,
        "--out",
        str(out_summary.parent),
        "--config",
        str(eval_cfg),
    ]
    timeout_s = float(config.get("experiment_timeout_minutes", 360)) * 60.0

    print("\nOFFICIAL EVALUATION: running BSDS MATLAB module before Codex...", flush=True)
    try:
        p = subprocess.run(
            cmd,
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
        if p.stdout:
            print(p.stdout, end="" if p.stdout.endswith("\n") else "\n", flush=True)
        if p.returncode == 0 and out_summary.exists():
            result = _load_json(out_summary)
            result["manifest_sha256"] = manifest_hash
            _save_json(out_summary, result)
            return result

        result = {
            "status": "evaluator_failed",
            "experiment_id": exp_id,
            "role": role,
            "returncode": int(p.returncode),
            "manifest": str(manifest.relative_to(ROOT)).replace("\\", "/"),
            "manifest_sha256": manifest_hash,
            "stdout_tail": "\n".join((p.stdout or "").splitlines()[-80:]),
            "stderr_tail": "\n".join((p.stderr or "").splitlines()[-80:]),
            "failure_policy": str(official.get("failure_policy", "report_and_continue")),
        }
        _save_json(out_summary, result)
        if str(official.get("failure_policy", "report_and_continue")) == "raise":
            raise RuntimeError(f"official evaluator failed for {exp_id}; inspect {out_summary}")
        return result

    except subprocess.TimeoutExpired as exc:
        result = {
            "status": "evaluator_timeout",
            "experiment_id": exp_id,
            "role": role,
            "manifest": str(manifest.relative_to(ROOT)).replace("\\", "/"),
            "manifest_sha256": manifest_hash,
            "message": str(exc),
            "failure_policy": str(official.get("failure_policy", "report_and_continue")),
        }
        _save_json(out_summary, result)
        if str(official.get("failure_policy", "report_and_continue")) == "raise":
            raise
        return result


def read_summary(exp_id: str) -> dict | None:
    p = _summary_path(exp_id)
    if not p.exists():
        return None
    try:
        return _load_json(p)
    except Exception:
        return None
