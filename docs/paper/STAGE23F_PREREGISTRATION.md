# Stage 23F preregistration - literature-comparable validation frontier

## Role and frozen inputs

Stage 23F is the first candidate-validation stage of the Stage-23 landscape.
It validates exactly the six cells in
`results/local_dev/stage23e_cached_descriptor_aggregator_landscape/stage23f_frontier.json`:
three prospectively selected primary cells and the equal-arithmetic-mean control
on the identical descriptor inputs. No cell, descriptor, aggregator, parameter,
or ordering may be added or replaced after BSDS500-validation access.

This is a landscape-transfer experiment, not detector promotion. Compact MFI
remains the incumbent regardless of the result. Stage 23F may establish which
`evidence structure -> aggregation property` relationships transfer to the
matched Berkeley development track and may guide the later, separately
preregistered Stage-23G gap intervention.

## Fitting and inference

The three descriptor sets are frozen by Stage 23E. Memberships and any fitted
aggregator parameters are fitted once from all 14 overlap-clean UDED-selection
images, excluding `03-35028` before byte access, using the exact Stage-23E
membership and fitting equations. Each primary and its equal-mean control share
the same fitted memberships. Validation images and annotations cannot fit or
normalize a map.

Only the four required evidence maps are extracted on native-resolution
BSDS500 validation: `gabor4_scale_persistence`,
`structure_tensor_coherence`, `halfdisc_distribution_contrast`, and
`fh_region_boundary`. Every exact descriptor map and every aggregated score
map is stored through the certified Stage-23 content-addressed cache. A valid
cache hit forbids extraction; a miss computes once; corruption fails closed.
All cached inference identities declare `gt_used=false`.

Soft scores are serialized directly to native-size 8-bit PNG without per-image
normalization. Berkeley evaluation uses all annotations, 99 thresholds,
`maxDist=0.0075`, thinning, and one-to-one matching. The local Windows matcher
remains `reference_reproduction_verified=false`; results are development-
decision-capable but cannot support a final SOTA claim.

## Transfer measurements and rule

Report ODS/OIS/AP for all six cells and compact MFI, plus primary-minus-matched-
mean deltas. A primary interaction is classified as **jointly transferable**
only if, versus its matched equal mean, ODS improves by at least `+0.002` and
OIS and AP are both nonnegative. Rank transferable primaries by ODS delta, AP
delta, OIS delta, then the frozen Stage-23E order. If none passes, record that
none of the three aggregation advantages transferred conjunctively; do not
backfill another Stage-23E cell.

This rule identifies an aggregation relationship only. It does not promote a
raw frontier cell over compact MFI and does not authorize tuning from BSDS
validation.

## Required artifacts

Required experiment artifacts are `summary.json`, `frontier_fit_parameters.json`,
`descriptor_cache_provenance.csv`, `aggregated_cache_provenance.csv`,
`frozen_map_hashes.csv`, six complete native-resolution frozen-map directories,
`official_eval_manifest.json`, and `best_method_preview.png`. The preview uses
sorted validation positions 1, 50, and 100. Each row contains input followed by
the three primary/control score pairs in frozen frontier order. It is
documentary and cannot alter the rule.

Pass requires exactly 100 images, 400 valid descriptor requests, 600 valid
aggregated-map requests, complete finite bounded native-size maps, converged
required fits, exact provenance validation, no validation-GT access by
inference, and all required artifacts. Completion advances to a separate
Stage-23G synthesis/checkpoint; it does not change the incumbent.
