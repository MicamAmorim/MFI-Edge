#!/usr/bin/env python3
"""PREFREEZE safe smoke test: synthetic GT-free H1/H2 predictions only."""
from pathlib import Path
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.paper_a_h1h2_inference_core import predict_from_native_maps

def main() -> int:
    recipe = json.loads((ROOT / "docs/paper_a_confirmation"
                        / "P1_DEVELOPMENT_RECIPE_UNATTESTED.json").read_text(encoding="utf-8"))
    yy, xx = np.indices((48, 52))
    image = np.zeros((48, 52, 3), dtype=np.float32)
    image[:, 23:28, :] = 1.0
    maps = {
        "halfdisc_distribution_contrast": (xx / 55).astype(np.float32),
        "pmi_dependency_deficit": (yy / 51).astype(np.float32),
        "fh_region_boundary": ((xx + yy) / 110).astype(np.float32),
        "structure_tensor_coherence": ((xx * 3 - yy + 51) / 210).astype(np.float32),
    }
    out = predict_from_native_maps(image, maps, recipe)
    print(json.dumps({
        "status": "SYNTHETIC_PREGT_INFERENCE_ONLY_NOT_CONFIRMATORY",
        "recipe_status": recipe["status"],
        "used_raw_images": False,
        "opened_GT_or_F1": False,
        "detector_maps_reprocessed": False,
        "hypotheses": {k: {
            "X": round(v.feature, 8),
            "candidate_threshold": v.candidate_threshold,
            "control_threshold": v.control_threshold,
            "candidate_pixels": int(v.candidate.sum()),
            "control_pixels": int(v.control.sum()),
        } for k, v in out.items()},
    }, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
