# Stage 14s preregistration — fixed half-order Riesz localizer

Date registered: 2026-10-07, before any Stage-14s metric or qualitative output
was inspected.

## Question and mechanism

Can a nonlocal fractional derivative preserve weaker boundary evidence better
than the integer first-order Scharr operator without sacrificing localization
or admitting excessive texture?

Mathieu et al. (2003, DOI `10.1016/S0165-1684(03)00194-4`) establish the
selectivity/noise-immunity motivation for noninteger differentiation in edge
detection. Zhang et al. (2020, DOI `10.1016/j.dsp.2019.102639`) further combine
fractional-order Gaussian derivatives with a Canny-like detection, NMS, and
thresholding pipeline for noisy natural images. The recent Caputo-k gradient
paper by Belhadi et al. (2025, DOI `10.5269/bspm.78430`) confirms continued
non-neural use of fractional gradient masks, but its image-specific parameter
examples do not justify a parameter search here.

Stage 14s therefore tests one canonical half-order point. On the unchanged
median-conditioned grayscale image, it computes the isotropic spectral Riesz
gradient

`G_x = F^-1[i w_x |w|^(alpha-1) F(I)]`,

`G_y = F^-1[i w_y |w|^(alpha-1) F(I)]`,

with `alpha=0.5`, zero DC response, and 32-pixel reflection padding. Its
magnitude receives the same robust percentile scaling used by the incumbent
classical detector stack, followed by NMS in the operator-derived normal
direction. The retained five-feature distorted-Choquet context gate is then
applied unchanged. This is a repository-specific Riesz realization, not a
claim to reproduce CRONE, FoGDbED, or the Caputo-k masks.

## Data, fitting, and fixed protocol

- UDED selection uses the existing 5 repeats x 3 folds.
- Compact membership fitting and each variant's score threshold remain inside
  each outer fold.
- Fractional order `0.5`, Riesz construction, reflection padding, scaling,
  orientation, and NMS are globally fixed before scoring.
- BSDS500 validation receives native-resolution soft maps exported from a
  context bank fitted on full UDED selection without reading BSDS ground truth.
- The official MATLAB evaluator uses all annotations, 99 thresholds,
  `maxDist=0.0075`, and thinning.
- UDED held-out, BSDS500 test, and BIPEDv2 test are forbidden.
- No order, padding, spectral taper, magnitude, normalization, conditioning,
  orientation, NMS, context, or fusion sweep is allowed after results are
  observed.

## Promotion rule

All criteria are conjunctive:

1. UDED aggregate F1 delta is nonnegative;
2. UDED aggregate precision delta is at least `-0.002`;
3. mean paired fold-F1 delta is nonnegative;
4. candidate wins at least 9 of 15 folds in F1;
5. official BSDS500-validation evaluation completes with feedback allowed;
6. BSDS-val ODS delta is at least `+0.002`;
7. BSDS-val OIS and AP deltas are both nonnegative.

Failure of the official attachment triggers attachment repair only. A failed
fixed point rejects only this half-order spectral Riesz realization and does
not authorize an order sweep from the outcome. Continue to the next distinct
agenda family.

## Outputs and qualitative policy

The runner writes aggregate, fold, per-image, and fractional-operator
diagnostics, a repository-local official exporter/manifest, and
`best_method_preview.png`. The fixed preview is the first validation image in
the first deterministic CV split with columns: conditioned input, ground
truth, incumbent prediction, candidate prediction, fractional magnitude, and
retained incumbent. It is documentary only.
