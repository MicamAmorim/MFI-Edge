# Stage 22E preregistration — positive-support quantile-reference calibration

## Status and causal branch

This is scientific stage 5/5 of the finite Stage-22 program and its only
candidate experiment. Stage 22C declared inter-image calibration dominant
(`0.607122`, two of three components at least `0.50`), while Stage 22D found
local competition non-dominant (`0.007265`, zero components at least `0.50`).
The mechanical rule therefore selects Branch C. No second candidate, retry
with different scientific parameters, or Stage-23 continuation is authorized
from this result.

## Fixed candidate

The detector before final score calibration is exactly the frozen Stage-20C
dominant-pair pipeline: `gabor4_s13` and `semiglobal_changepoint`, fold-fitted
memberships, monotone 2-additive Choquet capacity, scalar context calibration,
the unchanged gate, and grayscale Scharr+NMS. Stage 22E changes only the scale
of the final continuous score map.

For each outer UDED training fold, compute the 255 midpoint quantiles
`q_k=(k+0.5)/255` of the strictly positive Stage-20C scores in every training
image. The reference quantile curve is the pointwise median of those per-image
curves, clipped below at `1/255` and made nondecreasing by cumulative maximum.
For a target image, zeros remain exactly zero. Each positive score is replaced
by the reference-curve value at its average empirical midrank among positive
pixels. Ties receive the same value. Linear interpolation is fixed. Thus the
transform is unlabeled, image-internal, monotone, deterministic, and exactly
support-preserving; it changes cross-image score comparability but cannot
change within-image pixel ordering.

The transform family, 255-point grid, midpoint ranks, pointwise median,
interpolation, tie rule, `1/255` floor, and boundary behavior are frozen here
before candidate execution. They are selected for direct histogram
standardization and exact 8-bit support preservation, not from the Stage-22C
normalization-simulation outcomes. No validation statistic selects a family
or constant. For the official BSDS500-validation export, the reference curve
is fitted from the 14 overlap-clean UDED-selection training images only; no
BSDS validation image or annotation participates in fitting.

## Evaluation and contracts

UDED uses the established five-repeat by three-fold overlap-clean protocol,
excluding `03-35028` without reading its protected-lineage bytes. All
Stage-20C model parameters and the new reference curve are fitted strictly
inside each outer training fold. Candidate and compact-incumbent thresholds
are fitted independently on the unchanged 41-point training grid.

The following must hold in addition to finite bounded output:

- exact positive-support equality with compact MFI on every scored image;
- no within-image ordering inversion, including deterministic tie handling;
- bitwise repeatability of the standardization;
- all 15 capacity fits converge;
- fixed overlap-clean UDED preview positions 1, 7, and 14 are emitted as
  `best_method_preview.png`.

Promotion is conjunctive and unchanged from the Stage-22 program:

- UDED aggregate F1 delta at least `+0.002` versus compact MFI;
- aggregate precision delta nonnegative;
- aggregate recall delta at least `-0.003`;
- mean paired fold-F1 delta nonnegative and at least 9/15 fold wins;
- standard-Berkeley BSDS500-validation ODS delta at least `+0.002`, with
  nonnegative OIS and AP deltas;
- every fit, support, monotonicity, repeatability, preview, and evaluator
  contract passes.

Berkeley `0.025`, Estrada–Jepson/KITT `0.025`, and thesis-legacy scores are
non-promotional and cannot rescue a failure. Reference reproduction remains
unverified. Whether Stage 22E passes or fails, Stage 22 ends immediately with
`continue=false` and the required causal synthesis; no tuning pass follows.
