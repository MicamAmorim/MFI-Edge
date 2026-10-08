from __future__ import annotations

"""MFI-Edge research autopilot v4.

Adds persistent scientific context injection, a default GPT-5.6 Sol model,
explicit goal-state handling, resilient autonomous literature escalation, and
a default-on official BSDS MATLAB evaluation hook that runs before Codex
analyzes completed image experiments.

Research-analysis failures are recoverable. If Codex/web research exhausts its
normal retries, the completed experiment remains pending and the controller
backs off and retries instead of terminating the scientific program.
"""

from pathlib import Path
import json
import os
import sys
import time

# Some Windows/Codex environments run Python with safe_path=True, which removes
# the script directory from sys.path. The v4 controller imports sibling modules
# from automation/, so add this directory explicitly before those imports.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import research_controller_v3 as v3
import official_eval_hook

core = v3.core

_ORIGINAL_BUILD_PROMPT = core._build_prompt
_ORIGINAL_ANALYZE_PENDING = core._analyze_pending

CONTEXT_FILE = core.AUTO / "SCIENTIFIC_CONTEXT.md"
SOTA_FILE = core.ROOT / "docs" / "paper" / "SOTA_TARGETS.md"
GOAL_FILE = core.AUTO / "research_goal.json"
OFFICIAL_EVAL_POLICY_FILE = core.AUTO / "OFFICIAL_EVAL_POLICY_V2.md"


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
                "docs/paper/MECHANISM_RESEARCH_AGENDA_2026-10-06_V2.md",
            )
        )
        return core.ROOT / rel
    except Exception:
        return core.ROOT / "docs" / "paper" / "MECHANISM_RESEARCH_AGENDA_2026-10-06_V2.md"


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

    hard_rules = """
## Controller hard requirements for new image experiments

- The official BSDS MATLAB module is default-on auxiliary analysis, not part of
  detector inference.
- Every newly registered image-based development experiment must provide an
  `official_eval_manifest.json` and a repository-local candidate exporter so
  BSDS500-validation ODS/OIS/AP can be computed before the scientific decision.
- If the attached official evaluation has `status=completed` and
  `feedback_allowed=true`, those metrics are decision-capable development
  evidence and MUST be considered jointly with UDED/synthetic development
  metrics.
- A candidate must not be promoted as the new benchmark-aligned incumbent while
  a required official validation evaluation is missing or failed. The
  underlying experiment remains scientifically valid; repair/retry the
  evaluator/export path without rerunning the protected benchmark or silently
  substituting the historical Python consensus proxy.
- BSDS500 test and other protected external/test results remain document-only
  and MUST NOT drive architecture, feature, threshold, routing, or parameter
  selection.
- Do not micro-tune a failed mechanism from its outcome. Use the injected
  mechanism agenda and live literature to choose one preregistered, bounded,
  mechanistically distinct falsification at a time.
"""

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
        + "\n\n## automation/OFFICIAL_EVAL_POLICY_V2.md\n\n"
        + eval_policy
        + "\n\n## Current mechanism research agenda\n\n"
        + agenda
        + "\n\n## Official-evaluation attachment for this event\n\n```json\n"
        + official_block
        + "\n```\n\n"
        + hard_rules
        + "\n\n"
        + base
    )


def _retry_wait(state: dict, exp_id: str, config: dict) -> float:
    failures = state.setdefault("analysis_retry_failures", {})
    n = int(failures.get(exp_id, 0)) + 1
    failures[exp_id] = n
    base = max(1.0, float(config.get("analysis_retry_backoff_seconds", 20)))
    cap = max(base, float(config.get("analysis_retry_backoff_max_seconds", 300)))
    return min(cap, base * (2.0 ** min(max(n - 1, 0), 6)))


def _sleep_with_stop(seconds: float) -> bool:
    remaining = max(0.0, float(seconds))
    while remaining > 0:
        if core.STOP_FILE.exists():
            return True
        dt = min(5.0, remaining)
        time.sleep(dt)
        remaining -= dt
    return core.STOP_FILE.exists()


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

    try:
        stop, decision = _ORIGINAL_ANALYZE_PENDING(
            state, pending, experiments, config, args
        )
    except RuntimeError as exc:
        # A completed experiment/result must never be lost because a Codex or
        # live-web research call transiently failed. v2 has already persisted
        # pending_analysis and the failure log before raising this exact error.
        if "Codex failed; result remains pending" not in str(exc):
            raise

        wait_s = _retry_wait(state, exp_id, config)
        state["updated_at"] = core._now()
        core._save_json(core.STATE_FILE, state)
        print(
            "\nCodex/research analysis failed after configured fallbacks. "
            f"Keeping {exp_id!r} pending and retrying after {wait_s:.0f}s. "
            "The benchmark will NOT rerun.",
            flush=True,
        )
        if _sleep_with_stop(wait_s):
            print("STOP file detected during analysis backoff; stopping cleanly.")
            return True, {
                "continue": False,
                "next_experiment_id": exp_id,
                "requires_human": False,
                "goal_reached": False,
                "scientific_decision": "Deferred pending analysis because STOP was requested.",
            }
        return False, {
            "continue": True,
            "next_experiment_id": exp_id,
            "requires_human": False,
            "goal_reached": False,
            "scientific_decision": "Retry pending Codex/research analysis without rerunning the experiment.",
            "reason": "Transient Codex/web analysis failure; result remains pending and scientifically unchanged.",
        }

    failures = state.setdefault("analysis_retry_failures", {})
    if exp_id in failures:
        failures.pop(exp_id, None)
        state["updated_at"] = core._now()
        core._save_json(core.STATE_FILE, state)

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
