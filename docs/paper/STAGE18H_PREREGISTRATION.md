# Stage 18h preregistration - spectral-residual proto-object context

Status: registered before candidate execution or benchmark-result inspection.

## Hypothesis and literature basis

Hou and Zhang, *Saliency Detection: A Spectral Residual Approach* (CVPR
2007, DOI `10.1109/CVPR.2007.383267`), model image-specific statistical
innovation by subtracting a local average from the image log-amplitude
spectrum while retaining Fourier phase. Their fixed experiment computes the
log spectrum at a 64-pixel visual scale, uses a `3x3` spectral average, and
smooths the squared inverse-transform magnitude with a Gaussian of sigma `8`.
The resulting map identifies unexpected proto-object support without trained
features or object categories.

Stage 18h asks whether this image-wide statistical-innovation signal supplies
context missing from the compact local/multiscale bank. The saliency map is
not treated as a boundary detector. It enters only as a positive membership
that may gate the unchanged Scharr+NMS localizer, preserving the project's
separation of context and precise localization. This is distinct from Stage
16x's normalized-cut graph globalization, Stage 17r's directional patch
recurrence, Stage 17h's local fractal fit, Stage 16p's membership midranks,
and Stage 18f's hierarchical curve search: the tested information is global
Fourier-domain departure from the image's own average log spectrum.

The primary paper and IEEE record were checked live on 2026-10-17. A public
third-party C++/Python port exists, but no immutable official author source was
established. The experiment therefore uses an equation-level repository
implementation and makes no exact-code reproduction claim.

## Fixed candidate

1. Use the unchanged median-conditioned grayscale image. Resize it
   isotropically so its longer side is `64`, with bilinear interpolation and
   antialiasing; do not pad or distort its aspect ratio.
2. Compute the two-dimensional FFT. Set
   `L=log(max(abs(F), eps*max(abs(F))))`, where `eps` is machine epsilon.
   Compute the spectral residual `R=L-uniform3x3(L)` with periodic frequency
   boundaries. Retain the original Fourier phase.
3. Compute `abs(ifft2(exp(R + i*phase)))^2`, then Gaussian-smooth at sigma
   `8` working pixels. Divide by the image maximum when nonzero, bilinearly
   restore native support, and clip numerical roundoff to `[0,1]`. A constant
   image receives an exact-zero cue. These fixed numerical/raster conventions
   disclose the repository realization; they are not claimed as unpublished
   author-code conventions.
4. Fit one positive logistic membership only inside each outer UDED-selection
   training fold. Its midpoint is the mean of edge and texture medians and its
   scale is the pooled IQR with a `1e-9` floor. Its singleton weight is
   `max(AUC-0.5,0)*(1+mutual_information)`. Eligibility requires training AUC
   at least `0.56`; an ineligible fold exactly reduces to the compact control.
5. When eligible, append the membership to the five retained memberships,
   renormalize singleton weights, and run the unchanged distorted-Choquet
   integral.

The compact bank, gamma `0.55`, gate strength `2.0`, floor `0.10`, median
conditioning, grayscale Scharr+NMS localizer, and fold threshold fitting are
unchanged. There is no visual-scale, spectral-filter, boundary-mode,
smoothing, normalization, color, multiscale, calibration, integration, gate,
localizer, or threshold search.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, saliency-cue calibration, eligibility, singleton weight, and the
  operating threshold are fit only within each outer training fold.
- BSDS500 validation: default official MATLAB attachment using all
  annotations, 99 thresholds, `maxDist=0.0075`, thinning, native-resolution
  8-bit soft output, and no export-time normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all protected data are not
  read.
- The unmodified Windows Berkeley matcher remains stochastic and reference-
  uncertified; the fixed-seed diagnostic matcher is forbidden for scoring.
- The fixed synthetic contract requires finite bounded maps, exact zero on a
  flat field, concentration and localization on one rare disk relative to
  its background, greater response concentration than fixed periodic and
  low-amplitude-noise fields, bitwise repeatability, and multiplicative-scale
  agreement within `1e-6`.

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
   least `+0.002`, and OIS and AP are nonnegative versus the incumbent.
8. Synthetic, finite/bounded, repeatability, runtime, and deterministic-
   preview contracts complete.

Failure of any condition rejects this fixed realization. Do not tune or
extend the working scale, spectral residual, phase handling, averaging,
smoothing, normalization, raster projection, cue calibration, eligibility,
integration, context, gate, localizer, or threshold grid from the result. Do
not advance to color, multiscale, quaternion, patchwise/windowed, alternative
spectral saliency, center-bias, learned saliency, saliency-boundary gradient,
or combinations with rejected cues.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `spectral_residual_calibration.csv`,
`spectral_residual_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and spectral-residual proto-object cue.
