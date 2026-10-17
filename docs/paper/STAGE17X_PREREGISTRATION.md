# Stage 17x preregistration - semi-global scanline change-point context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Jevnisek and Avidan, *Semi Global Boundary Detection* (Computer Vision and
Image Understanding 152:21-28, 2016, DOI
`10.1016/j.cviu.2016.07.004`), represent an image by scanlines, optimally
segment each one-dimensional signal with dynamic programming, and merge
boundary evidence across directions. Their central claim is that a scanline
is a useful mid-level representation: it extends beyond a local patch without
requiring a single global two-dimensional partition. Their method uses an MDL
penalty to control segment count. Bellman's dynamic-programming curve
approximation (CACM 4(6):284, 1961, DOI `10.1145/366573.366611`) supplies the
optimization basis, and Schwarz's model-dimension criterion (Annals of
Statistics 6(2):461-464, 1978, DOI `10.1214/aos/1176344136`) supplies the
fixed `log(N)` complexity penalty used here.

Stage 17x tests one bounded repository surrogate of that principle, not the
complete SGBD detector. It deliberately omits the authors' learned texton
representation, semi-global smoothing, fitted MDL temperature and weighting,
marginalization over segment counts, and optional ultrametric-contour
postprocessing. The hypothesis is that boundary support from an optimally
selected piecewise-constant model over full rows and columns supplies
adaptive, mid-level region-transition evidence not present in the retained
local Gabor/Hessian responses.

This mechanism is distinct from the recently closed local patch/activity
sequence, Stage 16x's two-dimensional spectral graph, Stage 16d's component-
tree region stability, Stage 14i's endpoint linking, Stage 14t's component
NFA attenuation, Stage 16h's connected-threshold persistence, and localizer
replacement. It neither modifies the image nor moves, creates, or removes
positive support in the incumbent Scharr+NMS score.

Primary sources were checked live on 2026-10-17: the peer-reviewed SGBD
article and author-hosted paper, the ACM Bellman record, and the Project
Euclid Schwarz record.

## Fixed candidate

On the unchanged median-conditioned grayscale image in `[0,1]`:

1. If the longer raster side exceeds `256`, bilinearly resize to a working
   grid whose longer side is exactly `256`; otherwise retain the native grid.
2. Process every complete row and every complete column independently.
3. For a scanline of length `N`, fit the exact least-squares piecewise-
   constant partition by dynamic programming. The cost is the sum of within-
   segment squared residuals plus `sigma_hat^2 * log(N)` for each segment.
   `sigma_hat` is the first-difference MAD divided by
   `0.6744897501960817*sqrt(2)`; only when that MAD is zero, use the RMS first
   difference divided by `sqrt(2)`. A constant line has one segment.
4. At every selected change point, assign the absolute difference between
   its adjacent segment means to both raster samples bordering that
   between-sample boundary.
5. Merge row and column evidence by pointwise maximum. If a working-grid
   resize occurred, bilinearly return the evidence to native raster size.
   No per-image normalization follows.

The raw cue is finite and bounded in `[0,1]`. There is no orientation search,
diagonal pass, texton or color feature, smoothing, segment-count cap, minimum
segment length, learned penalty, target adapter, morphological operation,
threshold, or postprocessing.

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
  on a flat field, deterministic repeatability, additive-offset and contrast-
  polarity invariance, positive-intensity-scale linearity, and stronger
  response to a clean vertical step than to a period-two checkerboard or fixed
  seed-17020 small Gaussian perturbation around mid-gray.

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
working-grid limit, scan directions, segment model, noise estimator, BIC
penalty, raster assignment, direction merge, resize, eligibility,
calibration, integration, context, gate, localizer, or thresholds from the
result. Do not advance to diagonal, multiscale, color/texton, smoothed,
segment-count-marginalized, learned-penalty, UCM, full-SGBD, scanline-DP, or
change-point variants.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `semiglobal_changepoint_calibration.csv`,
`semiglobal_changepoint_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and semi-global change-point cue.
