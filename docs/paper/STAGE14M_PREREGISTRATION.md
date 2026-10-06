# Stage 14m preregistration — linear probability-of-boundary cue fusion

Date registered: 2026-10-06, before Stage 14m result inspection.

## Motivation and hypothesis

Stages 14j–14l did not establish incremental value from phase congruency,
CIELAB vector gradients, or a fixed texture-distribution feature. Adding and
tuning another descriptor is therefore not the next step. Stage 11b already
showed that a fold-trained linear diagnostic extracted signed information from
the multiscale signature, but that model was never evaluated as an edge
detector.

Martin, Fowlkes and Malik (2004, DOI `10.1109/TPAMI.2004.1273918`) formulate
local boundary detection as posterior estimation from image cues and report
that simple linear logistic cue combination was adequate. Stage 14m tests the
corresponding aggregation hypothesis in the retained MFI architecture: the
compact features may already contain sufficient evidence, while the fixed
positive Choquet gate may be too restrictive to calibrate that evidence with
the precise localizer.

The candidate is deliberately linear and auditable. It is not a neural model,
does not add a descriptor, and does not reproduce the Berkeley Pb detector.
It learns only a regularized linear probability-of-boundary mapping from the
incumbent Scharr+NMS response, compact Choquet context, their explicit product,
and the five retained membership maps. Predictions are restricted to the
Scharr+NMS support so localization remains assigned to the incumbent localizer.

## Authorized data and fixed comparison

- Use only the 15 UDED selection images.
- Use the established deterministic 5 repeats x 3 folds.
- Never load or inspect UDED held-out, BSDS500 test, or BIPEDv2 test outcomes.
- Relearn the positive bank inside every training fold, then retain exactly
  `gabor4_s5`, `hessian_s7`, `gabor4_s13`, `hessian_s13`, and
  `gabor4_scale_persistence`.
- Keep median conditioning, distorted-Choquet gamma `0.55`, Scharr+NMS,
  incumbent gate strength `2.0`, floor `0.10`, resize policy, tolerant metric,
  and fold construction fixed.
- Fit one threshold independently for each variant on each training fold and
  freeze it on the paired validation fold.

Control: the retained compact positive Choquet context multiplicatively gating
Scharr+NMS.

Candidate: class-balanced L2-regularized logistic regression with fixed
`L2=1.0` and these eight ordered inputs:

1. Scharr+NMS response;
2. compact distorted-Choquet context;
3. their product;
4. the five retained positive memberships in the order listed above.

Training samples are restricted to positive Scharr+NMS support. A sample is a
training positive when it falls within the fixed evaluation tolerance of the
training GT. Per image and class, at most 2,500 pixels are used. Candidate
negatives comprise half the highest-Scharr available negatives and half a
seeded random sample of the remainder. Standardization, coefficients, and bias
are fitted only on the outer training fold. No feature, regularization,
sampling, interaction, or classifier sweep is allowed.

## Primary endpoint and promotion rule

Aggregate tolerant F1 across all paired outer validation events is primary.
Promote the candidate only if all conditions hold:

1. aggregate F1 delta versus the incumbent is at least `+0.001`;
2. aggregate precision delta is at least `-0.002`;
3. mean paired fold F1 delta is positive;
4. the candidate wins at least 9 of 15 paired fold events; and
5. the optimizer reports convergence in all 15 fold fits.

Repeated-CV fold events are descriptive, not independent samples. If any
criterion fails, retain the compact incumbent and do not tune the linear model
from this result. A pass is development support only and requires a separate
confirmation before freezing a new generation.

## Required outputs

- `summary.json`
- `variant_ranking.csv`
- `fold_results.csv`
- `per_image_metrics.csv`
- `model_coefficients.csv`
- `training_samples.csv`
- `best_method_preview.png`

The deterministic preview uses the first validation image of the first split.
Columns are conditioned input, ground truth, compact incumbent prediction,
linear-logistic candidate prediction, and retained best. It is documentary
only and cannot affect promotion.
