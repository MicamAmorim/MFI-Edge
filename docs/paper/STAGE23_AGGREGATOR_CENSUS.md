# Stage 23 aggregation census and first-landscape shortlist

## Purpose

Stage 23 compares aggregation behavior under identical cached evidence. The
question is not whether a named operator wins in isolation, but which property
is useful for a particular complementarity/error structure. Choquet remains a
supported hypothesis, not a default conclusion.

All fitted aggregators must be trained strictly inside the outer development
fold. Fixed operators have no fitted parameters. Every family receives the same
input maps, fold membership, membership calibration contract, localizer, and
postprocessing within a factorial cell.

## Mathematical behavior census

| Family | Representative form | Behavior / assumption | Main diagnostic value |
|---|---|---|---|
| Additive sum/mean | `sum_i w_i x_i`, equal or nonnegative fitted weights | full compensation; no interactions | establishes whether combination alone explains a gain; Kittler et al. (1998) motivates the robust fixed-sum control |
| Disjunctive | `max_i x_i` | any strong source is sufficient | favors unique recall; exposes false-positive union burden |
| Conjunctive | `min_i x_i` | all sources must agree | favors consensus/precision; exposes brittle missing evidence |
| Product/geometric | product or geometric mean | soft conjunction with strong low-input penalty | catalogued, but omitted from first screen because `min` supplies the bounded conjunctive control and the factorial budget is finite |
| Order statistic / OWA | weighted sorted inputs; fixed median here | criterion identity ignored after sorting; robust k-of-n semantics | tests majority evidence without fitted interactions; Yager (1988) is the primary source |
| Sugeno / lattice | `max_A min(min_{i in A} x_i, mu(A))` | idempotent, ordinal, coalition-limited support | tests qualitative capacity semantics without arithmetic compensation |
| Choquet integral | weighted ordered increments of a monotone capacity | arithmetic compensation with explicit coalition interactions | tests whether pair synergy/redundancy matters |
| Distorted-probability Choquet | `mu(A)=(sum_{i in A} w_i)^gamma` | compact nonadditivity with no free pair parameters | incumbent low-variance control |
| 2-additive Choquet | singleton and pair Möbius terms under monotonicity | explicit bounded pair interactions | tests Stage-19's interaction finding under the new evidence landscape |
| Nonnegative logistic/additive | sigmoid of nonnegative linear score | fitted additive calibration and unequal evidence reliability | supervised classical additive control; separates weighting/calibration from nonadditivity |

## Frozen first-landscape aggregator families

Stage 23E may compare exactly the following eight families. It may not add a
ninth family after inspecting results. Exact optimization, tie handling, and
membership-calibration details must be frozen in the Stage-23E preregistration,
but those details may not change the semantic contracts below.

| ID | Canonical aggregator id | Fixed/fitted | Contract |
|---|---|---|---|
| A01 | `equal_arithmetic_mean` | fixed | equal nonnegative weights summing to one; identity-preserving additive control |
| A02 | `nonnegative_logistic_additive` | outer-fold fitted | class-balanced logistic loss, nonnegative cue coefficients, intercept allowed, one preregistered regularization value; no interactions |
| A03 | `maximum_disjunction` | fixed | pixelwise maximum |
| A04 | `minimum_conjunction` | fixed | pixelwise minimum |
| A05 | `median_owa` | fixed | central order statistic; for even input count use the arithmetic mean of the two central values, fixed before results |
| A06 | `sugeno_capacity` | outer-fold fitted capacity | discrete max-min Sugeno integral with a monotone normalized capacity; capacity-fitting objective must match A08 where mathematically possible |
| A07 | `distorted_choquet_gamma055` | outer-fold singleton fitting, fixed distortion | incumbent ordinary Choquet increments with `mu(A)=(sum w_A)^0.55`; gamma is not refit |
| A08 | `monotone_2additive_choquet` | outer-fold fitted | singleton and pair Möbius terms only, normalized monotone capacity, deterministic convex fit and convergence checks |

For one-input controls, all idempotent families collapse to the input and need
not be run redundantly. For two inputs, the median convention in A05 reduces to
the arithmetic mean and should be reported as an algebraic duplicate rather
than a separate empirical win. Stage 23E must record these structural aliases.

## Fair-comparison contract

1. Descriptor maps are loaded from the certified Stage-23 cache. An aggregator
   may not invoke a descriptor extractor.
2. Each descriptor set uses one fixed membership/calibration interface across
   all eight families. Family-specific calibration is forbidden unless the
   Stage-23E preregistration declares it as part of the mathematical family and
   supplies an equivalent control.
3. Fitted weights/capacities and detection thresholds are learned inside the
   outer UDED fold. Fixed operators see no labels.
4. Report precision, recall, F1, ranking/AP proxy, score distribution,
   calibration, localization support, stability, runtime, and fit failures.
5. Pair interaction is interpreted only relative to equal-additive and fitted-
   additive controls. A Choquet win over a single descriptor is insufficient.
6. A family that improves F1 but collapses ranking/AP is a different behavioral
   cell, not an unconditional winner.
7. All negative cells remain in the landscape table.

## Bounded factorial size

The maximum Stage-23E input sets are those frozen by Stage 23D: eight pairs,
four triples, one five-map incumbent anchor, and up to two single controls.
With algebraic duplicates skipped and explicitly labeled, this is at most 13
multi-input sets by eight aggregator families (104 nominal cells), not a
descriptor powerset. A smaller preregistered screen is allowed if Stage 23D
finds fewer qualifying complementary sets; the budget may not be backfilled
with redundant sets.

## Primary sources

- Kittler, Hatef, Duin and Matas, *On Combining Classifiers*, TPAMI 20(3),
  1998, DOI `10.1109/34.667881`.
- Yager, *On Ordered Weighted Averaging Aggregation Operators in
  Multicriteria Decisionmaking*, IEEE SMC 18(1), 1988, DOI
  `10.1109/21.87068`.
- Sugeno, *Theory of Fuzzy Integrals and Its Applications*, Tokyo Institute of
  Technology doctoral thesis, 1974.
- Grabisch, *k-order Additive Discrete Fuzzy Measures and Their
  Representation*, Fuzzy Sets and Systems 92(2), 1997, DOI
  `10.1016/S0165-0114(97)00168-1`.
- Choquet, *Theory of Capacities*, Annales de l'Institut Fourier 5, 1954,
  DOI `10.5802/aif.53`.

The literature ledger records how each source affects the Stage-23 design.
