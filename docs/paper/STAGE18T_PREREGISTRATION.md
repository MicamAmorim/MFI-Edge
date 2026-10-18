# Stage 18t preregistration - isotonic membership calibration

Status: registered before candidate-result inspection. Date: 2026-10-18.

## Question and literature basis

Does the retained compact context transfer poorly because its five memberships
are forced through one hand-shaped sigmoid family, even when each underlying cue
has the correct ordering?

Zadrozny and Elkan, *Transforming Classifier Scores into Accurate Multiclass
Probability Estimates* (KDD 2002, DOI `10.1145/775047.775151`), establish that
isotonic regression can monotonically calibrate an arbitrary ranking score.
Niculescu-Mizil and Caruana, *Predicting Good Probabilities with Supervised
Learning* (ICML 2005, DOI `10.1145/1102351.1102430`), compare isotonic and
sigmoid calibration and emphasize fitting calibration without evaluation-set
leakage. Stage 18t transfers only the monotone calibration principle to fuzzy
memberships; it does not claim that the resulting memberships are population
posterior probabilities.

This is mechanistically distinct from Stage 14m's multivariate logistic cue
fusion: no joint decision boundary, interaction, regularization coefficient, or
new classifier replaces Choquet aggregation. It also differs from Stage 16p's
label-free, image-internal empirical-CDF transform: Stage 18t fits one monotone
map per retained cue using only the current outer training fold and applies that
frozen map to validation images.

## Fixed candidate

First compute the unchanged five sigmoid memberships. For each retained feature
independently, use the established deterministic edge-versus-texture samples
from the outer UDED training fold. Edge and texture each receive total sample
weight `0.5`. Fit the weighted squared-loss nondecreasing isotonic solution by
pool-adjacent violators, aggregating exact score ties first. The fitted mapping
is piecewise constant; values outside the training range receive the nearest
terminal block value.

Replace each sigmoid membership by its fold-fitted isotonic value before the
unchanged distorted-Choquet integral. The five raw features, feature selection,
singleton weights, gamma `0.55`, gate strength `2.0`, floor `0.10`, median
conditioning, grayscale Scharr+NMS localizer, and fold-fitted threshold grid are
unchanged. For the BSDS500-validation exporter, the same procedure is fitted
once on all UDED-selection development images without reading BSDS ground truth.

There is no bin count, smoothing coefficient, shrinkage strength, spline,
cross-feature term, or searched calibration choice.

## Development protocol and promotion rule

UDED selection uses seed `20261009`, five repeats by three folds, leakage-free
bank/membership/calibrator/threshold fitting, and fixed candidate mechanics.
Promotion requires all of:

- aggregate F1 delta at least `+0.002` versus compact MFI;
- aggregate precision delta at least `-0.002`;
- aggregate recall delta at least `-0.003`;
- mean paired fold-F1 delta nonnegative and at least `9/15` fold wins;
- exact candidate/incumbent positive-score support equality;
- completed official BSDS500-validation attachment with ODS delta at least
  `+0.002` and nonnegative OIS and AP deltas.

The rule is conjunctive. The Stage-15a stochastic/reference-unverified Windows
matcher caveat remains. BSDS500 test, UDED held-out, BIPEDv2 test, and other
protected feedback are forbidden.

## Fixed contracts and artifacts

Before dataset access, deterministic checks must establish finite bounded and
nondecreasing mappings, exact tie aggregation, a balanced constant-score result
of `0.5`, and bitwise repeatability. The runner records per-fold calibration
diagnostics and asserts exact positive-score support equality.

The runner must emit `best_method_preview.png` at fixed UDED-selection positions
1, 8, and 15 with columns: input, ground truth, compact-MFI out-of-fold
prediction, candidate out-of-fold prediction, and mean isotonic-calibrated
membership. It must also emit an official BSDS500-validation manifest and
native-resolution 8-bit exporter without per-image score normalization.
Qualitative outputs are documentary only.

## Locked interpretation

Do not tune or extend class weights, label definitions, sample counts, PAV loss,
ties, extrapolation, bins, smoothing, shrinkage, splines, calibration families,
feature subsets, weights, capacity, aggregation, gate, localizer, or thresholds
from the result. Do not combine isotonic calibration with rejected cues or use
BSDS validation to choose a calibration form. Failure closes this fixed
per-membership monotone-calibration realization and routes to a mechanistically
distinct live-literature checkpoint.
