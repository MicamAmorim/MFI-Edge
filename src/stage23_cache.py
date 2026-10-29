from __future__ import annotations

"""Content-addressed Stage-23 cache for reusable scientific arrays.

The cache is deliberately independent of any particular descriptor. Callers
provide a complete scientific identity and a zero-argument compute function.
For an exact identity, the compute function is invoked at most once unless the
artifact is explicitly removed/repaired.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import hashlib
import json
import os
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_ROOT = ROOT / "cache" / "local_dev" / "stage23"
SCHEMA_VERSION = 1


class CacheError(RuntimeError):
    pass


class CacheCorruptionError(CacheError):
    pass


@dataclass(frozen=True)
class CacheIdentity:
    dataset: str
    split: str
    image_id: str
    artifact_type: str
    artifact_id: str
    preprocessing_id: str
    parameters: dict[str, Any]
    implementation: str
    implementation_version: str
    code_version: str
    source_sha256: str | None = None
    gt_used: bool = False

    def canonical_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = SCHEMA_VERSION
        return payload

    def cache_key(self) -> str:
        raw = json.dumps(
            self.canonical_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


def _safe_component(value: str) -> str:
    value = str(value).strip().replace("\\", "_").replace("/", "_")
    if not value or value in {".", ".."}:
        raise ValueError(f"unsafe/empty cache path component: {value!r}")
    return value


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def artifact_paths(identity: CacheIdentity, root: Path | None = None) -> tuple[Path, Path, Path]:
    base = Path(root or DEFAULT_CACHE_ROOT)
    key = identity.cache_key()
    folder = (
        base
        / _safe_component(identity.artifact_type)
        / _safe_component(identity.dataset)
        / _safe_component(identity.split)
        / _safe_component(identity.artifact_id)
        / key
    )
    stem = _safe_component(identity.image_id)
    return folder / f"{stem}.npy", folder / f"{stem}.json", folder / f"{stem}.lock"


def _load_metadata(meta_path: Path) -> dict[str, Any]:
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CacheCorruptionError(f"invalid cache metadata {meta_path}: {exc}") from exc


def load_cached(identity: CacheIdentity, root: Path | None = None) -> np.ndarray | None:
    data_path, meta_path, _ = artifact_paths(identity, root)
    if not data_path.exists() and not meta_path.exists():
        return None
    if not data_path.exists() or not meta_path.exists():
        raise CacheCorruptionError(
            f"partial cache artifact for {identity.artifact_id}/{identity.image_id}: "
            f"data={data_path.exists()} metadata={meta_path.exists()}"
        )

    meta = _load_metadata(meta_path)
    expected_key = identity.cache_key()
    if meta.get("schema_version") != SCHEMA_VERSION:
        raise CacheCorruptionError(f"cache schema mismatch for {data_path}")
    if meta.get("cache_key") != expected_key:
        raise CacheCorruptionError(f"cache identity mismatch for {data_path}")
    if meta.get("identity") != identity.canonical_payload():
        raise CacheCorruptionError(f"cache provenance mismatch for {data_path}")

    actual_hash = sha256_file(data_path)
    if meta.get("artifact_sha256") != actual_hash:
        raise CacheCorruptionError(f"cache hash mismatch for {data_path}")

    try:
        arr = np.load(data_path, allow_pickle=False)
    except Exception as exc:
        raise CacheCorruptionError(f"cannot read cached array {data_path}: {exc}") from exc

    if list(arr.shape) != list(meta.get("shape", [])):
        raise CacheCorruptionError(f"cache shape mismatch for {data_path}")
    if str(arr.dtype) != str(meta.get("dtype")):
        raise CacheCorruptionError(f"cache dtype mismatch for {data_path}")
    return arr


def _acquire_lock(lock_path: Path, timeout_s: float = 300.0, poll_s: float = 0.1) -> int:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    while True:
        try:
            return os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.monotonic() - started > timeout_s:
                raise CacheError(f"timed out waiting for cache lock {lock_path}")
            time.sleep(poll_s)


def _release_lock(fd: int, lock_path: Path) -> None:
    try:
        os.close(fd)
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def save_cached(identity: CacheIdentity, array: np.ndarray, root: Path | None = None) -> np.ndarray:
    if identity.gt_used:
        raise CacheError(
            "refusing to persist an inference evidence artifact whose identity declares gt_used=true"
        )

    arr = np.asarray(array)
    if arr.dtype == object:
        raise CacheError("object arrays are not permitted in Stage-23 cache")

    data_path, meta_path, lock_path = artifact_paths(identity, root)
    data_path.parent.mkdir(parents=True, exist_ok=True)

    fd = _acquire_lock(lock_path)
    try:
        existing = load_cached(identity, root)
        if existing is not None:
            return existing

        tmp_data = data_path.with_name(data_path.name + f".tmp-{os.getpid()}")
        tmp_meta = meta_path.with_name(meta_path.name + f".tmp-{os.getpid()}")
        try:
            with tmp_data.open("wb") as handle:
                np.save(handle, arr, allow_pickle=False)
                handle.flush()
                os.fsync(handle.fileno())

            artifact_hash = sha256_file(tmp_data)
            metadata = {
                "schema_version": SCHEMA_VERSION,
                "cache_key": identity.cache_key(),
                "identity": identity.canonical_payload(),
                "shape": list(arr.shape),
                "dtype": str(arr.dtype),
                "artifact_sha256": artifact_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            tmp_meta.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
            os.replace(tmp_data, data_path)
            os.replace(tmp_meta, meta_path)
        finally:
            for p in (tmp_data, tmp_meta):
                try:
                    p.unlink()
                except FileNotFoundError:
                    pass

        loaded = load_cached(identity, root)
        if loaded is None:
            raise CacheError(f"cache write vanished unexpectedly: {data_path}")
        return loaded
    finally:
        _release_lock(fd, lock_path)


def get_or_compute(
    identity: CacheIdentity,
    compute: Callable[[], np.ndarray],
    root: Path | None = None,
) -> tuple[np.ndarray, bool]:
    """Return `(array, cache_hit)` without silently recomputing an exact hit."""

    cached = load_cached(identity, root)
    if cached is not None:
        return cached, True

    if identity.gt_used:
        raise CacheError(
            "refusing to compute/cache inference evidence with gt_used=true"
        )

    data_path, _meta_path, lock_path = artifact_paths(identity, root)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    fd = _acquire_lock(lock_path)
    try:
        # Another worker may have filled the cache while we waited.
        cached = load_cached(identity, root)
        if cached is not None:
            return cached, True

        arr = np.asarray(compute())
        if arr.dtype == object:
            raise CacheError("object arrays are not permitted in Stage-23 cache")

        tmp_data = data_path.with_name(data_path.name + f".tmp-{os.getpid()}")
        meta_path = artifact_paths(identity, root)[1]
        tmp_meta = meta_path.with_name(meta_path.name + f".tmp-{os.getpid()}")
        try:
            with tmp_data.open("wb") as handle:
                np.save(handle, arr, allow_pickle=False)
                handle.flush()
                os.fsync(handle.fileno())
            artifact_hash = sha256_file(tmp_data)
            metadata = {
                "schema_version": SCHEMA_VERSION,
                "cache_key": identity.cache_key(),
                "identity": identity.canonical_payload(),
                "shape": list(arr.shape),
                "dtype": str(arr.dtype),
                "artifact_sha256": artifact_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            tmp_meta.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
            os.replace(tmp_data, data_path)
            os.replace(tmp_meta, meta_path)
        finally:
            for p in (tmp_data, tmp_meta):
                try:
                    p.unlink()
                except FileNotFoundError:
                    pass

        verified = load_cached(identity, root)
        if verified is None:
            raise CacheError(f"cache write vanished unexpectedly: {data_path}")
        return verified, False
    finally:
        _release_lock(fd, lock_path)
