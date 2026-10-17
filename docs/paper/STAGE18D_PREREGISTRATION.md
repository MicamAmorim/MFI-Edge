# Stage 18d preregistration - active micro-drift variance context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Schmittwilken and Maertens, *Fixational Eye Movements Enable Robust Edge
Detection* (Journal of Vision 22(8):5, 2022, DOI
`10.1167/jov.22.8.5`), show that small Brownian image shifts convert spatial
luminance discontinuities into temporal response variation. Their non-oriented
multiscale model uses five isotropic difference-of-Gaussian filters, simulated
ocular drift, temporal integration, and scale-specific normalization. The
paper further shows that temporal filtering plus squared-mean integration can
be replaced by variance of the dynamically sampled filter response (the
`S-V-N` control). The official author repository is pinned at commit
`cb35f82f8c0064f346f689dbc49a34eb9d694972`; its published simulation constants
are 40 pixels/degree, diffusion `20 arcmin^2/s`, a 0.2-second fixation, 10 Hz
sampling for the variance model, ten trials, and DoG center sigmas
`0.016/0.032/0.064/0.128/0.256` degrees with surround sigma twice the center.

Stage 18d tests one bounded repository adaptation of that active-sampling
principle as context. Its causal hypothesis is temporal: a stable spatial
discontinuity should create concentrated response variance when the image is
sampled along small fixation-like shifts, while a flat region remains static.
This differs from the closed static patch/activity cues, directional
derivatives, phase/fractional localizers, conditioning filters, contour
linkers, response/region graphs, scanline or region partitions, aggregation
changes, and detector fusion. Although the cue contains multiscale isotropic
DoG filtering, it neither changes the incumbent localizer nor selects an edge
scale; variance under active micro-shifts is the single tested mechanism.

The implementation is equation-level and repository-local. It does not copy
or claim exact reproduction of the author's simulation/evaluation pipeline.
In particular, reflection preserves native raster size instead of cropping a
0.5-degree border, one preregistered seed fixes the otherwise stochastic
Brownian trials, and the normalized response is mapped monotonically into
`[0,1]` for use as a fuzzy membership precursor.

## Fixed candidate

For every unchanged median-conditioned grayscale image in `[0,1]`:

1. Construct the five isotropic DoG responses with center sigmas
   `0.64/1.28/2.56/5.12/10.24` pixels (40 pixels/degree times the published
   degree sigmas) and surround sigma exactly twice the center. Gaussian
   filtering uses reflection at raster boundaries.
2. Generate exactly ten 0.2-second Brownian drift trials from NumPy
   `default_rng(20261017)`, the published diffusion `20/60^2 deg^2/s`, and the
   published variance-control sampling rate 10 Hz. Each trial has three
   frames including the zero displacement; positions are cumulatively summed,
   converted at 40 pixels/degree, rounded to integer pixels, and accepted only
   when both axes move, matching the author-code guard. The resulting ten
   integer paths are frozen in the experiment metadata.
3. For every scale and trial, reflect-shift the DoG response along the three
   positions and compute population variance over frames. Average the ten
   trial-variance maps. Divide each scale map by its own image mean when that
   mean is nonzero, average the five normalized maps, and apply the fixed
   bounded map `E/(1+E)`. No image label, ground truth, dataset identity, or
   candidate result participates in this computation.
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
threshold grid are unchanged. There is no drift, filter, scale, trial, seed,
boundary, normalization, mapping, calibration, integration, or threshold
search.

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
- A fixed synthetic contract must verify finite bounded output, zero response
  on a flat field, exact repeatability, positive-affine invariance within
  `1e-6`, and localization of a clean vertical step. The step's response q90
  must exceed fixed low-amplitude checkerboard and seed-18004 noise q90 values.

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
8. Synthetic, finite/bounded, repeatability, runtime, and deterministic preview
   contracts complete.

Failure of any condition rejects this fixed realization. Do not tune or
extend the fixation duration, sampling rate, diffusion, pixels/degree, drift
seed or paths, trial count, DoG scales or ratio, boundary handling, temporal
statistic, normalization, bounded mapping, calibration, eligibility,
integration, context, gate, localizer, or threshold grid from the result. Do
not advance to random ensembles, subpixel/interpolated drift, oriented,
color, adaptive, learned, event-camera, temporal-filter, or full active-vision
variants, and do not combine this cue with rejected mechanisms.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `active_drift_calibration.csv`,
`active_drift_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and active-drift variance cue.
