# Stage 21D preregistration — ranking versus localization diagnosis

## Role and frozen inputs

Stage 21D is a diagnostic-only continuation of the finite Stage-21 program. It
uses the exact frozen BSDS500-validation PNGs for compact MFI and Stage 20A--D,
their already reported standard-Berkeley ODS thresholds, and all validation
annotations. It fits no detector, changes no threshold, reruns no matcher, and
cannot promote a model. BSDS500 test is not read. Berkeley reference
reproduction remains unverified.

## Fixed diagnostics

For each frozen method, score ranking is measured against a descriptive binary
label: a pixel is positive when it lies within `0.0075 * image diagonal` of the
union of human boundary pixels. Report pooled pixel AUC, pixel average
precision, positive/negative score distributions, and image-level versions.
These are not official Berkeley metrics and do not replace one-to-one matching.

At each method's already frozen standard-Berkeley ODS threshold, report
bidirectional Euclidean distance distributions from GT union pixels to predicted
pixels and from predicted pixels to GT union pixels. Report support fractions at
`0.0075` and `0.025` diagonal without changing the maps. To probe duplicated or
parallel response, report the number of thresholded predictions within the
standard-tolerance disk around each GT pixel and the fraction with multiplicity
at least two. This is explicitly a near-GT multiplicity surrogate, not an
oriented parallel-edge count or Berkeley correspondence result.

The diagnosis must distinguish ranking evidence, localization evidence, and a
mixed explanation rather than selecting a new mechanism. The full Stage-21C
finding is carried forward: Stage 20C has higher precision-envelope values at
fixed recalls and a positive envelope-area contrast over the common recall
range, yet lower official raw-curve AP, so threshold-order irregularity must not
be hidden by an envelope-only summary.

## Artifacts and continuation

The runner writes `score_rank_diagnostics.csv`, `distance_distributions.csv`,
`tolerance_support.csv`, `duplicate_parallel_surrogate.csv`,
`per_image_diagnosis.csv`, `summary.json`, `summary.md`, the mandatory
`official_eval_manifest.json`, and a byte-identical fixed positions 1/50/100
`best_method_preview.png` from Stage 21B. Completion advances only to Stage 21E
spatial-tolerance response curves; it does not authorize Stage 21H.
