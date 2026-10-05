from __future__ import annotations

import numpy as np

from src.ch_mfi import CHMFIConfig, distorted_probability_capacity, run_ch_mfi
from src.context_maps import analyze_context
from src.pipeline import precompute_multiscale_features


def synthetic_image(n=96):
    rng = np.random.default_rng(7)
    x = np.zeros((n, n), dtype=np.float32)
    x[18:72, 22:70] = 0.75
    yy, xx = np.ogrid[:n, :n]
    ring = np.abs(np.hypot(xx - 63, yy - 36) - 17) <= 1.5
    x[ring] = 1.0
    x += 0.035 * rng.normal(size=x.shape)
    return np.clip(x, 0.0, 1.0)


def check_result(name, result, shape):
    arrays = [result.score, result.mfi, result.uncertainty, result.localizer]
    for a in arrays:
        assert a.shape == shape, (name, a.shape, shape)
        assert np.all(np.isfinite(a)), f"{name}: non-finite values"
    assert len(result.scale_confidences) == 5
    print(
        f"OK {name}: score=[{result.score.min():.4f},{result.score.max():.4f}] "
        f"mfi=[{result.mfi.min():.4f},{result.mfi.max():.4f}] "
        f"unc={result.uncertainty.mean():.4f}",
        flush=True,
    )


def main():
    img = synthetic_image()
    pre, names = precompute_multiscale_features(img, (25, 13, 7, 5, 3), feature_mode="oriented")
    ctx = analyze_context(img)
    n = len(names)
    uniform = np.ones(n) / n

    configs = [
        CHMFIConfig(
            name="fixed_power",
            within_measure={"kind": "power", "q": 0.2},
            hierarchy="global_local",
            operator_mode="fixed",
            controller="bilateral_exp",
        ),
        CHMFIConfig(
            name="conditional_distprob",
            within_measure=distorted_probability_capacity(uniform, gamma=0.85),
            hierarchy="global_local",
            operator_mode="conditional",
            controller="soft",
        ),
        CHMFIConfig(
            name="dCF_sqrt",
            within_measure={"kind": "additive", "weights": uniform.tolist()},
            dissimilarity="sqrt",
            hierarchy="global_local",
            controller="bilateral_exp",
        ),
    ]

    for cfg in configs:
        result = run_ch_mfi(img, cfg, precomputed=pre, context=ctx)
        check_result(cfg.name, result, img.shape)

    print(f"LOCAL_ARCHITECTURE_SMOKE_OK descriptors={n} names={list(names)}", flush=True)


if __name__ == "__main__":
    main()
