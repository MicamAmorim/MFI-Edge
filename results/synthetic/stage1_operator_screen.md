# Synthetic benchmark — Stage 1 operator screen

Date: 2026-10-04

This is the first exhaustive screen over the aggregation operator families on the five deterministic synthetic test images.

## Fixed settings

- Scales: 33, 25, 17, 11, 7, 5, 3
- Power-measure parameter: q = 0.1
- Refine quantile: 0.82
- Heterogeneity quantile: 0.82
- Refinement dilation radius: 3
- Evaluation protocol: SEval-like, with non-maximum suppression
- Spatial tolerance: 2 pixels
- Threshold sweep: 25 quantile-spaced thresholds
- Operators screened: 183
  - 21 CF variants
  - 14 CC variants from the prototype's copula/overlap-like subset
  - 148 numerically admissible CF1F2 pairs

## Current ranking

| Rank | Operator | ODS | OIS | AP | ROC-AUC |
|---:|---|---:|---:|---:|---:|
| 1 | CF1F2_CL_CL | 0.4190 | 0.3844 | 0.2780 | 0.9109 |
| 2 | CC_CL | 0.3688 | 0.3479 | 0.2335 | 0.8891 |
| 3 | CF_CL | 0.3385 | 0.2598 | 0.2180 | 0.8767 |
| 4 | CF1F2_CL_TL | 0.2650 | 0.2659 | 0.1553 | 0.8283 |
| 5 | CF1F2_TM_TM | 0.2528 | 0.1820 | 0.1542 | 0.8362 |
| 6 | CF1F2_TM_FNA | 0.2528 | 0.1820 | 0.1542 | 0.8362 |
| 7 | CC_TM | 0.2496 | 0.1804 | 0.1516 | 0.8351 |
| 8 | CF1F2_TM_CL | 0.2356 | 0.1738 | 0.1345 | 0.8347 |
| 9 | CC_TDP | 0.1998 | 0.1305 | 0.1132 | 0.7445 |
| 10 | CF1F2_TDP_TDP | 0.1998 | 0.1305 | 0.1132 | 0.7445 |

## Interpretation

The preliminary winner is **CF1F2(CL, CL)**. It also leads the raw/no-NMS ranking, so its advantage is not only a post-processing artefact.

These values are for the synthetic benchmark only. They are useful for selecting and ablating the method, but they are **not numerically comparable with published BSDS500 results** until the detector is run on the same BSDS500 split with the official boundary matching/evaluation protocol.

The next sweep should vary q, scale sets, refinement thresholds, and post-processing for the leading operators before moving to BSDS500.
