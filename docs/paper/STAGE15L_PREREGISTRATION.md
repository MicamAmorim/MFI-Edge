# Stage 15l preregistration — image-regime characterization

Status: registered after Stage 15k and before inspecting any association
between image properties and cross-method performance. This is a diagnostic
stage; it does not train a router, select an architecture, or rerun a detector
or matcher.

## Question

Which predeclared, image-internal regimes are associated with the fixed-output
F1 differences among the frozen Stage-15 methods, and in particular with the
gap between the strongest single reference (SED) and the unchanged MFI
incumbent?

## Frozen inputs and role

Use the 100 BSDS500-validation images, their existing annotations, the frozen
MFI/SED/EDPF/CO/SCO/Compass/QFrD maps, and Stage 15k's already parsed
per-image official counts. No detector, threshold sweep, or MATLAB matcher is
rerun. BSDS500 validation is development diagnosis data. The Stage-15a
stochastic/reference-uncertified matcher caveat remains.

## Predeclared regime variables

All image intensities are converted to float grayscale in `[0,1]` without
per-image normalization.

1. `texture_density`: fraction of pixels whose absolute residual from a
   Gaussian blur with sigma 1.5 exceeds 0.05.
2. `local_contrast`: mean Gaussian-window standard deviation at sigma 1.5.
3. `global_contrast`: grayscale 90th minus 10th percentile.
4. `incumbent_edge_density`: fraction of frozen incumbent-map pixels at or
   above its already reported ODS threshold.
5. `incumbent_fragmentation_per_10k`: 8-connected component count per 10,000
   thresholded incumbent edge pixels.
6. `incumbent_mean_component_size`: thresholded incumbent edge pixels divided
   by its 8-connected component count.
7. `orientation_entropy`: 12-bin, gradient-magnitude-weighted entropy of
   Scharr orientation modulo pi, normalized by log(12).
8. `curvature_complexity`: mean modulo-pi orientation change between
   horizontally/vertically adjacent thresholded incumbent edge pixels,
   normalized by pi.
9. `coarse_to_fine_gradient_ratio`: mean Scharr magnitude after Gaussian
   sigma 4 divided by the mean at sigma 1, with only a numerical epsilon.
10. `gt_density`: fraction of pixels marked by at least one annotator.
11. `annotator_agreement`: mean annotator fraction conditional on a pixel
    marked by at least one annotator.

The incumbent-derived variables are diagnostic properties of a frozen output,
not proposed routing features.

## Fixed analyses

- Use Stage 15k's `ods_raw_nearest` per-image F1 only.
- For each property, compute Spearman correlation with every method's F1 delta
  versus SED and versus the incumbent. Apply one Benjamini-Hochberg correction
  across the complete correlation family.
- For each property and delta, also report the deterministic high-minus-low
  quartile mean contrast. Quartiles are formed by stable sorting on property
  value and assigning the first and last 25 images; no cut point is optimized.
- Record the Stage-15k fixed-threshold oracle winner by image only as a
  descriptive label and report winner counts in each property quartile. Do not
  fit or validate a classifier, decision tree, threshold rule, mixture, or
  router.

No p-value, correlation, or quartile result can authorize an MFI change before
Stages 15m–15o are complete and a separate architecture experiment is
preregistered.

## Outputs and qualitative artifact

Emit `image_regime_features.csv`, `regime_associations.csv`,
`quartile_winner_counts.csv`, `summary.json`, and
`best_method_preview.png`. The preview uses sorted validation positions 1, 50,
and 100 with columns input, mean annotator boundary, frozen incumbent, and
exact SED; row labels show the predeclared image-regime measurements. It is
documentary only.

No `official_eval_manifest.json` is emitted because this stage creates no
candidate map and invokes no evaluator; it diagnoses frozen maps and existing
official count tables only.

## Decision semantics

Record the associations without selecting a router. Then register exactly one
Stage-15m pixel/segment complementarity diagnosis over the same frozen output
family. The compact Choquet-gated Scharr+NMS controller remains unchanged.
