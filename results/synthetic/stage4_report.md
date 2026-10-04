# Stage 4 — conditioning, MFI proposal, Scharr localization and MFI-guided linking

Date: 2026-10-04

## Current architecture

The current development model is:

```text
image
  -> robust preconditioning (median 3x3)
  -> orientation-aware multiscale MFI proposal
  -> MFI ROI (top 40% confidence; q_ROI=0.60)
  -> Scharr response + orientation-aware non-maximum suppression
  -> MFI-guided geodesic edge linking
  -> final edge map
```

The MFI backbone remains `CF1F2(CL,CL)` with the power fuzzy measure q=0.1 and scales 25,13,7,5,3. The operator re-ranking was repeated after correction of the old diagonal GT and on the new validation benchmark; `CF1F2(CL,CL)` remains the nominal winner and is essentially tied with `CC(CL)`.

The present shorthand for the full variant is **MFI-Edge-SCHARR-GL**, where GL denotes MFI-guided geodesic linking.

## Synthetic benchmark v2

A new deterministic benchmark was generated specifically for development and robustness analysis.

- validation: 40 images
- held-out test: 60 images
- image size: 96x96
- primitives: line, stripe, circle, ellipse, rectangle, triangle, sinusoidal boundary, multiple objects and T-junction
- degradation families: clean, Gaussian noise, salt-and-pepper, speckle, Gaussian blur, motion blur, illumination gradient, texture, artificial edge gaps, and compound degradation
- GT is generated from the clean binary primitive before degradation
- gap samples deliberately weaken a segment in the observed image while keeping the GT edge continuous

Validation is used for selecting conditioning, ROI threshold and linking parameters. The held-out test is evaluated only after selection. The threshold used for the final binary test result is fixed from validation.

## Operator re-ranking on robust validation

Top configurations with global median3 conditioning and oriented descriptors:

| Rank | Operator | ROI q | ODS | OIS | AP |
|---:|---|---:|---:|---:|---:|
| 1 | CF1F2(CL,CL) | 0.60 | 0.91336 | 0.91426 | 0.94388 |
| 2 | CC(CL) | 0.60 | 0.91336 | 0.91426 | 0.94387 |
| 3 | CF1F2(TM,CL) | 0.60 | 0.91069 | 0.90822 | 0.93832 |
| 4 | CF1F2(TM,OmM) | 0.60 | 0.90620 | 0.90378 | 0.92877 |
| 5 | CF1F2(TM,TM) | 0.60 | 0.90518 | 0.90067 | 0.93102 |

## Conditioning experiment

Preconditioning before MFI was compared using the validation set. The best setting was **median 3x3**.

| Precondition | ROI q | ODS | OIS | AP | R50 |
|---|---:|---:|---:|---:|---:|
| **median3** | **0.60** | **0.91336** | **0.93131** | **0.95414** | **0.97018** |
| gaussian sigma=0.6 | 0.60 | 0.85988 | 0.88561 | 0.88914 | 0.94142 |
| box3 | 0.60 | 0.84215 | 0.85898 | 0.87644 | 0.91708 |
| none | 0.60 | 0.82727 | 0.88837 | 0.83137 | 0.93380 |

The result is particularly compatible with a benchmark containing impulse noise: a robust median preconditioner removes isolated corruptions without the same degree of edge spreading caused by isotropic averaging.

### Conditioning only inside the MFI ROI

After median3 preconditioning, an additional ROI-only conditioning stage was tested.

| ROI conditioner | ODS | OIS | AP |
|---|---:|---:|---:|
| **none** | **0.91336** | **0.93131** | 0.95414 |
| median3 | 0.90846 | 0.92619 | **0.95533** |
| mean shift | 0.89287 | 0.92792 | 0.93986 |
| gravitational S4-like | 0.89011 | 0.91293 | 0.93788 |
| gravitational S3-like | 0.88079 | 0.90775 | 0.92429 |
| bilateral | 0.87598 | 0.89111 | 0.93324 |
| anisotropic diffusion | 0.86631 | 0.88500 | 0.93012 |

Thus, **the second strong smoothing stage was not selected**: median3 before MFI was enough for the current benchmark. The gravitational variants remain useful ablations but do not win here.

The gravitational implementation in this repository is explicitly a stable grayscale adaptation of the published spatial-colour gravitational mechanism, not a claim of bit-for-bit reproduction of the authors' original RGB implementation.

## ROI-only computation cost

On a small 96x96 subset, sparse/tiled ROI filtering did not automatically provide speedup because tile/halo and Python overhead dominate. The only tested conditioner with a clear filtering-stage gain was bilateral (~1.98x). Cheap filters were faster on the whole tiny image. The gravitational Python implementation was also slower in tiled form.

This means ROI-only conditioning is **not currently claimed as a general computational speedup**. It remains a promising implementation strategy for larger images, smaller ROI fractions, and optimized C++/GPU kernels.

## Edge linking experiment

The new MFI-guided geodesic linker connects nearby endpoints only when a minimum-cost path is supported by detector evidence, MFI confidence and orientation consistency.

Path cost:

```text
cost = alpha*(1-Scharr) + beta*(1-MFI confidence) + gamma*orientation mismatch
```

Best validation linker: `max_gap=8`, `max_mean_cost=0.60`.

| Linking | ODS | Recall | mean GT components | largest-component GT coverage | endpoints |
|---|---:|---:|---:|---:|---:|
| **MFI geodesic** | **0.91975** | **0.85195** | **5.18** | **0.53684** | **7.95** |
| none | 0.91336 | 0.84085 | 13.68 | 0.30312 | 24.25 |
| closing r=2 | 0.91181 | 0.83830 | 12.83 | 0.31719 | 22.98 |

The improvement in F score is modest, but the connectivity gain is large. This is exactly the behaviour expected from a linking stage: it repairs gaps without indiscriminately thickening the entire boundary map.

## Held-out test — 60 unseen synthetic images

Selected only from validation:

- precondition: median3
- MFI features: oriented
- MFI aggregation: CF1F2(CL,CL), q=0.1
- scales: 25,13,7,5,3
- MFI ROI q: 0.60 (top 40%)
- localizer: Scharr + NMS
- linker: MFI-geodesic, gap=8, cost=0.60
- binary threshold: fixed validation threshold = 1.0

Final held-out result:

| Precision | Recall | F1 |
|---:|---:|---:|
| **0.99716** | **0.84202** | **0.91304** |

Connectivity on held-out test:

- largest-component GT coverage: **0.47717**
- mean GT-overlapping edge components: **5.77**
- mean endpoints: **9.0**

Without linking at the same fixed threshold:

- precision 0.99750
- recall 0.83160
- F1 0.90703
- largest-component GT coverage 0.28274
- components 12.07
- endpoints 21.23

So geodesic linking gives +0.0060 absolute F1 and +0.0104 recall while nearly doubling the fraction of the GT captured by the dominant connected component.

## Continuous-score comparison on held-out test

Before binary linking, the MFI-gated continuous response was evaluated with the same development metric sweep as the classical baselines.

| Method | ODS | OIS | AP | R50 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| **MFI-Edge-SCHARR** | **0.90703** | **0.92383** | **0.96024** | **0.96927** | **0.71896** |
| Sobel | 0.86314 | 0.90892 | 0.88483 | 0.94666 | 0.65445 |
| Prewitt | 0.84738 | 0.89760 | 0.87980 | 0.94693 | 0.60975 |
| Scharr | 0.82563 | 0.89478 | 0.80825 | 0.91293 | 0.67792 |

The hybrid architecture therefore outperforms the tested standalone classical detectors on this held-out synthetic robustness benchmark.

## Robustness by degradation family — final fixed-threshold linked method

| Family | F1 |
|---|---:|
| salt-and-pepper | **0.99490** |
| clean | 0.98139 |
| illumination | 0.96717 |
| blur | 0.94000 |
| Gaussian noise | 0.93463 |
| artificial gaps | 0.92972 |
| speckle | 0.92429 |
| texture | 0.82715 |
| compound | 0.78601 |
| motion blur | 0.76868 |

Current weak points are therefore **motion blur, compound degradation, and textured backgrounds**. These should drive the next benchmark rather than further tuning on easy clean primitives.

## Example where connectivity metrics reveal an improvement hidden by F1

For a held-out rectangle-gap sample, the pre-link and post-link maps have essentially the same tolerant F1, but the topology changes dramatically:

- before: 19 GT-overlapping components, largest-component coverage 0.0861, 38 endpoints
- after: 1 GT-overlapping component, largest-component coverage 0.8975, 2 endpoints

This demonstrates why boundary continuity must be reported alongside pixel/boundary F scores when evaluating edge linking.

## Important evaluation caveats

1. ODS/OIS/AP here use the project's fast tolerant boundary proxy, not the official BSDS bipartite boundary matcher.
2. The synthetic validation/test split prevents parameter selection on the held-out set, but natural-image validation is still required.
3. The current empirical H0/self-calibration is a development mechanism. A paper-grade model should calibrate H0 only on training data and freeze it before validation/test.
4. The current power fuzzy measure is cardinality-only and does not learn feature-specific interactions.
5. The MFI ROI is a percentile-confidence/ranking map, not a calibrated posterior probability.

## Current conclusion

The strongest development result so far supports a four-stage interpretation:

**conditioning -> MFI proposal -> classical localization -> MFI-guided linking**.

MFI is most useful as a spatial evidence/proposal mechanism. Scharr supplies one-pixel localization, and geodesic linking uses the MFI confidence again to repair short gaps with strong geometric/evidential support.
