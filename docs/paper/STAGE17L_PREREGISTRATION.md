# Stage 17l preregistration - isotropic surround-isolation context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Grigorescu, Petkov, and Westenberg, *Contour and boundary detection improved
by surround suppression of texture edges* (Image and Vision Computing 22,
2004, DOI `10.1016/j.imavis.2003.12.004`) augment a gradient detector with a
non-classical-receptive-field mechanism. Their isotropic form convolves local
edge energy with the positive part of a difference of Gaussians whose scales
are `sigma` and `4*sigma`. The paper's suppression slope
`atan(surround/local_energy)` is small for isolated contours and large for
dense texture edges. The primary paper reports that this contextual step
selectively suppresses texture responses while preserving isolated edges and
region boundaries.

Stage 17l tests only the complementary positive evidence carried by that
suppression slope. It does not reuse the paper's searched suppression factor,
gradient thresholds, slope hysteresis, or complete detector. This is distinct
from Stage 14b's learned negative-evidence branch, Stage 14l/15o's opposed
texture-distribution cues, Stage 16h's connected-threshold persistence,
Stage 16x's global graph, and the local entropy, fractal, GMRF, rank, tensor,
profile, self-similarity, structural-gating, conditioning, fusion, aggregation,
and localizer replacements already closed.

The fixed test is justified despite those negative results because the
published mechanism measures a different object: feature-density contrast in
an annular neighbourhood around the incumbent local edge energy. Exact SED,
the strongest matched non-trained Stage-15 reference, independently supports
surround modulation as a serious contextual family, but its frozen benchmark
outcomes do not set any Stage-17l parameter.

## Fixed candidate

Compute the established pre-NMS Scharr magnitude `M` on the unchanged
median-conditioned grayscale image. Set the inner Gaussian sigma to `1` pixel,
anchoring the annulus to the incumbent's local `3x3` Scharr footprint, and the outer sigma to the paper's fixed
`4*sigma` relation. Sample the positive part of `G_4-G_1` on a fixed radius-12
support (three outer sigmas), normalize it to unit L1 mass, and use reflection
at finite raster boundaries. Let its convolution with `M` be `t`.

At pixels with `M>1e-12`, define positive isolation evidence

`E = 1 - (2/pi) * atan(t/M)`.

At zero-energy pixels set `E=0`. The arctangent maps the paper's nonnegative
suppression slope to `[0,1]`; the ratio makes `E` invariant to positive global
rescaling of `M`. There is no suppression-strength parameter, threshold,
orientation weighting, image-wise normalization, or searched spatial setting.

Fit one positive logistic membership only inside each outer UDED-selection
training fold. Its midpoint is the mean of the training edge and texture
medians and its scale is the pooled training interquartile range with only a
`1e-9` numerical floor. Fit its singleton weight by the established rule
`max(AUC-0.5,0) * (1+mutual_information)`. The cue is eligible only when
training edge-versus-texture AUC is at least `0.56`; an ineligible fold is
exactly the compact control. When eligible, append it as a sixth membership
and renormalize singleton weights before the unchanged distorted-Choquet
integral.

The retained five memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
threshold grid are unchanged. This is an equation-level repository surrogate,
not an exact reproduction of the published detector or postprocessor.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, cue calibration, eligibility, singleton weight, and operating
  threshold are fit only inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native-resolution 8-bit soft
  output without per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all other protected data are
  not read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.
- A fixed synthetic contract must verify finite bounded output, zero response
  on a zero-energy field, unit annular-kernel mass with a zero centre,
  deterministic repeatability, positive-scale invariance, and greater mean
  evidence on one isolated line than on fixed dense-line and seeded-random
  edge fields.

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

Failure of any condition rejects this fixed realization. Do not tune or vary
the Gaussian scales or ratio, numerical support, kernel rectification,
orientation dependence, energy source, suppression slope mapping, boundary
handling, eligibility, calibration, context integration, Choquet parameters,
gate, localizer, or thresholds from the result. Do not advance to adaptive,
anisotropic, multiscale, color, end-stopped, facilitated, or learned surround
variants from the outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `surround_calibration.csv`,
`surround_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and isotropic surround-isolation cue.
