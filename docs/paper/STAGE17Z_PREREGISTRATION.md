# Stage 17z preregistration - adaptive polynomial residual context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

De Simone, Kenne, and Zullo, *High-fidelity image analysis of
archaeological artifacts using adaptive polynomial approximation* (Numerical
Algorithms, 2026, DOI `10.1007/s11075-026-02497-3`), interpret edges as
locations where an adaptive low-degree polynomial representation cannot
explain the image. Their PolyEdge method recursively subdivides the raster,
fits stable bivariate polynomial approximations on Chebyshev admissible
meshes, and combines four reconstruction residuals. This is a representation-
failure signal rather than another local derivative, fixed patch basis,
texture histogram, connected-response transform, or one-dimensional
change-point model.

The paper and its official MIT-licensed repository were checked live on
2026-10-17. The author repository is pinned at commit
`53277503faae02514cc9249bccd2083210c00138`. Stage 17z calls the unchanged
author Python pipeline and fixes the Section-7 settings: degree `6`,
Chebyshev admissible meshes with continuous sampling, maximum depth `8`,
minimum cell size `4`, RMSE tolerance `1e-3`, Gaussian sigma `1`, and the
equal average of the four independently min-max-normalized residuals. It uses
the continuous residual only; the author's percentile threshold is not run.

This is not a reproduction of the paper's archaeological demonstrations or
binary comparisons. The author pipeline receives MFI's unchanged median-
conditioned grayscale image and its residual is integrated only as one
candidate context membership. It is mechanistically distinct from Stage
17x's row/column piecewise-constant segmentation, Stage 17t's fixed `3x3`
Frei-Chen subspace, Stage 17r's patch recurrence, Stage 17h's local scaling,
and the closed conditioning, graph, morphology, phase, topology, aggregation,
fusion, and localizer families.

## Fixed candidate

For every unchanged median-conditioned grayscale image in `[0,1]`:

1. Run the pinned, clean author PolyEdge source with the fixed settings above.
2. Construct the author residuals `EO=|I-PO|`, `ES=|S-PS|`,
   `DO=|I-PS|`, and `DS=|S-PO|`, where `PO` and `PS` are independent
   adaptive polynomial reconstructions of the original and sigma-1 Gaussian-
   smoothed rasters.
3. Preserve the author's independent min-max normalization of the four maps
   and their equal arithmetic average. Do not threshold or postprocess it.
4. Fit one positive logistic membership only inside each outer UDED-selection
   training fold. The midpoint is the mean of training edge and texture
   medians; the scale is the pooled training interquartile range with a
   `1e-9` floor. The singleton weight is
   `max(AUC-0.5,0)*(1+mutual_information)`. Eligibility requires training AUC
   at least `0.56`; an ineligible fold is exactly the compact control.
5. When eligible, append the membership to the retained five and renormalize
   singleton weights before the unchanged distorted-Choquet integral.

The retained five memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
threshold grid are unchanged. There is no source modification, parameter
search, residual selection, fusion search, resize, target adapter, or
candidate-driven normalization beyond the published author pipeline.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, cue calibration, eligibility, singleton weight, and operating
  threshold are fit only inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native-resolution 8-bit soft
  output without export-time per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all protected data are not
  read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.
- A fixed synthetic contract must verify source provenance, finite bounded
  output, zero response on a flat field, bitwise repeatability, affine
  photometric invariance, a localized clean-step response, and clean-step peak
  response greater than the fixed checkerboard and seed-17022 small-noise
  controls.

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
8. Source, synthetic, finite/bounded, repeatability, runtime, and deterministic
   preview contracts complete.

Failure of any condition rejects this fixed realization. Do not tune or
extend the polynomial degree/basis/nodes, subdivision, stopping tolerance,
smoothing, residual choice/normalization/combination, thresholding,
calibration, eligibility, integration, context, gate, localizer, or threshold
grid from the result. Do not advance to adaptive degree, alternate nodes,
anisotropic subdivision, coefficient analysis, color, multiscale residual
propagation, source modifications, or a repository surrogate.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `adaptive_polynomial_calibration.csv`,
`adaptive_polynomial_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and adaptive polynomial residual cue.
