# Stage 23G4 preregistration - SCO multiscale-persistence gap diagnosis

## Role and prospective hypothesis

Experiment ID: `stage23g4_sco_persistence_gap_diagnosis`.

Stage 23G4 is a frozen-map diagnosis, not an intervention or promotion
experiment. Stage 23G3 supplied the exact SCO surface on both authorized
development domains. SCO combines oriented double-opponent chromatic and
achromatic evidence at fixed Gaussian scale `1.1` with modified local
spatial-sparseness suppression, but it has no explicit cross-scale persistence
test. The single missing-family hypothesis is therefore the already frozen
`gabor4_scale_persistence` evidence map.

This choice is prospective and does not reinterpret a failed Stage-23F cell.
Persistence is part of the retained MFI bank and is available under exact
Stage-23 cache identities on both domains. The Stage-23F minimum relationship
between persistence and structure-tensor coherence failed conjunctively; that
negative aggregation result remains closed. No other cue is screened here.

## Frozen inputs and cache contract

No detector or descriptor may run.

- UDED target maps are the fourteen exact-author SCO PNGs from Stage 23G3.
  The protected-lineage item `03-35028` remains excluded before image, GT, or
  map bytes are read.
- UDED cue maps are the exact Stage-23C cached
  `gabor4_scale_persistence` artifacts for those fourteen images.
- BSDS target maps are the 100 frozen native-resolution exact SCO PNGs from
  Stage 15E.
- BSDS cue maps are the exact Stage-23F cached persistence artifacts for all
  validation images.
- Every SCO PNG, cache identity, manifest, and artifact hash must validate.
  Missing or mismatched input fails closed; extraction or repair is forbidden.

Expected accounting is 114 cue-cache hits, zero detector runs, and zero
descriptor computations.

## Threshold and spatial contract

The diagnosis creates no fused map.

- UDED SCO diagnostic thresholds are fitted only on outer-training images in
  a fixed 5x3 partition with seed `20261031`.
- UDED persistence uses its exact Stage-23C outer-training-fold thresholds.
- BSDS SCO uses its frozen Stage-15E standard-Berkeley ODS threshold.
- BSDS persistence uses the full-overlap-clean-UDED membership midpoint from
  the frozen Stage-23F pair-03 fit. BSDS annotations fit nothing.
- Spatial support uses union-GT proximity at `0.0075` image diagonal. These
  measures are descriptive and are not official ODS/OIS/AP.

For every occurrence preserve rank correlation, target/cue GT coverage,
cue-only GT support, rescue of target misses, unsupported cue response, and
`P(cue correct | SCO wrong)`.

## Frozen gap-support rule

Persistence is a supported SCO gap only if all four conditions hold separately
on overlap-clean UDED and BSDS500 validation:

1. mean cue-only GT fraction is at least `0.02`;
2. mean `P(cue correct | SCO wrong)` is at least `0.50`;
3. cue-only GT support is nonempty on at least `60%` of images;
4. mean SCO/cue Spearman correlation is at most `0.80`.

Failure closes SCO/persistence without cue or target substitution. Passing
authorizes only a separately preregistered intervention. Because no nontrivial
Stage-23F aggregation transferred conjunctively, the only prospective
downstream control is an equal arithmetic mean after the already frozen
Stage-23F persistence membership transform. No weight search, refit,
conjunction, Choquet backfill, router, or SCO parameter change is allowed.

## Outputs and decision limits

Required outputs are `summary.json`, `per_image_gap_metrics.csv`,
`frozen_input_provenance.csv`, `threshold_provenance.csv`,
`official_eval_manifest.json`, and `best_method_preview.png`. The fixed preview
uses UDED positions 1/7/14 and BSDS validation positions 1/50/100, with columns
input / GT union / exact SCO / cached persistence.

The official attachment is incumbent-only because no candidate map exists.
Stage 23G4 cannot alter compact MFI, promote SCO, or make a final benchmark
claim. Berkeley reference reproduction remains unverified.
