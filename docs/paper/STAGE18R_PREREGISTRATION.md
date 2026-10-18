# Stage 18r preregistration — contrast-polarity continuation context

Status: registered before candidate-result inspection.  Date: 2026-10-18.

## Question and literature basis

Can signed contrast-polarity continuation distinguish persistent natural
boundaries from locally oriented but polarity-incoherent texture while leaving
the retained localizer unchanged?

Geisler and Perry, *Contour Statistics in Natural Images: Grouping Across
Occlusions*, Visual Neuroscience 26(1):109–121 (2009), DOI
`10.1017/S0952523808080875`, measured natural edge-element co-occurrence as a
joint function of geometry and contrast polarity.  Their ideal-observer and
psychophysical results show that contrast sign supplies grouping information
in addition to good continuation.  Stage 18r tests only that qualitative
mechanism.  It is not a reproduction of their log-Gabor extractor, annotated
natural-statistics table, or Bayesian observer.

This is distinct from Stage 16z's signless local structure tensor, Stage 14r's
unoriented-polarity SE(2) lift, Stage 16l's binary EDPF chain support, and Stage
18l's signed patch torque/closure moment.  Stage 14b concerned the spatial
placement of learned anti-texture evidence, not intensity-contrast polarity
along a contour.  No closed cue or aggregation result is combined here.

## Fixed candidate

Input is the unchanged median-conditioned grayscale image.  Compute signed
Scharr gradients and normalize every nonzero gradient to unit length.  At each
pixel, use the perpendicular local tangent and bilinearly sample the signed
unit-gradient field symmetrically at fixed distances `1`, `2`, and `4` pixels
with reflection at the raster boundary.  For each distance, clip both center-
to-neighbour dot products below at zero and take their geometric mean.  The cue
is the unweighted mean of the three distance responses, clipped to `[0,1]`,
with zero assigned where the center gradient is zero.

The cue is calibrated and made eligible only inside each outer UDED training
fold by the established AUC `>=0.56` rule.  When eligible it is appended as one
positive membership to the retained distorted-Choquet context.  The five
retained memberships, singleton fitting, gamma `0.55`, gate strength `2.0`,
floor `0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-
fitted threshold procedure are unchanged.

The candidate is a bounded repository surrogate.  The three dyadic tangent
offsets are fixed before results as the smallest range that tests immediate and
short continuation without a new window, fitted scale, diffusion, linking, or
contour graph.

## Development protocol and promotion rule

UDED selection uses the established seed `20261009`, five repeats by three
folds, leakage-free bank/membership/threshold fitting, and fixed candidate
parameters.  Promotion requires all of:

- aggregate F1 delta at least `+0.002` versus compact MFI;
- aggregate precision delta nonnegative;
- aggregate recall delta at least `-0.003`;
- mean paired fold-F1 delta nonnegative and at least `9/15` fold wins;
- cue eligibility in at least `12/15` folds;
- exact candidate/incumbent positive-score support equality;
- completed official BSDS500-validation attachment with ODS delta at least
  `+0.002` and nonnegative OIS and AP deltas.

The rule is conjunctive.  The Stage-15a stochastic/reference-unverified Windows
matcher caveat remains.  BSDS500 test, UDED held-out, BIPEDv2 test, and other
protected feedback are forbidden.

## Fixed contracts and artifacts

Before dataset access, deterministic synthetic checks must establish finite and
bounded output, zero flat response, strong straight-step continuation,
suppression at a contrast-polarity reversal junction, global inversion and
positive-affine invariance, 90-degree rotation equivariance, and bitwise
repeatability.  Per-image runtime and cue diagnostics are recorded.

The runner must emit `best_method_preview.png` at fixed UDED-selection
positions 1, 8, and 15 with columns: input, ground truth, compact-MFI
out-of-fold prediction, candidate out-of-fold prediction, and polarity-
continuation cue.  It must also emit an official BSDS500-validation manifest
and native-resolution 8-bit exporter with no per-image score normalization.
Qualitative outputs are documentary only.

## Locked interpretation

Do not tune or extend tangent distances, gradient operator, sign convention,
interpolation, bilateral support rule, distance fusion, calibration,
eligibility, integration, context, gate, localizer, or thresholds from the
result.  Do not advance to curved transport, learned association fields,
polarity likelihood tables, color polarity, multiscale polarity, linking,
completion, diffusion, graph optimization, or combinations with rejected cues.
Failure closes this fixed realization and routes to a mechanistically distinct
live-literature checkpoint.
