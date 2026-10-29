# Stage 23D preregistration - cached UDED complementarity map

## Role and firewall

Stage 23D is a GT-conditioned analysis over the exact 182 descriptor artifacts
created by Stage 23C. It uses only the same 14-image overlap-clean UDED
selection manifest. The excluded protected-lineage item `03-35028` remains
excluded before image or GT bytes are read. No descriptor extractor may run,
no cache artifact may be repaired or overwritten, and no protected or external
split is read.

This stage may freeze input sets for Stage 23E, but it cannot fit an aggregator,
promote a detector, or alter compact MFI. Individual Stage-23C F1 is used only
as a deterministic tie-breaker and for the two permitted single controls; it
cannot remove a descriptor before all thirteen maps enter the pairwise analysis.

## Cache and fold contract

- Reconstruct every Stage-23C cache identity from its frozen implementation and
  source hash, then call `load_cached`; any miss, hash mismatch, provenance
  mismatch, shape drift, or manifest failure aborts the experiment.
- The extractor entry point is never called. Exactly 182 cache hits and zero
  computations are required.
- Reuse the Stage-23C five-repeat, three-fold image-grouped partition with seed
  `20261029`.
- Within each outer fold, each descriptor's balanced operating threshold is
  fitted on training images with the unchanged 41-point tolerant-F1 grid and
  frozen on validation images.
- Tolerance is the repository UDED proxy at `0.0075` image diagonal. It is not
  Berkeley one-to-one matching.

## Pairwise measurements

All 78 unordered descriptor pairs are reported. Raw-score Pearson and Spearman
correlations are computed per image and summarized by their image mean and
median. At the outer-fold balanced thresholds report GT-pixel coverage shared
by both descriptors and unique to either descriptor; supported and unsupported
prediction overlap; each descriptor's unique false-positive burden; reciprocal
`P(A correct | B wrong)` and `P(B correct | A wrong)` on the union of tolerant
GT support and prediction supports; localization support; and the fraction of
image/repeat observations with bilateral nonzero unique GT coverage.

Precision-, balanced-, and recall-regime behavior is additionally measured at
outer-training pooled raw-score quantiles `0.90`, the fitted balanced threshold,
and `0.60`, respectively. These labels describe operating regimes only; they
are not official precision/recall endpoints.

## Redundancy and deterministic forwarding rule

Descriptor families are frozen in the runner. A pair is eligible only when it
is cross-family and its absolute mean per-image Spearman correlation is at most
`0.95`. Its fixed complementarity score is:

`0.25*(1-|rho_s|) + 0.25*mean(unique_GT_A+unique_GT_B) +`
`0.20*mean(reciprocal conditional correctness) +`
`0.15*bilateral-unique stability + 0.15*(1-mean unique-FP burden)`.

Every term is clipped to `[0,1]`. Eligible pairs are sorted by descending score
and then descriptor ids. A greedy pass forwards at most eight pairs, with at
most three appearances per descriptor and at most two pairs for the same
unordered family pair. The budget is not backfilled with an ineligible pair.
Redundancy clusters are connected components at absolute mean Spearman at least
`0.90`; they are reported but do not independently prune the pair list.

## Triple and control rule

Triple candidates must contain three distinct families, use only descriptors
appearing in forwarded pairs, and have all three constituent pairs among the
top 24 eligible pair rows. At most the first 24 such triples by mean constituent
pair score receive higher-order calculation. Their fixed score is:

`0.35*union_GT_coverage + 0.25*sum(member-exclusive_GT_coverage) +`
`0.20*majority_prediction_precision + 0.10*mean_pair_score +`
`0.10*exclusive-support_stability`.

The sorted greedy result forwards at most four triples, with at most two triple
appearances per descriptor. A missing qualifying triple is not replaced.

The unchanged incumbent anchor is
`gabor4_s5,hessian_s7,gabor4_s13,hessian_s13,gabor4_scale_persistence`.
Two single controls are frozen after analysis: the highest Stage-23C aggregate
F1 descriptor and the descriptor with the highest mean eligible-pair score
(falling to the next if identical). Ties are lexicographic.

## Required artifacts and pass condition

Required outputs are `pairwise_complementarity.csv`, `pairwise_per_image.csv`,
`operating_regime_complementarity.csv`, `redundancy_clusters.json`,
`triple_complementarity.csv`, `stage23e_input_sets.json`, cache provenance,
summary, an incumbent-only official manifest, and `best_method_preview.png`.
The preview uses fixed sorted positions 1, 7, and 14 with columns input, GT, and
all thirteen cached maps. It is documentary only.

Pass requires all 182 exact cache loads, all 78 pair rows, finite metrics, all
registered artifacts, no extractor call, and no protected-lineage byte read.
A pass registers Stage 23E over only the emitted sets and the eight frozen
aggregator families.
