# Stage 18p preregistration - median OWA compact-context aggregation

Status: registered before candidate execution or benchmark-result inspection.

## Hypothesis and literature basis

The long sequence of single-cue additions has usually been eligible but too
small or dataset-asymmetric, and Stage 18n was eligible in only `2/15` folds.
Stage 18p therefore adds no cue. It asks whether the incumbent Choquet
context's arithmetic compensation is less transferable than an explicit
majority-of-cues order statistic.

Yager, *On Ordered Weighted Averaging Aggregation Operators in Multicriteria
Decisionmaking* (IEEE Transactions on Systems, Man, and Cybernetics 18(1),
1988, DOI `10.1109/21.87068`), defines OWA aggregation after sorting inputs;
the median is the parameter-free OWA whose sole nonzero ordered weight selects
the central value. With the retained five memberships, this means that at
least three cues must reach a level before the context reaches that level.
Unlike Stage 16r's capacity-limited Sugeno max-min integral, this candidate has
no coalition capacity, singleton reliability weight, min-with-capacity step,
or learned aggregation parameter. It is a robust order-statistic aggregation
test, not another descriptor, a Choquet/Sugeno mixture, or a retuning of a
failed cue.

## Fixed candidate

Let the five retained fold-calibrated memberships be sorted in ascending order
as `x_(1) <= ... <= x_(5)`. The candidate context is exactly

`M(x) = x_(3)`.

Equivalently, in descending OWA order its fixed ordered-weight vector is
`[0, 0, 1, 0, 0]`. The candidate deliberately ignores the fold-fitted
singleton weights and gamma in aggregation; those quantities remain used by
the unchanged distorted-Choquet control. There is no weight search, trim
fraction, interpolation, capacity, mixture, epsilon, image-adaptive rule,
new cue, or eligibility decision.

The five retained features and fold-fitted membership calibration, median
conditioning, grayscale Scharr+NMS localizer, gate strength `2.0`, floor
`0.10`, and fold-fitted operating thresholds remain unchanged. Because the
gate multiplier is always strictly positive, the candidate and control must
preserve the localizer's positive support exactly.

## Development protocol

- UDED selection: five repeats by three folds with established seed
  `20261009`. Feature-bank fitting, membership calibration, and operating
  thresholds remain inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment using every
  annotation, 99 thresholds, `maxDist=0.0075`, thinning, native-resolution
  8-bit soft output, and no export-time normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all protected data are not
  read.
- The unmodified Windows Berkeley matcher remains stochastic and reference-
  uncertified; the fixed-seed diagnostic matcher is forbidden for scoring.
- Algebraic checks require finite bounded output, exact repeatability,
  componentwise monotonicity, idempotence, permutation invariance, exact
  equality to the central order statistic, and exact score-support
  preservation.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is nonnegative.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. Candidate and incumbent soft scores have exactly the same positive support.
6. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are nonnegative versus the incumbent.
7. All algebraic contracts and the deterministic preview complete.

Failure of any condition rejects this fixed realization. Do not tune or
extend the OWA vector, quantifier, order statistic, trimming, weights,
membership count, capacity, mixture, calibration, context gate, localizer, or
threshold grid from the result, and do not advance to adaptive, weighted,
learned, spatial, image-conditioned, or cue-selected OWA variants.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `median_owa_diagnostics.csv`,
`best_method_preview.png`, `official_eval_manifest.json`, and the controller's
official-evaluation summary. The preview uses fixed UDED-selection positions
1, 8, and 15 with columns: input, ground truth, incumbent out-of-fold
prediction, candidate out-of-fold prediction, and median-OWA context.
