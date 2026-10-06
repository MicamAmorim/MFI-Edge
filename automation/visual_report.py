from __future__ import annotations

"""Small dependency-free PNG/grid utilities for experiment previews.

Only NumPy plus the Python standard library are required. The grid intentionally
avoids typography so experiment summaries can define row/column labels without
adding a plotting dependency to every runner.
"""

from pathlib import Path
import struct
import zlib

import numpy as np


def _to_rgb_uint8(image: np.ndarray) -> np.ndarray:
    x = np.asarray(image)
    if x.ndim == 2:
        if x.dtype == bool:
            y = x.astype(np.uint8) * 255
        else:
            y = np.asarray(x, dtype=float)
            finite = np.isfinite(y)
            if not finite.any():
                y = np.zeros_like(y, dtype=float)
            else:
                lo = float(np.nanmin(y[finite]))
                hi = float(np.nanmax(y[finite]))
                if lo >= 0.0 and hi <= 1.0:
                    y = y * 255.0
                elif hi > 255.0 or lo < 0.0:
                    span = max(hi - lo, 1e-12)
                    y = (y - lo) * 255.0 / span
            y = np.clip(np.nan_to_num(y), 0, 255).astype(np.uint8)
        return np.repeat(y[..., None], 3, axis=2)
    if x.ndim == 3 and x.shape[2] >= 3:
        y = np.asarray(x[..., :3], dtype=float)
        if np.nanmax(y) <= 1.0:
            y = y * 255.0
        return np.clip(np.nan_to_num(y), 0, 255).astype(np.uint8)
    raise ValueError(f"unsupported image shape for preview: {x.shape}")


def _resize_nearest(image: np.ndarray, height: int, width: int) -> np.ndarray:
    x = _to_rgb_uint8(image)
    yi = np.minimum((np.arange(height) * x.shape[0] / height).astype(int), x.shape[0] - 1)
    xi = np.minimum((np.arange(width) * x.shape[1] / width).astype(int), x.shape[1] - 1)
    return x[yi[:, None], xi[None, :]]


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def write_png(path: str | Path, rgb: np.ndarray) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    x = _to_rgb_uint8(rgb)
    h, w, _ = x.shape
    raw = b"".join(b"\x00" + x[row].tobytes() for row in range(h))
    data = b"\x89PNG\r\n\x1a\n"
    data += _png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    data += _png_chunk(b"IDAT", zlib.compress(raw, 9))
    data += _png_chunk(b"IEND", b"")
    path.write_bytes(data)
    return path


def write_panel_grid(
    path: str | Path,
    rows: list[list[np.ndarray]],
    *,
    panel_height: int = 192,
    panel_width: int = 192,
    gap: int = 4,
) -> Path:
    if not rows or not rows[0]:
        raise ValueError("preview grid requires at least one panel")
    cols = len(rows[0])
    if any(len(row) != cols for row in rows):
        raise ValueError("all preview rows must have the same number of panels")
    h = len(rows) * panel_height + (len(rows) - 1) * gap
    w = cols * panel_width + (cols - 1) * gap
    canvas = np.full((h, w, 3), 255, dtype=np.uint8)
    for r, row in enumerate(rows):
        for c, panel in enumerate(row):
            y0 = r * (panel_height + gap)
            x0 = c * (panel_width + gap)
            canvas[y0:y0 + panel_height, x0:x0 + panel_width] = _resize_nearest(panel, panel_height, panel_width)
    return write_png(path, canvas)
