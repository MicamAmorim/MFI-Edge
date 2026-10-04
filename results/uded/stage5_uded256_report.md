# Stage 5 — UDED natural-image generalization check

Date: 2026-10-04

## Goal

Evaluate whether the Stage-5 fuzzy-measure variants selected/fit **only on synthetic data** retain useful behaviour on a natural-image dataset without adapting the model to UDED.

Dataset: **UDED — Unified Dataset for Edge Detection** (`xavysp/UDED`), 30 test images with perceptual edge ground truth.

The UDED test is intentionally treated as evaluation-only. No UDED label is used for learning fuzzy measures, context routers or the MFI ROI threshold.

## Evaluation setup used in this run

Because the first full-resolution Railway attempt exceeded the available memory, this run downsamples only when necessary so the longest image side is at most 256 pixels, preserving aspect ratio; GT masks use nearest-neighbour resampling.

Pipeline:

```text
image
  -> median 3x3
  -> oriented multiscale MFI, scales 25,13,7,5,3
  -> fuzzy measure selected/fitted on synthetic benchmark only
  -> MFI confidence ROI using the ROI quantile selected on synthetic validation
  -> Scharr response
  -> orientation-aware NMS
  -> continuous edge score
```

Aggregation family: `CF1F2(CL,CL)`.

Important: this run uses the project fast tolerant boundary proxy (tolerance 0.75% of the image diagonal), not the official Berkeley bipartite boundary matcher. Therefore these values are for **internal generalization analysis**, not direct publication-grade comparison to UDED paper numbers.

## Main result

The strongest natural-image variant was **scale_additive_learned**:

| Metric | Value |
|---|---:|
| ODS | **0.737037** |
| OIS | **0.781368** |
| AP | **0.769530** |
| F0.5 ODS | **0.748800** |
| R50 | **0.821683** |
| ROC-AUC | 0.616130 |
| GT coverage by MFI ROI | **0.827239** |

The learned scale-specific capacity therefore generalized better than the global learned capacity, context router and the fixed power measures in this first UDED test.

## Top 20 fuzzy-measure variants on UDED

| Rank | Measure | Kind | Synthetic ROI q | ODS | OIS | AP | F0.5 ODS | R50 | ROI GT coverage |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | scale_additive_learned | scale_router | 0.50 | **0.737037** | 0.781368 | **0.769530** | **0.748800** | **0.821683** | 0.827239 |
| 2 | scale_2additive_learned | scale_router | 0.50 | 0.735316 | 0.779825 | 0.767183 | 0.748546 | 0.812649 | **0.829234** |
| 3 | sugeno_learned_sum0.60 | sugeno_lambda | 0.50 | 0.734774 | **0.781936** | 0.767823 | 0.747047 | 0.816161 | 0.826167 |
| 4 | context_additive_estimated | context_router | 0.50 | 0.732043 | 0.780714 | 0.766058 | 0.744416 | 0.815993 | 0.809797 |
| 5 | additive_learned | additive | 0.50 | 0.731765 | 0.781815 | 0.766218 | 0.744156 | 0.817308 | 0.812170 |
| 6 | sugeno_learned_sum1.00 | sugeno_lambda | 0.50 | 0.730710 | 0.781891 | 0.763844 | 0.744165 | 0.806296 | 0.825112 |
| 7 | power_q2 | power | 0.50 | 0.730238 | **0.784003** | 0.762186 | 0.742222 | 0.807558 | 0.826542 |
| 8 | context_2additive_estimated | context_router | 0.50 | 0.729432 | 0.781297 | 0.763591 | 0.743254 | 0.806327 | 0.816152 |
| 9 | power_q1 | power | 0.50 | 0.729129 | 0.781267 | 0.761168 | 0.743546 | 0.799302 | 0.817088 |
| 10 | additive_uniform | additive | 0.50 | 0.729129 | 0.781267 | 0.761168 | 0.743546 | 0.799302 | 0.817088 |
| 11 | sugeno_learned_sum0.80 | sugeno_lambda | 0.50 | 0.728839 | 0.781641 | 0.762935 | 0.742938 | 0.805454 | 0.824143 |
| 12 | 2additive_learned | two_additive | 0.50 | 0.728614 | 0.778612 | 0.760801 | 0.744290 | 0.794747 | 0.814765 |
| 13 | sugeno_learned_sum1.20 | sugeno_lambda | 0.50 | 0.727931 | 0.781739 | 0.761374 | 0.741938 | 0.800774 | 0.823189 |
| 14 | adaptive_power_dispersion | adaptive_power | 0.50 | 0.726767 | 0.782332 | 0.759334 | 0.741540 | 0.797019 | 0.816870 |
| 15 | power_q0.7 | power | 0.50 | 0.726514 | 0.777951 | 0.754482 | 0.741547 | 0.782295 | 0.791938 |
| 16 | power_q1.5 | power | 0.50 | 0.726103 | 0.783090 | 0.760172 | 0.740315 | 0.800111 | 0.825993 |
| 17 | hetero_power_inverse | heterogeneity_power | 0.50 | 0.720013 | 0.779845 | 0.752653 | 0.737142 | 0.777120 | 0.810600 |
| 18 | adaptive_power_max | adaptive_power | 0.50 | 0.715842 | 0.767498 | 0.748020 | 0.731928 | 0.783693 | 0.771507 |
| 19 | power_q0.4 | power | 0.50 | 0.702083 | 0.756399 | 0.726559 | 0.727804 | 0.724237 | 0.706954 |
| 20 | sugeno_learned_sum1.40 | sugeno_lambda | 0.60 | 0.697536 | 0.762666 | 0.739997 | 0.721378 | 0.669450 | 0.726595 |

## Classical baselines in the same internal protocol

| Method | ODS | OIS | AP | F0.5 ODS | R50 |
|---|---:|---:|---:|---:|---:|
| **Scharr + NMS** | **0.763802** | 0.802404 | **0.795898** | 0.758096 | **0.982425** |
| Prewitt + NMS | 0.763698 | 0.802485 | 0.794328 | 0.758150 | 0.981426 |
| Sobel + NMS | 0.763438 | **0.802508** | 0.794854 | **0.758456** | 0.981689 |
| Canny persistence | 0.666753 | 0.679847 | 0.584870 | 0.625708 | 0.912577 |

## Interpretation

This is a useful negative/diagnostic result rather than a failure of the whole MFI idea.

1. **The fuzzy MFI gate transfers to natural images, but it currently removes too many true natural edges.** The best MFI variant covers about 82.7% of GT edge neighbourhoods, while the raw Scharr response achieves much higher recall in this protocol.
2. **Scale-dependent learned measures transfer best.** This supports the hypothesis that the reliability of descriptors is scale-dependent and that one global capacity is too restrictive.
3. **The synthetic winner is not the natural-image winner.** `sugeno_learned_sum1.40`, which was strongest on synthetic validation, drops to rank 20 on UDED. This is direct evidence of a synthetic-to-natural domain gap and argues against selecting the final measure only on synthetic data.
4. **MFI is currently better interpreted as a proposal/prior than as a hard gate.** On synthetic data hard gating was highly effective; on UDED, hard gating caps recall. The next natural-image variant should use soft multiplicative/additive modulation or a hierarchical prior rather than zeroing the detector outside the ROI.
5. **The ranking itself is informative.** Learned scale routing, learned additive capacity, and moderate Sugeno capacities occupy the top positions; very aggressive learned Sugeno mass (`sum1.40`) generalizes poorly.

## Immediate next experiment

For UDED and later BSDS/BIPED, compare:

```text
A. hard gate:     score = Scharr * 1[conf >= q]
B. soft gate:     score = Scharr * (epsilon + (1-epsilon)*conf^gamma)
C. residual prior score = Scharr * (1 + lambda*(conf-0.5))
D. rank fusion:   weighted combination of Scharr rank and MFI rank
E. hierarchical:  MFI limits/refines candidate scales, but never deletes a strong Scharr edge outright
```

The validation target should explicitly optimize the precision-recall trade-off on a natural-image validation split, and the final paper evaluation should use the official/compatible bipartite boundary matching protocol.

## Reproducibility

Experiment branch: `experiment/uded-railway`.

Relevant scripts:

- `benchmark_uded.py` — full-resolution UDED runner.
- `benchmark_uded_quick.py` — memory-safe downscaled runner used for this result.
- `benchmark_measure_competition.py` — synthetic Stage-5 measure fitting/selection.

Successful memory-safe code commit before this report: `d9325d75a8d3569d4b497c38d4e7b1ec55605b85`.
