# Stage 14p preregistration — MFI-coupled Ambrosio–Tortorelli phase field

Date registered: 2026-10-07, before any Stage-14p metric or qualitative output
was inspected.

## Question

Can a classical diffuse-interface optimization suppress isolated texture
responses and recover a more coherent boundary set when the retained MFI
context is used only as a spatial prior?

This is mechanistically distinct from Stage 14o. Stage 14o changed fuzzy
uncertainty representation and failed every UDED non-collapse condition.
Stage 14p restores the retained crisp compact Choquet context and changes only
the localization basis from gated Scharr+NMS to an optimized phase field.

## Literature and mechanism

The Ambrosio–Tortorelli functional is a classical elliptic approximation to
the Mumford–Shah free-discontinuity problem. Hintermüller, Stengl and Surowiec,
*Uncertainty Quantification in Image Segmentation Using the
Ambrosio–Tortorelli Approximation of the Mumford–Shah Energy*, Journal of
Mathematical Imaging and Vision 63 (2021), DOI
`10.1007/s10851-021-01034-2`, supports treating its phase variable as a
continuous reconstructed-edge object.

For conditioned image `f`, reconstruction `u`, smooth-region field `v`, and
retained compact Choquet context `C`, the repository discretizes

`0.5||u-f||^2 + alpha v^2 |grad u|^2`

`+ beta [epsilon |grad v|^2 + (1-v)^2/(4 epsilon)] + eta C v^2`.

The last term is nonnegative and encourages `v` to fall only where the
already-retained MFI context supports a discontinuity. The soft edge field is
`1-v`; the candidate map is its nonmaximum suppression along the unchanged
image-gradient orientation. The incumbent remains the compact Choquet-gated
grayscale Scharr+NMS map.

## Fixed numerical configuration

The input lattice and intensities are normalized, and one configuration is
fixed before evaluation:

- `alpha = 1.0`;
- `beta = 0.10`;
- `epsilon = 1.5` pixels;
- MFI coupling `eta = 0.005`;
- 16 alternating Jacobi iterations from `u=f`, `v=1`.

These values define a narrow few-pixel diffuse interface with weak MFI
coupling relative to the reconstruction and phase-well terms. They are a
minimal normalized operationalization, not a claim to reproduce the 2021
uncertainty study. There is no parameter, iteration-count, coupling, NMS, or
energy-family sweep. A failure does not authorize post-result tuning.

## Data and leakage controls

- UDED selection: existing 5 repeats x 3 folds.
- Compact-bank fitting and the score threshold occur inside each outer fold.
- The phase-field coefficients are fixed globally and are never fitted.
- BSDS500 validation is development data and receives a candidate exported
  from full UDED selection without reading BSDS ground truth.
- UDED held-out, BSDS500 test, and BIPEDv2 test are forbidden.

## Promotion rule

All criteria are conjunctive:

1. UDED aggregate F1 delta is nonnegative;
2. UDED aggregate precision delta is nonnegative;
3. mean paired fold-F1 delta is nonnegative;
4. candidate wins at least 9 of 15 folds;
5. official BSDS500-validation evaluation completes with feedback allowed;
6. BSDS-val ODS delta is at least `+0.002`;
7. BSDS-val OIS and AP deltas are both nonnegative.

A failed official attachment triggers attachment repair only. A candidate that
fails either development axis is not promoted. The original compact positive
Choquet gate remains incumbent unless every criterion passes.

## Outputs

The runner writes aggregate/fold/image metrics, phase-field diagnostics,
`official_eval_manifest.json`, and `best_method_preview.png`. The preview uses
the first validation image in the first deterministic repeated-CV split and
shows conditioned input, ground truth, incumbent prediction, candidate
prediction, soft phase field, and current retained incumbent. It is
documentary only and cannot change the decision.

## Failure interpretation

Failure rejects this fixed MFI-coupled AT discretization, not variational
phase fields in general. Do not tune its coefficients from the result. Move
to the shearlet singularity localizer or another mechanistically distinct
registered agenda item.
