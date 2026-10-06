from __future__ import annotations

"""MFI-Edge local research autopilot.

The controller owns the long-running experiment loop. Codex is invoked only after
an experiment finishes (or fails), edits the local workspace once, emits a small
structured decision, and exits. The controller then validates/versions the edit
and optionally runs the next allow-listed experiment.

This intentionally avoids a continuously-running agent and keeps final-test
feedback policies explicit in automation/experiments.json.
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


def _run(args, *, cwd=ROOT, check=True, capture=True, input_text=None, timeout=None):
    p = subprocess.run(
        [str(x) for x in args],
        cwd=str(cwd),
        input=input_text,
        text=True,
        capture_output=capture,
        timeout=timeout,
        check=False,
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
    out = _git("status", "--porcelain").stdout
    return [x for x in out.splitlines() if x.strip()]


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
        # `call` is required so cmd returns control and propagates the batch exit code.
        command_text = "call \"" + str(script) + "\""
        if args:
            command_text += " " + " ".join(args)
        return ["cmd.exe", "/d", "/s", "/c", command_text]
    raise ValueError(f"unsupported runner {runner!r}; use python or bat")


def _stream_process(cmd: list[str], log_path: Path, timeout_s: float) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(f"COMMAND: {cmd!r}\nSTART: {_now()}\n\n")
        log.flush()
        p = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            errors="replace",
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
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-int(n):])


def _compact_results(spec: dict) -> dict:
    manifest = []
    primary_json = None
    for raw in spec.get("result_files", []):
        p = ROOT / raw
        item = {"path": str(raw).replace("\\", "/"), "exists": p.exists()}
        if p.exists():
            item["bytes"] = int(p.stat().st_size)
            if p.suffix.lower() == ".json" and p.stat().st_size <= 80000:
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
                        rows = []
                        for i, row in enumerate(reader):
                            if i < 4:
                                rows.append(row)
                            else:
                                break
                    item["csv_preview"] = rows
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
    codex = _codex_binary()
    if not codex:
        raise RuntimeError("Codex CLI not found. Install/login first, then verify `codex --version`.")
    run_dir = RUNTIME / "codex" / f"iteration_{iteration:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / "prompt.txt"
    answer_path = run_dir / "answer.json"
    stdout_path = run_dir / "codex_stdout.log"
    prompt_path.write_text(prompt, encoding="utf-8")

    cmd = [
        codex,
        "exec",
        "--sandbox", "workspace-write",
        "--ask-for-approval", "never",
        "--config", f"model_reasoning_effort={config.get('reasoning_effort', 'low')}",
        "--output-schema", str(SCHEMA_FILE),
        "--output-last-message", str(answer_path),
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.append("-")

    timeout = float(config.get("codex_timeout_minutes", 25)) * 60.0
    p = subprocess.run(
        cmd,
        cwd=str(ROOT),
        input=prompt,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout_path.write_text(
        (p.stdout or "") + ("\n--- STDERR ---\n" + p.stderr if p.stderr else ""),
        encoding="utf-8",
        errors="replace",
    )
    return int(p.returncode), answer_path, stdout_path


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
        "created_at": _now(),
        "updated_at": _now(),
        "iteration": 0,
        "codex_calls": 0,
        "next_experiment_id": start,
        "completed_successfully": [],
        "history": [],
        "branch": config["branch"],
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=None, help="experiment id to start/resume from")
    ap.add_argument("--model", default=os.environ.get("MFI_CODEX_MODEL"), help="optional Codex model; default uses CLI configuration")
    ap.add_argument("--once", action="store_true", help="run at most one experiment/Codex decision")
    ap.add_argument("--no-codex", action="store_true", help="run experiment only, then stop")
    ap.add_argument("--no-push", action="store_true", help="commit locally but do not push")
    ap.add_argument("--reset-state", action="store_true", help="discard local runtime state and start fresh")
    ap.add_argument("--dry-run", action="store_true", help="show the first experiment command without running")
    args = ap.parse_args()

    config = _load_json(CONFIG_FILE)
    start = args.start or str(config.get("start_experiment", "stage13a_bsds_transfer"))
    RUNTIME.mkdir(parents=True, exist_ok=True)
    if args.reset_state and STATE_FILE.exists():
        STATE_FILE.unlink()
    state = _load_json(STATE_FILE) if STATE_FILE.exists() else _new_state(config, start)
    if args.start:
        state["next_experiment_id"] = args.start

    _preflight(config, args.no_codex)
    wall_start = time.monotonic()

    while True:
        if STOP_FILE.exists():
            print(f"STOP file detected: {STOP_FILE}")
            break
        if int(state["iteration"]) >= int(config.get("max_iterations", 8)):
            print("Maximum iteration budget reached.")
            break
        if int(state["codex_calls"]) >= int(config.get("max_codex_calls", 8)) and not args.no_codex:
            print("Maximum Codex-call budget reached.")
            break
        if (time.monotonic() - wall_start) / 3600.0 >= float(config.get("max_wall_hours", 12)):
            print("Maximum wall-time budget reached.")
            break

        experiments = _load_json(EXPERIMENTS_FILE)
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
        print(f"AUTOPILOT ITERATION {int(state['iteration']) + 1}: {exp_id}")
        print("ROLE:", spec.get("role", "development"))
        print("POLICY:", spec.get("feedback_policy", "development_feedback_allowed"))
        print("COMMAND:", " ".join(cmd))
        print("=" * 78)
        if args.dry_run:
            return 0

        state["iteration"] = int(state["iteration"]) + 1
        state["updated_at"] = _now()
        _save_json(STATE_FILE, state)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = RUNTIME / "logs" / f"{stamp}_{exp_id}.log"
        timeout_s = float(config.get("experiment_timeout_minutes", 360)) * 60.0
        exit_code = _stream_process(cmd, log_path, timeout_s)
        result_summary = _compact_results(spec)

        if exit_code == 0 and exp_id not in state["completed_successfully"]:
            state["completed_successfully"].append(exp_id)

        event = {
            "time": _now(),
            "experiment_id": exp_id,
            "exit_code": int(exit_code),
            "log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
            "git_head": _head(),
        }

        if args.no_codex:
            event["decision"] = "no_codex"
            state["history"].append(event)
            state["updated_at"] = _now()
            _save_json(STATE_FILE, state)
            print("Experiment finished; --no-codex requested, stopping.")
            break

        prompt = _build_prompt(exp_id, spec, exit_code, log_path, result_summary)
        print("\nExperiment finished. Calling Codex once for analysis/editing...")
        rc, answer_path, codex_log = _call_codex(prompt, config, int(state["iteration"]), args.model)
        state["codex_calls"] = int(state["codex_calls"]) + 1
        if rc != 0 or not answer_path.exists():
            event["codex_error"] = {"returncode": rc, "log": str(codex_log.relative_to(ROOT))}
            state["history"].append(event)
            _save_json(STATE_FILE, state)
            raise RuntimeError(f"Codex failed; inspect {codex_log}")

        decision = _load_json(answer_path)
        event["decision"] = decision
        changed = _validate_codex_changes(config)
        commit_sha = _commit_and_push(decision, config, changed, args.no_push)
        if commit_sha:
            event["commit"] = commit_sha

        state["history"].append(event)
        state["updated_at"] = _now()
        next_id = decision.get("next_experiment_id")
        state["next_experiment_id"] = next_id
        _save_json(STATE_FILE, state)

        print("\nCODEX DECISION:")
        print(json.dumps(decision, indent=2, ensure_ascii=False))
        if commit_sha:
            print("Committed:", commit_sha)

        if bool(decision.get("requires_human")):
            print("Codex requested human review; stopping safely.")
            break
        if not bool(decision.get("continue")):
            print("Codex ended the research loop.")
            break
        if not next_id:
            print("Codex requested continue but returned no next experiment; stopping.")
            break

        # Reload after Codex edits and verify the next id is explicitly allow-listed.
        experiments = _load_json(EXPERIMENTS_FILE)
        if next_id not in experiments:
            raise RuntimeError(
                f"Codex proposed {next_id!r} but did not register it in automation/experiments.json"
            )
        if args.once:
            print("--once requested; next experiment is ready but will not run yet:", next_id)
            break

    state["updated_at"] = _now()
    _save_json(STATE_FILE, state)
    print(f"\nAutopilot state: {STATE_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
