# Stage 5 — UDED: hard gating versus soft/residual MFI prior

Date: 2026-10-04

## Purpose

The first UDED transfer experiment showed that the synthetic-selected **hard MFI gate** removes too many valid natural-image edges. This follow-up tests the same MFI evidence as a softer prior over Scharr+NMS rather than as a binary deletion mask.

This is an exploratory natural-domain experiment. The learned fuzzy measures still come from the synthetic Stage-5 benchmark, but the 30 UDED images are now split deterministically into 15 selection images and 15 held-out images so that fusion strategy selection and held-out reporting are separated.

## Protocol

- UDED: 30 images from `xavysp/UDED`.
- Memory-safe evaluation: longest image side <= 256 px, aspect ratio preserved; GT nearest-neighbour resized.
- Base detector: median3 -> Scharr -> orientation-aware NMS.
- MFI: oriented descriptors, scales 25,13,7,5,3, `CF1F2(CL,CL)`.
- Fuzzy measures are learned/selected from synthetic data.
- Natural split: alternating original UDED order, 15 selection / 15 held-out.
- Metric: project tolerant boundary proxy at 0.75% of image diagonal, **not** the official Berkeley bipartite matcher.

Fusion families tested:

```text
hard gate:
    score = Scharr * 1[conf >= q]

soft multiplicative gate:
    score = Scharr * (eps + (1-eps)*conf^gamma)

residual prior:
    score = Scharr * clip(1 + lambda*(conf-0.5), 0.05, inf)

rank fusion:
    score = (1-alpha)*rank(Scharr) + alpha*conf
```

## Scharr-only reference

| Split | ODS | OIS | AP | R50 |
|---|---:|---:|---:|---:|
| Selection (15) | **0.766421** | 0.779212 | 0.764123 | 0.977839 |
| Held-out (15) | **0.759495** | **0.809222** | **0.821252** | **0.972288** |

## Selection result

The strongest selected MFI fusion was `power_q0.2 + residual(lambda=0.25)`:

| Measure | Fusion | ODS | OIS | AP | R50 |
|---|---|---:|---:|---:|---:|
| power_q0.2 | residual lambda=.25 | **0.765925** | 0.778738 | 0.750403 | 0.977758 |
| power_q0.2 | residual lambda=.50 | 0.765712 | 0.778742 | 0.748272 | 0.977432 |
| power_q0.2 | soft eps=.25 gamma=.5 | 0.765342 | 0.777368 | 0.747571 | 0.975357 |
| power_q0.2 | soft eps=.50 gamma=1 | 0.765166 | 0.777959 | 0.747936 | 0.976700 |
| context_additive_estimated | residual lambda=.25 | 0.764360 | 0.779338 | 0.754534 | 0.978450 |

Crucially, the best selected MFI fusion **did not beat the Scharr-only reference on the selection half**: 0.765925 versus 0.766421 ODS (delta = -0.000496). Therefore the selection data do not support a claim that MFI fusion is already superior to Scharr on natural images.

The qualitative pattern is nevertheless clear: **mild residual modulation dominates hard gating**. None of the hard-gate variants reached the selected top 20.

## Held-out result for configurations selected on the other half

The top selected configurations transfer as follows:

| Measure | Fusion | Selection ODS | Held-out ODS | Held-out OIS | Held-out AP | R50 |
|---|---|---:|---:|---:|---:|---:|
| context_additive_estimated | residual lambda=.50 | 0.761430 | **0.760600** | 0.807617 | 0.821424 | 0.971918 |
| context_additive_estimated | residual lambda=.25 | 0.764360 | 0.760337 | 0.808876 | **0.822138** | 0.972245 |
| additive_learned | residual lambda=.50 | 0.760262 | 0.760179 | 0.807306 | 0.818642 | 0.972027 |
| sugeno_learned_sum1.40 | residual lambda=.50 | 0.761775 | 0.760059 | 0.808287 | 0.819361 | 0.972049 |
| power_q0.2 | residual lambda=.25 | **0.765925** | 0.760040 | **0.809869** | 0.820039 | 0.972114 |

Compared with Scharr-only on the same held-out half:

- best held-out ODS among preselected configurations: **0.760600 vs 0.759495**, delta **+0.001106**;
- its AP: **0.821424 vs 0.821252**, delta **+0.000172**;
- its OIS: **0.807617 vs 0.809222**, delta **-0.001605**.

A second configuration, `context_additive_estimated + residual(lambda=.25)`, gives ODS +0.000842 and AP +0.000886 versus Scharr, while OIS is nearly tied (-0.000346).

`power_q0.2 + residual(lambda=.25)` gives ODS +0.000545 and OIS +0.000647, but AP -0.001213.

These differences are extremely small and should be interpreted as **statistical ties until a paired uncertainty/significance analysis is performed**.

## What changed from the hard-gate experiment

On all 30 UDED images, the earlier hard-gate experiment had:

- best MFI hard-gated ODS: `scale_additive_learned` = **0.737037**;
- Scharr+NMS ODS = **0.763802**.

Thus the hard gate lost about 0.0268 absolute ODS. The residual-prior experiment removes nearly all of that penalty: the best held-out residual configuration is essentially tied with raw Scharr and slightly above it in ODS.

This supports a stronger architectural interpretation:

> **MFI is useful on natural images as a confidence/prior field, not as an unconditional veto mask.**

The MFI signal can gently reweight detector evidence without deleting strong local edges that fall outside a synthetic-calibrated ROI.

## Measure behaviour across domains

The transfer pattern is also informative:

1. `sugeno_learned_sum1.40`, the synthetic-validation winner, was only rank 20 in the zero-shot hard-gate UDED test. This is direct evidence of a synthetic-to-natural domain gap.
2. Scale-specific learned measures were strongest under hard gating, suggesting scale-dependent descriptor reliability.
3. Under residual fusion, the context-estimated additive measure transfers well, while the simple `power_q0.2` is the best selection-half configuration. A more complex learned capacity is therefore not automatically better under domain shift.

## Current conclusion

There are now two distinct UDED findings:

- **zero-shot hard gate:** MFI hurts natural-image recall and underperforms Scharr;
- **natural selection / held-out soft-prior experiment:** mild MFI residual modulation recovers the baseline and is statistically indistinguishable from, or marginally better than, Scharr in ODS.

The next step should not be further aggressive ROI tuning. It should be:

1. paired bootstrap/confidence intervals for the residual-vs-Scharr difference;
2. MFI-guided geodesic linking on the natural selection/held-out split;
3. evaluation at original resolution with more memory;
4. official/compatible bipartite boundary matching before any comparison to published UDED ODS/OIS;
5. natural-image calibration of H0 and/or a train/validation protocol on BSDS/BIPED, while preserving UDED as a genuinely external generalization set.

## Reproducibility

Branch: `experiment/uded-railway`.

Fusion experiment code: `benchmark_uded_fusion.py`.

Railway experiment commit: `ddbe09094fae86e76427c09d21c014d56a653014`.

Completion markers observed in the run:

```text
UDED_FUSION_V1_DONE
UDED_FUSION_PIPELINE_DONE
```
