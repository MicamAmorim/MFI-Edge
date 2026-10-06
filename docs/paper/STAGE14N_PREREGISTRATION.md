# Stage 14n preregistration — shallow edge-forest localizer

## Status and scientific question

This protocol is fixed before any Stage 14n metric is inspected. Stage 14n is
a development-only falsification on the 15-image UDED selection subset. UDED
held-out, BSDS500 test, BIPEDv2 test, and all other inspected external results
are excluded from model fitting, parameter choice, interpretation, and
promotion.

Stage 14m showed that a fold-fitted linear classifier over the retained
memberships and Scharr+NMS support increased precision but reduced recall and
F1. The next question is mechanistically different:

> Can a bounded randomized decision forest learn stable nonlinear cue
> interactions and a dense boundary score from the retained interpretable
> signature, while fixed gradient-direction NMS preserves localization?

This tests a non-neural learned-localizer family. It does not tune Stage 14m,
does not reproduce Structured Edges or Oriented Edge Forests, and does not
claim structured-mask prediction.

## Literature rationale and alternatives considered

Dollár and Zitnick's Structured Forests (ICCV 2013; TPAMI 2015, DOI
`10.1109/TPAMI.2014.2377715`) showed that randomized forests over simple image
channels can learn local edge structure. Hallman and Fowlkes' Oriented Edge
Forests (CVPR 2015, DOI `10.1109/CVPR.2015.7298782`) simplified the label space
to oriented edge categories, used class-balanced randomized forests, averaged
leaf posteriors, and localized the resulting boundary evidence. These papers
justify testing nonlinear forest inference without importing a neural model.

Three distinct next families were considered at the checkpoint:

1. a shallow forest localizer over the retained compact signature;
2. graph-spectral globalization of the incumbent response;
3. a full structured-patch forest with offset/orientation labels.

The first is selected because it is the smallest test of the unresolved
nonlinear-learning hypothesis after Stage 14m. Spectral globalization is
deferred because Stage 14i already failed a topology/global-consistency
intervention, while a full structured-patch forest would simultaneously
change labels, patch representation, sharpening, and compositing. A positive
Stage 14n result would justify that larger structured redesign; a negative
result will not be repaired by sweeping forest size or depth.

## Fixed data and outer protocol

- Dataset: UDED selection only, obtained exactly as `raw[0::2]` in the Stage
  12 lineage.
- Images: exactly 15.
- Resize: maximum side 256.
- Validation: five repeats by three folds from the established deterministic
  `_make_repeated_folds` schedule, seed `20261006`.
- Leakage control: compact membership calibration, forest fitting, and score
  threshold fitting occur inside each outer training fold.
- Evaluation: the existing tolerant event-count evaluator with tolerance
  `0.0075 * image diagonal` and 41 training-threshold candidates.
- Both incumbent and candidate fit their own operating threshold on the same
  outer training fold and freeze it on the paired validation fold.

## Incumbent

The control is the retained five-feature positive distorted-Choquet context
gate:

- `gabor4_s5`
- `hessian_s7`
- `gabor4_s13`
- `hessian_s13`
- `gabor4_scale_persistence`

It keeps gamma `0.55`, gate strength `2.0`, floor `0.10`, median conditioning,
and grayscale Scharr+NMS localization.

## Candidate: one bounded nonlinear localizer change

The candidate fits a pure NumPy randomized binary decision forest in each
outer training fold. Its ten fixed channels are:

1. dense raw Scharr magnitude;
2. Scharr+NMS;
3. compact Choquet context;
4. raw Scharr times context;
5. Scharr+NMS times context;
6–10. the five compact positive memberships in the order above.

The dense forest posterior replaces the fixed multiplicative gate as the
candidate score. Fixed grayscale gradient orientation then supplies ordinary
NMS. Thus the forest may recover candidate responses outside the incumbent's
already-suppressed Scharr support, but it cannot learn or alter the NMS
orientation.

Forest parameters are fixed before scoring:

- 48 trees;
- maximum depth 8;
- minimum leaf size 40;
- `ceil(sqrt(10)) = 4` randomly selected features per node;
- four random split thresholds per selected feature, drawn between its node
  10th and 90th percentiles;
- Gini-gain node selection;
- class-balanced bootstrap for each tree;
- Laplace-smoothed leaf probabilities and posterior averaging;
- at most 1,500 positive and 1,500 negative samples per training image;
- negatives split between highest raw-Scharr hard negatives and deterministic
  random negatives.

Positive training pixels are the training GT dilated by the evaluation
tolerance. This is a binary local-boundary surrogate rather than the
orientation/offset label space of OEF. No tree count, depth, leaf size,
sampling amount, channel set, loss, calibration transform, or multiscale
forest variant is swept.

## Endpoints and conjunction promotion rule

The primary endpoint is aggregate event-count F1 across all 15 outer
validation events. Promotion requires every condition below:

1. candidate aggregate F1 minus incumbent aggregate F1 is at least `+0.001`;
2. candidate aggregate precision minus incumbent aggregate precision is at
   least `-0.002`;
3. mean paired fold-F1 delta is positive;
4. the candidate wins at least 9 of 15 paired folds;
5. all 15 fitted forests produce finite validation predictions.

Training AUC, mean tree size/depth, and Gini feature importance are diagnostic
only. They cannot override the promotion conjunction.

If promoted, the shallow forest becomes a provisional development candidate
requiring another preregistered confirmation/freeze decision before any new
external evaluation. If not promoted, the compact Choquet controller remains
incumbent. Stage 14n outcomes may not be used to tune forest hyperparameters,
sampling, channels, probability calibration, or support. A failure triggers a
mechanistically distinct literature escalation; it does not license a fuller
forest sweep.

## Deterministic qualitative artifact

The runner must write `best_method_preview.png` using the first validation
image of the first deterministic split. Columns are:

1. conditioned input;
2. ground truth;
3. compact incumbent prediction;
4. shallow edge-forest prediction;
5. retained best prediction under the preregistered conjunction.

The preview is documentary only and cannot change parameters, interpretation,
promotion, or the next experiment.
