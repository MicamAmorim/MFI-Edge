# Stage 16p preregistration - empirical-copula Choquet context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

The repeated Stage-14/16 pattern is not simply a shortage of individually
discriminative cues: several fixed additions were eligible on UDED and improved
BSDS validation while failing the joint rule. One plausible failure mode is
that absolute membership marginals vary by image and dataset, so the retained
Choquet integral receives differently calibrated numerical evidence even when
the within-image ordering remains informative.

Zabih and Woodfill's non-parametric rank transform shows that relative ordering
can provide a robust representation when raw photometric values change
(*Non-Parametric Local Transforms for Computing Visual Correspondence*, ECCV
1994, DOI `10.1007/BFb0028345`). The probability-integral/empirical-copula
construction likewise separates marginal distributions from dependence by
mapping each variable through its empirical CDF. Stage 16p tests a bounded,
repository-specific application of that principle to the five **existing**
positive memberships. It is not a reproduction of Zabih and Woodfill's local
intensity rank transform and does not fit a target-domain adapter.

## Fixed candidate

For each image and each of the five calibrated membership maps independently,
flatten the `N` pixels, assign equal values their average one-indexed rank `r`,
and replace the value by the empirical-CDF midrank

`u = (r - 0.5) / N`.

The transform is deterministic, maps every channel strictly into `(0, 1)`,
preserves strict ordering, and maps ties to ties. The five transformed channels
are passed to the unchanged distorted-Choquet integral with the same
outer-training-fold singleton weights and gamma `0.55`. The candidate therefore
changes only the marginal representation supplied to the existing dependence-
sensitive aggregation. It does not add, remove, or refit a feature; use labels,
dataset identity, target-set statistics, or method/oracle outputs; or change the
median conditioning, gate strength `2.0`, floor `0.10`, grayscale Scharr+NMS
localizer, or threshold fitting. Each image is normalized independently using
only its own unlabeled membership maps.

The control is the unchanged compact MFI path using its ordinary fold-fitted
logistic memberships. There is no blending coefficient, neighborhood, binning,
clipping quantile, inverse-normal transform, or normalization search.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, singleton weights, membership calibration, and operating thresholds
  remain inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native resolution, and direct
  8-bit soft PNG export without per-image output normalization.
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
6. Finite/bounded, strict-order-preservation, tie-preservation, constant-map,
   and repeat-determinism checks pass; the deterministic preview is present.

Failure of any condition rejects this fixed realization. Do not tune the rank
definition, tie handling, normalization scope, feature subset, weights, gamma,
gate, localizer, or threshold grid from the result.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `rank_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and mean empirical-rank membership.
