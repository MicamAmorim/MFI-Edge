from __future__ import annotations

"""MFI-Edge local research autopilot v2.

Runs long local experiments and invokes Codex only after an experiment finishes.
The controller is resumable: if Codex fails after a completed experiment, the next
launch analyzes the existing result instead of rerunning the experiment.
"""

from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
AUTO = ROOT / "automation"
RUNTIME = AUTO / "runtime"
STOP_FILE = AUTO / "STOP"
CONFIG_FILE = AUTO / "config.json"
EXPERIMENTS_FILE = AUTO / "experiments.json"
SCHEMA_FILE = AUTO / "decision.schema.json"
POLICY_FILE = AUTO / "CODEX_POLICY.md"
STATE_FILE = RUNTIME / "state.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def _run(args, *, cwd=ROOT, check=True, input_text=None, timeout=None):
    p = subprocess.run(
        [str(x) for x in args], cwd=str(cwd), input=input_text, text=True,
        capture_output=True, timeout=timeout, check=False,
    )
    if check and p.returncode != 0:
        raise RuntimeError(
            f"command failed ({p.returncode}): {' '.join(map(str, args))}\n"
            f"STDOUT:\n{p.stdout or ''}\nSTDERR:\n{p.stderr or ''}"
        )
    return p


def _git(*args, check=True):
    return _run(["git", *args], check=check)


def _branch() -> str:
    return _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def _head() -> str:
    return _git("rev-parse", "HEAD").stdout.strip()


def _status_lines() -> list[str]:
    return [x for x in _git("status", "--porcelain").stdout.splitlines() if x.strip()]


def _changed_paths() -> list[str]:
    tracked = _git("diff", "--name-only").stdout.splitlines()
    staged = _git("diff", "--cached", "--name-only").stdout.splitlines()
    untracked = _git("ls-files", "--others", "--exclude-standard").stdout.splitlines()
    return sorted({x.strip().replace("\\", "/") for x in tracked + staged + untracked if x.strip()})


def _safe_relpath(value: str, suffixes: tuple[str, ...]) -> Path:
    p = Path(value)
    if p.is_absolute() or ".." in p.parts or not str(p).lower().endswith(suffixes):
        raise ValueError(f"unsafe experiment path: {value}")
    full = (ROOT / p).resolve()
    if ROOT.resolve() not in full.parents and full != ROOT.resolve():
        raise ValueError(f"path escapes repository: {value}")
    if not full.exists():
        raise FileNotFoundError(full)
    return full


def _validate_arg(x: str) -> str:
    s = str(x)
    if any(ch in s for ch in "&|><^\n\r"):
        raise ValueError(f"unsafe experiment argument: {s!r}")
    return s


def _experiment_command(spec: dict) -> list[str]:
    runner = str(spec.get("runner", "python")).lower()
    args = [_validate_arg(x) for x in spec.get("args", [])]
    if runner == "python":
        script = _safe_relpath(str(spec["path"]), (".py",))
        return [sys.executable, str(script), *args]
    if runner == "bat":
        script = _safe_relpath(str(spec["path"]), (".bat",))
        if os.name != "nt":
            raise RuntimeError(".bat experiments require Windows")
        text = "call \"" + str(script) + "\""
        if args:
            text += " " + " ".join(args)
        return ["cmd.exe", "/d", "/s", "/c", text]
    raise ValueError(f"unsupported runner {runner!r}; use python or bat")


def _stream_process(cmd: list[str], log_path: Path, timeout_s: float) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(f"COMMAND: {cmd!r}\nSTART: {_now()}\n\n")
        log.flush()
        p = subprocess.Popen(
            cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, errors="replace",
        )
        assert p.stdout is not None
        try:
            while True:
                line = p.stdout.readline()
                if line:
                    print(line, end="", flush=True)
                    log.write(line)
                    log.flush()
                elif p.poll() is not None:
                    break
                if time.monotonic() - started > timeout_s:
                    p.kill()
                    log.write("\nAUTOPILOT_TIMEOUT\n")
                    return 124
                time.sleep(0.05)
            return int(p.wait())
        finally:
            if p.poll() is None:
                p.kill()


def _tail(path: Path, n=60) -> str:
    if not path.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-int(n):])


def _compact_results(spec: dict) -> dict:
    manifest = []
    primary_json = None
    for raw in spec.get("result_files", []):
        p = ROOT / raw
        item = {"path": str(raw).replace("\\", "/"), "exists": p.exists()}
        if p.exists():
            item["bytes"] = int(p.stat().st_size)
            if p.suffix.lower() == ".json" and p.stat().st_size <= 120000:
                try:
                    obj = _load_json(p)
                    if p.name.lower() == "summary.json":
                        primary_json = obj
                except Exception as exc:
                    item["parse_error"] = str(exc)
            elif p.suffix.lower() == ".csv":
                try:
                    with p.open("r", encoding="utf-8-sig", newline="") as f:
                        reader = csv.reader(f)
                        item["csv_preview"] = [row for _, row in zip(range(4), reader)]
                except Exception as exc:
                    item["parse_error"] = str(exc)
        manifest.append(item)
    return {"files": manifest, "summary_json": primary_json}


def _codex_binary() -> str | None:
    return shutil.which("codex") or shutil.which("codex.cmd")


def _build_prompt(exp_id: str, spec: dict, exit_code: int, log_path: Path, result_summary: dict) -> str:
    policy = POLICY_FILE.read_text(encoding="utf-8")
    payload = {
        "experiment_id": exp_id,
        "description": spec.get("description", ""),
        "role": spec.get("role", "development"),
        "feedback_policy": spec.get("feedback_policy", "development_feedback_allowed"),
        "exit_code": int(exit_code),
        "git_head_before_analysis": _head(),
        "result_summary": result_summary,
        "log_tail": _tail(log_path, 80 if exit_code else 25),
    }
    return (
        policy
        + "\n\n# Current controller event\n\n"
        + "The local experiment has finished. Analyze this event, inspect only the files you need, "
          "make the smallest justified repository edits, update the research record when appropriate, "
          "and either register exactly one next experiment or stop.\n\n"
        + "```json\n"
        + json.dumps(payload, indent=2, ensure_ascii=False, default=str)
        + "\n```\n"
    )


def _call_codex(prompt: str, config: dict, iteration: int, model: str | None) -> tuple[int, Path, Path]:
    """Call Codex headlessly with bounded retries.

    Codex CLI 0.157.x accepts approval_policy as a config override for `exec`.
    Using the former `exec --ask-for-approval ...` form is not portable across
    recent CLI builds, so approval is supplied through `--config` instead.
    """
    codex = _codex_binary()
    if not codex:
        raise RuntimeError("Codex CLI not found. Install/login first, then verify `codex --version`.")

    run_dir = RUNTIME / "codex" / f"iteration_{iteration:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / "prompt.txt"
    answer_path = run_dir / "answer.json"
    combined_log = run_dir / "codex_stdout.log"
    prompt_path.write_text(prompt, encoding="utf-8")
    if answer_path.exists():
        answer_path.unlink()

    cmd = [
        codex,
        "exec",
        "--sandbox", "workspace-write",
        "--config", "approval_policy=never",
        "--config", f"model_reasoning_effort={config.get('reasoning_effort', 'low')}",
        "--output-schema", str(SCHEMA_FILE),
        "--output-last-message", str(answer_path),
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.append("-")

    timeout = float(config.get("codex_timeout_minutes", 25)) * 60.0
    retries = max(0, int(config.get("codex_retries", 2)))
    logs = []
    last_rc = 1
    for attempt in range(1, retries + 2):
        print(f"CODEX attempt {attempt}/{retries + 1}...", flush=True)
        try:
            p = subprocess.run(
                cmd, cwd=str(ROOT), input=prompt, text=True,
                capture_output=True, timeout=timeout, check=False,
            )
            last_rc = int(p.returncode)
            logs.append(
                f"=== ATTEMPT {attempt} rc={last_rc} ===\n"
                + (p.stdout or "")
                + ("\n--- STDERR ---\n" + p.stderr if p.stderr else "")
            )
            if last_rc == 0 and answer_path.exists():
                break
        except subprocess.TimeoutExpired as exc:
            last_rc = 124
            logs.append(f"=== ATTEMPT {attempt} TIMEOUT ===\n{exc}\n")
        if attempt <= retries:
            time.sleep(min(10.0, 2.0 * attempt))

    combined_log.write_text("\n".join(logs), encoding="utf-8", errors="replace")
    return last_rc, answer_path, combined_log


def _validate_codex_changes(config: dict) -> list[str]:
    changed = _changed_paths()
    protected = {str(x).replace("\\", "/") for x in config.get("protected_paths", [])}
    hits = sorted(set(changed) & protected)
    if hits:
        raise RuntimeError(
            "Codex changed protected scientific files; refusing auto-commit. Review manually:\n  - "
            + "\n  - ".join(hits)
        )
    for cmd in config.get("validation_commands", []):
        _run(cmd, check=True)
    py_files = [ROOT / p for p in changed if p.endswith(".py") and (ROOT / p).exists()]
    if py_files:
        _run([sys.executable, "-m", "py_compile", *map(str, py_files)], check=True)
    return changed


def _commit_and_push(decision: dict, config: dict, changed: list[str], no_push: bool) -> str | None:
    if not changed or not config.get("auto_commit", True):
        return None
    _git("add", "-A")
    _git("diff", "--cached", "--check")
    if not _git("diff", "--cached", "--name-only").stdout.strip():
        return None
    message = str(decision.get("commit_message") or "research: automated iteration").strip()
    if len(message) > 120:
        message = message[:117] + "..."
    _git("commit", "-m", message)
    sha = _head()
    if config.get("auto_push", True) and not no_push:
        _git("push", str(config.get("remote", "origin")), str(config["branch"]))
    return sha


def _new_state(config: dict, start: str) -> dict:
    return {
        "created_at": _now(), "updated_at": _now(), "iteration": 0,
        "codex_calls": 0, "next_experiment_id": start,
        "completed_successfully": [], "history": [],
        "pending_analysis": None, "branch": config["branch"],
    }


def _preflight(config: dict, no_codex: bool) -> None:
    if not (ROOT / ".git").exists():
        raise RuntimeError(f"not a Git repository: {ROOT}")
    if _branch() != str(config["branch"]):
        raise RuntimeError(f"switch to {config['branch']} before running autopilot (current: {_branch()})")
    dirty = _status_lines()
    if dirty:
        raise RuntimeError("working tree must be clean before autopilot:\n" + "\n".join(dirty))
    _git("pull", "--ff-only", str(config.get("remote", "origin")), str(config["branch"]))
    if not no_codex:
        codex = _codex_binary()
        if not codex:
            raise RuntimeError("Codex CLI not found in PATH. Run `codex --version` and login before autopilot.")
        v = _run([codex, "--version"], check=False)
        if v.returncode != 0:
            raise RuntimeError("Codex CLI exists but `codex --version` failed")
        print("CODEX:", (v.stdout or v.stderr).strip())


def _legacy_pending(state: dict, experiments: dict) -> dict | None:
    """Recover a completed experiment from v1 state after a Codex-only failure."""
    pending = state.get("pending_analysis")
    if pending:
        return pending

    history = state.get("history") or []
    if history:
        last = history[-1]
        exp_id = last.get("experiment_id")
        if last.get("codex_error") and exp_id in state.get("completed_successfully", []):
            log_rel = last.get("log")
            if exp_id in experiments and log_rel:
                return {
                    "experiment_id": exp_id,
                    "exit_code": int(last.get("exit_code", 0)),
                    "log": log_rel,
                    "recovered_from_v1": True,
                }

    exp_id = state.get("next_experiment_id")
    if exp_id and exp_id in state.get("completed_successfully", []) and exp_id in experiments:
        logs = sorted((RUNTIME / "logs").glob(f"*_{exp_id}.log"), key=lambda p: p.stat().st_mtime)
        if logs:
            return {
                "experiment_id": exp_id,
                "exit_code": 0,
                "log": str(logs[-1].relative_to(ROOT)).replace("\\", "/"),
                "recovered_from_v1": True,
            }
    return None


def _analyze_pending(state: dict, pending: dict, experiments: dict, config: dict,
                     args) -> tuple[bool, dict]:
    exp_id = str(pending["experiment_id"])
    if exp_id not in experiments:
        raise RuntimeError(f"pending experiment {exp_id!r} is no longer registered")
    spec = experiments[exp_id]
    log_path = ROOT / str(pending["log"])
    exit_code = int(pending.get("exit_code", 0))
    result_summary = _compact_results(spec)
    prompt = _build_prompt(exp_id, spec, exit_code, log_path, result_summary)

    print("\nExperiment result already exists. Calling Codex only; benchmark will NOT rerun.")
    rc, answer_path, codex_log = _call_codex(prompt, config, int(state["iteration"]), args.model)
    state["codex_calls"] = int(state.get("codex_calls", 0)) + 1
    state["updated_at"] = _now()
    _save_json(STATE_FILE, state)
    if rc != 0 or not answer_path.exists():
        event = {
            "time": _now(), "experiment_id": exp_id, "exit_code": exit_code,
            "log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
            "git_head": _head(),
            "codex_error": {"returncode": rc, "log": str(codex_log.relative_to(ROOT)).replace("\\", "/")},
        }
        state.setdefault("history", []).append(event)
        state["pending_analysis"] = pending
        _save_json(STATE_FILE, state)
        raise RuntimeError(f"Codex failed; result remains pending. Inspect {codex_log}")

    decision = _load_json(answer_path)
    changed = _validate_codex_changes(config)
    commit_sha = _commit_and_push(decision, config, changed, args.no_push)
    event = {
        "time": _now(), "experiment_id": exp_id, "exit_code": exit_code,
        "log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
        "git_head": _head(), "decision": decision,
    }
    if commit_sha:
        event["commit"] = commit_sha
    state.setdefault("history", []).append(event)
    state["pending_analysis"] = None
    state["next_experiment_id"] = decision.get("next_experiment_id")
    state["updated_at"] = _now()
    _save_json(STATE_FILE, state)

    print("\nCODEX DECISION:")
    print(json.dumps(decision, indent=2, ensure_ascii=False))
    if commit_sha:
        print("Committed:", commit_sha)

    stop = bool(decision.get("requires_human")) or not bool(decision.get("continue"))
    if bool(decision.get("continue")) and not decision.get("next_experiment_id"):
        print("Codex requested continue but returned no next experiment; stopping.")
        stop = True
    if decision.get("next_experiment_id"):
        latest = _load_json(EXPERIMENTS_FILE)
        if decision["next_experiment_id"] not in latest:
            raise RuntimeError(
                f"Codex proposed {decision['next_experiment_id']!r} but did not register it in automation/experiments.json"
            )
    return stop, decision


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=None, help="experiment id to start/resume from")
    ap.add_argument("--model", default=os.environ.get("MFI_CODEX_MODEL"), help="optional Codex model")
    ap.add_argument("--once", action="store_true", help="run at most one experiment/Codex decision")
    ap.add_argument("--no-codex", action="store_true", help="run experiment only, then stop")
    ap.add_argument("--no-push", action="store_true", help="commit locally but do not push")
    ap.add_argument("--reset-state", action="store_true", help="discard runtime state and start fresh")
    ap.add_argument("--dry-run", action="store_true", help="show the next action without running")
    args = ap.parse_args()

    config = _load_json(CONFIG_FILE)
    start = args.start or str(config.get("start_experiment", "stage13a_bsds_transfer"))
    RUNTIME.mkdir(parents=True, exist_ok=True)
    if args.reset_state and STATE_FILE.exists():
        STATE_FILE.unlink()
    state = _load_json(STATE_FILE) if STATE_FILE.exists() else _new_state(config, start)
    state.setdefault("pending_analysis", None)
    if args.start:
        state["next_experiment_id"] = args.start

    _preflight(config, args.no_codex)
    wall_start = time.monotonic()
    actions_done = 0

    while True:
        experiments = _load_json(EXPERIMENTS_FILE)
        pending = _legacy_pending(state, experiments)

        if STOP_FILE.exists():
            print(f"STOP file detected: {STOP_FILE}")
            break

        # Recovery has priority over iteration/call budgets because it prevents a
        # completed one-shot experiment from being rerun just to retry analysis.
        if pending and not args.no_codex:
            if args.dry_run:
                print(f"DRY RUN: resume Codex analysis for {pending['experiment_id']} (no benchmark rerun)")
                return 0
            state["pending_analysis"] = pending
            _save_json(STATE_FILE, state)
            stop, _ = _analyze_pending(state, pending, experiments, config, args)
            actions_done += 1
            if args.once or stop:
                break
            continue

        if int(state.get("iteration", 0)) >= int(config.get("max_iterations", 8)):
            print("Maximum iteration budget reached.")
            break
        if int(state.get("codex_calls", 0)) >= int(config.get("max_codex_calls", 8)) and not args.no_codex:
            print("Maximum Codex-call budget reached.")
            break
        if (time.monotonic() - wall_start) / 3600.0 >= float(config.get("max_wall_hours", 12)):
            print("Maximum wall-time budget reached.")
            break

        exp_id = state.get("next_experiment_id")
        if not exp_id:
            print("No next experiment registered; stopping.")
            break
        if exp_id not in experiments:
            raise RuntimeError(f"next experiment {exp_id!r} is not registered in {EXPERIMENTS_FILE}")
        spec = experiments[exp_id]
        if spec.get("one_shot") and exp_id in state.get("completed_successfully", []):
            raise RuntimeError(f"refusing to rerun one-shot experiment already completed: {exp_id}")

        cmd = _experiment_command(spec)
        print("\n" + "=" * 78)
        print(f"AUTOPILOT ITERATION {int(state.get('iteration', 0)) + 1}: {exp_id}")
        print("ROLE:", spec.get("role", "development"))
        print("POLICY:", spec.get("feedback_policy", "development_feedback_allowed"))
        print("COMMAND:", " ".join(cmd))
        print("=" * 78)
        if args.dry_run:
            return 0

        state["iteration"] = int(state.get("iteration", 0)) + 1
        state["updated_at"] = _now()
        _save_json(STATE_FILE, state)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = RUNTIME / "logs" / f"{stamp}_{exp_id}.log"
        timeout_s = float(config.get("experiment_timeout_minutes", 360)) * 60.0
        exit_code = _stream_process(cmd, log_path, timeout_s)

        if exit_code == 0 and exp_id not in state.setdefault("completed_successfully", []):
            state["completed_successfully"].append(exp_id)

        pending = {
            "experiment_id": exp_id,
            "exit_code": int(exit_code),
            "log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
            "created_at": _now(),
        }
        state["pending_analysis"] = pending
        state["updated_at"] = _now()
        _save_json(STATE_FILE, state)

        if args.no_codex:
            print("Experiment finished; --no-codex requested. Analysis remains pending.")
            break

        stop, _ = _analyze_pending(state, pending, experiments, config, args)
        actions_done += 1
        if args.once or stop:
            break

    state["updated_at"] = _now()
    _save_json(STATE_FILE, state)
    print(f"\nAutopilot state: {STATE_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
