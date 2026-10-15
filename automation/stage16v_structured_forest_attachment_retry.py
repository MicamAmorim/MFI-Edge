from __future__ import annotations

"""Prepare the frozen Stage-16v result for an attachment-only BSDS retry."""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.stage16v_structured_forest_venv_launcher import materialize_model


RESULT = ROOT / "results" / "local_dev" / "stage16v_structured_forest"
REQUIRED = (
    "summary.json",
    "variant_ranking.csv",
    "fold_results.csv",
    "per_image_metrics.csv",
    "map_hashes.json",
    "best_method_preview.png",
    "official_eval_manifest.json",
)


def main() -> int:
    missing = [name for name in REQUIRED if not (RESULT / name).is_file()]
    if missing:
        raise RuntimeError(f"frozen Stage-16v artifacts missing: {missing}")
    summary = json.loads((RESULT / "summary.json").read_text(encoding="utf-8"))
    if summary.get("stage") != "16v-structured-forest":
        raise RuntimeError("unexpected frozen Stage-16v summary")
    materialize_model()
    print("STAGE16V_ATTACHMENT_RETRY_READY frozen_cv=true model_hash_verified=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
