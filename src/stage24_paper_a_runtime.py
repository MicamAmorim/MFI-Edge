from __future__ import annotations
"""End-to-end CPU timing audit with no reused detector maps.

These numbers are an engineering diagnostic, not a cross-hardware speed claim.
The UDED sample IDs are fixed, the code executes detector extraction from the
input image through inference and postprocessing, and logs hardware/platform.
"""
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import median_filter
from skimage.transform import resize

from src.classical_detectors import detector_score
from src.postprocess import non_maximum_suppression,gradient_orientation
from src.stage23_descriptors import compute_descriptor
from src.stage24_integrity import resize_score_to_native
from src.stage24_recertification_ops import inference_recipe
from run_stage24_residual_campaign import norm_image
from src.stage24_recertification_cv import write_csv,write_json


def run_runtime_audit(items, frozen, output, *, max_images=4, repeats=2):
    if max_images<1 or repeats<1:
        raise ValueError("Runtime sampling must be positive")
    output=Path(output)
    models=frozen["models"]
    valid=["winner","best_single"]
    if not all(x in models for x in valid):
        raise RuntimeError("Frozen winner and best-single required")
    selected=sorted(items,key=lambda v:v["id"])[:max_images]
    rows=[]
    for case in selected:
        img=np.asarray(case["img"])
        h,w=img.shape[:2]
        for name in valid+["scharr_raw_nms","scharr_median3_nms"]:
            warming=[]
            for trial in range(repeats+1):
                t0=time.perf_counter()
                if name.startswith("scharr_"):
                    pre=(median_filter(img,size=(3,3,1)) if img.ndim==3
                         else median_filter(img,size=3)) if "median3" in name else img
                    grad=detector_score(pre,"scharr",1.0)
                    score=non_maximum_suppression(grad,gradient_orientation(pre,1.0))
                else:
                    model=models[name]
                    inf=norm_image(img)
                    maps=[]
                    for desc in model["descriptors"]:
                        raw=np.asarray(compute_descriptor(desc,inf),np.float32)
                        maps.append(resize_score_to_native(raw,(h,w)))
                    score=inference_recipe(maps,model,img)
                elapsed=time.perf_counter()-t0
                if np.asarray(score).shape!=(h,w) or not np.isfinite(score).all():
                    raise RuntimeError("Invalid full-pipeline runtime score "+name)
                if trial>0:
                    rows.append({"image_id":case["id"],"model":name,
                                 "trial":trial,"runtime_seconds":float(elapsed),
                                 "native_shape":f"{h}x{w}",
                                 "include_cached_descriptors":False,
                                 "timing":"input_to_float_score_after_NMS"})
    write_csv(output/"runtime_end_to_end_per_image.csv",rows)
    grouped={}
    for name in sorted({r["model"] for r in rows}):
        nums=[r["runtime_seconds"] for r in rows if r["model"]==name]
        grouped[name]={"mean_seconds":float(statistics.mean(nums)),
                       "median_seconds":float(statistics.median(nums)),
                       "n_trials":len(nums)}
    write_json(output/"runtime_end_to_end_manifest.json",{
        "status":"descriptive_repeated_CPU_benchmark",
        "hardware":{"platform":platform.platform(),"machine":platform.machine(),
                    "cpu":platform.processor(),"logical_cores":os.cpu_count(),
                    "python":sys.version,"numpy":np.__version__},
        "warmup_runs_per_image":1,"measured_repetitions":repeats,
        "distinct_images":len(selected),
        "all_descriptor_maps_recomputed":True,
        "cache_reused":False,"scope":"selected images; no claim about universal performance",
        "summary":grouped})
    return rows
