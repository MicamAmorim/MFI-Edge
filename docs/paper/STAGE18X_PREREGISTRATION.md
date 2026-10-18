# Stage 18x preregistration - dual-stencil Teager-energy context

Status: registered before candidate-result inspection. Date: 2026-10-18.

## Question and literature basis

Can a nonlinear instantaneous-energy statistic identify compact boundary
activity that is missed by the retained linear/curvature descriptors while
rejecting one-stencil lattice oscillation, without changing localization or
adding another smoothing, calibration, aggregation, graph, or contour-linking
mechanism?

Boudraa and Diop, *Image Contrast Enhancement Based on 2D Teager-Kaiser
Operator*, ICIP 2008, DOI `10.1109/ICIP.2008.4712471`, give complementary
axial Type-1A and diagonal Type-1B discrete 2-D Teager-Kaiser quadratic energy
operators and describe them as local-activity/edge-strength statistics.
Boudraa, Salzenstein, and Cexus, *Two-dimensional continuous higher-order
energy operators*, Optical Engineering 44(11), DOI `10.1117/1.2128125`,
provides the continuous energy-operator framework and diagonal extensions.
The ICIP paper combines the two stencils by maximum inside a contrast-
enhancement pipeline. Stage 18x instead tests a conservative positive
consensus so that a response must be supported by both complementary stencils.
This fixed consensus is a disclosed repository adaptation, not an exact
reproduction of either source method.

The mechanism is distinct from Stage 18v's windowed signed-gradient
cancellation ratio: it uses an unsmoothed quadratic interaction between the
center sample and symmetric neighbor products. It is also distinct from the
closed local-patch bases, step/facet regression, Hessian/tensor, phase,
wavelet/fractional, morphology, calibration, aggregation, smoothing, graph,
region, and contour-completion families. It adds one cue and does not combine
rejected evidence.

## Fixed candidate

Input is the unchanged median-conditioned grayscale image in `[0,1]`. With
one-sample reflected boundary handling, compute

`A = 2*I^2 - I_left*I_right - I_up*I_down`

and

`B = 2*I^2 - I_ul*I_lr - I_ur*I_ll`.

Positive evidence is

`sqrt(max(A,0) * max(B,0)) / 2`.

For bounded input, each operator lies in `[-2,2]`; rectification, geometric
consensus, and division by two therefore bound the cue in `[0,1]` without an
epsilon, image statistic, or fitted scale. The geometric mean is fixed before
results because it encodes conjunctive axial/diagonal support and suppresses a
checkerboard that excites only one complementary stencil. Negative energy is
assigned zero rather than reinterpreted as positive evidence.

The cue is calibrated and made eligible only inside each outer UDED training
fold by the established AUC `>=0.56` rule. When eligible it is appended as one
positive membership to the retained distorted-Choquet context. The five
retained memberships, singleton fitting, gamma `0.55`, gate strength `2.0`,
floor `0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-
fitted threshold procedure are unchanged. For BSDS500 validation, calibration
is fitted once on all UDED-selection development images without reading BSDS
ground truth.

## Development protocol and promotion rule

UDED selection uses seed `20261009`, five repeats by three folds, leakage-free
bank/membership/threshold fitting, and fixed candidate mechanics. Promotion
requires all of:

- aggregate F1 delta at least `+0.002` versus compact MFI;
- aggregate precision delta nonnegative;
- aggregate recall delta at least `-0.003`;
- mean paired fold-F1 delta nonnegative and at least `9/15` fold wins;
- cue eligibility in at least `12/15` folds;
- exact candidate/incumbent positive-score support equality;
- completed official BSDS500-validation attachment with ODS delta at least
  `+0.002` and nonnegative OIS and AP deltas.

The rule is conjunctive. The Stage-15a stochastic/reference-unverified Windows
matcher caveat remains. BSDS500 test, UDED held-out, BIPEDv2 test, and other
protected feedback are forbidden.

## Fixed contracts and artifacts

Before dataset access, deterministic checks must establish finite bounded
output, zero flat and checkerboard responses, stronger response to a single
step than to the fixed checkerboard and low-amplitude noise fields, exact
repeatability, and quadratic positive-scale covariance. Per-image runtime and
axial/diagonal response diagnostics are recorded. Exact positive-score support
preservation is asserted after context gating.

The runner must emit `best_method_preview.png` at fixed UDED-selection
positions 1, 8, and 15 with columns: input, ground truth, compact-MFI
out-of-fold prediction, candidate out-of-fold prediction, and Teager-energy
cue. It must also emit an official BSDS500-validation manifest and native-
resolution 8-bit exporter without per-image score normalization. Qualitative
outputs are documentary only.

## Locked interpretation

Do not tune or extend the axial/diagonal stencils, reflection, rectification,
consensus, normalization, calibration, eligibility, integration, context,
gate, localizer, or thresholds from the result. Do not advance to alternative
TKEO discretizations, max/mean fusion, higher-order energy operators,
multiscale/wavelet/color variants, demodulation, contrast enhancement, or
combinations with rejected cues. Failure closes this fixed nonlinear-energy
realization and routes to a mechanistically distinct live-literature
checkpoint.
