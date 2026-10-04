# Stage 5 — preliminary fuzzy-measure competition

Date: 2026-10-04

## Goal

Keep multiple fuzzy-measure formulations alive as competing MFI variants rather than prematurely selecting one. The fuzzy measure is now an explicit experimental axis of MFI-Edge.

Implemented families include:

- symmetric power capacities across a q grid;
- SWAFED-inspired local adaptive power capacities (max, min, product, mean, geometric mean, harmonic mean, Lukasiewicz, Hamacher, ODiv and dispersion);
- heterogeneity-conditioned power capacities;
- uniform and learned additive capacities;
- locally adaptive additive weights (evidence, softmax and reliability);
- Sugeno lambda capacities with learned singleton densities;
- constrained learned 2-additive capacities;
- constrained learned full capacities (n<=8, optional expensive run);
- scale-dependent learned capacity banks;
- context/degradation-conditioned capacity banks with both oracle and image-estimated routing;
- Shapley-value and pair-interaction diagnostics.

All non-symmetric capacities preserve descriptor identity after sorting by evaluating the actual nested coalitions A_(i), rather than reducing the measure to subset cardinality.

## Experimental protocol for this preliminary screen

- synthetic benchmark v2;
- original validation split divided deterministically into 20 capacity-fit images + 20 model-selection images;
- 60-image held-out test retained separately;
- median 3x3 preconditioning;
- oriented descriptors;
- scales 25,13,7,5,3;
- CF1F2(CL,CL) aggregation for the measure-only screen;
- Scharr + NMS localization;
- MFI ROI gating;
- prototype tolerant boundary evaluation (not official BSDS matching).

The preliminary core screen used ROI q=0.55 across 34 measure variants. The repository benchmark now sweeps ROI q = 0.50...0.85 and includes additional heavier scale/context 2-additive and full-capacity variants.

## Validation screen — leading core variants

| Measure | ODS | OIS | AP | R50 | ROI GT coverage |
|---|---:|---:|---:|---:|---:|
| Sugeno lambda, learned singleton densities, sum=0.60 | **0.9141** | **0.9212** | **0.9524** | **0.9758** | **0.9901** |
| Power q=1.5 | 0.9137 | 0.9205 | 0.9498 | 0.9712 | 0.9817 |
| Power q=0.1 | 0.9131 | 0.9199 | 0.9486 | 0.9696 | 0.9707 |
| Power q=0.4 | 0.9128 | 0.9192 | 0.9484 | 0.9694 | 0.9754 |
| Power q=0.2 | 0.9123 | 0.9202 | 0.9497 | 0.9722 | 0.9823 |
| Sugeno lambda sum=0.80 | 0.9093 | 0.9139 | 0.9464 | 0.9686 | 0.9811 |
| learned 2-additive | 0.9079 | 0.9134 | 0.9443 | 0.9666 | 0.9796 |
| learned additive | 0.9063 | 0.9113 | 0.9422 | 0.9633 | 0.9779 |

The first important result is that the original q=0.1 power measure is no longer assumed to be optimal. A less concave power capacity (q around 1.5) and a learned Sugeno-lambda capacity are at least as competitive in this harder benchmark.

## Held-out diagnostic for the leading fixed/preselected families

Using ROI q=0.55 and fitting the Sugeno singleton densities only on the 20 fit images:

| Measure | ODS | OIS | AP | R50 | ROC-AUC | ROI GT coverage |
|---|---:|---:|---:|---:|---:|---:|
| **Power q=1.5** | **0.9209** | **0.9215** | **0.9578** | **0.9830** | **0.7344** | **0.9900** |
| Sugeno lambda sum=0.60 | 0.9199 | 0.9208 | 0.9564 | 0.9790 | 0.7331 | 0.9884 |
| Power q=0.2 | 0.9192 | 0.9193 | 0.9543 | 0.9744 | 0.7327 | 0.9794 |
| Power q=0.1 | 0.9178 | 0.9116 | 0.9510 | 0.9693 | 0.7319 | 0.9687 |

This held-out diagnostic is intentionally not used to retune the variants. The difference between q=1.5 and learned Sugeno is small, so neither should be discarded.

## Learned Sugeno capacity

For the sum=0.60 variant, learned singleton densities on the fit split were approximately:

| Descriptor | density | Shapley |
|---|---:|---:|
| grad | 0.0964 | 0.1585 |
| laplacian | 0.0574 | 0.0981 |
| hessian | 0.0603 | 0.1029 |
| coherence_iso | 0.0338 | 0.0592 |
| normal_contrast | **0.1050** | **0.1711** |
| normal_minus_tangent | **0.1045** | **0.1705** |
| steered_hessian | 0.0577 | 0.0986 |
| gabor4 | 0.0849 | 0.1412 |

The resulting Sugeno lambda is approximately +1.93, producing a non-additive superadditive capacity from singleton densities whose sum is 0.60.

## Preliminary 2-additive interpretation

One constrained 2-additive fit concentrated Shapley importance on:

- normal_contrast: ~0.472;
- normal_minus_tangent: ~0.264;
- gabor4: ~0.264.

The strongest pair interactions were negative (redundancy), especially normal_contrast with gabor4 and normal_contrast with normal_minus_tangent. This is an exploratory diagnostic, not yet a stable scientific conclusion; larger fit splits and bootstrap intervals are needed.

## Adaptive-q result

Directly transferring the sliding-window adaptive-q idea to the current descriptor vector did not beat the best fixed/learned capacities in the first global screen. This does **not** reject adaptive measures: the original SWAFED mechanism adapts q from neighbourhood-difference structure, whereas the current MFI variant adapts q from the descriptor vector. These are different objects. The variants remain in the registry for the full factorial study and for condition-specific analysis.

## Next exhaustive search

`benchmark_measure_operator_factorial.py` crosses:

- all aggregation/operator specifications already defined by MFI-Edge;
- all registered fixed/adaptive/learned fuzzy measures;
- the expanded MFI ROI grid;

and supports chunked execution/resume. With 183 aggregation specifications, approximately 38 measure variants when the full learned capacity is enabled, and 8 ROI thresholds, the fuzzy-layer-only space is already about **55,632 configurations** before adding conditioning, descriptor mode, scale schedules, final localizer and linking variants.

The next stage should therefore preserve every variant in the registry while using chunked/tournament execution and a frozen held-out test to avoid model-selection leakage.
