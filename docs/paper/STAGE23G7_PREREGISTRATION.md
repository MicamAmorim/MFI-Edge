# Stage 23G7 preregistration - Compass scale-persistence gap diagnosis

## Role and prospective hypothesis

Experiment ID: `stage23g7_compass_persistence_gap_diagnosis`.

Stage 23G7 is a frozen-map diagnosis, not an intervention or promotion
experiment. Stage 23G6 supplied the exact Compass surface on both authorized
development domains. Compass compares opposed adaptive CIE-Lab distributions
at the single published sigma-4 scale and maximizes Earth Mover's Distance over
orientation. The author project explicitly leaves integration across scale as
unresolved. The single missing-family hypothesis is therefore the already
frozen `gabor4_scale_persistence` evidence map.

This choice does not reinterpret the failed SCO/persistence equal-mean
intervention. That result remains binding evidence against preselecting equal
mean or any other downstream fusion for Compass. No other cue is screened.

## Frozen inputs and cache contract

No detector or descriptor may run.

- UDED target maps are the fourteen exact-author Compass PNGs from Stage 23G6;
  protected-lineage item `03-35028` remains excluded before byte access.
- UDED cue maps are the exact Stage-23C cached persistence artifacts.
- BSDS target maps are the 100 frozen Stage-15F Compass PNGs.
- BSDS cue maps are the exact Stage-23F cached persistence artifacts.
- Every target PNG, cache identity, manifest, and artifact hash must validate.
  Missing or mismatched input fails closed; extraction, repair, or regeneration
  is forbidden.

Expected accounting is 114 cue-cache hits, zero detector runs, and zero
descriptor computations.

## Threshold and spatial contract

The diagnosis creates no fused map. UDED Compass thresholds are fitted only on
outer-training images in the fixed 5x3 partition with seed `20261031`; UDED
persistence uses the exact Stage-23C outer-training thresholds. BSDS Compass
uses the frozen Stage-15F standard-Berkeley ODS threshold, while persistence
uses the frozen all-overlap-clean-UDED Stage-23F membership midpoint. BSDS
annotations fit nothing.

Spatial support uses union-GT proximity at `0.0075` image diagonal. Preserve
rank correlation, target/cue GT coverage, cue-only GT support, rescue of target
misses, unsupported cue response, and `P(cue correct | Compass wrong)`. These
are descriptive gap measures, not official ODS/OIS/AP.

## Frozen gap-support rule

Persistence is a supported Compass gap only if all four conditions hold
separately on overlap-clean UDED and BSDS500 validation:

1. mean cue-only GT fraction is at least `0.02`;
2. mean `P(cue correct | Compass wrong)` is at least `0.50`;
3. cue-only GT support is nonempty on at least `60%` of images;
4. mean Compass/cue Spearman correlation is at most `0.80`.

Failure closes Compass/persistence without substitution. Passing authorizes
only a later separately preregistered intervention decision. It does not
authorize equal mean, a weight search, a scale sweep, cue substitution,
Choquet backfill, routing, or Compass parameter changes. Any later aggregation
must be chosen prospectively while preserving the negative Stage-23F and G5
evidence and the Stage-23 promotion framework.

## Outputs and decision limits

Required outputs are `summary.json`, `per_image_gap_metrics.csv`,
`frozen_input_provenance.csv`, `threshold_provenance.csv`,
`official_eval_manifest.json`, and `best_method_preview.png`. The fixed preview
uses UDED positions 1/7/14 and BSDS validation positions 1/50/100, with columns
input / GT union / exact Compass / cached persistence.

The official attachment is incumbent-only because no candidate map exists.
Stage 23G7 cannot alter compact MFI, promote Compass, or make a final benchmark
claim. Berkeley reference reproduction remains unverified.
