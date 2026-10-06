from __future__ import annotations

"""MFI-Edge research autopilot v4.

Adds persistent scientific context injection, a default GPT-5.6 Sol model,
explicit goal-state handling, resilient autonomous literature escalation, and
an optional official BSDS MATLAB evaluation hook that runs before Codex analyzes
completed image experiments.
"""

from pathlib import Path
import json
import os

import research_controller_v3 as v3
import official_eval_hook

core = v3.core

_ORIGINAL_BUILD_PROMPT = core._build_prompt
_ORIGINAL_ANALYZE_PENDING = core._analyze_pending

CONTEXT_FILE = core.AUTO / "SCIENTIFIC_CONTEXT.md"
SOTA_FILE = core.ROOT / "docs" / "paper" / "SOTA_TARGETS.md"
GOAL_FILE = core.AUTO / "research_goal.json"
OFFICIAL_EVAL_POLICY_FILE = core.AUTO / "OFFICIAL_EVAL_POLICY.md"


def _read_optional(path: Path) -> str:
    if not path.exists():
        return "(missing)"
    return path.read_text(encoding="utf-8", errors="replace")


def _research_agenda_file() -> Path:
    try:
        cfg = json.loads(core.CONFIG_FILE.read_text(encoding="utf-8"))
        rel = str(
            cfg.get(
                "research_agenda_file",
                "docs/paper/MECHANISM_RESEARCH_AGENDA_2026-10-06.md",
            )
        )
        return core.ROOT / rel
    except Exception:
        return core.ROOT / "docs" / "paper" / "MECHANISM_RESEARCH_AGENDA_2026-10-06.md"


def _build_prompt_v4(
    exp_id: str,
    spec: dict,
    exit_code: int,
    log_path: Path,
    result_summary: dict,
) -> str:
    base = _ORIGINAL_BUILD_PROMPT(
        exp_id, spec, exit_code, log_path, result_summary
    )
    context = _read_optional(CONTEXT_FILE)
    sota = _read_optional(SOTA_FILE)
    goal = _read_optional(GOAL_FILE)
    eval_policy = _read_optional(OFFICIAL_EVAL_POLICY_FILE)
    agenda = _read_optional(_research_agenda_file())
    official_eval = official_eval_hook.read_summary(exp_id)

    official_block = (
        json.dumps(official_eval, indent=2, ensure_ascii=False, default=str)
        if official_eval is not None
        else "(not run / not applicable)"
    )

    return (
        "# Persistent scientific memory\n\n"
        "The following context is injected on every decision. Treat "
        "experiment-specific preregistrations and source files as authoritative "
        "when they contain finer-grained protocol details.\n\n"
        "## automation/SCIENTIFIC_CONTEXT.md\n\n"
        + context
        + "\n\n## automation/research_goal.json\n\n```json\n"
        + goal
        + "\n```\n\n## docs/paper/SOTA_TARGETS.md\n\n"
        + sota
        + "\n\n## automation/OFFICIAL_EVAL_POLICY.md\n\n"
        + eval_policy
        + "\n\n## Current mechanism research agenda\n\n"
        + agenda
        + "\n\n## Official-evaluation attachment for this event\n\n```json\n"
        + official_block
        + "\n```\n\n"
        + base
    )


def _analyze_pending_v4(
    state: dict,
    pending: dict,
    experiments: dict,
    config: dict,
    args,
):
    exp_id = str(pending["experiment_id"])
    spec = experiments.get(exp_id, {})
    official_eval_hook.maybe_run(exp_id, spec, config)
    stop, decision = _ORIGINAL_ANALYZE_PENDING(
        state, pending, experiments, config, args
    )

    goal_reached = bool(decision.get("goal_reached", False))
    hard_blocker = bool(decision.get("requires_human", False))
    if goal_reached:
        print(
            "\nGENERALIZED SOTA GOAL REACHED. "
            "Autonomous loop is stopping for final review."
        )
        return True, decision
    if hard_blocker:
        blocker = decision.get("human_blocker") or "unspecified hard blocker"
        print(f"\nHARD HUMAN BLOCKER: {blocker}")
        return True, decision

    next_id = decision.get("next_experiment_id")
    if bool(decision.get("continue")) and next_id:
        return False, decision

    fallback = str(
        config.get(
            "autonomous_research_fallback",
            "autonomous_literature_escalation",
        )
    )
    latest = core._load_json(core.EXPERIMENTS_FILE)
    if fallback not in latest:
        raise RuntimeError(
            f"Autonomous fallback {fallback!r} is not registered in "
            f"{core.EXPERIMENTS_FILE}"
        )
    state["next_experiment_id"] = fallback
    state["updated_at"] = core._now()
    core._save_json(core.STATE_FILE, state)
    print(
        "\nNo hard blocker and goal not reached. "
        f"Routing automatically to research fallback: {fallback}"
    )
    return False, decision


core._build_prompt = _build_prompt_v4
core._analyze_pending = _analyze_pending_v4


if __name__ == "__main__":
    try:
        config = json.loads(core.CONFIG_FILE.read_text(encoding="utf-8"))
        default_model = str(config.get("default_model", "")).strip()
        if default_model:
            os.environ.setdefault("MFI_CODEX_MODEL", default_model)
    except Exception:
        pass
    raise SystemExit(core.main())
