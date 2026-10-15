# Stage 17b preregistration - local nonparametric rank context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Bovik, Huang and Munson introduced nonparametric rank-sum statistics for edge
detection and reported effective behavior on both noisy and uncontaminated
images (*Nonparametric tests for edge detection in noise*, Pattern Recognition
19(3):209-219, 1986, DOI `10.1016/0031-3203(86)90011-7`). Smeraldi later
formalized normalized orientation-selective ranklets as Haar-like spatial
partitions evaluated with the Mann-Whitney statistic (*Ranklets:
orientation-selective non-parametric features applied to face detection*, ICPR
2002, DOI `10.1109/ICPR.2002.1047924`). The ranklet response is invariant to
strictly monotone gray-level transformations and has an immediate pairwise
ordering interpretation.

Stage 17b tests whether a compact local two-sample ordering statistic supplies
boundary evidence that transfers across UDED selection and BSDS500 validation.
It is not Stage 16p's image-wide empirical-CDF remapping of already calibrated
memberships, Stage 16j's parametric one-dimensional step-template fit, or Stage
14l's half-disc LBP-histogram distance. It makes no distributional or edge-shape
assumption, uses raw local intensity order only, and leaves the Scharr+NMS
localizer unchanged.

## Fixed candidate

On the unchanged median-conditioned grayscale image, use a radius-2 square
support. For each of four fixed partitions (left/right, top/bottom, and the two
diagonals), exclude the central separating line and compare the two ten-sample
half-neighborhoods. Each opposed sample pair contributes `+1`, `-1`, or `0`
according to its signed order; zero is equivalent to half credit for a tie in
the usual Mann-Whitney probability. Divide by the 100 sample pairs to obtain a
signed response in `[-1,1]`. The cue is the maximum absolute response over the
four orientations, in `[0,1]`.

Fit one positive logistic membership only inside each outer UDED-selection
training fold. Its midpoint is the mean of the training edge and texture
medians and its scale is the pooled training interquartile range, with only a
`1e-9` numerical floor. Fit its singleton weight by the established rule
`max(AUC-0.5,0) * (1+mutual_information)`. The cue is eligible only when
training edge-versus-texture AUC is at least `0.56`; an ineligible fold is
exactly the compact control. When eligible, append it as a sixth membership and
renormalize singleton weights before the unchanged distorted-Choquet integral.

The retained five memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
threshold grid are unchanged. There is no radius, orientation, scale,
partition, tie-rule, rank aggregation, membership, fusion, or threshold search.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Cue calibration,
  eligibility, singleton weight, compact-bank fitting, and operating threshold
  are fit only inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native-resolution 8-bit soft
  output without per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all other protected data are
  not read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.
- A fixed synthetic contract must verify finite bounded repeatable output,
  positive response around a vertical step, zero response on a flat field, and
  exact invariance under a strictly monotone squared gray-level transform.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is nonnegative.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The rank cue is training-eligible in at least `12/15` folds.
6. Candidate and incumbent soft scores have exactly the same positive support
   in every evaluated fold image.
7. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are both nonnegative versus the unchanged
   incumbent.
8. The synthetic contract, finite/bounded checks, runtime diagnostics, and
   deterministic preview complete.

Failure of any condition rejects this fixed realization. Do not tune the
radius, partitions, orientations, tie handling, rank statistic, evidence
reduction, eligibility, calibration, context integration, Choquet parameters,
gate, localizer, or thresholds from the result. Do not advance to multiscale,
variance-ranklet, color-ranklet, or learned rank variants from this outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `rank_calibration.csv`, `rank_diagnostics.csv`,
`best_method_preview.png`, `official_eval_manifest.json`, and the controller's
official-evaluation summary. The preview uses fixed UDED-selection positions
1, 8, and 15 with columns: input, ground truth, incumbent out-of-fold
prediction, candidate out-of-fold prediction, and local rank-contrast cue.
