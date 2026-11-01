# Stage 23G8 preregistration - Compass/persistence nonnegative logistic intervention

## Role and frozen hypothesis

Experiment ID: `stage23g8_compass_persistence_logistic_additive`.

Stage 23G7 established complementarity transfer for cached
`gabor4_scale_persistence` relative to exact author Compass on both authorized
development domains. Stage 23G8 tests exactly one intervention: the Stage-23E
class-balanced nonnegative logistic additive family over two common monotone
memberships, exact Compass score and cached persistence evidence.

This choice is prospective. Compass is an opposed-region distribution detector,
so the closest frozen Stage-23 landscape analogue is persistence plus half-disc
distribution contrast. That pair selected nonnegative logistic addition on UDED
and preserved operational ODS/OIS, but not AP, on BSDS validation. Stage 23G8
therefore tests whether the same aggregation property transfers to the complete
Compass detector while retaining operational and ranking conclusions separately.
It does not reinterpret Stage 23F or the failed Stage-23G5 equal mean.

## Frozen inputs, fitting, and inference

- Reuse the fourteen hash-certified Stage-23G6 Compass maps and exact Stage-23C
  persistence cache artifacts on overlap-clean UDED selection. Exclude
  `03-35028` before byte access.
- Reuse the 100 frozen Stage-15F Compass maps and exact Stage-23F persistence
  cache artifacts on BSDS500 validation. No detector or descriptor may run.
- In each UDED outer training fold, fit both monotone memberships with the exact
  Stage-23E median/IQR equations, then fit the exact Stage-23E class-balanced
  logistic objective with nonnegative coefficients, intercept, L2 ridge `1e-3`,
  at most 30,000 deterministic class-balanced pixels, and seed `20261031` plus
  the registered fold offset. Fit baseline and candidate thresholds independently
  on the same outer-training images.
- For BSDS inference, fit one final membership/logistic model from all fourteen
  overlap-clean UDED images only. BSDS images and annotations fit nothing.
- Candidate output is the intrinsic logistic probability. Serialize by
  round-to-nearest 8-bit without per-image normalization.

No coefficient clipping beyond the registered nonnegative constraints, weight
search, equal-mean fallback, alternative aggregator, cue, target, router, Compass
parameter, or post-calibration is permitted.

## Development and transfer rules

UDED uses the fixed 5x3 image-blocked partition with seed `20261031`. Relative
to exact Compass, the UDED gate passes only if all are true:

1. aggregate F1 improves by at least `+0.002`;
2. aggregate precision and recall each change by at least `-0.003`;
3. mean fold F1 delta is positive;
4. candidate F1 wins at least `9/15` folds; and
5. all `15/15` logistic fits converge with finite nonnegative cue coefficients.

Standard Berkeley BSDS500 validation compares the frozen candidate with the
same exact Compass baseline at `nthresh=99`, `maxDist=0.0075`, thinning on, and
all annotations:

- operational transfer: `Delta ODS >= +0.002` and `Delta OIS >= 0`;
- ranking transfer: `Delta AP >= 0`;
- complete-transfer eligibility: UDED gate plus both BSDS gates.

Operational pass with AP failure is operational-only and may authorize at most
one separately preregistered ranking diagnosis under the Stage-23 amendment.
Operational or UDED failure closes Compass/persistence without substitution.

## Contracts and outputs

The run must report zero detector runs, zero descriptor computations, 114 exact
cue-cache hits, finite bounded native-size maps, exact input hashes, deterministic
model hashes, and exact formula repeatability. Required artifacts are
`summary.json`, `fold_results.csv`, `per_image_metrics.csv`,
`model_provenance.csv`, `frozen_input_provenance.csv`,
`frozen_map_hashes.csv`, `map_provenance.jsonl`, 100 frozen BSDS candidate maps,
`official_eval_manifest.json`, and `best_method_preview.png`.

The fixed preview uses UDED positions 1/7/14 and BSDS positions 1/50/100 with
columns input / GT union / exact Compass / persistence membership / logistic
candidate. It is documentary only. Compact distorted-Choquet MFI remains the
incumbent pending the complete rule, and Berkeley reference reproduction remains
unverified.
