from __future__ import annotations

"""Bridge frozen local-dev research artifacts into the standalone WebUI branch."""

from pathlib import Path
import json
import os

import numpy as np

from .classical_detectors import detector_score
from .conditioning import apply_conditioning
from .pipeline import precompute_multiscale_features
from .postprocess import gradient_orientation, non_maximum_suppression
from .research_signature_runtime import EPS, relational_signature_tensor

ROOT = Path(__file__).resolve().parents[1]
SCALES = (25, 13, 7, 5, 3)
COMPACT_FEATURES = (
    "gabor4_s5",
    "hessian_s7",
    "gabor4_s13",
    "hessian_s13",
    "gabor4_scale_persistence",
)

# Stage-14c aggregate repeated-CV result. It is a development metric, not an
# external/generalization claim.
COMPACT_CV_F1 = 0.75905


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("MFI_RESEARCH_ROOT", "").strip()
    if env:
        roots.append(Path(env).expanduser())
    roots.extend([
        ROOT,
        ROOT.parent / "MFI-Edge",
        ROOT.parent / "MFI-Edge-local-dev",
        ROOT.parent / "MFI-Edge-dev",
    ])
    out: list[Path] = []
    seen: set[str] = set()
    for p in roots:
        try:
            q = p.resolve()
        except Exception:
            q = p
        key = str(q).lower()
        if key not in seen:
            seen.add(key)
            out.append(q)
    return out


def find_stage12d_bundle() -> Path | None:
    rel = Path("results/local_dev/stage12d_bipolar_cv/frozen_candidates.json")
    for root in _candidate_roots():
        p = root / rel
        if p.exists():
            return p
    return None


def research_source_status() -> dict:
    bundle = find_stage12d_bundle()
    return {
        "available": bundle is not None,
        "bundle": str(bundle) if bundle is not None else None,
        "hint": (
            "Set MFI_RESEARCH_ROOT to the active mfi-edge-local-dev worktree "
            "if the frozen Stage-12d artifact is not auto-detected."
        ),
    }


def _load_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _research_model(
    *,
    model_id: str,
    name: str,
    status: str,
    metric_value: float,
    measure: str,
    strategy: str,
    priority: float,
    bundle: Path,
    config: dict,
    bank_mode: str,
    threshold: float | None,
    benchmark: str,
    note: str,
) -> dict:
    return {
        "id": model_id,
        "name": name,
        "engine": "signature_gate",
        "status": status,
        "benchmark": benchmark,
        "rank_basis": "research_status_then_declared_development_metric",
        "metric_label": "Repeated-CV F1",
        "metric_value": float(metric_value),
        "secondary_label": "Threshold",
        "secondary_value": (
            "adaptive visualization" if threshold is None else f"frozen {float(threshold):.5f}"
        ),
        "measure": measure,
        "strategy": strategy,
        "threshold": None if threshold is None else float(threshold),
        "threshold_fallback_quantile": 0.90,
        "display_priority": float(priority),
        "note": note,
        "_bundle_path": str(bundle),
        "_config": dict(config),
        "_bank_mode": bank_mode,
    }


def load_research_models() -> list[dict]:
    bundle = find_stage12d_bundle()
    if bundle is None:
        return []
    try:
        payload = _load_payload(bundle)
        candidates = payload["candidates"]
    except Exception:
        return []

    compact_cfg = {
        "family": "positive_control",
        "gamma_plus": 0.55,
        "gamma_minus": None,
        "lambda": 0.0,
        "strength": 2.0,
        "floor": 0.10,
    }
    rows = [
        _research_model(
            model_id="stage14-compact-positive-incumbent",
            name="Stage 14 · Compact Positive Context Gate",
            status="current-incumbent",
            metric_value=COMPACT_CV_F1,
            measure="5-feature distorted Choquet γ0.55",
            strategy="Scharr+NMS × fuzzy context gate",
            priority=5000,
            bundle=bundle,
            config=compact_cfg,
            bank_mode="compact_positive",
            threshold=None,
            benchmark="UDED selection · repeated leakage-free CV",
            note=(
                "Current retained compact research architecture. The WebUI uses an adaptive "
                "quantile because Stage 14c validated the compact bank by CV but did not export "
                "a single final all-selection threshold."
            ),
        )
    ]

    specs = [
        ("positive_control", "stage12d-positive-frozen", "Stage 12d · Positive Fuzzy Frozen", 4200),
        ("bicapacity", "stage12d-bicap-frozen", "Stage 12d · Separable Bicapacity Frozen", 4100),
        ("ratio_control", "stage12d-ratio-frozen", "Stage 12d · Ratio Control Frozen", 4000),
    ]
    for key, model_id, name, priority in specs:
        row = candidates.get(key)
        if not isinstance(row, dict):
            continue
        cfg = dict(row.get("config", {}))
        rows.append(_research_model(
            model_id=model_id,
            name=name,
            status="frozen-stage12d-representative",
            metric_value=float(row.get("repeated_cv_F1", 0.0)),
            measure=str(cfg.get("family", key)),
            strategy=(
                f"γ+={cfg.get('gamma_plus')} · γ-={cfg.get('gamma_minus')} · "
                f"λ={cfg.get('lambda')} · gate a={cfg.get('strength')} floor={cfg.get('floor')}"
            ),
            priority=priority,
            bundle=bundle,
            config=cfg,
            bank_mode="full",
            threshold=row.get("threshold_fitted_on_all_selection"),
            benchmark="UDED selection · repeated leakage-free CV",
            note=(
                "Exact Stage-12d frozen representative loaded from the active local-dev artifact. "
                "External Stage-13 outcomes are intentionally not used to rank these entries."
            ),
        ))
    return rows


def _normalized_bank(rows: list[dict]) -> list[dict]:
    out = [dict(x) for x in rows]
    total = sum(float(x.get("weight", 0.0)) for x in out) or 1.0
    for x in out:
        x["weight"] = float(x.get("weight", 0.0)) / total
    return out


def _banks(payload: dict, model: dict):
    positive = list(payload.get("positive_bank", []))
    negative = list(payload.get("texture_negative_bank", []))
    if model.get("_bank_mode") == "compact_positive":
        positive = [x for x in positive if str(x.get("feature")) in COMPACT_FEATURES]
        found = {str(x.get("feature")) for x in positive}
        if found != set(COMPACT_FEATURES):
            missing = sorted(set(COMPACT_FEATURES) - found)
            raise RuntimeError(f"Frozen bank is missing compact features: {missing}")
        positive.sort(key=lambda x: COMPACT_FEATURES.index(str(x["feature"])))
    return _normalized_bank(positive), _normalized_bank(negative)


def _membership_stack(item: dict, feature_names: list[str], spec: list[dict], target: str):
    tensor, names = relational_signature_tensor(item, feature_names)
    index = {n: i for i, n in enumerate(names)}
    mus = []
    ws = []
    for row in spec:
        feature = str(row["feature"])
        if feature not in index:
            raise RuntimeError(f"Frozen feature {feature!r} is unavailable in WebUI runtime")
        x = np.asarray(tensor[..., index[feature]], float)
        edge_direction = float(row["edge_direction"])
        direction = edge_direction if target == "edge" else -edge_direction
        z = direction * (x - float(row["midpoint"])) / max(float(row["scale"]), EPS)
        mu = 1.0 / (1.0 + np.exp(-np.clip(z, -20.0, 20.0)))
        mus.append(mu.astype(np.float32))
        ws.append(float(row["weight"]))
    if not mus:
        h, w = tensor.shape[:2]
        return np.empty((h, w, 0), np.float32), np.empty(0, float)
    weights = np.asarray(ws, float)
    weights /= max(float(weights.sum()), EPS)
    return np.stack(mus, axis=-1), weights


def _distorted_choquet(memberships: np.ndarray, weights: np.ndarray, gamma: float):
    x = np.asarray(memberships, dtype=float)
    if x.shape[-1] == 0:
        return np.zeros(x.shape[:-1], np.float32)
    w = np.asarray(weights, dtype=float)
    w /= max(float(w.sum()), EPS)
    order = np.argsort(x, axis=-1)
    xs = np.take_along_axis(x, order, axis=-1)
    ww = np.take_along_axis(np.broadcast_to(w, x.shape), order, axis=-1)
    suffix = np.flip(np.cumsum(np.flip(ww, axis=-1), axis=-1), axis=-1)
    cap = np.power(np.clip(suffix, 0.0, 1.0), float(gamma))
    prev = np.concatenate([np.zeros((*xs.shape[:-1], 1)), xs[..., :-1]], axis=-1)
    out = np.sum((xs - prev) * cap, axis=-1)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def _normalized_bicapacity(pos: np.ndarray, neg: np.ndarray, lam: float):
    l = max(float(lam), 0.0)
    return np.clip((pos - l * neg + l) / max(1.0 + l, EPS), 0.0, 1.0).astype(np.float32)


def _ratio_control(pos: np.ndarray, neg: np.ndarray, lam: float, prior: float = 0.05):
    q = max(float(prior), EPS)
    return np.clip((pos + q) / (pos + float(lam) * neg + 2.0 * q), 0.0, 1.0).astype(np.float32)


def _context_gate(localizer: np.ndarray, context: np.ndarray, strength: float, floor: float):
    c = np.clip(np.asarray(context, np.float32), 0.0, 1.0)
    gate = float(floor) + (1.0 - float(floor)) * np.power(c, float(strength))
    return np.asarray(localizer, np.float32) * gate.astype(np.float32)


def prepare_signature_image(img: np.ndarray) -> dict:
    pre_img = apply_conditioning(img, "median", size=3)
    features, names = precompute_multiscale_features(pre_img, SCALES, feature_mode="oriented_ms")
    orientation = gradient_orientation(pre_img, 1.0)
    scharr = non_maximum_suppression(detector_score(pre_img, "scharr", 1.0), orientation)
    return {
        "img": img,
        "pre_img": pre_img,
        "features": features,
        "feature_names": list(names),
        "orientation": orientation,
        "scharr": scharr,
    }


def infer_signature_arrays(prepared: dict, model: dict) -> dict:
    payload = _load_payload(Path(str(model["_bundle_path"])))
    positive_bank, negative_bank = _banks(payload, model)
    names = list(prepared["feature_names"])

    pos_memberships, pos_weights = _membership_stack(prepared, names, positive_bank, "edge")
    pos = _distorted_choquet(
        pos_memberships, pos_weights, float(model["_config"].get("gamma_plus", 1.0))
    )

    cfg = dict(model["_config"])
    family = str(cfg.get("family", "positive_control"))
    neg = np.zeros_like(pos, dtype=np.float32)
    if family == "positive_control":
        context = pos
    else:
        neg_memberships, neg_weights = _membership_stack(prepared, names, negative_bank, "texture")
        neg = _distorted_choquet(
            neg_memberships, neg_weights, float(cfg.get("gamma_minus", 1.0))
        )
        lam = float(cfg.get("lambda", 1.0))
        if family == "separable_bicapacity":
            context = _normalized_bicapacity(pos, neg, lam)
        elif family == "ratio_control":
            context = _ratio_control(pos, neg, lam)
        else:
            raise RuntimeError(f"Unsupported research family: {family}")

    score = _context_gate(
        prepared["scharr"],
        context,
        float(cfg.get("strength", 2.0)),
        float(cfg.get("floor", 0.10)),
    )

    diagnostics = [
        {"label": "Contexto fuzzy", "tick": "Σ", "map": context},
        {"label": "Evidência positiva", "tick": "+", "map": pos},
    ]
    if family != "positive_control":
        diagnostics.append({"label": "Anti-textura", "tick": "−", "map": neg})

    if model.get("_bank_mode") == "compact_positive":
        for i, row in enumerate(positive_bank):
            diagnostics.append({
                "label": str(row["feature"]),
                "tick": str(i + 1),
                "map": pos_memberships[..., i],
            })

    return {
        "score": np.asarray(score, np.float32),
        "context": np.asarray(context, np.float32),
        "positive": np.asarray(pos, np.float32),
        "negative": np.asarray(neg, np.float32),
        "diagnostics": diagnostics,
    }
