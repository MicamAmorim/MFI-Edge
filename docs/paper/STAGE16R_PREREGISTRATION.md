# Stage 16r preregistration - Sugeno qualitative context aggregation

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

The completed generation-2 tests show that adding individually discriminative
cues and removing image-wise membership marginals do not resolve the recurring
BSDS-positive/UDED-weak pattern. The next bounded question is therefore not
whether another cue is missing, but whether the incumbent context's arithmetic
compensation is itself poorly transferable. A Choquet integral accumulates
weighted membership increments, so several moderate cues can compensate for a
weak one. The Sugeno integral instead uses only order, minimum and maximum: a
response is limited jointly by a membership level and the capacity of the
coalition supporting that level.

De Campos and Bolaños (1992, DOI `10.1016/0165-0114(92)90037-5`) formally
compare Choquet and Sugeno integrals and identify their shared capacity basis
but distinct quantitative versus qualitative aggregation semantics.
Marco-Detchart et al. (2023, DOI `10.1007/978-3-031-39965-7_28`) compare both
families in edge detection and report broadly similar structures with
differences in texture and external boundaries. These sources justify one
fixed max-min aggregation falsification; they do not establish that it will
improve this repository's detector.

## Fixed candidate

Let the five retained calibrated positive memberships at a pixel be sorted as
`x_(1) <= ... <= x_(5)`. Let `A_i` be the suffix coalition from `i` through
`5`. Stage 16r uses

`S_mu(x) = max_i min(x_(i), mu(A_i))`,

with exactly the incumbent capacity

`mu(A) = (sum_{j in A} w_j)^0.55`,

where the normalized singleton weights `w_j` are fit inside the same outer
UDED training fold. The control remains the ordinary distorted-Choquet
integral over the same memberships, weights and capacity. There is no mixture,
interpolation, alternative t-norm, weight search, capacity search, cue change,
or dataset adapter.

The candidate changes only the aggregation functional. The five retained
features and membership calibration, median conditioning, grayscale
Scharr+NMS localizer, gate strength `2.0`, floor `0.10`, and fold-fitted
operating thresholds remain unchanged. This is distinct from Stage 14f's RDF
increment replacement and Stage 16p's per-image marginal-rank transform.

## Development protocol

- UDED selection: five repeats by three folds with established seed
  `20261009`. Feature-bank fitting, membership calibration, singleton weights,
  and operating thresholds remain inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment with all annotations,
  99 thresholds, `maxDist=0.0075`, thinning enabled, native resolution, and
  direct 8-bit soft PNG export without per-image output normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and other protected data are not
  read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is at least `-0.002`.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are both nonnegative versus the unchanged
   incumbent.
6. Finite/bounded, repeat-determinism, componentwise-monotonicity,
   idempotence, joint-permutation, and capacity-normalization checks pass; the
   deterministic preview is present.

Failure of any condition rejects this fixed realization. Do not tune the
max-min operators, capacity, gamma, singleton weights, memberships, gate,
localizer, threshold grid, or a Choquet/Sugeno mixture from the result.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `sugeno_diagnostics.csv`,
`best_method_preview.png`, `official_eval_manifest.json`, and the controller's
official-evaluation summary. The preview uses fixed UDED-selection positions
1, 8, and 15 with columns: input, ground truth, incumbent out-of-fold
prediction, candidate out-of-fold prediction, and Sugeno context.
