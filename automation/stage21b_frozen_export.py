from __future__ import annotations

"""Copy one Stage-21B frozen map set; never reconstruct detector output."""

from pathlib import Path
import argparse
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "stage20a_full_shortlist_2additive_choquet": ROOT / "automation/runtime/official_eval_cache/experiments/stage20a_full_shortlist_2additive_choquet/stage20a_full_shortlist_2additive_choquet/val",
    "stage20b_interaction_core_2additive_choquet": ROOT / "automation/runtime/official_eval_cache/experiments/stage20b_interaction_core_2additive_choquet/stage20b_interaction_core_2additive_choquet/val",
    "stage20c_dominant_pair_2additive_choquet": ROOT / "automation/runtime/official_eval_cache/experiments/stage20c_dominant_pair_2additive_choquet/stage20c_dominant_pair_2additive_choquet/val",
    "stage20d_incumbent_bank_2additive_choquet": ROOT / "automation/runtime/official_eval_cache/experiments/stage20d_incumbent_bank_2additive_choquet/stage20d_incumbent_bank_2additive_choquet/val",
}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True, choices=sorted(SOURCES))
    ap.add_argument("--image-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--split", required=True)
    args = ap.parse_args()
    if args.split != "val":
        raise RuntimeError("Stage 21B frozen artifacts are validation-only")
    src, out = SOURCES[args.method], Path(args.output_dir)
    expected = sorted(Path(args.image_dir).glob("*.jpg"))
    maps = sorted(src.glob("*.png"))
    if len(expected) != 100 or [p.stem for p in maps] != [p.stem for p in expected]:
        raise RuntimeError(f"incomplete frozen map set for {args.method}")
    out.mkdir(parents=True, exist_ok=True)
    for p in maps:
        shutil.copy2(p, out / p.name)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
