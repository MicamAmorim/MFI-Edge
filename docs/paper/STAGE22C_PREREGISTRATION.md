# Stage 22C preregistration — inter-image score calibration diagnosis

## Status and scope

This is scientific stage 3/5 of the finite Stage-22 program. It is a frozen-
artifact diagnostic, not a detector experiment. It may not fit, regenerate,
select, promote, or alter a detector, rerun a matcher, read BSDS500 test, or
change the compact-MFI incumbent. It uses only the exact compact-MFI and
Stage-20C BSDS500-validation maps, the existing standard-Berkeley per-image
count tables, validation annotations for diagnostic labels, and validation
images for fixed image-regime summaries.

## Fixed inputs

- compact distorted-Choquet MFI frozen validation maps;
- Stage-20C dominant-pair 2-additive Choquet frozen validation maps;
- Stage-21B standard-Berkeley `maxDist=0.0075`, `nthresh=99`, thinning-on
  per-image count tables (no matcher rerun);
- all BSDS500-validation human annotations, used only for the diagnostics
  declared below;
- fixed preview positions 1, 50, and 100.

Reference reproduction remains unverified. All Stage-22C AP quantities derived
from tolerant-union pixels or resampled count curves are diagnostic and are
not substituted for official Berkeley AP.

## Required analyses

For each method and image, report serialized-score positive-support density,
entropy, dynamic range, and quantiles 0.01/0.10/0.25/0.50/0.75/0.90/0.99,
together with the standard-Berkeley per-image best threshold and F. Report the
best-threshold variance and IQR. Relate best threshold to fixed score and image
regime measures (support density, ODS-threshold density, grayscale entropy,
mean gradient, and gradient q90) and to Stage-20C changes in per-image best F
and diagnostic precision-envelope area using Spearman correlation.

Decompose ranking into pooled tolerant-union AUC/AP and the mean per-image
AUC/AP at the standard `0.0075` diagonal tolerance. The fixed cross-image
ranking discrepancy is `mean(within-image AUC) - pooled AUC`.

The GT-derived oracle is an upper-bound diagnostic only. Two complementary
views are fixed. First, map each image's per-image best standard-Berkeley
threshold to 0.5 by the unique continuous piecewise-linear monotone transform
fixing 0 and 1, then aggregate the frozen count tables over a common 99-point
grid. Second, fit the exact per-image monotone least-squares isotonic mapping
from serialized score level to tolerant-union boundary probability and measure
pooled pixel AP. The latter is the `oracle diagnostic AP` in the dominance
score. Both use validation GT, are forbidden as candidates, and are described
as recoverability bounds rather than deployable estimates.

Evaluate these fixed unlabeled, image-internal monotone transformations only as
diagnostic simulations against tolerant-union labels: identity, empirical-CDF
midrank, q01–q99 clipping, mean/standard-deviation logistic scaling, and
median/MAD logistic scaling. No simulation is selected, promoted, or carried
to Stage 22E from its validation result.

## Calibration-dominance statistic frozen before inspection

The decision statistic is computed for Stage 20C only:

1. `threshold_dispersion_component = clip(IQR(per-image best threshold)/0.20, 0, 1)`;
2. `oracle_recovery_component = clip((oracle diagnostic AP - raw diagnostic AP)/0.02, 0, 1)`;
3. `cross_image_rank_component = clip((mean within-image AUC - pooled AUC)/0.05, 0, 1)`;
4. `calibration_dominance_score` is the arithmetic mean of the three components.

Calibration is declared dominant only when the score is at least `0.60` and at
least two components are at least `0.50`. These constants cannot change after
Stage 22C. Stage 22C alone chooses no candidate: Stage 22D must independently
compute its preregistered NMS/competition-dominance score, after which Stage
22E follows the mechanical branch rule in the Stage-22 program.

## Outputs and continuation

The runner must write machine-readable per-image score/threshold tables,
association, rank-decomposition, oracle-rescaling, normalization-simulation,
and dominance-component tables; `summary.json`; the canonical fixed-position
`best_method_preview.png`; and a documentary official-evaluation manifest that
exports the unchanged Stage-20C maps. Completion registers only Stage 22D.
