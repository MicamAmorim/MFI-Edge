# Stage 17j preregistration - local brightness-entropy context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Shiozaki, *Edge Extraction Using Entropy Operator* (Computer Vision, Graphics,
and Image Processing 36(1), 1986, DOI
`10.1016/S0734-189X(86)80025-1`) defines the brightness values in a local
region as a normalized probability distribution. Its Shannon entropy is high
when brightness is locally even and falls when a severe brightness transition
concentrates probability unevenly. The paper uses this entropy operator to
extract smooth edge pictures without derivative filters. The primary record
fixes the mechanism, and later primary exposition of the Shiozaki distribution
states it explicitly as `p(y)=I(y)/sum I(j)`.

Stage 17j tests only that local information-concentration signal as context. It
is mechanistically distinct from Stage 17h's across-scale stochastic law,
Stage 17d's globally fitted conditional innovation, Stage 17b's opposed-sample
ranks, Stage 16z's orientation tensor, Stage 14l/15o's cross-region texture
distributions, and all closed structural, aggregation, conditioning, and
localizer replacements. No histogram binning, opposed-half comparison,
orientation selection, scale fit, or dataset adapter is introduced.

## Fixed candidate

On the unchanged median-conditioned grayscale image, use Shiozaki's fixed
`3x3` neighbourhood. For neighbourhood intensities `I_i` with positive sum
`S`, define `p_i=I_i/S` and

`E = 1 - (-sum_i p_i log p_i) / log(9)`.

An all-zero neighbourhood receives `E=0`. Reflection is fixed at raster
boundaries. The cue is already in `[0,1]`; it receives no per-image
normalization, histogram bins, threshold, orientation, or additional filter.
The implementation evaluates the algebraically equivalent stable expression
`H=log(S)-sum(I_i log I_i)/S`.

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
threshold grid are unchanged. This is an equation-level realization of the
local brightness distribution, not a reproduction of the paper's complete
thresholded edge-picture pipeline.

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
  on a constant field, deterministic repeatability, multiplicative intensity-
  scale invariance, and stronger response near a fixed step than on fixed
  low-amplitude checkerboard and seeded-noise controls.

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
the window, intensity offset, probability definition, entropy family or order,
zero-sum rule, boundary handling, eligibility, calibration, context
integration, Choquet parameters, gate, localizer, or thresholds from the
result. Do not advance to multiscale, clustered, Renyi/Tsallis, color, spatial,
histogram-binned, cross-half, or learned entropy variants from the outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `entropy_calibration.csv`,
`entropy_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and brightness-entropy-deficit cue.
