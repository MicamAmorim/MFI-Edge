# Stage 16z preregistration - scalar structure-tensor orientation context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Bigun, Granlund and Wiklund formalized local orientation estimation with a
second-moment/structure tensor (*Multidimensional orientation estimation with
applications to texture analysis and optical flow*, TPAMI 13(8):775-790,
1991, DOI `10.1109/34.85668`). Weickert makes the scalar construction and its
interpretation explicit: Gaussian-average the outer products of image
gradients; flat neighborhoods have two zero eigenvalues, a straight edge has
one dominant eigenvalue, and corners or locally isotropic structure have two
nonzero eigenvalues (*Coherence-enhancing diffusion of colour images*, Image
and Vision Computing 17:201-212, 1999, DOI
`10.1016/S0262-8856(98)00102-4`). Weickert's illustrated orientation analysis
uses noise scale `0.5` and integration scale `4`.

Stage 16z tests whether this local one-orientation evidence can distinguish
boundary-like support from multidirectional texture/junction clutter across
both development datasets. This is not Stage 14k's per-pixel CIELAB Di Zenzo
color-gradient localizer: Stage 16z is scalar, spatially integrated, and enters
only as one context membership while grayscale Scharr+NMS remains unchanged.
It also does not run coherence-enhancing diffusion, replace the localizer,
construct a graph, link contours, or use dataset identity.

## Fixed candidate

On the unchanged median-conditioned grayscale image `u`, compute Gaussian
derivatives at fixed noise scale `sigma=0.5`, then form

`J = G_rho * [[u_x^2, u_x u_y], [u_x u_y, u_y^2]]`

with fixed integration scale `rho=4`. The cue is the nonnegative orientation
evidence

`lambda_max(J) - lambda_min(J)`

implemented equivalently as

`sqrt((J11-J22)^2 + 4 J12^2)`.

The eigenvalue difference is used instead of normalized coherence so the cue
tends continuously to zero in flat regions; Weickert explicitly notes the
flat-region instability of the normalized ratio. Values are clipped only to
the analytic image-score range `[0,1]`; there is no per-image normalization.

Fit one positive logistic membership only inside each outer UDED-selection
training fold. Its midpoint is the mean of the training edge and texture
medians and its scale is the pooled training interquartile range, with only a
`1e-9` nonzero numerical floor. Fit its singleton weight using the established rule
`max(AUC-0.5,0) * (1+mutual_information)`. The cue is eligible only when its
training edge-versus-texture AUC is at least `0.56`; an ineligible fold is
exactly the compact control. When eligible, append it as a sixth membership
and renormalize singleton weights before the unchanged distorted-Choquet
aggregation.

The five retained memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
threshold grid are unchanged. There is no tensor-scale search, normalized
coherence variant, color tensor, diffusion, cue mixture, router, or
dataset-specific branch.

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
- A fixed synthetic contract must verify finite/bounded and exactly repeatable
  output, greater evidence near a vertical step than in remote flat bands, and
  greater step evidence than mean evidence on a two-pixel checkerboard.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is nonnegative.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The orientation cue is training-eligible in at least `12/15` folds.
6. Candidate and incumbent soft scores have exactly the same positive support
   in every evaluated fold image.
7. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are both nonnegative versus the unchanged
   incumbent.
8. The synthetic contract, finite/bounded checks, runtime diagnostics, and
   deterministic preview complete.

Failure of any condition rejects this fixed realization. Do not tune the
noise or integration scales, derivative implementation, boundary handling,
eigenvalue evidence, eligibility, calibration, context integration, Choquet
parameters, gate, localizer, or thresholds from the result. Do not advance to
coherence-enhancing diffusion or color/multiscale tensor variants from this
outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `orientation_calibration.csv`,
`orientation_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and structure-tensor orientation evidence.
