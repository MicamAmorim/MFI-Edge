from __future__ import annotations

"""MFI-Edge research autopilot v5 for Stage 23.

v5 keeps the mature v4 orchestration/evaluation behavior while isolating the
new campaign in its own experiment registry and appending Stage-23-specific
cache/protocol rules after the generic policy/context blocks so the active
campaign override has final precedence.
"""

from pathlib import Path
import json
import os
import sys

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import research_controller_v4 as v4

core = v4.core
ROOT = core.ROOT
AUTO = core.AUTO
STAGE23_POLICY = AUTO / "STAGE23_POLICY.md"
STAGE23_CONTEXT = AUTO / "STAGE23_CONTEXT.md"
STAGE23_PROMOTION_AMENDMENT = ROOT / "docs" / "paper" / "STAGE23_PROMOTION_FRAMEWORK_2026-10-31.md"

# Stage 23 has a clean registry so the new agent cannot accidentally continue
# a historical Stage-15/22 experiment by id.
core.EXPERIMENTS_FILE = AUTO / "stage23_experiments.json"

_V4_BUILD_PROMPT = core._build_prompt


def _read(path: Path) -> str:
    if not path.exists():
        return "(missing)"
    return path.read_text(encoding="utf-8", errors="replace")


def _build_prompt_v5(exp_id: str, spec: dict, exit_code: int, log_path: Path, result_summary: dict) -> str:
    base = _V4_BUILD_PROMPT(exp_id, spec, exit_code, log_path, result_summary)
    override = (
        "# Stage 23 mandatory final override\n\n"
        "The following policy, context, and prospective promotion amendment are authoritative "
        "for the active Stage-23 branch. They supersede conflicting historical references in the "
        "generic policy above. The promotion amendment is prospective only: it must not alter or "
        "re-score already completed Stage-23 experiments or an already frozen preregistration.\n\n"
        "## automation/STAGE23_POLICY.md\n\n"
        + _read(STAGE23_POLICY)
        + "\n\n## automation/STAGE23_CONTEXT.md\n\n"
        + _read(STAGE23_CONTEXT)
        + "\n\n## docs/paper/STAGE23_PROMOTION_FRAMEWORK_2026-10-31.md\n\n"
        + _read(STAGE23_PROMOTION_AMENDMENT)
    )
    return base + "\n\n" + override + "\n"


core._build_prompt = _build_prompt_v5


if __name__ == "__main__":
    try:
        config = json.loads(core.CONFIG_FILE.read_text(encoding="utf-8"))
        default_model = str(config.get("default_model", "")).strip()
        if default_model:
            os.environ.setdefault("MFI_CODEX_MODEL", default_model)
    except Exception:
        pass
    raise SystemExit(core.main())
