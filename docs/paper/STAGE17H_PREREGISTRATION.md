# Stage 17h preregistration - local fractal-scaling context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Toennies and Schnabel, *Edge Detection Using the Local Fractal Dimension*
(IEEE CBMS 1994, pp. 34-39, DOI `10.1109/38.55153`) model local gray-level
variation as fractional Brownian motion. Their central observation is that an
edge adds a deterministic component that violates ordinary scale-independent
stochastic image behavior; local fractal behavior can therefore distinguish
edges from region interiors and noise. They report conventional-detector-like
behavior at low noise and greater robustness in high noise.

Stage 17h tests a fixed, bounded repository surrogate of that principle. It
asks whether reliable, high local first-order scaling exponent supplies
transferable positive boundary context. This is not a persistence transform:
it estimates a local fractional-Brownian structure-function law from image
increments and measures its exponent and fit. It is also distinct from the
closed local-rank, GMRF conditional-surprise, structure-tensor, photometric,
spectral-graph, profile, self-similarity, structural-gating, aggregation, and
localizer-replacement tests.

## Fixed candidate

Use the unchanged median-conditioned grayscale image. At dyadic pixel lags
`h={1,2,4}`, compute absolute gray-level increments along horizontal,
vertical, and the two diagonal axes. Average the four axis responses, then
take their reflection-padded `9x9` local mean. The support is not searched:
`9=2*4+1` is the smallest odd centered support containing the largest lag.
These three values form the local first-order structure function `S1(h)`.

Fit the three-point least-squares line

`log S1(h) = a + H log h`

with only machine epsilon protecting the logarithm. Let `R2` be its local
coefficient of determination. The fixed positive evidence is

`clip(H,0,1) * clip(R2,0,1) * S1(4)`.

The amplitude factor keeps a constant patch exactly zero; the exponent and
fit factors attenuate rapidly alternating or noise-like variation that lacks
a reliable positive scaling law. There is no per-image normalization,
threshold, fitted image parameter, scale selection, or target-dataset
adaptation.

Fit one positive logistic membership only inside each outer UDED-selection
training fold. Its midpoint is the mean of the training edge and texture
medians and its scale is the pooled training interquartile range, with only a
`1e-9` numerical floor. Fit its singleton weight by the established rule
`max(AUC-0.5,0) * (1+mutual_information)`. The cue is eligible only when
training edge-versus-texture AUC is at least `0.56`; an ineligible fold is
exactly the compact control. When eligible, append it as a sixth membership
and renormalize singleton weights before the unchanged distorted-Choquet
integral.

The retained five memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
threshold grid are unchanged. This is a repository surrogate of the published
fractal mechanism, not an exact reconstruction of the authors' implementation.

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
- A fixed synthetic contract must verify finite output in `[0,1]`, zero output
  on a constant field, deterministic repeatability, and stronger evidence on
  an ideal step band than on fixed checkerboard and seeded-noise controls.

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
the lags, support, directions, increment statistic, regression, clipping,
reliability/amplitude factors, boundary handling, eligibility, calibration,
context integration, Choquet parameters, gate, localizer, or thresholds from
the result. Do not advance to multifractal spectra, alternative fractal-
dimension estimators, wavelet fractals, color fractals, multiscale variants,
or learned fractal models from the outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `fractal_calibration.csv`,
`fractal_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and local fractal-scaling cue.
