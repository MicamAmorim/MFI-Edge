# Stage 16x preregistration - spectral-graph globalization context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Arbeláez, Maire, Fowlkes and Malik globalize a local boundary map by treating
the strongest intervening contour between nearby pixels as a barrier in a
sparse affinity graph, solving a normalized-cut eigenproblem, and converting
the lowest nontrivial eigenvectors back into a contour signal through their
spatial gradients (*Contour Detection and Hierarchical Image Segmentation*,
TPAMI 33(5):898-916, 2011, DOI `10.1109/TPAMI.2010.161`). The paper fixes
graph radius `5`, affinity scale `rho=0.1`, and `16` nontrivial eigenvectors.
Its spectral signal supplies image-wide partition evidence: unlike a local
patch classifier, a response is supported by the low-frequency structure of
the full image graph.

Stage 16x asks whether that global evidence can improve the compact MFI
context without replacing or suppressing the precise localizer. This directly
addresses Stage 16v's BSDS-positive but UDED recall-collapse result: the
candidate remains a sixth fold-eligible positive membership, retains the
incumbent score support through the existing positive gate floor, and must
still satisfy a strict recall non-collapse condition. It is distinct from the
closed structured/shallow forests, detector averaging, conditioning,
component/region/chain gates, connected-threshold persistence, local
profile/self-similarity cues, empirical marginal normalization, fuzzy
aggregation replacement, and finite-scale localizer replacement families.

## Fixed candidate

Use the unchanged median-conditioned grayscale Scharr+NMS map as the local
boundary input. For every pair of graph pixels within radius `5`, define

`W_ij = exp(-max(local_boundary along segment i-j) / 0.1)`.

With `D_ii=sum_j W_ij`, solve the normalized equivalent of
`(D-W)v=lambda Dv`. Retain the `16` lowest nontrivial eigenvectors, compute the
ordinary spatial gradient magnitude of each, weight it by
`1/sqrt(lambda)`, and sum. Apply only the parameter-free monotone compression
`x/(1+x)`, then bilinearly restore the native/local-development raster size.

For bounded runtime, the graph is constructed after aspect-preserving
bilinear reduction to maximum side `96`. This makes the implementation a
repository-specific bounded surrogate of spectral Pb, not exact gPb. It does
not reproduce gPb's brightness/color/texton local cues, oriented Gaussian
derivative bank, learned local-cue weights, learned spectral fusion weight, or
final sigmoid. The maximum graph side is a preregistered computational bound,
not a searched detector parameter.

The spectral cue's positive logistic membership and singleton weight are fit
only inside each outer UDED-selection training fold using the existing rule
`max(AUC - 0.5, 0) * (1 + mutual_information)`. It is eligible only when its
training edge-versus-texture AUC is at least `0.56`; an ineligible fold is
exactly the compact control. When eligible, append it as a sixth membership
and renormalize singleton weights before the unchanged distorted-Choquet
aggregation.

The five retained memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
threshold grid are unchanged. No gPb/forest weight, detector fusion, router,
or dataset identity is used.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Cue calibration,
  eligibility, singleton weight, compact bank fitting, and operating threshold
  are fit inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native-resolution 8-bit soft
  output without per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and other protected data are not
  read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.
- A fixed synthetic vertical-step contract must verify finite/bounded output,
  exact repeatability within `1e-6`, and greater mean spectral support near the
  step than in remote image bands.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is nonnegative.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The spectral cue is training-eligible in at least `12/15` folds.
6. Candidate and incumbent soft scores have exactly the same positive support
   in every evaluated fold image.
7. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are both nonnegative versus the unchanged
   incumbent.
8. The synthetic contract, finite/bounded checks, runtime diagnostics, and
   deterministic preview complete.

Failure of any condition rejects this fixed realization. Do not tune the
graph size, radius, affinity scale, line sampling, eigenvector count,
eigensolver, gradient, compression, interpolation, eligibility, membership
calibration, Choquet parameters, gate, localizer, or thresholds from the
result. Do not advance to exact/learned gPb fusion based on this outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `spectral_calibration.csv`,
`spectral_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and spectral-globalization cue.
