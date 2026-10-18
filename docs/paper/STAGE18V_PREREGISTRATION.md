# Stage 18v preregistration - relative-variation coherence context

Status: registered before candidate-result inspection. Date: 2026-10-18.

## Question and literature basis

Can a local signed-gradient coherence ratio distinguish a persistent structural
transition from high-contrast oscillatory texture while leaving the retained
localizer unchanged?

Xu, Yan, Xia, and Jia, *Structure Extraction from Texture via Relative Total
Variation*, ACM Transactions on Graphics 31(6), Article 139 (2012), DOI
`10.1145/2366145.2366158`, define windowed total variation by Gaussian-weighted
absolute directional differences and windowed inherent variation by the
magnitude of the corresponding weighted signed-difference sum. Opposite
texture gradients cancel in inherent variation, whereas a coherent structural
transition reinforces. Their official MATLAB implementation uses sigma `3` by
default and a 15-sample Gaussian support.

Stage 18v tests only the bounded local variation principle. It does not run the
paper's nonconvex RTV regularizer, iterative structure extraction, linear
solver, or any image smoothing. It is distinct from the signless Stage-16z
structure tensor, which squares gradients and cannot express polarity
cancellation, and from Stage-18r bilateral tangent continuation, which compares
separate edge elements rather than signed variation within a spatial window.
It is also not a calibration, aggregation, localizer, or rejected-cue
combination.

## Fixed candidate

Input is the unchanged median-conditioned grayscale image. Compute horizontal
and vertical forward differences, assigning zero terminal difference. For each
direction, use a reflected Gaussian window with sigma `3` and radius `7`
(`15x15` support) to compute:

- total variation: the Gaussian average of the absolute differences;
- inherent variation: the absolute Gaussian average of the signed differences.

Positive evidence is
`(|G*dx| + |G*dy|) / (G*|dx| + G*|dy|)`, with zero assigned when the
denominator is zero. The triangle inequality bounds this ratio in `[0,1]`, so
there is no epsilon, clipping scale, image normalization, or fitted cue
parameter.

The cue is calibrated and made eligible only inside each outer UDED training
fold by the established AUC `>=0.56` rule. When eligible it is appended as one
positive membership to the retained distorted-Choquet context. The five
retained memberships, singleton fitting, gamma `0.55`, gate strength `2.0`,
floor `0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-
fitted threshold procedure are unchanged. For BSDS500 validation, the
calibration is fitted once on all UDED-selection development images without
reading BSDS ground truth.

This is an equation-level repository realization, not exact author-code
reproduction. Reflection and the direct bounded ratio are disclosed fixed
adapter choices made before results.

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
output, zero flat response, stronger response to a single step than to fixed
checkerboard and noise fields, positive-scale and additive-offset invariance,
and bitwise repeatability. Per-image runtime and variation diagnostics are
recorded. Exact positive-score support preservation is asserted after context
gating.

The runner must emit `best_method_preview.png` at fixed UDED-selection
positions 1, 8, and 15 with columns: input, ground truth, compact-MFI
out-of-fold prediction, candidate out-of-fold prediction, and relative-
variation cue. It must also emit an official BSDS500-validation manifest and
native-resolution 8-bit exporter without per-image score normalization.
Qualitative outputs are documentary only.

## Locked interpretation

Do not tune or extend the derivative, Gaussian scale/support, boundary rule,
direction set, ratio, zero-denominator handling, calibration, eligibility,
integration, context, gate, localizer, or thresholds from the result. Do not
advance to iterative RTV smoothing, alternative total-variation penalties,
multiscale/color/adaptive variants, learned structure-texture decomposition, or
combinations with rejected cues. Failure closes this fixed realization and
routes to a mechanistically distinct live-literature checkpoint.
