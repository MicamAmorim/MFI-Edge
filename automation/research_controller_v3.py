from __future__ import annotations

"""MFI-Edge research autopilot v3.

Thin compatibility wrapper around v2 that keeps normal iterations cheap but
escalates research-planning checkpoints to stronger reasoning and live Codex web
search when the installed CLI exposes a --search option.
"""

from pathlib import Path
import subprocess
import time

import research_controller_v2 as core

_ORIGINAL_CALL_CODEX = core._call_codex


def _call_codex_v3(prompt: str, config: dict, iteration: int, model: str | None):
    is_research = '"role": "research_planning"' in prompt or '"role": "literature_escalation"' in prompt
    if not is_research:
        return _ORIGINAL_CALL_CODEX(prompt, config, iteration, model)

    codex = core._codex_binary()
    if not codex:
        raise RuntimeError("Codex CLI not found. Install/login first, then verify `codex --version`.")

    run_dir = core.RUNTIME / "codex" / f"iteration_{iteration:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / "prompt.txt"
    answer_path = run_dir / "answer.json"
    combined_log = run_dir / "codex_stdout.log"
    prompt_path.write_text(prompt, encoding="utf-8")
    if answer_path.exists():
        answer_path.unlink()

    help_proc = subprocess.run(
        [codex, "exec", "--help"], cwd=str(core.ROOT), capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=False,
    )
    help_text = (help_proc.stdout or "") + (help_proc.stderr or "")
    has_search = "--search" in help_text

    cmd = [codex, "exec"]
    if has_search:
        cmd.append("--search")
    cmd.extend([
        "--sandbox", "workspace-write",
        "--config", "approval_policy=never",
        "--config", f"model_reasoning_effort={config.get('research_reasoning_effort', 'medium')}",
        "--output-schema", str(core.SCHEMA_FILE),
        "--output-last-message", str(answer_path),
    ])
    if model:
        cmd.extend(["--model", model])
    cmd.append("-")

    timeout = float(config.get("codex_timeout_minutes", 25)) * 60.0
    retries = max(0, int(config.get("codex_retries", 2)))
    logs = [f"RESEARCH_ESCALATION web_search={'live' if has_search else 'unavailable'}"]
    last_rc = 1
    for attempt in range(1, retries + 2):
        print(
            f"CODEX research attempt {attempt}/{retries + 1} "
            f"(reasoning={config.get('research_reasoning_effort', 'medium')}, "
            f"web_search={'on' if has_search else 'off'})...",
            flush=True,
        )
        try:
            p = subprocess.run(
                cmd, cwd=str(core.ROOT), input=prompt, text=True,
                encoding="utf-8", errors="replace", capture_output=True,
                timeout=timeout, check=False,
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


core._call_codex = _call_codex_v3

if __name__ == "__main__":
    raise SystemExit(core.main())
