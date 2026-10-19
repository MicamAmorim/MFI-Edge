# Stage 18z preregistration - fold-fitted ICA sparse context

Status: registered before candidate-result inspection. Date: 2026-10-19.

## Question and literature basis

Can a compact, unlabeled, fold-fitted natural-image code provide a boundary
context statistic that transfers better than another hand-designed activity
cue? Bell and Sejnowski, *The "Independent Components" of Natural Scenes are
Edge Filters*, Vision Research 37(23), DOI
`10.1016/S0042-6989(97)00121-1`, showed that ICA of natural-image patches
produces localized, oriented filters and sparser responses than PCA/ZCA.
Hyvarinen, *Fast and Robust Fixed-Point Algorithms for Independent Component
Analysis*, IEEE Transactions on Neural Networks 10(3), DOI
`10.1109/72.761722`, supplies the robust fixed-point ICA estimator used here.

Stage 18z tests only the information-theoretic representation principle. It
does not reproduce an author edge detector, a biological network, or a
supervised classifier. Inference is a fixed bank of linear filters followed by
a closed-form response-concentration statistic; it contains no neural network,
neural feature extractor, or gradient-trained embedding. The ICA parameters
are fitted by classical batch matrix optimization on unlabeled development
patches.

This is the first generation-2 test in which the added primitive itself is
learned without labels inside every outer fold. It is distinct from the closed
fixed Gabor/Frei-Chen bases, supervised logistic/forest models, GMRF residual,
patch recurrence, polynomial residual, local entropy/rank/PMI, nonlinear
Teager energy, aggregation, calibration, graph, region, conditioning, and
contour-linking families. It adds no rejected cue.

## Fixed candidate

For every outer UDED training fold, sample exactly 256 patches from each
unchanged median-conditioned grayscale training image with seed derived only
from the established split seed. Patches are `7x7`, spatially mean-centered,
L2-normalized, and constant patches are discarded. Fit exactly 16 components:

1. subtract the training-patch feature mean;
2. PCA-whiten to the 16 largest positive eigen-directions;
3. run symmetric tanh FastICA for at most 500 iterations at tolerance `1e-6`;
4. symmetrically decorrelate each update and deterministically orient filter
   signs.

Nonconvergence or rank deficiency is an implementation failure, not a license
to change the component count, patch support, samples, nonlinearity, seed,
tolerance, or solver.

At each pixel, apply the fitted filters to the centered, L2-normalized local
patch. Let `a_k` be the absolute component responses and `K=16`. Evidence is

`clip((max_k(a_k)/sqrt(sum_k(a_k^2)) - 1/sqrt(K)) / (1 - 1/sqrt(K)), 0, 1)`.

A locally constant patch receives zero. This statistic is high when one
independent component dominates and low when activity is distributed across
many components. It has no fitted decision weight, per-image normalization, or
target adapter. Candidate-response calibration and the AUC `>=0.56`
eligibility decision remain inside the outer UDED training fold. When eligible,
the statistic is appended as one positive membership to the retained
distorted-Choquet context. For BSDS500 validation, both ICA and calibration are
fitted once on all UDED-selection development images without reading BSDS
ground truth.

The retained five memberships, singleton fitting, gamma `0.55`, gate strength
`2.0`, floor `0.10`, median conditioning, grayscale Scharr+NMS localizer, and
fold-fitted threshold procedure are unchanged.

## Development protocol and promotion rule

UDED selection uses seed `20261009`, five repeats by three folds, leakage-free
ICA/bank/membership/threshold fitting, and fixed candidate mechanics.
Promotion requires all of:

- aggregate F1 delta at least `+0.002` versus compact MFI;
- aggregate precision delta nonnegative;
- aggregate recall delta at least `-0.003`;
- mean paired fold-F1 delta nonnegative and at least `9/15` fold wins;
- cue eligibility in at least `12/15` folds;
- exact candidate/incumbent positive-score support equality;
- completed official BSDS500-validation attachment with ODS delta at least
  `+0.002` and nonnegative OIS and AP deltas.

The rule is conjunctive. The Stage-15a stochastic/reference-unverified Windows
matcher caveat remains. BSDS500 test, UDED held-out, BIPEDv2 test, and other
protected feedback are forbidden.

## Fixed contracts and artifacts

Before dataset access, deterministic checks must establish finite bounded
output, zero response on a flat field, positive response on a fixed step,
exact repeated inference, positive-affine invariance, repeated-model hash
identity, converged ICA, whitened-covariance accuracy, and unmixing
orthogonality. Each fit records sample count, iterations, convergence,
retained eigenvalue range, whitening error, orthogonality error, and model
hash. Per-image evidence and runtime diagnostics are also recorded. Exact
positive-score support preservation is asserted after context gating.

The runner must emit `best_method_preview.png` at fixed UDED-selection
positions 1, 8, and 15 with columns: input, ground truth, compact-MFI
out-of-fold prediction, candidate out-of-fold prediction, and deterministic
ICA concentration cue. The final cue column is documentary and may come from
the deterministic final fold model; it is not an optimization signal. The
runner must also emit an official BSDS500-validation manifest and native-
resolution 8-bit exporter without per-image score normalization.

## Locked interpretation

Do not tune or extend patch size, patch sampling, whitening, component count,
FastICA nonlinearity/iterations/tolerance, sign/order handling, response
concentration, flat rule, calibration, eligibility, integration, context,
gate, localizer, or thresholds from the result. Do not advance to sparse
coding, overcomplete dictionaries, convolutional ICA, independent subspaces,
color/multiscale ICA, supervised atom selection, learned classifiers, neural
implementations, or combinations with rejected cues. Failure closes this
fixed independent-component representation and routes to a mechanistically
distinct live-literature checkpoint.
