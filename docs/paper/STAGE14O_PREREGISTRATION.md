# Stage 14o preregistration — interval uncertainty and reliability-conditioned capacity

Date registered: 2026-10-06, before any Stage-14o metric or qualitative output
was inspected.

## Question

Can explicit ignorance from disagreement among the five retained positive
memberships improve trust calibration without replacing the precise grayscale
Scharr+NMS localizer?

This is mechanistically distinct from Stage 14n. The forest attempted to learn
a nonlinear boundary posterior and lost precision. Stage 14o leaves the
incumbent features, localizer, gamma, gate, and floor fixed, and changes only
how uncertain context is represented and how it deforms the capacity.

## Primary literature basis

- Marco-Detchart et al., *Sliding window based adaptative fuzzy measure for
  edge detection*, Expert Systems 42(2):e13730, first published 2024,
  DOI `10.1111/exsy.13730`. The method supports image-local adaptation of a
  fuzzy measure instead of one globally fixed measure.
- Bustince, Barrenechea, Pagola and Fernandez, *Interval-valued fuzzy sets
  constructed from matrices: Application to edge detection*, Fuzzy Sets and
  Systems 160(13):1819–1840, DOI `10.1016/j.fss.2008.08.005`. The paper
  motivates interval width as image-derived uncertainty rather than another
  crisp membership.

The experiment is a repository-specific synthesis of these principles, not a
claim to reproduce either published detector.

## Data and leakage controls

- Primary natural-image axis: the existing 15-image UDED selection subset,
  5 repeats x 3 folds.
- UDED held-out, BSDS500 test, and BIPEDv2 test are forbidden.
- Positive-bank fitting, membership calibration, uncertainty normalization,
  and threshold fitting occur inside each outer training fold.
- BSDS500 validation is an explicitly designated development split. The frozen
  full-UDED-selection candidate is exported without reading BSDS ground truth
  and evaluated by the official MATLAB multi-annotator module.

## Fixed candidate

For the five retained compact memberships `mu_i(x)`:

1. Compute raw disagreement `d(x) = std_i(mu_i(x))`.
2. On each outer training fold only, set `s` to the pooled pixelwise 95th
   percentile of `d`; define `u(x)=clip(d(x)/s,0,1)`.
3. Define interval memberships
   `mu_i^-(x)=clip(mu_i(x)-u(x)/2,0,1)` and
   `mu_i^+(x)=clip(mu_i(x)+u(x)/2,0,1)`.
4. Let `g_C` be the retained gamma-0.55 distorted capacity and `g_A` the
   additive capacity using the same singleton weights. Use the valid local
   capacity `g_x=(1-u(x))g_C+u(x)g_A`.
5. Evaluate lower and upper Choquet envelopes under `g_x`. Their midpoint is
   contextual evidence and their width is ignorance.
6. Apply the fixed gate as
   `floor + (1-floor) * midpoint^2 * (1-width)`, then multiply by the
   unchanged grayscale Scharr+NMS localizer. The width penalty is applied once,
   outside the context power.

There is no width, quantile, gamma, gate, capacity-family, feature, or
threshold-grid sweep.

## Comparators and endpoints

The sole comparator is the retained compact positive distorted-Choquet gate,
refit under the same outer folds. UDED reports aggregate precision, recall and
F1 plus paired fold deltas. BSDS500 validation reports official ODS, OIS and
AP for incumbent and candidate.

Benchmark-aligned promotion requires every condition below:

1. UDED aggregate F1 delta at least `-0.0015`;
2. UDED aggregate precision delta at least `-0.002`;
3. UDED mean paired fold-F1 delta at least `-0.0015`;
4. candidate wins at least 6 of 15 UDED folds;
5. official BSDS500-validation evaluation completes with feedback allowed;
6. official BSDS-val ODS delta at least `+0.002`;
7. official BSDS-val OIS and AP deltas are both nonnegative.

All criteria are conjunctive. A missing/failed official attachment leaves the
promotion decision pending and triggers repair of the exporter/evaluator only;
it does not authorize rerunning or changing the scientific candidate.

## Qualitative and diagnostic outputs

`best_method_preview.png` uses the first validation image of the first
deterministic repeated-CV split. Panels are conditioned input, ground truth,
incumbent prediction, candidate prediction, uncertainty field, and the current
retained incumbent (promotion remains pending until official evaluation). The
preview is documentary only.

The runner also saves fold/image metrics and uncertainty-scale/interval-width
diagnostics. No qualitative output may alter the decision.

## Failure interpretation

Failure rejects this single fixed interval/capacity construction. It does not
show that interval-valued fuzzy sets or adaptive fuzzy measures are universally
ineffective. No post-result tuning of width, normalization quantile, capacity
endpoints, or uncertainty definition is permitted; the next experiment must
move to the Ambrosio–Tortorelli phase-field family or another mechanistically
distinct agenda item.
