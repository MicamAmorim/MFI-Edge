# Stage 22D preregistration — local competition / NMS rank-swap diagnosis

## Status and scope

This is scientific stage 4/5 of the finite Stage-22 program. It is a frozen-
pipeline diagnostic, not a detector experiment. It may not fit, select,
promote, or alter a detector; sweep an NMS parameter; rerun a matcher; read
BSDS500 test; or change compact MFI. It reconstructs the compact-MFI and
Stage-20C BSDS500-validation pipelines exactly as in Stage 21F and requires
all 200 final serialized maps to match their frozen PNGs byte for byte.

Stage 22C has already declared calibration dominant under its independent
frozen rule. That result does not change any definition or threshold below.
Stage 22E is chosen only after this stage computes the independent competition
score.

## Fixed inputs and stages

- the registered 14-image overlap-clean UDED fits used to reconstruct compact
  MFI and Stage 20C;
- the 100 BSDS500-validation images and every human annotation;
- the exact frozen compact-MFI and Stage-20C validation PNGs;
- pipeline stages `context`, shared pre-NMS Scharr, pre-NMS context/local
  product, and byte-verified final post-NMS score;
- standard-Berkeley frozen ODS thresholds `0.18` and `0.255` only for the
  descriptive final operating-point density;
- fixed preview positions 1, 50, and 100.

All pixel analyses use within-image average percentile ranks, so inter-image
score calibration cannot by itself create a local rank swap. A high-consensus
pixel is supported by at least half of an image's human annotations. A pixel
is near any annotation when it is within `0.0075` image diagonal of their
union. Local neighborhoods are fixed `5x5` squares (Chebyshev radius 2).

## Required analyses

For each method and image, report rank changes from context to pre-NMS
context/local coupling and from that coupling to final NMS. Report the mean
rank and top-decile retention of high-consensus pixels. For every
high-consensus pixel, record whether Stage 20C wins over compact MFI before
NMS but loses after NMS, and the converse.

At each method's frozen final ODS density, report near-GT prediction
multiplicity, parallel/duplicate response counts, and pre-NMS-to-final
suppression events split into high-consensus, near-union, and unsupported
locations. A parallel/duplicate response is an additional selected pixel in a
radius-2 neighborhood of a high-consensus pixel beyond the first selected
pixel.

For the early-PR attribution, take the globally highest-scoring one percent of
Stage-20C final pixels. A false positive is outside the fixed tolerant union.
It is attributed first to local competition when a radius-2 high-consensus
pixel has a higher Stage-20C pre-NMS combined score but a lower final score.
Among the remaining false positives, it is attributed to score-scale mismatch
when it would not be selected by the image's own top-one-percent cutoff. The
categories are mutually exclusive; remaining errors are unresolved. This is
a descriptive surrogate, not Berkeley matching or AP.

## NMS/competition-dominance statistic frozen before inspection

The decision statistic is computed for Stage 20C only:

1. `high_consensus_demotion_component` is the positive excess over compact
   MFI in the fraction of high-consensus pixels that start in the pre-NMS top
   quartile and lose at least `0.10` within-image percentile rank after NMS,
   divided by `0.10` and clipped to `[0,1]`;
2. `local_error_attribution_component` is the mutually exclusive local-
   competition share of Stage-20C early false positives divided by `0.25` and
   clipped to `[0,1]`;
3. `excess_multiplicity_component` is the positive relative increase in
   Stage-20C near-GT selected-pixel multiplicity over compact MFI, divided by
   `0.05` and clipped to `[0,1]`.

`competition_dominance_score` is the arithmetic mean. Local competition is
declared dominant only when the score is at least `0.60` and at least two
components are at least `0.50`. The normalizers and decision thresholds are
fixed before Stage 22D output exists.

## Mechanical continuation rule

After Stage 22D:

- calibration dominant and competition not dominant: register exactly one
  Stage-22E Branch-C candidate;
- competition dominant and calibration not dominant: register exactly one
  Stage-22E Branch-N candidate;
- both dominant: choose the larger dominance score; an exact score tie ends
  without a candidate;
- neither dominant: end Stage 22 after Stage 22D without a candidate.

No validation diagnostic may select the transform family or constants for a
Branch-C candidate, and no NMS sweep is permitted for Branch N. A candidate,
if authorized, must be fully frozen from BSDS500 train and overlap-clean UDED
training before BSDS500 validation.

## Outputs

The runner writes per-image transition, local-swap, suppression/multiplicity,
early-error-attribution, and dominance tables; `summary.json`; the canonical
fixed-position `best_method_preview.png`; and a documentary official manifest
exporting unchanged Stage-20C maps. Intermediate endpoints are diagnostic and
non-promotional. Completion either registers the single mechanically selected
Stage 22E candidate or closes the finite program under the rule above.
