# Stage 23G5 preregistration - SCO/persistence equal-mean intervention

## Role and frozen hypothesis

Experiment ID: `stage23g5_sco_persistence_equal_mean`.

Stage 23G4 passed its four gap-support conditions separately on overlap-clean
UDED selection and BSDS500 validation. Stage 23G5 therefore executes the only
intervention authorized by that preregistration: the equal arithmetic mean of
the exact author SCO score and the cached `gabor4_scale_persistence` evidence
after the frozen Stage-23E/F sigmoid membership equation. This is one bounded
candidate test, not a weight search. SCO source, parameters, rasterization,
and postprocessing are unchanged. No other cue, aggregator, router, or target
may be substituted.

## Inputs, fitting, and cache discipline

- Reuse the fourteen hash-certified Stage-23G3 SCO maps and exact Stage-23C
  persistence cache artifacts on overlap-clean UDED selection. Exclude
  protected-lineage item `03-35028` before any byte access.
- Reuse the 100 frozen Stage-15E SCO maps and exact Stage-23F persistence cache
  artifacts on BSDS500 validation. No detector or descriptor may run.
- On each UDED outer split, fit only the persistence sigmoid midpoint and scale
  with the exact Stage-23E equations on outer-training images and tolerant-union
  labels. Apply that transform to training and validation images. Fit SCO and
  candidate thresholds independently on the same outer-training images.
- For BSDS inference, use the already frozen all-14-UDED Stage-23F pair-03
  persistence midpoint `0.5513500943779945` and scale
  `0.2824956402182579`. BSDS images or annotations fit nothing.
- The candidate is exactly `0.5 * SCO + 0.5 * persistence_membership`, clipped
  only for numerical safety to `[0,1]`, then serialized by round-to-nearest
  8-bit without per-image normalization.
- Persist the BSDS candidate maps, hashes, transform provenance, and resumable
  cache/provenance records. Missing or mismatched frozen input fails closed.

## Development rules

UDED uses the fixed 5x3 image-blocked partition with seed `20261031`. Relative
to exact SCO, the UDED intervention passes only if all are true:

1. aggregate F1 improves by at least `+0.002`;
2. aggregate precision and recall each change by at least `-0.003`;
3. mean fold F1 is positive; and
4. candidate fold F1 wins at least `9/15` comparisons.

The standard Berkeley BSDS500-validation comparison is candidate versus the
same frozen exact SCO baseline at `nthresh=99`, `maxDist=0.0075`, thinning on,
and all annotations. Interpret its axes prospectively under the Stage-23
promotion amendment:

- operational transfer: delta ODS at least `+0.002` and delta OIS nonnegative;
- ranking transfer: delta AP nonnegative;
- complete transfer: both operational and ranking transfer, plus the UDED gate.

An operational pass with AP failure is a positive operational-only result, not
an incumbent replacement or Stage-23H candidate. It may authorize at most one
separately preregistered bounded ranking/calibration diagnosis. Any operational
failure or UDED-gate failure closes SCO/persistence without substitution.

## Contracts and outputs

The run must report zero detector runs, zero descriptor computations, 114 exact
cue-cache hits, finite bounded native-size maps, exact input hashes, and exact
formula repeatability. Required artifacts are `summary.json`,
`fold_results.csv`, `per_image_metrics.csv`, `transform_provenance.csv`,
`frozen_map_hashes.csv`, `official_eval_manifest.json`, the 100 frozen BSDS
candidate maps, and `best_method_preview.png`. The preview uses UDED positions
1/7/14 and BSDS positions 1/50/100 with columns input / GT union / exact SCO /
persistence membership / equal mean. It is documentary only.

Compact distorted-Choquet MFI remains the incumbent unless the complete
transfer rule passes and a later explicit freeze decision is made. Berkeley
reference reproduction remains unverified.
