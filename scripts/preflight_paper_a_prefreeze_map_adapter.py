#!/usr/bin/env python3
"""GT-free synthetic preflight for actual Stage23 descriptors (not a confirmation)."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.paper_a_prefreeze_map_adapter import DESCRIPTORS, predict_original_pregt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real-stage23",action="store_true",
                        help="Run four real Stage23 descriptors on a SYNTHETIC image; can be computationally slower")
    args=parser.parse_args()
    yy,xx=np.indices((48,52))
    original=np.zeros((48,52,3),dtype=np.float32)
    original[:,21:30,:]=1
    original[...,0]+=((xx+yy)%13)/100
    recipe=json.loads((ROOT/"docs/paper_a_confirmation"/"P1_DEVELOPMENT_RECIPE_UNATTESTED.json").read_text(encoding="utf-8"))
    if args.real_stage23:
        maker=None
    else:
        def maker(name,im):
            y,x=np.indices(im.shape[:2],dtype=float)
            idx=DESCRIPTORS.index(name)
            return ((x*(idx+1)+y*(3-idx))/(im.shape[0]*4+im.shape[1]*4)).astype(np.float32)
    r=predict_original_pregt(original,recipe,descriptor_fn=maker)
    print(json.dumps({
      "status":"SYNTHETIC_ORIGINAL_IMAGE_PREGT_NO_CONFIRMATORY_GT",
      "actual_stage23_implementation_invoked":args.real_stage23,
      "image_or_GT_dataset_read":False,
      "development_fit_rerun":False,
      "original_geometry":r.original_geometry,
      "inference_geometry":r.inference_geometry,
      "hypotheses":{key:{"X":round(v.feature,8),
                          "candidate_pixels":int(v.candidate.sum()),
                          "control_pixels":int(v.control.sum())}
                    for key,v in r.predictions.items()},
    },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
