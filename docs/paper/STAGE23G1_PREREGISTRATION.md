# Stage 23G1 preregistration - SED opposed-distribution gap diagnosis

## Role and target selection

Experiment ID: `stage23g1_sed_halfdisc_gap_diagnosis`.

Stage 23G1 is a frozen-map diagnosis, not a detector intervention or promotion
experiment. The selected strong non-neural target is Akbarinia and Parraga's
full Surround-modulation Edge Detector (SED), using the exact author MATLAB
implementation pinned at commit
`11514b80162e5cd93fd244515189649656105a14`.

SED is selected because it is the strongest exact, strictly untrained
Stage-15 reference under the common BSDS500-validation path
(`0.678546/0.709152/0.712814` ODS/OIS/AP), already has frozen native BSDS
validation maps, and already has frozen UDED-selection maps. The local Berkeley
matcher remains reference-unverified, and the paper's BSDS500-test metrics are
documentary only. No protected or test outcome selects this target.

The primary paper and official repository were refreshed live at this
checkpoint. SED already contains balanced and imbalanced color opponency,
twelve-orientation Gaussian derivatives, V1 full/far/iso/orthogonal surround,
multiscale far-surround response, V2 orthogonal pooling/texture suppression,
shape feedback, and author NMS. It does not explicitly compare opposed local
region distributions. The single missing-family hypothesis is therefore the
already frozen Stage-23 half-disc distribution-contrast map.

This choice is supported prospectively, not by a new detector score. In Stage
23C the half-disc cue was a deliberately retained weak single map; in Stage 23D
it had low rank redundancy and stable unique GT support across many families,
including the highest selected pairwise complementarity score with FH region
boundaries (`0.670820`). Stage 23F did **not** validate any nontrivial
aggregation relationship: minimum and nonnegative logistic aggregation gained
ODS/OIS but lost AP, and median OWA failed all metrics. Those failures remain
negative evidence and are not reinterpreted as success.

## Frozen inputs and cache contract

No detector or descriptor may run.

- UDED target maps: exact Stage-16b author-SED PNGs. The known protected-lineage
  item `03-35028` is excluded before its image, GT, or SED-map bytes are read.
- UDED cue maps: exact Stage-23C cached
  `halfdisc_distribution_contrast` artifacts for the fourteen overlap-clean
  images.
- BSDS target maps: exact Stage-15b native-resolution author-SED PNGs.
- BSDS cue maps: exact Stage-23F native-resolution cached half-disc artifacts
  for all 100 validation images.
- Every SED PNG must match its frozen recorded SHA-256. Every descriptor cache
  identity, manifest, and artifact hash must validate. A miss or mismatch fails
  closed; extraction or repair is forbidden in this experiment.

The expected accounting is fourteen UDED and 100 BSDS cue-cache hits, zero
descriptor computations, and zero detector runs.

## Threshold and spatial contract

This diagnosis creates no fused score.

- UDED SED is binarized at a diagnostic threshold fitted only from the
  overlap-clean outer-training images in the identical Stage-23 5x3 partition.
  The SED maps remain frozen; only this non-deployable analysis threshold is
  fitted, and the excluded lineage item never participates.
- UDED half-disc is binarized at its exact Stage-23C outer-training-fold
  threshold for the same occurrence.
- BSDS SED uses its existing Stage-15b standard-Berkeley ODS threshold.
- BSDS half-disc uses the already fitted full-overlap-clean-UDED membership
  midpoint from the frozen Stage-23F pair-04 model. BSDS annotations do not fit
  or normalize it.
- Spatial support uses the descriptive union-GT tolerance of `0.0075` image
  diagonal. These proximity measures are not official Berkeley ODS/OIS/AP.

For each image occurrence report SED/cue rank correlation, SED and cue GT
coverage, cue-only GT support relative to SED, rescue of SED-missed GT, cue-only
unsupported response, and `P(cue correct | SED wrong)`. Preserve all rows.

## Frozen gap-support rule

The half-disc family is declared a supported SED gap only if **all four**
conditions hold separately on both overlap-clean UDED and BSDS500 validation:

1. mean cue-only GT fraction is at least `0.02`;
2. mean `P(cue correct | SED wrong)` is at least `0.50`;
3. cue-only GT support is nonempty on at least `60%` of images;
4. mean SED/cue Spearman correlation is at most `0.80`.

Failure closes the SED/half-disc route without substituting another cue or
target at this checkpoint. Passing authorizes only a separate preregistered
intervention, not promotion.

Because no Stage-23F nontrivial aggregation transferred conjunctively, the
prospective downstream aggregation is the matched
`equal_arithmetic_mean` control after the already frozen Stage-23F UDED
half-disc membership transform. It is selected for its minimal assumptions,
not because Stage 23F established superiority. It may be tested only if the
gap-support rule passes, and its exact formula/promotion rule must be registered
before execution. No weight search, logistic refit, minimum conjunction,
median OWA, Choquet backfill, or target-specific router is allowed.

## Outputs and decision limits

Required outputs are `summary.json`, `per_image_gap_metrics.csv`,
`frozen_input_provenance.csv`, `threshold_provenance.csv`,
`official_eval_manifest.json`, and `best_method_preview.png`. The fixed preview
contains UDED positions 1/7/14 followed by BSDS validation positions 1/50/100,
with columns input, GT union, exact SED score, and cached half-disc score.

The official manifest is incumbent-only because this diagnosis creates no
candidate map and the existing SED official result is already frozen. The
preview and incumbent attachment are documentary. Stage 23G1 cannot change
compact MFI, promote SED, or claim an improved detector.
