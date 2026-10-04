# Stage 6 — UDED fixed-threshold natural-image benchmark

Date: 2026-10-04

## Protocol

This experiment evaluates MFI-guided fusion on the 30-image UDED set using a stricter selection/held-out protocol.

- Images resized to max side 256 px.
- Alternating original UDED order split: 15 selection / 15 held-out.
- For every score/fusion variant, the binary threshold is selected **only on the selection half**, frozen, and then applied once to held-out.
- Primary boundary metric uses the project's tolerant dilation proxy with tolerance proportional to image diagonal (`frac_diag=0.0075`). This is **not** the official Berkeley bipartite matcher.
- Paired bootstrap on the held-out images: 5000 resamples.
- Baseline: Scharr + NMS.
- MFI variants use the learned/adaptive fuzzy-measure bank produced by the synthetic training/validation pipeline and are fused with the Scharr score through residual/soft fusion rules.

## Baseline

Selection:

- threshold = 0.1050051764
- ODS = 0.76642145
- OIS = 0.77921163
- AP = 0.76412345
- R50 = 0.97783928

Frozen-threshold held-out:

- precision = 0.66712117
- recall = 0.88845593
- F1 = **0.76204228**
- mean image F1 = 0.76963771

## Best selection-ranked MFI configuration

`power_q0.2 + residual(lambda=0.25)`

Selection:

- threshold = 0.1030298681
- ODS = 0.76592529
- OIS = 0.77873835
- AP = 0.75040284
- R50 = 0.97775788

Frozen-threshold held-out:

- precision = 0.66762488
- recall = 0.88771578
- F1 = **0.76209818**
- delta vs Scharr baseline = **+0.00005590**

Paired bootstrap delta F1:

- mean delta = +0.00006491
- 95% CI = **[-0.00225959, +0.00261458]**
- P(delta > 0) = 0.5026

Therefore there is no evidence that this selection winner improves on Scharr under the current held-out protocol.

## Most promising adaptive/contextual configuration

`context_additive_estimated + residual(lambda=0.25)`

Selection ODS = 0.76425768.

Frozen-threshold held-out:

- precision = 0.67025544
- recall = 0.88697564
- F1 = **0.76353504**
- delta vs Scharr baseline = **+0.00149276**

Paired bootstrap delta F1:

- mean delta = +0.00146496
- 95% CI = **[-0.00080449, +0.00394975]**
- P(delta > 0) = **0.8910**

This is the strongest positive signal observed in the bootstrap top-5, but its 95% interval still crosses zero; it is therefore promising rather than statistically established.

## Other fixed-threshold held-out examples

| Measure / strategy | Held-out F1 | Delta vs baseline |
|---|---:|---:|
| context_additive_estimated + residual 0.50 | **0.76433821** | **+0.00229593** |
| context_additive_estimated + residual 0.25 | 0.76353504 | +0.00149276 |
| sugeno 1.40 + residual 0.50 | 0.76327169 | +0.00122940 |
| sugeno 1.40 + residual 0.25 | 0.76318020 | +0.00113791 |
| additive_learned + residual 0.25 | 0.76282003 | +0.00077775 |
| power q=0.2 + residual 0.25 | 0.76209818 | +0.00005590 |
| Scharr baseline | 0.76204228 | 0 |

Note: the table above includes configurations not necessarily in the bootstrap top-5 selected by selection ODS. The largest held-out delta must not be treated as an unbiased winner because choosing it after observing held-out would be test-set selection.

## Main interpretation

1. The very large synthetic gains do **not** transfer directly to UDED natural images.
2. MFI remains informative: learned/contextual measures assign substantially higher confidence to GT edge pixels than simple `power_q0.2` in this run (roughly 0.69–0.70 vs 0.58), but the present score-fusion mechanism converts only a small part of that ranking advantage into F1.
3. The selection-best `power_q0.2` fusion is essentially tied with Scharr on held-out.
4. `context_additive_estimated` shows a consistent positive direction and deserves a dedicated natural-image tuning protocol, but the present 15-image held-out split is too small to establish superiority.
5. The next natural-image experiments should focus on **how MFI is injected** (gating, residual prior, threshold conditioning, linking, and scale-specific confidence), not only on changing the fuzzy capacity.

## Caveats

- 15/15 is a small split.
- Bootstrap is paired but cannot replace repeated splits or cross-validation.
- Evaluation uses a tolerant dilation proxy rather than official BSDS-style bipartite boundary matching.
- Images are resized to <=256 px.
- Learned fuzzy measures were obtained from the synthetic development pipeline, so this experiment primarily measures cross-domain transfer rather than natural-image-trained adaptation.
