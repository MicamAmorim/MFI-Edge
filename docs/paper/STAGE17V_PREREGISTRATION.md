# Stage 17v preregistration - morphological blur-minimum context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Van Vliet, Young, and Beckers, *A Nonlinear Laplace Operator as Edge Detector
in Noisy Images* (Computer Vision, Graphics, and Image Processing 45(2):
167-195, 1989, DOI `10.1016/0734-189X(89)90131-X`), define the nonlinear
Laplacian through the largest positive and negative center-to-neighbour
differences. Their Eq. 4 rewrites Lee's morphological edge strength as

`min(gradmax, -gradmin)`.

For a unit square mask this is

`min(max_neighbourhood(I)-I, I-min_neighbourhood(I))`.

The statistic is positive only when the center has both brighter and darker
support in the same neighbourhood. It therefore encodes a two-sided local
transition: a smooth ramp receives positive strength, while a flat patch, an
ideal two-level checkerboard pixel, and the extremal center of an isolated
impulse receive zero. Van Vliet et al. specifically motivate this
blur-minimum strength as less noise-sensitive than ordinary gradients and
show that its ridges coincide with their nonlinear-Laplacian zero crossings
on blurred profiles.

Stage 17v tests only that fixed two-sided strength as one context membership.
It does not run the paper's Gaussian smoother, nonlinear-Laplacian
zero-crossing segmentation, distance transforms, contour extraction, or
thresholding. The hypothesis is that requiring simultaneous bright-side and
dark-side support adds transition-shape evidence that the retained marginal
Gabor/Hessian magnitudes do not express.

This mechanism differs from Stage 17t's linear orthogonal patch-subspace
occupancy, Stage 17p's one-sided local gradient outlier, Stage 17b's opposed
rank statistic, Stage 16j's oriented parametric profile fitting, and Stage
14l's half-disc texture histogram. It is also not the previously available
local range descriptor: range is `max-min`, whereas the present statistic is
zero at either local extreme and retains only the smaller of the two
center-to-extreme distances.

Primary sources were checked live on 2026-10-16: the peer-reviewed article
record above and the authors' equation-bearing 1988 Delft proceedings
version, DOI `10.1016/B978-0-444-87137-4.50011-4`.

## Fixed candidate

On the unchanged median-conditioned grayscale image in `[0,1]`, use the
paper's unit-coefficient square realization and its smallest discussed support:
a reflected `3x3` neighbourhood. Let

- `u = max_3x3(I) - I`,
- `d = I - min_3x3(I)`, and
- `E = min(u,d)`.

No Gaussian smoothing is added because the incumbent median conditioning is
unchanged. There is no zero-crossing extraction, threshold, per-image
normalization, orientation choice, scale choice, shape choice, or fitted
transform in the raw cue. For unit-range input `E` lies in `[0,0.5]`.

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
threshold grid are unchanged.

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
- A fixed synthetic contract must verify finite bounded output, zero response
  on a flat field, deterministic repeatability, additive-offset invariance,
  contrast-polarity invariance, positive-intensity-scale linearity, and a
  positive three-level ramp center exceeding a sharp binary step, a period-two
  checkerboard, an isolated impulse center, and a fixed seed-17018 small
  Gaussian perturbation around mid-gray.

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
8. The synthetic, finite/bounded, repeatability, runtime, and deterministic
   preview contracts complete.

Failure of any condition rejects this fixed realization. Do not tune the
support, shape, order-statistic definition, smoothing, zero-crossing rule,
boundary handling, normalization, eligibility, calibration, integration,
context, gate, localizer, or thresholds from the result. Do not advance to
larger, circular, weighted, multiscale, color, adaptive-SNR, hierarchical,
zero-crossing, contour-extraction, or complete nonlinear-Laplacian variants.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `morphological_blur_minimum_calibration.csv`,
`morphological_blur_minimum_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and morphological blur-minimum cue.
