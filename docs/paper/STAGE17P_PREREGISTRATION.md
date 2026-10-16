# Stage 17p preregistration - local robust-gradient outlier context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Black and Sapiro, *Edges as Outliers: Anisotropic Smoothing Using Local Image
Statistics* (Scale-Space 1999, LNCS 1682:259-270, DOI
`10.1007/3-540-48236-9_23`; author PDF
`https://cs.brown.edu/research/pubs/pdfs/1999/Black-1999-EOA.pdf`), interpret
edges as gradient-magnitude outliers relative to robust local gradient
variation. Their central mechanism is that the gradient needed to count as an
edge should rise in textured regions and fall in locally smooth regions. They
estimate robust gradient scale with the median absolute deviation (MAD), using
the Gaussian-consistency factor `1.4826`, and use that scale to control
anisotropic diffusion.

Stage 17p tests only the local robust-statistical representation as one
positive context membership. It performs no diffusion, restoration, or edge-
stopping iteration and therefore is a bounded repository surrogate rather
than a reproduction of the complete Black-Sapiro method. The hypothesis is
that local gradient outlier salience will suppress repeated texture while
retaining weak boundaries that are unusual in their own neighbourhood, which
may transfer more consistently across the UDED/BSDS regime difference than
another absolute activity cue.

This is distinct from Stage 17d's image-global Gaussian Markov conditional
innovation, Stage 17b's opposed-half Mann-Whitney contrast, Stage 17l's fixed
annular surround density, and the closed conditioning/PDE family. It uses
actual local gradient amplitude and a robust local dispersion estimate; it
does not rank opposed intensity samples, posit a global generative field,
compare fixed surround bands, or modify the image/localizer.

## Fixed candidate

On the unchanged median-conditioned grayscale image, compute scikit-image's
Scharr magnitude `g` before NMS. In one centered `9x9` window with reflection
at raster boundaries, compute

- `m = median(g)`,
- `s = 1.4826 * median(|g-m|)`, and
- `d = max(g-m,0)`.

Define bounded positive evidence

`E = d / (d+s)`

when the denominator is greater than the fixed numerical floor `1e-12`, and
zero otherwise. The `9x9` window is the single preregistered repository
discretization: it provides 81 samples for a local robust majority while a
one-pixel contour occupies a minority of the window. It is not claimed as a
published Black-Sapiro default and is not searched. `E` lies in `[0,1]`, is
zero on a constant field, and is invariant to positive global intensity
scaling (up to the numerical floor). There is no image-wise normalization,
adaptive window, noise fit, threshold, or searched coefficient.

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
  on a flat field, deterministic repeatability, positive-intensity-scale
  invariance, and clean-step response greater than fixed checkerboard and
  seeded-noise controls.

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
window, gradient operator, robust center/scale, MAD factor, excess or bounded
mapping, boundary handling, eligibility, calibration, integration, context,
gate, localizer, or thresholds from the result. Do not advance to multiscale,
anisotropic, color, oriented-window, alternative M-estimator, adaptive-window,
diffusion, restoration, or learned outlier variants from the outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `robust_outlier_calibration.csv`,
`robust_outlier_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and robust-gradient outlier cue.
