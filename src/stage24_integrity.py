from __future__ import annotations

"""Stage 24 evaluation-integrity primitives.

Scientific invariants:
- Ground truth is never resized.
- Soft scientific maps remain floating-point arrays.
- Tolerance belongs to matching, not to the training target.
- Internal UDED evaluation uses maximum-cardinality one-to-one boundary matching.
- Final BSDS ODS/OIS/AP must come from the repository's official Berkeley MATLAB path.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
from typing import Iterable, Sequence

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching
from scipy.spatial import cKDTree
from skimage.transform import resize


@dataclass(frozen=True)
class BoundaryCounts:
    tp: int
    fp: int
    fn: int
    pred_count: int
    gt_count: int
    tolerance_px: int

    @property
    def precision(self) -> float:
        if self.pred_count == 0:
            return 1.0 if self.gt_count == 0 else 0.0
        return self.tp / self.pred_count

    @property
    def recall(self) -> float:
        if self.gt_count == 0:
            return 1.0
        return self.tp / self.gt_count

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 0.0 if p + r == 0 else 2.0 * p * r / (p + r)

    def to_dict(self) -> dict[str, float | int]:
        d = asdict(self)
        d.update(precision=self.precision, recall=self.recall, F1=self.f1)
        return d


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tolerance_pixels(shape: Sequence[int], ratio: float = 0.0075) -> int:
    if len(shape) < 2:
        raise ValueError("shape must contain H,W")
    h, w = int(shape[0]), int(shape[1])
    return max(1, int(round(float(ratio) * float(np.hypot(h, w)))))


def exact_binary_gt(gt: np.ndarray) -> np.ndarray:
    value = np.asarray(gt)
    if value.ndim == 3:
        value = value[..., 0]
    if value.ndim != 2:
        raise ValueError(f"ground truth must be 2-D, got {value.shape}")
    if np.issubdtype(value.dtype, np.bool_):
        out = value.copy()
    elif np.issubdtype(value.dtype, np.integer):
        out = value > (0.5 * np.iinfo(value.dtype).max)
    else:
        out = value > 0.5
    return np.asarray(out, dtype=bool)


@dataclass(frozen=True)
class BoundaryReference:
    """Immutable training-GT geometry reusable across threshold candidates.

    Use only for the same unmodified ground-truth image. No labels from held-out
    images are used when selecting thresholds.
    """
    mask: np.ndarray
    coords: np.ndarray
    tree: cKDTree | None
    tolerance_px: int
    count: int


def prepare_boundary_reference(
    gt: np.ndarray, *, tolerance_ratio: float = 0.0075,
    tolerance_px: int | None = None,
) -> BoundaryReference:
    mask = exact_binary_gt(gt).copy()
    mask.setflags(write=False)
    tol = tolerance_pixels(mask.shape, tolerance_ratio) if tolerance_px is None else max(0, int(tolerance_px))
    coords = np.argwhere(mask)
    tree = cKDTree(coords.astype(float)) if len(coords) and tol else None
    return BoundaryReference(mask, coords, tree, tol, len(coords))


def _match_indices(
    pred: np.ndarray, gt: np.ndarray, tol: int,
    *, reference: BoundaryReference | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Exact maximum-cardinality matching; prune isolated prediction rows."""
    pred_xy = np.argwhere(np.asarray(pred, bool))
    gt_xy = reference.coords if reference is not None else np.argwhere(np.asarray(gt, bool))
    if len(pred_xy) == 0 or len(gt_xy) == 0:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)

    tree = reference.tree if reference is not None else cKDTree(gt_xy.astype(float))
    neighborhoods = tree.query_ball_point(pred_xy.astype(float), r=float(tol), p=2.0)
    lengths = np.fromiter((len(js) for js in neighborhoods), dtype=np.intp,
                          count=len(neighborhoods))
    active = np.flatnonzero(lengths)
    if not len(active):
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)

    # Keep the exact original edge relation; isolated rows cannot participate in
    # a matching and need not inflate the sparse graph's row dimension.
    edge_count = int(lengths.sum())
    rows = np.repeat(np.arange(len(active), dtype=np.intp), lengths[active])
    cols = np.fromiter((j for js in neighborhoods for j in js),
                       dtype=np.intp, count=edge_count)
    graph = csr_matrix(
        (np.ones(edge_count, dtype=np.uint8), (rows, cols)),
        shape=(len(active), len(gt_xy)),
    )
    matched_gt = maximum_bipartite_matching(graph, perm_type="column")
    matched_active = np.flatnonzero(matched_gt >= 0)
    pred_idx = active[matched_active].astype(np.int64, copy=False)
    gt_idx = np.asarray(matched_gt[matched_active], dtype=np.int64)
    return pred_idx, gt_idx


def one_to_one_boundary_counts(
    pred: np.ndarray,
    gt: np.ndarray,
    *,
    tolerance_ratio: float = 0.0075,
    tolerance_px: int | None = None,
    reference: BoundaryReference | None = None,
) -> BoundaryCounts:
    p = np.asarray(pred, dtype=bool)
    g = reference.mask if reference is not None else exact_binary_gt(gt)
    if p.shape != g.shape:
        raise ValueError(f"prediction/GT shape mismatch: {p.shape} vs {g.shape}")
    tol = (reference.tolerance_px if reference is not None else
           tolerance_pixels(g.shape, tolerance_ratio) if tolerance_px is None
           else max(0, int(tolerance_px)))
    pred_count = int(np.count_nonzero(p))
    gt_count = reference.count if reference is not None else int(np.count_nonzero(g))
    # Exact cardinality shortcuts: identity coordinates give distinct legal
    # matches, so a full inclusion achieves the upper bound min(|P|,|GT|).
    if tol == 0:
        tp = int(np.count_nonzero(p & g))
    elif pred_count == 0 or gt_count == 0:
        tp = 0
    elif pred_count >= gt_count and not np.any(g & ~p):
        tp = gt_count
    elif gt_count >= pred_count and not np.any(p & ~g):
        tp = pred_count
    else:
        # A distinct nearest-neighbour assignment is a CERTIFICATE of a
        # maximum-cardinality match when it covers the smaller side. A failed
        # certificate is NOT treated as a mismatch: use the exact graph solver.
        pred_xy = np.argwhere(p)
        if pred_count >= gt_count:
            gt_xy = reference.coords if reference is not None else np.argwhere(g)
            distances, neighbors = cKDTree(pred_xy.astype(float)).query(
                gt_xy.astype(float), k=1, distance_upper_bound=float(tol)+1e-8)
            certified = (np.all(distances <= float(tol)+1e-8) and
                         len(np.unique(neighbors)) == gt_count)
        else:
            tree = reference.tree if reference is not None else cKDTree(np.argwhere(g).astype(float))
            distances, neighbors = tree.query(
                pred_xy.astype(float), k=1, distance_upper_bound=float(tol)+1e-8)
            certified = (np.all(distances <= float(tol)+1e-8) and
                         len(np.unique(neighbors)) == pred_count)
        if certified:
            tp = min(pred_count, gt_count)
        else:
            pred_idx, _ = _match_indices(p, g, tol, reference=reference)
            tp = int(len(pred_idx))
    return BoundaryCounts(
        tp=tp,
        fp=pred_count - tp,
        fn=gt_count - tp,
        pred_count=pred_count,
        gt_count=gt_count,
        tolerance_px=tol,
    )


def aggregate_counts(counts: Iterable[BoundaryCounts]) -> BoundaryCounts:
    values = list(counts)
    if not values:
        return BoundaryCounts(0, 0, 0, 0, 0, 0)
    tp = sum(x.tp for x in values)
    fp = sum(x.fp for x in values)
    fn = sum(x.fn for x in values)
    pred = sum(x.pred_count for x in values)
    gt = sum(x.gt_count for x in values)
    return BoundaryCounts(tp, fp, fn, pred, gt, max(x.tolerance_px for x in values))


def evaluate_scores(
    scores: Sequence[np.ndarray],
    gts: Sequence[np.ndarray],
    threshold: float,
    *,
    tolerance_ratio: float = 0.0075,
) -> tuple[BoundaryCounts, list[BoundaryCounts]]:
    if len(scores) != len(gts):
        raise ValueError("scores and gts length mismatch")
    per = [
        one_to_one_boundary_counts(np.asarray(s) >= threshold, gt, tolerance_ratio=tolerance_ratio)
        for s, gt in zip(scores, gts)
    ]
    return aggregate_counts(per), per


def canonical_threshold_candidates(scores: Sequence[np.ndarray], count: int = 101) -> np.ndarray:
    finite = [np.asarray(x, float).ravel() for x in scores if np.size(x)]
    if not finite:
        return np.array([0.5], dtype=float)
    flat = np.concatenate(finite)
    flat = flat[np.isfinite(flat)]
    if flat.size == 0:
        raise ValueError("no finite scores")
    q = np.linspace(0.0, 1.0, max(3, int(count)))
    values = np.unique(np.quantile(flat, q))
    return values.astype(float)


def select_threshold(
    scores: Sequence[np.ndarray],
    gts: Sequence[np.ndarray],
    *,
    count: int = 101,
    tolerance_ratio: float = 0.0075,
) -> dict[str, float | int]:
    best: tuple[float, float, float, float, BoundaryCounts] | None = None
    for threshold in canonical_threshold_candidates(scores, count):
        counts, _ = evaluate_scores(scores, gts, float(threshold), tolerance_ratio=tolerance_ratio)
        key = (counts.f1, counts.precision, counts.recall, float(threshold))
        if best is None or key > best[:4]:
            best = (*key, counts)
    assert best is not None
    threshold = float(best[3])
    counts = best[4]
    return {"threshold": threshold, **counts.to_dict()}


def resize_score_to_native(score: np.ndarray, native_shape: Sequence[int]) -> np.ndarray:
    """Register a FLOAT score to native GT geometry. GT itself is never transformed."""
    value = np.asarray(score)
    if value.ndim != 2 or not np.issubdtype(value.dtype, np.floating):
        raise TypeError("scientific score must be a 2-D floating-point array")
    target = (int(native_shape[0]), int(native_shape[1]))
    if value.shape == target:
        return np.asarray(value, dtype=np.float32)
    out = resize(
        value.astype(np.float32),
        target,
        order=1,
        mode="reflect",
        anti_aliasing=True,
        preserve_range=True,
    )
    return np.asarray(out, dtype=np.float32)


def save_float_artifact(path: Path, array: np.ndarray, identity: dict) -> dict:
    path = Path(path)
    if path.suffix.lower() != ".npy":
        raise ValueError("canonical scientific artifacts must use .npy")
    value = np.asarray(array)
    if not np.issubdtype(value.dtype, np.floating):
        raise TypeError("canonical scientific artifacts must be floating point")
    if not np.all(np.isfinite(value)):
        raise ValueError("non-finite scientific artifact")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".npy.tmp")
    with tmp.open("wb") as f:
        np.save(f, np.asarray(value, dtype=np.float32), allow_pickle=False)
    tmp.replace(path)
    payload = {
        "schema_version": 1,
        "identity": identity,
        "artifact_sha256": sha256_file(path),
        "shape": list(value.shape),
        "dtype": "float32",
    }
    sidecar = path.with_suffix(".json")
    sidecar.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return payload


def load_float_artifact(path: Path, expected_identity: dict | None = None) -> np.ndarray:
    path = Path(path)
    if path.suffix.lower() != ".npy":
        raise ValueError("PNG/JPEG/other quantized files are not scientific-map inputs")
    sidecar = path.with_suffix(".json")
    if not path.is_file() or not sidecar.is_file():
        raise FileNotFoundError(path)
    meta = json.loads(sidecar.read_text(encoding="utf-8"))
    if expected_identity is not None and meta.get("identity") != expected_identity:
        raise RuntimeError("scientific artifact identity mismatch")
    if meta.get("artifact_sha256") != sha256_file(path):
        raise RuntimeError("scientific artifact hash mismatch")
    value = np.load(path, allow_pickle=False)
    if not np.issubdtype(value.dtype, np.floating):
        raise TypeError("quantized artifact rejected")
    if list(value.shape) != meta.get("shape"):
        raise RuntimeError("scientific artifact shape mismatch")
    if not np.all(np.isfinite(value)):
        raise RuntimeError("non-finite scientific artifact")
    return np.asarray(value, dtype=np.float32)


def deterministic_seed(base_seed: int, *parts: object) -> int:
    payload = "|".join([str(int(base_seed)), *(str(x) for x in parts)]).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:4], "little") & 0x7FFFFFFF
