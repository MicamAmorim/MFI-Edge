from __future__ import annotations

"""Stable entrypoint for the second-wave CH-MFI v2 local benchmark.

It reuses the tested checkpoint/bootstrap infrastructure from
`benchmark_local_ch_mfi.py` while swapping in the v2 model/grid. Optional
learned files are read from environment variables:

MFI_REGIME_SHAPLEY=results/local_dev/regime_shapley.json
MFI_SCALE_CAPACITY_BANK=results/local_dev/scale_capacity_bank.json
"""

import os

import benchmark_local_ch_mfi as bench
from benchmark_uded_stage7 import bootstrap_delta as _stage7_bootstrap_delta
from src.ch_mfi_v2 import CHMFIv2Config, run_ch_mfi_v2
from src.research_grid_v2 import build_grid as build_grid_v2


_REGIME = os.environ.get("MFI_REGIME_SHAPLEY")
_SCALE = os.environ.get("MFI_SCALE_CAPACITY_BANK")


def _grid(preset, n_features):
    return build_grid_v2(preset, n_features, regime_file=_REGIME, scale_file=_SCALE)


_original_eval = bench.evaluate_selection


def _eval(cfg, select_items, n_thresholds):
    row, summaries = _original_eval(cfg, select_items, n_thresholds)
    row["architecture"] = "CH-MFI-v2"
    row["aggregation_variant"] = getattr(cfg, "aggregation_variant", "standard")
    row["rdf"] = getattr(cfg, "rdf", "")
    row["swafed_mode"] = getattr(cfg, "swafed_mode", "")
    row["inspired_weight_function"] = getattr(cfg, "inspired_weight_function", "")
    row["has_regime_shapley"] = bool(getattr(cfg, "regime_importance", None))
    row["has_scale_capacity_bank"] = bool(getattr(cfg, "scale_specific_measures", None))
    return row, summaries


def _bootstrap_compat(candidate_counts, baseline_counts, n_boot=5000, seed=20261004):
    """Compatibility with benchmark_local_ch_mfi's historical return schema.

    benchmark_local_ch_mfi passes candidate first and baseline second, whereas
    Stage-7 bootstrap_delta expects baseline first. Preserve the intended
    candidate-minus-baseline sign and expose both old and canonical key names.
    """
    r = _stage7_bootstrap_delta(
        baseline_counts,
        candidate_counts,
        n_boot=n_boot,
        seed=seed,
    )
    return {
        "ci_low": r["delta_F1_ci95_low"],
        "ci_high": r["delta_F1_ci95_high"],
        "p_positive": r["p_delta_gt_0"],
        **r,
    }


bench.CHMFIConfig = CHMFIv2Config
bench.run_ch_mfi = run_ch_mfi_v2
bench.build_grid = _grid
bench.evaluate_selection = _eval
bench.bootstrap_delta = _bootstrap_compat


if __name__ == "__main__":
    bench.main()
