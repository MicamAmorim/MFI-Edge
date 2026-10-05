from __future__ import annotations

from pathlib import Path
import argparse
import io
import json
import shutil
import zipfile

import pandas as pd
import requests

from benchmark_uded import load_uded, prepare
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import benchmark_parallel_scaling, save_parallel_plot
from src.fuzzy_measures import measure_registry


def ensure_uded(root: Path):
    if root.exists() and any(root.iterdir()):
        return
    root.parent.mkdir(parents=True, exist_ok=True)
    tmp_parent = root.parent
    url = "https://github.com/xavysp/UDED/archive/refs/heads/main.zip"
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(tmp_parent)
    extracted = tmp_parent / "UDED-main"
    if root.exists():
        shutil.rmtree(root)
    shutil.move(str(extracted), str(root))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", required=True)
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--n-images", type=int, default=2)
    args = ap.parse_args()

    root = Path(args.uded_root)
    model_dir = Path(args.model_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    ensure_uded(root)
    learned = json.loads((model_dir / "learned_measures.json").read_text(encoding="utf-8"))
    context_model = json.loads((model_dir / "context_router.json").read_text(encoding="utf-8"))
    feature_names = json.loads((model_dir / "feature_names.json").read_text(encoding="utf-8"))

    # Prepare only the tiny subset used by this microbenchmark so 4-worker tests
    # do not reproduce the memory pressure of the full 30-image scientific sweep.
    raw = load_uded(root)[: max(1, int(args.n_images))]
    raw = resize_items(raw, int(args.max_side))
    items, _ = prepare(raw)

    specs = [s for s in measure_registry(len(feature_names), learned=learned)
             if s.get("routing") != "oracle"]
    specs_by_name = {str(s["name"]): s for s in specs}

    df = benchmark_parallel_scaling(
        specs_by_name,
        items,
        context_model,
        workers=(1, 2, 4),
        n_images=len(items),
    )
    df.to_csv(out / "parallel_scaling.csv", index=False)
    save_parallel_plot(df, out / "parallel_scaling.png")

    best = df.sort_values("elapsed_s").iloc[0]
    summary = {
        "n_images": len(items),
        "max_side": int(args.max_side),
        "workers_tested": df["workers"].astype(int).tolist(),
        "best_workers": int(best["workers"]),
        "best_elapsed_s": float(best["elapsed_s"]),
        "best_speedup_vs_1": float(best["speedup_vs_1"]),
        "rows": df.to_dict("records"),
        "note": "Microbenchmark only: four representative fuzzy measures on a tiny real-image subset. Main Stage-7 scientific sweep remains sequential/checkpointed for memory safety.",
    }
    (out / "parallel_scaling_summary.json").write_text(
        json.dumps(summary, indent=2, default=float), encoding="utf-8"
    )
    print("STAGE7_PARALLEL_SCALING_DONE", flush=True)
    print(df.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
