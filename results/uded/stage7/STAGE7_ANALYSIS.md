# UDED Stage 7 — family/generalization analysis

The exhaustive Stage-7 sweep evaluated **1,575 configurations** = 35 fuzzy-measure variants × 45 fusion/controller configurations on UDED, with threshold chosen on the natural-image selection split and frozen for the held-out split.

## Baseline

- Scharr+NMS selection ODS: **0.766421**
- Scharr+NMS frozen held-out F1: **0.762042**

## Valid selection winner

**local_additive_evidence + soft_e0.25_g0.5**

- selection ODS: **0.770589**
- held-out F1: **0.756437**
- selection gain vs Scharr: **+0.004167**
- held-out delta vs Scharr: **-0.005605**
- transfer gap: **-0.009772**

The bootstrap top-10 exactly matches the Stage-7 selection top-10. The selected winner does not beat Scharr on held-out.

## Held-out diagnostic only — not model selection

The strongest held-out row was **context_additive_estimated + soft_e0.50_g2**:

- selection ODS: **0.760246**
- held-out F1: **0.765044**
- held-out delta vs Scharr: **+0.003002**

This row is post-hoc and must not be relabeled as the selected winner. It is useful as a hypothesis for the next experiment.

## Main family signal

Only **12.7%** of all Stage-7 configurations beat Scharr on the held-out split. Median held-out delta over all 1,575 configurations was **-0.023068** and mean delta was **-0.055415**. This confirms that direct MFI modulation can easily over-constrain the detector.

The most robust fusion family in aggregate was **residual modulation**:

- 140 configurations
- mean held-out delta: **-0.000483**
- median held-out delta: **+0.000043**
- **55.7%** of residual configurations beat Scharr
- best post-hoc held-out F1 within the family: **0.764461**

`adaptive_exp` was next-best among the direct controller families, while `rank`, the current `geodesic`, and hard proposal-style gating were substantially less robust on natural images.

The context-conditioned fuzzy family is notable despite not winning selection: **28.9%** of its configurations beat Scharr on held-out, and its best rows dominate the post-hoc held-out list. This motivates Stage 8's local heterogeneity controller and mixture-of-measures router.

## Interpretation

Stage 7 suggests that the problem is not simply whether MFI contains useful edge evidence. The key issue is how strongly and where that evidence should alter the final detector. Mild residual/contextual modulation generalizes much better than aggressive hard gating or current topology linking.

Stage 8 therefore keeps all non-oracle fuzzy measures in competition, introduces an explicit local heterogeneity map, adds heterogeneity-aware residual/exponential/soft controllers, replaces the previous linking rule with a contextual hysteresis rule, and adds a local mixture-of-measures router. To reduce repeated selection overfitting, candidate ranking is based on 3-fold inner cross-validation within the 15-image selection half; held-out is evaluated only for the selection-ranked finalists.
