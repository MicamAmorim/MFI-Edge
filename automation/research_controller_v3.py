from __future__ import annotations

"""MFI-Edge research autopilot v3.

Thin compatibility wrapper around v2 that keeps normal iterations cheap but
escalates research-planning checkpoints to stronger reasoning and web search.

Research calls use a resilient web-search ladder. A transient live-search
failure must not halt the scientific program: the controller tries configured
search modes in order and, if all research modes fail, may fall back to the
normal Codex path while preserving the pending experiment/result state.
"""

from pathlib import Path
import subprocess
import time

import research_controller_v2 as core

_ORIGINAL_CALL_CODEX = core._call_codex


def _research_web_modes(config: dict) -> list[str]:
    raw = config.get("research_web_search_fallbacks")
    if raw is None:
        raw = [config.get("research_web_search", "live")]
    if isinstance(raw, str):
        raw = [raw]

    allowed = {"disabled", "cached", "indexed", "live"}
    modes: list[str] = []
    for value in raw:
        mode = str(value).strip().lower()
        if mode not in allowed:
            raise ValueError(
                "research web-search modes must be one of: "
                "disabled, cached, indexed, live"
            )
        if mode not in modes:
            modes.append(mode)
    if not modes:
        modes = ["live"]
    return modes


def _research_call_once(
    prompt: str,
    config: dict,
    iteration: int,
    model: str | None,
    web_mode: str,
    attempt_no: int,
    attempt_total: int,
):
    codex = core._codex_binary()
    if not codex:
        raise RuntimeError(
            "Codex CLI not found. Install/login first, then verify `codex --version`."
        )

    run_dir = core.RUNTIME / "codex" / f"iteration_{iteration:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    answer_path = run_dir / "answer.json"
    reasoning = str(config.get("research_reasoning_effort", "medium"))

    cmd = [
        codex,
        "exec",
        "--sandbox", "workspace-write",
        "--config", "approval_policy=never",
        "--config", f"model_reasoning_effort={reasoning}",
        "--config", f'web_search="{web_mode}"',
        "--output-schema", str(core.SCHEMA_FILE),
        "--output-last-message", str(answer_path),
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.append("-")

    timeout = float(config.get("codex_timeout_minutes", 25)) * 60.0
    print(
        f"CODEX research attempt {attempt_no}/{attempt_total} "
        f"(reasoning={reasoning}, web_search={web_mode})...",
        flush=True,
    )
    try:
        p = subprocess.run(
            cmd,
            cwd=str(core.ROOT),
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return int(p.returncode), p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"TIMEOUT: {exc}"


def _call_codex_v3(prompt: str, config: dict, iteration: int, model: str | None):
    is_research = (
        '"role": "research_planning"' in prompt
        or '"role": "literature_escalation"' in prompt
    )
    if not is_research:
        return _ORIGINAL_CALL_CODEX(prompt, config, iteration, model)

    codex = core._codex_binary()
    if not codex:
        raise RuntimeError(
            "Codex CLI not found. Install/login first, then verify `codex --version`."
        )

    run_dir = core.RUNTIME / "codex" / f"iteration_{iteration:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / "prompt.txt"
    answer_path = run_dir / "answer.json"
    combined_log = run_dir / "codex_stdout.log"
    prompt_path.write_text(prompt, encoding="utf-8")
    if answer_path.exists():
        answer_path.unlink()

    modes = _research_web_modes(config)
    logs = [
        "RESEARCH_ESCALATION "
        f"reasoning={config.get('research_reasoning_effort', 'medium')} "
        f"web_modes={modes!r}"
    ]
    last_rc = 1
    total = len(modes)

    for i, mode in enumerate(modes, start=1):
        if answer_path.exists():
            answer_path.unlink()
        rc, stdout, stderr = _research_call_once(
            prompt, config, iteration, model, mode, i, total
        )
        last_rc = int(rc)
        logs.append(
            f"=== WEB MODE {mode} rc={last_rc} ===\n"
            + stdout
            + ("\n--- STDERR ---\n" + stderr if stderr else "")
        )
        if last_rc == 0 and answer_path.exists():
            combined_log.write_text(
                "\n".join(logs), encoding="utf-8", errors="replace"
            )
            return last_rc, answer_path, combined_log
        time.sleep(min(5.0, float(i)))

    if bool(config.get("research_fallback_to_normal_codex", True)):
        logs.append(
            "=== ALL RESEARCH WEB MODES FAILED; FALLING BACK TO NORMAL CODEX ==="
        )
        combined_log.write_text(
            "\n".join(logs), encoding="utf-8", errors="replace"
        )
        rc, normal_answer, normal_log = _ORIGINAL_CALL_CODEX(
            prompt, config, iteration, model
        )
        try:
            normal_text = normal_log.read_text(
                encoding="utf-8", errors="replace"
            )
        except Exception:
            normal_text = ""
        logs.append(
            f"=== NORMAL FALLBACK rc={int(rc)} ===\n{normal_text}"
        )
        combined_log.write_text(
            "\n".join(logs), encoding="utf-8", errors="replace"
        )
        return int(rc), normal_answer, combined_log

    combined_log.write_text(
        "\n".join(logs), encoding="utf-8", errors="replace"
    )
    return last_rc, answer_path, combined_log


core._call_codex = _call_codex_v3

if __name__ == "__main__":
    raise SystemExit(core.main())
