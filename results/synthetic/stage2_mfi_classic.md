> **SUPERSEDED DATA WARNING (2026-10-04):** the original synthetic diagonal ground truth had a slope mismatch relative to the generated image boundary. Numerical results below are preserved for history but must not be used as current benchmark results. See `results/synthetic/stage3_orientation.md` and re-run the full sweep on the corrected dataset.\n\n# Stage 2 — MFI-gated classical edge detectors

Date: 2026-10-04

## Idea

The MFI map is now used as a proposal/attention stage instead of the final edge map.

1. Compute MFI-Edge with the Stage-1 winner: CF1F2(CL, CL), q=0.1, scales 33,25,17,11,7,5,3.
2. Convert the MFI surprisal map to a within-image percentile confidence map.
3. Build a binary ROI from the highest MFI-confidence region.
4. Apply a classical edge detector only inside that ROI.
5. Apply NMS to the continuous classical response where applicable.
6. Evaluate ODS, OIS, AP, R50 and ROC-AUC with the current synthetic tol=2 proxy.

Important: the percentile confidence is a rank/confidence map, not a calibrated posterior probability.

## Sweep

ROI percentile thresholds:
0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95

ROI dilation:
0, 1, 2, 3, 5 pixels

Gating:
hard and soft

Classical detectors:
Sobel, Scharr, Prewitt, Roberts, Laplacian, LoG, Gaussian gradient and Canny.

LoG/Gaussian-gradient sigmas:
0.8, 1.0, 1.4, 2.0

## Best continuous hybrid methods

| Method | ROI q | dilation | ODS | OIS | AP | R50 | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| MFI-Edge-SCHARR | 0.70 | 0 | 0.8759 | 0.8438 | 0.8116 | 0.9053 | 0.7771 |
| MFI-Edge-LoG | 0.70 | 0 | 0.8758 | 0.8469 | 0.8062 | 0.9244 | 0.7580 |
| MFI-Edge-SOBEL | 0.70 | 0 | 0.8738 | 0.8424 | 0.8131 | 0.8982 | 0.7797 |
| MFI-Edge-GaussianGrad | 0.70 | 0 | 0.8715 | 0.8399 | 0.8093 | 0.8942 | 0.7871 |
| MFI-Edge-PREWITT | 0.70 | 0 | 0.8708 | 0.8417 | 0.8164 | 0.8894 | 0.7779 |
| MFI-Edge-ROBERTS | 0.70 | 0 | 0.8272 | 0.8001 | 0.7169 | 0.9236 | 0.6381 |
| MFI-Edge-LAPLACIAN | 0.80 | 0 | 0.7323 | 0.6982 | 0.6067 | 0.8290 | 0.7422 |

Stage-1 MFI-only reference:
ODS 0.4190, OIS 0.3844, AP 0.2780.

## MFI gain over the matching classical detector

| Detector | Delta ODS | Delta OIS | Delta AP | Delta ROC-AUC |
|---|---:|---:|---:|---:|
| Scharr | +0.0000 | +0.0000 | +0.0147 | +0.0421 |
| Sobel | +0.0000 | +0.0000 | +0.0146 | +0.0427 |
| Prewitt | +0.0000 | +0.0000 | +0.0146 | +0.0451 |
| LoG | +0.0025 | +0.0027 | +0.0115 | +0.0452 |
| Gaussian gradient | +0.0000 | +0.0000 | +0.0117 | +0.0400 |
| Roberts | +0.0169 | +0.0200 | +0.0399 | +0.0646 |
| Laplacian | +0.0996 | +0.0983 | +0.1406 | +0.0523 |

The strongest effect of MFI gating is not necessarily on the single best F threshold. For already-strong gradient detectors, ODS is saturated on this simple synthetic set, while AP and ROC-AUC improve because MFI suppresses background responses over the full operating range.

## Tuned Canny

A separate Canny sweep used the MFI ROI directly as Canny's mask, with sigma in 0.8,1.2,1.6 and several low/high quantile threshold pairs.

Best tested MFI-Edge-CANNY:
- ROI q = 0.80
- dilation = 0
- sigma = 1.6
- low = 0.20
- high = 0.40
- ODS = 0.5927
- OIS = 0.6351
- AP = 0.4197
- recall at ODS = 0.9244

The Canny AP is based on the discrete low/high threshold sweep, so it should be treated as a family/grid AP proxy rather than directly equated to the continuous-response AP above.

## Main conclusion

The hybrid architecture is substantially stronger than using MFI as the final edge map. MFI works better here as an attention/proposal mechanism, while the classical detector performs precise localization.

The current Stage-2 winner by ODS is MFI-Edge-SCHARR. By AP, MFI-Edge-PREWITT is slightly higher (0.8164), while MFI-Edge-LoG has the highest OIS (0.8469) and R50 (0.9244).

These are development metrics on the five synthetic images and use the current tolerant proxy. They are not yet official BSDS500-comparable numbers.
