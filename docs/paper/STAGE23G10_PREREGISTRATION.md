# Stage 23G10 preregistration - QFrD / FH region-boundary gap diagnosis

## Role and hypothesis

Stage 23G10 is a frozen-map diagnosis, not an intervention. Exact QFrD already
contains joint RGB quaternion fractional-spectral edge evidence, Gaussian
conditioning, NMS, and hysteresis, but no region-adaptive segmentation model.
The single missing-family hypothesis is therefore the cached Felzenszwalb-
Huttenlocher region-boundary evidence. This choice does not reopen persistence,
half-disc, or any closed SED/SCO/Compass intervention route.

## Frozen inputs

The experiment must hash-validate and reuse the fourteen Stage-23G9 overlap-
clean QFrD maps, the 100 frozen Stage-15I QFrD validation maps, and the 114
exact Stage-23 FH cache artifacts. No detector or descriptor may run. The
known protected-lineage UDED item remains excluded before byte access.

UDED QFrD thresholds are fitted only on outer-training images in the fixed
5x3 split with seed `20261031`; FH thresholds are the frozen Stage-23C outer-
training thresholds. BSDS QFrD uses the existing Stage-15I ODS threshold and
FH uses the median of the fifteen frozen Stage-23C training thresholds. BSDS
annotations fit nothing.

## Gap rule

FH support is a QFrD gap only if all four conditions hold independently on
overlap-clean UDED and BSDS500 validation:

1. mean cue-only GT fraction is at least `0.02`;
2. mean `P(cue correct | QFrD wrong)` is at least `0.50`;
3. cue-only GT support is nonempty on at least `60%` of images;
4. mean QFrD/cue Spearman correlation is at most `0.80`.

Failure closes QFrD/FH without substitution. Passing authorizes only a later,
separately preregistered intervention decision; it does not authorize a fusion,
weight search, cue substitution, QFrD parameter change, or promotion.

## Artifacts

Required outputs are `summary.json`, `per_image_gap_metrics.csv`,
`frozen_input_provenance.csv`, `threshold_provenance.csv`,
`official_eval_manifest.json`, and `best_method_preview.png`. The fixed preview
uses UDED positions 1/7/14 followed by BSDS validation positions 1/50/100 with
panels `input | GT union | exact QFrD | cached FH region boundary`. The
official attachment is incumbent-only because no candidate exists.
