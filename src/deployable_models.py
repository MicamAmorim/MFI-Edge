from __future__ import annotations

from pathlib import Path
import csv
import json
from typing import Any, Dict, List

from .research_deploy import load_research_models

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "models" / "deployable_registry.json"
STAGE7_FULL = ROOT / "results" / "uded" / "stage7" / "selection_all.csv"


def _enrich_frozen_thresholds(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


def _legacy_models(path: Path) -> List[Dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    rows = _enrich_frozen_thresholds([dict(x) for x in rows])
    for row in rows:
        row.setdefault("engine", "stage7")
        row.setdefault("status", "legacy-stage7-screened")
        row.setdefault("rank_basis", "selection_ODS")
        row.setdefault("threshold_fallback_quantile", 0.90)
        row.setdefault("metric_label", "Stage 7 selection ODS")
        row.setdefault("metric_value", row.get("selection_ODS"))
        row.setdefault("secondary_label", "Historical held-out F1")
        row.setdefault("secondary_value", row.get("heldout_F1"))
        row.setdefault("display_priority", 1000.0 + float(row.get("selection_ODS", 0.0)))
    return rows


def load_deployable_models(path: Path | None = None) -> List[Dict[str, Any]]:
    """Load current research models plus the historical Stage-7 registry.

    Research models are shown first when the WebUI can see the active local-dev
    frozen artifact. Metrics from different protocols are labelled explicitly and
    are not silently treated as directly comparable.
    """
    p = Path(path or REGISTRY_PATH)
    rows = load_research_models() + _legacy_models(p)
    rows.sort(key=lambda x: float(x.get("display_priority", 0.0)), reverse=True)
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return rows


def model_by_id(model_id: str, path: Path | None = None) -> Dict[str, Any]:
    for row in load_deployable_models(path):
        if str(row.get("id")) == str(model_id):
            return row
    raise KeyError(f"Unknown deployable model: {model_id}")
