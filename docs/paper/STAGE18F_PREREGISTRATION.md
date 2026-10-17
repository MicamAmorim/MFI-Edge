# Stage 18f preregistration - hierarchical triangle-partition context

Status: registered before candidate execution or benchmark-result inspection.

## Hypothesis and literature basis

Ofir, Galun, Nadler, and Basri, *Fast Detection of Curved Edges at Low SNR*
(CVPR 2016, DOI `10.1109/CVPR.2016.30`), formulate faint-edge detection as
a search over an exponentially large family of curves. Their triangle-
partition tree and dynamic program aggregate contrast and shape evidence over
long candidate curves, allowing a longer edge to be detected at lower local
SNR than a short edge. The official author MATLAB repository is pinned at
commit `19dc4845b26f81b68f40bc2e3e36bfe1c59d01d2`, tree
`fa9866f16e8679e77123a2a807978886a9a83595`. Its immutable core source and
shipped Windows MEX surface passed an R2023a synthetic smoke test. No explicit
source license was located, so the ignored checkout is not redistributed.

Stage 18f tests the author response as one context cue rather than replacing
the incumbent localizer. The mechanism is image-wide hierarchical curve
evidence, not another local derivative/activity statistic, image conditioner,
response graph, accepted-region partition, contour linker, aggregation rule,
detector average, or Scharr replacement. It is also distinct from Stage 17x's
independent row/column partitions: the triangle tree searches a combinatorial
family of two-dimensional curved paths and scores their accumulated contrast
and shape.

The author implementation is designed around 129-pixel blocks. A native
author-code run would require many overlapping blocks per image and is not the
tested question. This experiment therefore uses exactly one whole-image block:
the unchanged median-conditioned grayscale image is isotropically fitted into
`129x129`, symmetrically reflection-letterboxed, passed to
`runIm(block,false,0)`, unletterboxed, and bilinearly restored to native
support. It is an immutable-author-code integration with a disclosed fixed
raster adapter, not an exact native-resolution reproduction of the published
detector.

## Fixed candidate

1. Use the author repository and tree hashes above. Verify a clean checkout
   and the unchanged parameter-index-zero contract in `getPrm.m` before every
   run.
2. Retain author defaults: filter width `2`, minimum contrast `8`, minimum
   curve length `5`, NMS threshold `0.5`, variance-test alpha `0.1`, maximum
   turn angle `48`, shape-score weight `0.001`, radian-score weight `0.0545`,
   shape sigma `30`, tree level `3`, assumed noise sigma `0.1`, and author NMS
   enabled. The second shifted pass is disabled because the one-block entry
   point is called with `addShift=false` exactly as in the author's demo.
3. Isotropically resize the longer input side to `129` with bilinear sampling
   and antialiasing on reduction. Center it in a `129x129` reflection-padded
   square. After author inference, crop that padding and bilinearly restore the
   response to the incoming raster. The author's response normalization is
   unchanged. Its all-zero flat-field division produces non-finite values; the
   fixed I/O adapter maps only non-finite values to zero and clips to `[0,1]`,
   with no added per-image normalization.
4. Fit one positive logistic membership only inside each outer UDED-selection
   training fold. Its midpoint is the mean of edge and texture medians and its
   scale is the pooled IQR with a `1e-9` floor. Its singleton weight is
   `max(AUC-0.5,0)*(1+mutual_information)`. Eligibility requires training AUC
   at least `0.56`; an ineligible fold exactly reduces to the compact control.
5. When eligible, append the membership to the five retained memberships,
   renormalize singleton weights, and run the unchanged distorted-Choquet
   integral.

The compact bank, gamma `0.55`, gate strength `2.0`, floor `0.10`, median
conditioning, grayscale Scharr+NMS localizer, and fold threshold fitting are
unchanged. There is no source, block, scale, padding, interpolation, author-
parameter, calibration, integration, gate, localizer, or threshold search.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, triangle-cue calibration, eligibility, singleton weight, and the
  operating threshold are fit only within each outer training fold.
- BSDS500 validation: default official MATLAB attachment using all
  annotations, 99 thresholds, `maxDist=0.0075`, thinning, native-resolution
  8-bit soft output, and no export-time normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all protected data are not
  read.
- The unmodified Windows Berkeley matcher remains stochastic and reference-
  uncertified; the fixed-seed diagnostic matcher is forbidden for scoring.
- The fixed synthetic contract requires finite bounded maps, an exact zero
  flat-field response after the disclosed adapter, positive horizontal and
  vertical step responses whose maximum integrated rows/columns lie within 16
  pixels of the ideal transition, and bitwise repeatability.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is nonnegative.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The cue is training-eligible in at least `12/15` folds.
6. Candidate and incumbent soft scores have exactly the same positive support
   in every evaluated fold image.
7. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are nonnegative versus the incumbent.
8. Source provenance, synthetic, finite/bounded, repeatability, runtime, and
   deterministic-preview contracts complete.

Failure of any condition rejects this fixed realization. Do not tune or
extend the triangle tree, author detector, curve family, scores, thresholds,
NMS, working block, resampling, padding, projection, calibration,
eligibility, integration, context, gate, localizer, or threshold grid from
the result. Do not advance to tiling, multiple blocks or scales, noise-sigma
estimation, alternative author modes, color, learned curves, native full-
detector replacement, or combinations with rejected cues.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `triangle_partition_calibration.csv`,
`triangle_partition_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and triangle-partition cue.
