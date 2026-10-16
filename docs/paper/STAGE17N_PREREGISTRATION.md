# Stage 17n preregistration - two-scale topological-sensitivity context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Amstutz and Fehrenbach, *Edge Detection Using Topological Gradients: A
Scale-Space Approach* (Journal of Mathematical Imaging and Vision 52,
2015, DOI `10.1007/s10851-015-0558-z`; author preprint HAL
`hal-01025706`), derive edge indicators as the sensitivity of a variational
image cost to insertion of an infinitesimal insulating crack. Their parabolic
variance-maximization indicator `h3` couples image gradients across heat
scales rather than treating one smoothed derivative independently. They also
derive an analytic one-point quadrature: `beta = 1-sqrt(1-4/pi^2)` and the
two-scale approximation `h4` at times `beta*T` and `(2-beta)*T`. Their natural
image illustration fixes `T=2`, corresponding to a Gaussian scale of two
pixels at the terminal heat time.

Stage 17n tests the positive crack-insertion sensitivity of that fixed `h4`
form as one context membership. The hypothesis is that agreement of gradient
direction and energy across the analytically coupled early and late heat
scales supplies boundary reliability that transfers better than another
single-scale activity statistic. This is distinct from Stage 16t's maximum
selection among three normalized derivative scales: Stage 17n neither selects
a scale nor replaces localization, and its evidence is the extremal
eigenvalue of a bilinear cross-scale topological-sensitivity form. It is also
distinct from the closed phase, persistence, spectral-graph, stochastic-
scaling, conditioning, localizer-replacement, and structural-gating tests.

The 2006 topological-asymptotic edge/restoration paper by Belaid et al. (DOI
`10.1016/j.crma.2005.12.009`) establishes the earlier crack-insertion image
model. It is background only; no restoration iteration, threshold, or
parameter is imported from it.

## Fixed candidate

On the unchanged median-conditioned grayscale image, compute Gaussian
derivative gradients `a` and `b` at heat times

- `t1 = beta*T`,
- `t2 = (2-beta)*T`,
- `T=2`, and
- `beta = 1-sqrt(1-4/pi^2)`.

Using the heat-kernel identity, the Gaussian standard deviations are fixed as
`sqrt(2*t1)` and `sqrt(2*t2)` (approximately `0.957` and `2.662` pixels).
Gaussian support is truncated numerically at four standard deviations and
reflection is used at raster boundaries to realize the paper's symmetric
extension without periodic seams.

Let `S=(a b^T + b a^T)/2`. The paper's quadratic form is
`-2*pi*T*n^T S n`; after minimizing over crack normal `n`, define positive
evidence

`E = 2*pi*T*max(lambda_max(S), 0)`.

There is no image-wise normalization, threshold, scale selection, adaptive
time, or searched coefficient. A positive global intensity rescaling by `c`
must rescale `E` by `c^2`; outer-fold membership calibration absorbs units
without using validation data.

Fit one positive logistic membership only inside each outer UDED-selection
training fold. Its midpoint is the mean of training edge and texture medians,
and its scale is the pooled training interquartile range with a `1e-9`
numerical floor. Its singleton weight is
`max(AUC-0.5,0)*(1+mutual_information)`. The cue is eligible only when the
training edge-versus-texture AUC is at least `0.56`; an ineligible fold is
exactly the compact control. When eligible, append it as a sixth membership
and renormalize singleton weights before the unchanged distorted-Choquet
integral.

The retained five memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
threshold grid are unchanged. This is an equation-level repository
realization of `h4`, not an exact reproduction of the authors' complete NMS,
hysteresis, finite-element, or detector pipeline.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, cue calibration, eligibility, singleton weight, and operating
  threshold are fit only inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native-resolution 8-bit soft
  output without per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all protected data are not
  read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.
- A fixed synthetic contract must verify finite nonnegative output, zero
  response on a flat field, deterministic repeatability, quadratic positive-
  intensity scaling, and a clean step response greater than fixed checkerboard
  and seeded-noise controls.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is nonnegative.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The cue is training-eligible in at least `12/15` folds.
6. Candidate and incumbent soft scores have exactly the same positive support
   in every evaluated fold image.
7. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are both nonnegative versus the unchanged
   incumbent.
8. The synthetic, finite/nonnegative, repeatability, runtime, and deterministic
   preview contracts complete.

Failure of any condition rejects this fixed realization. Do not tune the heat
time, beta, Gaussian derivative discretization/support, boundary handling,
eigenvalue mapping, intensity scaling, eligibility, calibration, integration,
context, gate, localizer, or thresholds from the result. Do not advance to
other topological-gradient costs, quadrature rules, elliptic/PDE variants,
color, multiscale, anisotropic, iterative-restoration, or learned variants
from the outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `topological_calibration.csv`,
`topological_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and two-scale topological-sensitivity cue.
