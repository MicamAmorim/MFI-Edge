from __future__ import annotations

from pathlib import Path
import csv
import json
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "models" / "deployable_registry.json"
STAGE7_FULL = ROOT / "results" / "uded" / "stage7" / "selection_all.csv"


def _enrich_frozen_thresholds(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fill exported Stage-7 frozen thresholds when the full CSV is present.

    The compact result committed during the Railway run contains ranking metrics but
    not the exact selected threshold. Once `selection_all.csv` is synced into the
    branch, the desktop registry automatically picks up the benchmark threshold.
    Until then, `threshold=None` remains explicit and the WebUI uses a clearly
    labelled adaptive quantile for visualization only.
    """
    if not STAGE7_FULL.exists():
        return rows
    try:
        with STAGE7_FULL.open("r", encoding="utf-8", newline="") as fh:
            full = list(csv.DictReader(fh))
    except Exception:
        return rows

    by_key = {}
    for item in full:
        key = (str(item.get("measure", "")), str(item.get("strategy", "")))
        by_key[key] = item

    for row in rows:
        if row.get("threshold") is not None:
            continue
        hit = by_key.get((str(row.get("measure", "")), str(row.get("strategy", ""))))
        if not hit:
            continue
        raw = hit.get("threshold") or hit.get("selection_threshold")
        if raw not in (None, ""):
            try:
                row["threshold"] = float(raw)
                row["threshold_source"] = "results/uded/stage7/selection_all.csv"
            except Exception:
                pass
    return rows


def load_deployable_models(path: Path | None = None) -> List[Dict[str, Any]]:
    """Load desktop/WebUI model configurations in validation-rank order.

    The WebUI deliberately uses an explicit deployable registry rather than every
    exploratory configuration from a factorial sweep. New validated models should
    be promoted into this registry. Ranking is based on the declared validation
    metric (currently UDED selection ODS), never on a post-hoc held-out view.
    """
    p = Path(path or REGISTRY_PATH)
    rows = json.loads(p.read_text(encoding="utf-8"))
    rows = _enrich_frozen_thresholds([dict(x) for x in rows])
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
