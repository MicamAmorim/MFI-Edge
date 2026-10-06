from __future__ import annotations

from io import BytesIO
from pathlib import Path
import base64
import json
import os
import time
from typing import List

import cv2
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.advanced_fusion import fuse_advanced
from src.classical_detectors import detector_score
from src.conditioning import apply_conditioning
from src.deployable_models import load_deployable_models, model_by_id
from src.fuzzy_measures import measure_registry
from src.hybrid import percentile_confidence
from src.pipeline import precompute_multiscale_features, multiscale_from_precomputed
from src.postprocess import gradient_orientation, non_maximum_suppression
from src.research_deploy import (
    infer_signature_arrays,
    prepare_signature_image,
    research_source_status,
)

ROOT = Path(__file__).resolve().parent
SCALES = (25, 13, 7, 5, 3)
MAX_COMPARE_MODELS = 4

app = FastAPI(title="MFI-Edge Desktop API", version="0.3.0")
origins = os.environ.get(
    "MFI_WEB_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in origins if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _data_url(arr: np.ndarray) -> str:
    x = np.asarray(arr)
    if x.dtype != np.uint8:
        x = np.clip(x, 0, 255).astype(np.uint8)
    if x.ndim == 2:
        im = Image.fromarray(x, mode="L")
    else:
        im = Image.fromarray(x[..., :3], mode="RGB")
    buf = BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _rgb_u8(img: np.ndarray) -> np.ndarray:
    x = np.asarray(img)
    if x.ndim == 2:
        x = np.repeat(x[..., None], 3, axis=2)
    x = x[..., :3]
    if np.issubdtype(x.dtype, np.floating):
        mx = float(np.nanmax(x)) if x.size else 1.0
        if mx <= 1.5:
            x = x * 255.0
    return np.clip(x, 0, 255).astype(np.uint8)


def _resize_max(img: np.ndarray, max_side: int) -> np.ndarray:
    h, w = img.shape[:2]
    m = max(h, w)
    if m <= int(max_side):
        return img
    scale = float(max_side) / float(m)
    nh, nw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    return np.asarray(Image.fromarray(_rgb_u8(img)).resize((nw, nh), Image.Resampling.LANCZOS))


def _norm01(a: np.ndarray) -> np.ndarray:
    x = np.nan_to_num(np.asarray(a, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    if not x.size:
        return np.zeros_like(x, dtype=float)
    lo, hi = np.percentile(x, [1.0, 99.0])
    if hi <= lo + 1e-12:
        lo, hi = float(np.min(x)), float(np.max(x))
    if hi <= lo + 1e-12:
        return np.zeros_like(x, dtype=float)
    return np.clip((x - lo) / (hi - lo), 0.0, 1.0)


def _heat_overlay(img: np.ndarray, attention: np.ndarray, alpha: float = 0.48) -> np.ndarray:
    base = _rgb_u8(img)
    a = (_norm01(attention) * 255.0).astype(np.uint8)
    heat_bgr = cv2.applyColorMap(a, cv2.COLORMAP_INFERNO)
    heat = cv2.cvtColor(heat_bgr, cv2.COLOR_BGR2RGB)
    out = (1.0 - float(alpha)) * base.astype(float) + float(alpha) * heat.astype(float)
    return np.clip(out, 0, 255).astype(np.uint8)


def _edge_overlay(img: np.ndarray, edge: np.ndarray) -> np.ndarray:
    out = _rgb_u8(img).copy()
    e = np.asarray(edge, dtype=bool)
    out[e] = np.array([255, 45, 45], dtype=np.uint8)
    return out


def _public_model(model: dict) -> dict:
    return {k: v for k, v in model.items() if not str(k).startswith("_")}


def _load_learned() -> dict:
    p = ROOT / "benchmark_outputs" / "stage5_measures" / "learned_measures.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _measure_spec(name: str, n_features: int) -> dict:
    specs = measure_registry(n_features, learned=_load_learned())
    for spec in specs:
        if str(spec.get("name")) == str(name):
            return {k: v for k, v in spec.items() if k != "name"}
    raise HTTPException(
        status_code=422,
        detail=(
            f"Measure '{name}' is not available. If this is a learned measure, "
            "copy benchmark_outputs/stage5_measures into the desktop checkout."
        ),
    )


def _threshold(score: np.ndarray, model: dict, requested_quantile: float | None):
    fixed = model.get("threshold")
    if fixed is not None:
        return float(fixed), "frozen-validation"
    q = float(
        requested_quantile
        if requested_quantile is not None
        else model.get("threshold_fallback_quantile", 0.90)
    )
    q = float(np.clip(q, 0.50, 0.999))
    x = np.asarray(score, dtype=float)
    vals = x[np.isfinite(x)]
    vals = vals[vals > 0]
    if not vals.size:
        return 0.0, f"adaptive-quantile-{q:.3f}"
    return float(np.quantile(vals, q)), f"adaptive-quantile-{q:.3f}"


def _decode_upload(data: bytes) -> np.ndarray:
    try:
        return np.asarray(Image.open(BytesIO(data)).convert("RGB"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image: {exc}") from exc


def _get_model(model_id: str) -> dict:
    try:
        return model_by_id(model_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def prepare_image(img: np.ndarray, max_side: int, engine: str = "stage7") -> dict:
    """Run model-independent work once per inference engine."""
    t0 = time.perf_counter()
    img = _resize_max(img, int(max_side))
    if str(engine) == "signature_gate":
        prepared = prepare_signature_image(img)
        prepared["prepare_ms"] = 1000.0 * (time.perf_counter() - t0)
        return prepared

    pre_img = apply_conditioning(img, "median", size=3)
    precomputed, feature_names = precompute_multiscale_features(
        pre_img, SCALES, feature_mode="oriented"
    )
    orientation = gradient_orientation(pre_img, 1.0)
    scharr = non_maximum_suppression(detector_score(pre_img, "scharr", 1.0), orientation)
    return {
        "img": img,
        "pre_img": pre_img,
        "precomputed": precomputed,
        "feature_names": feature_names,
        "scharr": scharr,
        "prepare_ms": 1000.0 * (time.perf_counter() - t0),
    }


def _signature_result(prepared: dict, model: dict, edge_quantile: float | None):
    t0 = time.perf_counter()
    img = prepared["img"]
    arrays = infer_signature_arrays(prepared, model)
    score = arrays["score"]
    thr, threshold_mode = _threshold(score, model, edge_quantile)
    edge = np.asarray(score) >= thr
    attention = []
    for item in arrays["diagnostics"]:
        a = np.asarray(item["map"], dtype=float)
        attention.append({
            "label": str(item["label"]),
            "scale": item.get("tick"),
            "overlay": _data_url(_heat_overlay(img, a)),
            "heatmap": _data_url((_norm01(a) * 255).astype(np.uint8)),
        })
    model_ms = 1000.0 * (time.perf_counter() - t0)
    return {
        "width": int(img.shape[1]),
        "height": int(img.shape[0]),
        "runtime_ms": float(prepared["prepare_ms"] + model_ms),
        "prepare_ms": float(prepared["prepare_ms"]),
        "model_runtime_ms": float(model_ms),
        "threshold": float(thr),
        "threshold_mode": threshold_mode,
        "attention": attention,
        "best_scale": _data_url((_norm01(arrays["context"]) * 255).astype(np.uint8)),
        "edge": _data_url((edge.astype(np.uint8) * 255)),
        "edge_overlay": _data_url(_edge_overlay(img, edge)),
        "score": _data_url((_norm01(score) * 255).astype(np.uint8)),
    }


def _stage7_result(prepared: dict, model: dict, edge_quantile: float | None):
    t0 = time.perf_counter()
    img = prepared["img"]
    spec = _measure_spec(str(model["measure"]), len(prepared["feature_names"]))
    scale_results, final_bits, best_scale = multiscale_from_precomputed(
        prepared["precomputed"],
        img.shape[:2],
        family="CF1F2",
        F1="CL",
        F2="CL",
        q=0.1,
        refine_quantile=0.82,
        heterogeneity_quantile=0.82,
        dilation_radius=3,
        measure_spec=spec,
        measure_context={},
    )
    confidence = percentile_confidence(final_bits)
    score = fuse_advanced(
        prepared["scharr"],
        confidence,
        str(model["strategy"]),
        dict(model.get("params", {})),
    )
    thr, threshold_mode = _threshold(score, model, edge_quantile)
    edge = np.asarray(score) >= thr

    attention = [
        {
            "label": "Fusão multiescala",
            "scale": None,
            "overlay": _data_url(_heat_overlay(img, confidence)),
            "heatmap": _data_url((_norm01(confidence) * 255).astype(np.uint8)),
        }
    ]
    for r in scale_results:
        c = percentile_confidence(r.bits)
        attention.append(
            {
                "label": f"Escala {int(r.window)}×{int(r.window)}",
                "scale": int(r.window),
                "overlay": _data_url(_heat_overlay(img, c)),
                "heatmap": _data_url((_norm01(c) * 255).astype(np.uint8)),
            }
        )

    model_ms = 1000.0 * (time.perf_counter() - t0)
    return {
        "width": int(img.shape[1]),
        "height": int(img.shape[0]),
        "runtime_ms": float(prepared["prepare_ms"] + model_ms),
        "prepare_ms": float(prepared["prepare_ms"]),
        "model_runtime_ms": float(model_ms),
        "threshold": float(thr),
        "threshold_mode": threshold_mode,
        "attention": attention,
        "best_scale": _data_url((_norm01(best_scale) * 255).astype(np.uint8)),
        "edge": _data_url((edge.astype(np.uint8) * 255)),
        "edge_overlay": _data_url(_edge_overlay(img, edge)),
        "score": _data_url((_norm01(score) * 255).astype(np.uint8)),
    }


def infer_prepared(prepared: dict, model: dict, edge_quantile: float | None):
    if str(model.get("engine", "stage7")) == "signature_gate":
        return _signature_result(prepared, model, edge_quantile)
    return _stage7_result(prepared, model, edge_quantile)


def infer_one(img: np.ndarray, model: dict, max_side: int, edge_quantile: float | None):
    prepared = prepare_image(img, max_side, str(model.get("engine", "stage7")))
    out = infer_prepared(prepared, model, edge_quantile)
    out["original"] = _data_url(_rgb_u8(prepared["img"]))
    return out


@app.get("/api/health")
def health():
    rows = load_deployable_models()
    return {
        "ok": True,
        "scales": list(SCALES),
        "models": len(rows),
        "research_models": sum(str(x.get("engine")) == "signature_gate" for x in rows),
        "research_source": research_source_status(),
        "max_compare_models": MAX_COMPARE_MODELS,
    }


@app.get("/api/models")
def models():
    rows = load_deployable_models()
    research = research_source_status()
    note = (
        "Current Stage-14 research models are shown first when the active local-dev frozen artifact is available. "
        "Each metric keeps its own protocol label; Stage-7 ODS and Stage-12/14 repeated-CV F1 are not treated as interchangeable. "
        "Entries without an exported frozen threshold use an adaptive quantile for visualization only."
    )
    if not research["available"]:
        note += " Research artifact not found; set MFI_RESEARCH_ROOT to the local-dev worktree to enable current models."
    return {
        "rank_basis": "current research status, then declared development metric",
        "note": note,
        "research_source_available": bool(research["available"]),
        "max_compare_models": MAX_COMPARE_MODELS,
        "models": [_public_model(x) for x in rows],
    }


@app.post("/api/infer")
async def infer(
    files: List[UploadFile] = File(...),
    model_id: str = Form(...),
    max_side: int = Form(768),
    edge_quantile: float | None = Form(None),
):
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one image")
    if len(files) > 64:
        raise HTTPException(status_code=400, detail="Maximum 64 images per request")
    model = _get_model(model_id)
    results = []
    for f in files:
        data = await f.read()
        img = _decode_upload(data)
        out = infer_one(img, model, max_side=max_side, edge_quantile=edge_quantile)
        out["filename"] = f.filename or "image"
        results.append(out)
    return {"model": _public_model(model), "results": results}


@app.post("/api/compare")
async def compare(
    files: List[UploadFile] = File(...),
    model_ids: str = Form(...),
    max_side: int = Form(768),
    edge_quantile: float | None = Form(None),
):
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one image")
    if len(files) > 64:
        raise HTTPException(status_code=400, detail="Maximum 64 images per request")
    try:
        ids = json.loads(model_ids)
        if not isinstance(ids, list):
            raise ValueError
    except Exception:
        ids = [x.strip() for x in str(model_ids).split(",") if x.strip()]
    ids = list(dict.fromkeys(str(x) for x in ids))
    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="Comparison requires at least 2 models")
    if len(ids) > MAX_COMPARE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Comparison supports at most {MAX_COMPARE_MODELS} models",
        )
    selected_models = [_get_model(mid) for mid in ids]

    results = []
    for f in files:
        data = await f.read()
        img = _decode_upload(data)
        prepared_by_engine = {}
        per_model = []
        for model in selected_models:
            engine = str(model.get("engine", "stage7"))
            if engine not in prepared_by_engine:
                prepared_by_engine[engine] = prepare_image(img, max_side=max_side, engine=engine)
            prepared = prepared_by_engine[engine]
            out = infer_prepared(prepared, model, edge_quantile=edge_quantile)
            out["model"] = _public_model(model)
            per_model.append(out)
        first = next(iter(prepared_by_engine.values()))
        results.append(
            {
                "filename": f.filename or "image",
                "width": int(first["img"].shape[1]),
                "height": int(first["img"].shape[0]),
                "prepare_ms": float(sum(x["prepare_ms"] for x in prepared_by_engine.values())),
                "original": _data_url(_rgb_u8(first["img"])),
                "models": per_model,
            }
        )
    return {
        "models": [_public_model(x) for x in selected_models],
        "shared_preprocessing": len({str(x.get("engine", "stage7")) for x in selected_models}) == 1,
        "preprocessing_mode": "shared within each inference engine",
        "results": results,
    }
