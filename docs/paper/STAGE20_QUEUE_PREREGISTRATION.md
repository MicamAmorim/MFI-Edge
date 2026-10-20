# Stage 20 frozen candidate queue preregistration

Status: frozen at Stage 19E before any Stage-20 candidate execution or
BSDS500-validation candidate result was inspected.

The authoritative machine-readable queue is
`automation/stage20_frozen_queue.json`. Its four entries are the complete
Stage-20 campaign. A failed candidate cannot be replaced, modified, reordered,
or used to change a later entry. There is no fifth candidate. The first passing
candidate stops the queue for generation freeze and confirmation planning. If
all four fail, the bounded program ends with a synthesis and no automatic
literature escalation.

## Evidence and family choice

Stage 19B found positive boundary association for all twelve frozen cues in
both development domains. Stage 19C then froze the six-cue shortlist:
`structure_tensor_coherence`, `gabor4_s13`,
`semiglobal_changepoint`, `hessian_s13`, `brightness_entropy`, and
`gabor4_s5`. Stage 19D ranked the monotone 2-additive Choquet family first by
the preregistered weaker-domain rule (balanced log loss `0.540647`, AUC
`0.822024`) without transfer collapse. The additive/logistic family was marked
transfer-collapsed and is excluded. Grabisch's 2-additive capacity formalism
(DOI `10.1016/S0165-0114(97)00168-1`) is used only for its bounded pairwise
interaction representation; the empirical selection comes solely from the
completed Stage-19 development analyses.

Stage 19C's positive shared-interaction-stability graph among shortlisted cues
contains `gabor4_s5--semiglobal_changepoint`,
`hessian_s13--semiglobal_changepoint`, `gabor4_s13--hessian_s13`,
`gabor4_s5--hessian_s13`, `gabor4_s13--semiglobal_changepoint`, and
`gabor4_s5--gabor4_s13`. Stage 19D's fitted capacities concentrated their
stable negative interaction on `gabor4_s13--semiglobal_changepoint`. These
pre-outcome facts define the pruned queue entries below.

## Shared implementation contract

Every entry changes the compact context only. Median conditioning, grayscale
Scharr+NMS localization, context-gate strength `2.0`, floor `0.10`, threshold
grid, and threshold fitting remain unchanged. For each outer UDED training
fold, raw cue maps are mapped to memberships using the Stage-19D median/IQR
rule, then a monotone 2-additive capacity is fitted with the existing
constrained learner, ridge `1e-4`, at most `30000` balanced samples, and the
established generation-2 seed `20261009`. The Stage-19D class-balanced scalar
logistic calibration with its fixed `1e-3` ridge is then fitted on the outer-training pixels and applied
to the Choquet score before the unchanged context gate. Memberships, capacity,
and scalar calibration are all refitted strictly inside each outer fold.

Inputs are downscaled only when their longest side exceeds 256 pixels for the
UDED CV and full-UDED fitting path. Each training image contributes a fixed
deterministic uniform sample of at most 4096 pixels to membership fitting; the
binary target is the single UDED GT dilated by the fixed `0.0075`-diagonal
analysis tolerance. Capacity fitting uses class-balanced subsampling from
those memberships and the learner's fixed 700-iteration maximum. The outer
detector threshold is selected independently for incumbent and candidate from
the unchanged 41-point quantile grid on the training images.

The UDED axis is five repeats by three image-blocked folds on the 14-item
overlap-clean selection manifest. Known item `03-35028` is excluded from
fitting and evaluation because its filename lineage identifies protected
BSDS500-test image `35028`; its image and GT bytes are not read. Candidate and
incumbent thresholds are fitted independently on each outer training fold.
For the BSDS500-validation attachment, the candidate memberships and capacity
are fitted once on all 14 overlap-clean UDED-selection images, without reading
BSDS train, validation GT, or protected data, and are applied at native
resolution. Predictions are serialized directly as 8-bit soft PNGs without
per-image normalization. The ordinary stochastic/reference-unverified Windows
Berkeley path remains required; the diagnostic fixed-seed matcher is forbidden.

Every run must emit `summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `capacity_parameters.csv`, `runtime.csv`,
`best_method_preview.png`, and `official_eval_manifest.json`. The preview uses
fixed overlap-clean UDED positions 1, 7, and 14 and has columns: input, ground
truth, incumbent out-of-fold prediction, candidate out-of-fold prediction,
and candidate continuous score. It is documentary only.

The conjunctive promotion rule is identical for all four entries. Relative to
the compact incumbent on the same 14 images, UDED aggregate F1 must improve by
at least `+0.002`, aggregate precision must be nonnegative, aggregate recall
must be at least `-0.003`, mean paired fold F1 must be nonnegative, and the
candidate must win at least 9 of 15 folds. All 15 capacity fits must converge;
predictions must be finite and bounded; candidate score support must exactly
equal incumbent support. The official attachment must complete, BSDS500-
validation ODS must improve by at least `+0.002`, and OIS and AP must both be
nonnegative. All conditions are required.

## Frozen order

1. `stage20a_full_shortlist_2additive_choquet`: all six Stage-19C cues. This
   is the direct translation of the family-identification result.
2. `stage20b_interaction_core_2additive_choquet`: `gabor4_s13`,
   `semiglobal_changepoint`, `hessian_s13`, and `gabor4_s5`, the positive
   shared-interaction core from Stage 19C.
3. `stage20c_dominant_pair_2additive_choquet`: `gabor4_s13` plus
   `semiglobal_changepoint`, the minimal pair carrying Stage 19D's dominant
   stable fitted interaction.
4. `stage20d_incumbent_bank_2additive_choquet`: the retained five-member bank,
   isolating the identified aggregation family as the only architecture
   change.

No entry may add isotonic calibration, mix the candidate with the incumbent,
change descriptor definitions, constrain a pair after inspecting an outcome,
or change fitting/evaluation parameters. Compact MFI remains incumbent until a
candidate passes the full rule.
