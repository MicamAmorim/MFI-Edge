from __future__ import annotations

"""Copy exact frozen Stage-22B map sets for the documentary official attachment."""

import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "stage20c_dominant_pair_2additive_choquet": ROOT / "automation/runtime/official_eval_cache/experiments/stage20c_dominant_pair_2additive_choquet/stage20c_dominant_pair_2additive_choquet/val",
    "stage21h_consensus_pairwise_choquet": ROOT / "automation/runtime/official_eval_cache/experiments/stage21h_consensus_pairwise_choquet_retry2/stage21h_consensus_pairwise_choquet/val",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", required=True, choices=sorted(SOURCES))
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--split", required=True)
    args = parser.parse_args()
    if args.split != "val":
        raise RuntimeError("Stage 22B frozen artifacts are validation-only")
    expected = sorted(Path(args.image_dir).glob("*.jpg"))
    maps = sorted(SOURCES[args.method].glob("*.png"))
    if len(expected) != 100 or [p.stem for p in maps] != [p.stem for p in expected]:
        raise RuntimeError(f"incomplete frozen map set for {args.method}")
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for path in maps:
        shutil.copy2(path, out / path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
