# Stage 12b — fuzzy signature results

## Protocol

Stage 12b kept **Scharr+NMS fixed as the spatial localizer** and replaced the Stage-12a weighted analytical signature with:

1. a positive boundary-evidence bank aggregated by a distorted-capacity Choquet integral;
2. an optional texture / anti-boundary bank;
3. dual combinations (`product`, `contrast`, `ratio`) controlling the fixed localizer.

The UDED development split remained 15 selection / 15 held-out. Feature banks and hyperparameters were derived from selection only.

## Primary selection result

The formally selection-ranked winner was:

`fuzzypos__g0.55__a2__floor0.1`

with:

- selection CV F1 = **0.764758**;
- selection ODS = **0.771850**;
- held-out F1 = **0.761234**;
- Scharr held-out F1 = **0.762042**;
- delta F1 = **-0.000809**;
- bootstrap 95% CI = **[-0.003805, 0.002827]**.

Therefore the formally selected positive-only fuzzy candidate does **not** beat Scharr.

## Important family-level signal

The top selection-ranked set nevertheless contains a strong and internally consistent dual-evidence pattern.

Among the seven configurations promoted to held-out by selection rank, five are dual models. Four of those five have paired-bootstrap confidence intervals entirely above zero:

| selection rank | configuration | delta F1 vs Scharr | 95% CI |
|---:|---|---:|---:|
| 2 | dual g=.55 product lambda=.35 a=2 | +0.002257 | [-0.001497, 0.005636] |
| 4 | dual g=.55 product lambda=.70 a=2 | **+0.005806** | **[0.000791, 0.011460]** |
| 5 | dual g=.55 product lambda=.70 a=1 | **+0.004746** | **[0.000983, 0.009209]** |
| 6 | dual g=1 product lambda=.35 a=2 | **+0.003619** | **[0.000931, 0.006484]** |
| 7 | dual g=.55 ratio lambda=1 a=2 | **+0.008162** | **[0.002532, 0.014814]** |

The rank-7 dual-ratio configuration reaches held-out F1 **0.770204**, with precision **0.678338** and recall **0.890851**.  This is the first Stage-12 family to show a simultaneous precision/recall improvement over Scharr in the inspected held-out subset.

This configuration must **not** be called the winner because it was not rank 1 on selection.  The scientifically valid observation is broader: **dual positive/texture evidence appears materially more promising than positive-only evidence.**

## Evidence-bank interpretation

The positive bank is dominated by Gabor and Hessian responses and multiscale Gabor relations.  The strongest positive feature is `gabor4_s5` (edge-v-texture AUC about 0.737).

The independent texture-oriented bank is weaker on individual AUC, but its strongest members are mostly **scale-location relations** rather than raw filter strengths:

- steered-Hessian scale centroid;
- Laplacian scale centroid;
- Hessian scale centroid;
- peak-fineness descriptors;
- normal-dominance / normal-tangent relations.

This is consistent with the hypothesis that texture differs from structural boundaries partly by **where across scale its curvature/orientation evidence concentrates**, not simply by raw response magnitude.

## Visual caveat

The saved Stage-12b `winner_preview.png` visualizes the formal selection winner, which is positive-only.  Its `Texture / anti` panel is therefore black by construction.  It should not be used to judge the dual family visually. Stage 12c will save a separate `best_dual_preview.png` selected without held-out re-ranking.

## Methodological issue discovered after Stage 12b

`cv_threshold_score` correctly fits thresholds out-of-fold.  However, Stage 12b constructed the positive/negative evidence banks once using **all 15 selection images before CV**.  Thus its reported `cv_F1` is threshold-leakage-free but **not feature-bank-selection-free**.

This does not contaminate the held-out evaluation, because held-out GT never entered bank construction.  It does mean that Stage-12b selection CV is optimistic and should not be used as final evidence for hyperparameter ordering.

## Decision

Proceed to **Stage 12c — leakage-free evidence-bank CV**:

- rebuild positive and negative banks inside every CV training fold;
- fit thresholds on training folds only;
- evaluate configurations on unseen validation folds;
- then refit on all selection data;
- use the repeatedly inspected UDED held-out set only as **development confirmation**.

Because UDED held-out has now influenced multiple architectural decisions, it is no longer defensible as a pristine publication test.  Final generalization claims must move to an untouched external protocol (BSDS500 and/or BIPED).

## Scientific implication

Stage 12b provides the first concrete evidence that the core fuzzy contribution may not be "more positive aggregation".  The more promising formulation is:

\[
C^+(x) = \text{boundary evidence},
\qquad
C^-(x) = \text{texture / anti-boundary evidence},
\]

followed by a contrastive or bipolar rule controlling a precise classical localizer.

A formal bipolar Choquet / bi-capacity model is therefore justified as a **conditional next step**, but only after Stage 12c confirms the dual-family signal under leakage-free selection.
