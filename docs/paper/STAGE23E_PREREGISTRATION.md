# Stage 23E preregistration - cached descriptor x aggregator landscape

## Role and firewall

Stage 23E is the bounded UDED aggregation screen authorized by Stage 23D. It
uses only the exact 182 cached descriptor maps from Stage 23C and the immutable
input sets in
`results/local_dev/stage23d_cached_complementarity_map/stage23e_input_sets.json`.
The excluded protected-lineage item `03-35028` remains excluded before image or
GT bytes are read. No descriptor extractor, cache repair, protected split, or
BSDS500-validation candidate map is permitted. The official attachment is
incumbent-only; Stage 23F is the first candidate validation landscape.

This stage identifies a small validation frontier and empirical
`evidence structure -> aggregation behavior` relationships. It cannot promote
a detector or alter compact MFI.

## Input sets and folds

The input sets are exactly the eight ordered pairs, four ordered triples,
five-cue incumbent anchor, and two single controls emitted by Stage 23D. They
may not be reordered, replaced, or backfilled. Reuse the five-repeat,
three-fold image-grouped UDED partition with seed `20261029` and the unchanged
41-point tolerant-F1 threshold grid. The UDED tolerance is `0.0075` of the
image diagonal and is not Berkeley one-to-one matching.

Every descriptor artifact must be reconstructed from its Stage-23C cache
identity and loaded through `load_cached`. Pass requires exactly 182 cache hits,
zero computations, and no manifest/hash/provenance failure.

## Shared membership interface

Within each outer training fold and descriptor set, each positive evidence map
uses the same monotone sigmoid membership for all families. The midpoint is the
mean of the training tolerant-boundary and background medians; scale is the
pooled training IQR with fixed floor `0.05`; direction is fixed positive.
Training targets are the tolerant GT union at `0.0075` diagonal. No family may
refit or reverse a membership. Model fitting uses at most 30,000 deterministic
class-balanced training pixels per set and fold.

## Frozen aggregator families

The eight families are exactly those frozen in the Stage-23 census:

1. `equal_arithmetic_mean`: fixed equal mean.
2. `nonnegative_logistic_additive`: class-balanced logistic loss on the common
   memberships, nonnegative coefficients, intercept, L2 ridge `1e-3`.
3. `maximum_disjunction`: fixed pixelwise maximum.
4. `minimum_conjunction`: fixed pixelwise minimum.
5. `median_owa`: fixed central order statistic; for an even input count use the
   arithmetic mean of the two central values.
6. `sugeno_capacity`: max-min Sugeno evaluation using exactly the same fitted
   monotone 2-additive capacity table as family 8. This shared capacity fit
   isolates max-min versus arithmetic Choquet semantics.
7. `distorted_choquet_gamma055`: ordinary Choquet increments with singleton
   weights equal to fixed positive training effect/reliability weights and
   gamma `0.55`.
8. `monotone_2additive_choquet`: repository constrained 2-additive fit using
   class-balanced squared error, ridge `1e-4`, and at most 30,000 samples.

The shared 2-additive capacity must converge and pass normalized monotonicity
checks. No scalar post-calibration is applied to families 1 or 3--8; the
logistic probability is intrinsic to family 2. Detection thresholds remain
outer-training-fold fitted.

## Algebraic aliases

All 120 nominal set-family cells are recorded. For a one-input set, families
1 and 3--8 are the same common membership and are evaluated once with explicit
alias rows; family 2 remains distinct for calibration diagnostics. For a
two-input set, `median_owa` is an alias of `equal_arithmetic_mean`. Aliases do
not count as independent wins or frontier candidates.

## Measurements

For every nominal cell report aggregate precision/recall/F1, mean and standard
deviation of fold F1, threshold mean/dispersion, fold wins versus the equal-mean
cell on the same inputs, support density, deterministic class-balanced
Brier/ECE, tolerant-union AUC and AP proxies, runtime, fit status, and model
hashes. Report F1 and AP deltas against both the equal-mean cell and the
strongest Stage-23C individual descriptor in the set. Preserve all negative
cells.

The AUC/AP/calibration sample is a deterministic maximum of 2,048 pixels per
validation image and is identical across families in a fold. These are UDED
tolerant-union diagnostics, not official Berkeley AP.

## Frozen Stage-23F frontier rule

Singles and algebraic aliases cannot enter the frontier. For each multi-input
set, take its best non-alias family among families 2--8 by descending mean fold
F1, then tolerant-union AP proxy, then canonical family id. A record is valid
only if every prediction is finite and bounded and every required fitted model
converged.

For each record compute

`0.50*(F1 - equal_mean_F1) + 0.25*(F1 - best_individual_F1) +`
`0.25*(AP_proxy - equal_mean_AP_proxy)`.

Sort by this score, then mean fold F1, AP proxy, input-set id, and family id.
A greedy pass selects at most three primary cells, with distinct input sets and
at most two appearances of one aggregator family. For every selected primary
cell, forward its matched equal-mean cell as a control. Thus Stage 23F receives
at most six cells. A negative score does not authorize backfilling or a new
family; it is retained transparently if all bounded candidates are negative.

## Required artifacts and pass condition

Required outputs are `descriptor_cache_provenance.csv`,
`landscape_cells.csv`, `fold_metrics.csv`, `per_image_metrics.csv`,
`fit_parameters.csv`, `evidence_aggregator_profiles.csv`,
`stage23f_frontier.json`, `runtime.csv`, `summary.json`, an incumbent-only
`official_eval_manifest.json`, and `best_method_preview.png`. The preview uses
fixed overlap-clean positions 1, 7, and 14 with input, GT, first-repeat
out-of-fold score/prediction for the highest-ranked primary cell, and its
matched equal-mean score/prediction. It is documentary only.

Pass requires the exact cache contract, all 120 nominal cells, 15 folds per
cell, finite metrics and predictions, all required fitted-model convergence,
complete artifacts, and no protected-lineage byte read. A pass advances to a
separate Stage-23F preregistration; it does not promote a model.
