from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "models" / "deployable_registry.json"


def load_deployable_models(path: Path | None = None) -> List[Dict[str, Any]]:
    """Load desktop/WebUI model configurations in validation-rank order.

    The WebUI deliberately uses an explicit deployable registry rather than every
    exploratory configuration from a factorial sweep. New validated models should
    be added here when they are promoted to the desktop branch. Ranking is based on
    the declared validation metric (currently UDED selection ODS), never on a
    post-hoc held-out view.
    """
    p = Path(path or REGISTRY_PATH)
    rows = json.loads(p.read_text(encoding="utf-8"))
    rows = [dict(x) for x in rows]
    rows.sort(key=lambda x: float(x.get("selection_ODS", float("-inf"))), reverse=True)
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
        row.setdefault("rank_basis", "selection_ODS")
        row.setdefault("threshold_fallback_quantile", 0.90)
    return rows


def model_by_id(model_id: str, path: Path | None = None) -> Dict[str, Any]:
    for row in load_deployable_models(path):
        if str(row.get("id")) == str(model_id):
            return row
    raise KeyError(f"Unknown deployable model: {model_id}")
