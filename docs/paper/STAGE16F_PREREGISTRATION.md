# Stage 16f preregistration — fixed rolling-guidance localizer conditioning

Date registered: 2026-10-09, before any Stage-16f metric or qualitative output
was inspected.

## Question and mechanism

Can fixed scale-aware removal of small image structures suppress unsupported
texture response while restoring the localization of larger boundaries well
enough to improve both UDED selection and BSDS500 validation?

Zhang, Shen, Xu, and Jia, *Rolling Guidance Filter* (ECCV 2014, DOI
`10.1007/978-3-319-10578-9_53`), distinguish structure scale from edge
magnitude. Their method first removes structures below a spatial scale and
then repeatedly joint-filters the original signal using the previous result as
guidance. The primary paper explains that small structures cannot return once
removed, whereas blurred larger boundaries progressively recover; the authors'
official project page also demonstrates the filter before classical Canny edge
detection.

Stage 16f is an equation-level repository reimplementation, not an exact
author-code reproduction. It applies grayscale rolling guidance to the
incumbent median-conditioned image with fixed `sigma_space=3`,
`sigma_range=0.1`, and four iterations. The primary paper supplies the
constant-initial-guide equations and repeatedly uses range sigma `0.1` and four
iterations. Spatial sigma `3`, range sigma `25/255` (rounded to `0.1`), and four
iterations are also the standard OpenCV RGF interface defaults, chosen here
before results rather than searched. Joint bilateral support is truncated at
three spatial standard deviations with reflection padding as a fixed numerical
convention. Stage 16f deliberately follows the paper's constant initialization,
not the source-image initialization reported as a defect in older OpenCV code.
The first iteration uses a constant guide and therefore reduces to Gaussian
weighted averaging; each later iteration averages the same fixed input using
the preceding result as its range guide.

Only the localizer input changes:

`median grayscale -> fixed rolling guidance -> Scharr + NMS`.

The retained five-feature context bank, distorted-Choquet gamma `0.55`, gate
strength `2.0`, floor `0.10`, fold-internal bank fitting, and fold-internal
threshold fitting are unchanged. No RGF parameter, context parameter,
threshold grid, mixture, or router is searched.

## Why this is a distinct bounded test

- Stage 16d gated an already formed edge score using response-derived stable
  adjacent regions. Stage 16f acts in the image domain before localization and
  uses scale rather than component support.
- Stage 16b averaged two complete detector outputs. Stage 16f has one MFI
  inference path and no detector fusion or external SED dependency.
- Stage 14h tested fixed gravitational smoothing, which caused a large clean
  loss despite a texture-specific benefit. Rolling guidance is mechanistically
  different because its iterative guide is designed to restore larger edge
  sharpness after small-structure removal. This is a new single-point
  falsification, not gravitational parameter tuning.
- Scharr, its orientation-derived NMS, and the compact fuzzy context remain in
  their retained roles; this is not another localizer-family replacement.

The hypothesis is motivated by two completed development observations. Stage
15m found substantially more unsupported fixed-contract response for MFI than
SED, and Stage 15l found that stronger references gained as incumbent edge
density/fragmentation increased. Stage 16f tests whether some of that error is
small-scale image structure rather than a response-map topology defect. These
observations do not set an image-specific scale or routing rule.

## Data and leakage control

- UDED selection only: five repeats of three-fold outer CV. Compact memberships
  and the operating threshold are fitted using each outer training fold only.
- UDED held-out, BSDS500 test, and BIPEDv2 test are forbidden.
- BSDS500 validation is the second development axis and is exported at native
  resolution as direct 8-bit soft PNG without per-image normalization.
- The BSDS exporter may fit the compact context bank from all UDED-selection
  images but may not read BSDS ground truth.
- The official attachment uses all annotations, 99 thresholds,
  `maxDist=0.0075`, thinning, and the unchanged unmodified Windows matcher.
  The matcher remains stochastic and reference-uncertified; the fixed-seed
  diagnostic binary is forbidden for dataset scoring.

## Promotion rule fixed before results

Promotion requires **every** condition:

1. UDED aggregate F1 delta versus compact MFI is at least `+0.002`.
2. UDED aggregate precision delta is at least `+0.002`, because texture
   suppression is the registered mechanism endpoint.
3. UDED aggregate recall delta is at least `-0.01`.
4. Mean paired fold-F1 delta is nonnegative.
5. Candidate F1 exceeds incumbent F1 in at least `9/15` folds.
6. The official BSDS500-validation attachment completes.
7. BSDS500-validation ODS delta is at least `+0.002`.
8. BSDS500-validation OIS and AP deltas are both nonnegative.
9. `best_method_preview.png` and the registered numeric artifacts exist.

The rule is conjunctive. A texture-specific diagnostic improvement, a gain on
only one dataset, or a result that improves precision by collapsing recall is
insufficient.

## Outputs and qualitative contract

The runner writes `summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `conditioning_diagnostics.csv`,
`official_eval_manifest.json`, and `best_method_preview.png`. The preview uses
fixed UDED-selection positions 1, 8, and 15. Columns are input, ground truth,
out-of-fold compact-MFI prediction, rolling-guidance conditioned grayscale,
and out-of-fold candidate prediction. It is documentary only.

## Outcome discipline

If any condition fails, do not tune spatial/range sigma, iteration count,
support truncation, color handling, median/RGF ordering, localizer mixture,
Choquet parameters, gate, or threshold grid from Stage-16f outcomes. Retain the
compact Choquet-gated median-conditioned Scharr+NMS controller and escalate to
a mechanistically distinct checkpoint. A failure applies only to this fixed
grayscale RGF realization, not to every scale-aware filter.
