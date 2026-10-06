# Stage 14l preregistration — oriented texture-distribution context

Date registered: 2026-10-06, before Stage 14l result inspection.

## Motivation and hypothesis

The retained compact context bank contains local Gabor and Hessian amplitudes
plus Gabor scale persistence, but it does not compare the distributions of
texture primitives on opposite sides of a putative boundary. Martin, Fowlkes
and Malik (2004, DOI `10.1109/TPAMI.2004.1273918`) showed that pointwise
brightness gradients and explicit two-sided texture-distribution gradients are
complementary local boundary cues. Their texture gradient compares texton
histograms in oriented half-discs with the chi-square distance. Ojala,
Pietikäinen and Mäenpää (2002, DOI `10.1109/TPAMI.2002.1017623`) established
rotation-invariant uniform local binary patterns and their occurrence
histograms as a compact non-neural texture representation.

Stage 14l tests a fixed, texton-free surrogate for that mechanism: uniform-LBP
histograms in opposed oriented half-discs, compared by chi-square distance.
It is not claimed to reproduce the learned Berkeley texton feature. The
hypothesis is that a two-sided texture-distribution shift supplies contextual
boundary evidence not represented by the incumbent pointwise amplitudes and
improves repeated-CV F1 while Scharr+NMS retains pixel localization.

## Authorized data and fixed comparison

- Use only the 15 UDED selection images.
- Use the established deterministic 5 repeats x 3 folds.
- Never load or inspect UDED held-out, BSDS500 test, or BIPEDv2 test outcomes.
- Relearn the positive bank inside every training fold, then retain exactly
  `gabor4_s5`, `hessian_s7`, `gabor4_s13`, `hessian_s13`, and
  `gabor4_scale_persistence`.
- Keep distorted-Choquet gamma `0.55`, Scharr+NMS, context-gate strength `2.0`,
  floor `0.10`, resize policy, tolerant metric, and fold construction fixed.
- Fit one threshold independently for each variant on each training fold and
  freeze it on the paired validation fold.

Control: the five-feature compact positive context.

Candidate: append one maximum-oriented texture-distribution feature computed
from rotation-invariant uniform LBP with 8 neighbors at radius 1. Compare its
10-bin occurrence histograms in opposite half-discs by chi-square distance at
8 evenly spaced orientations. The half-disc radius is fixed at 2 percent of
the resized image diagonal, with a minimum of 3 pixels. These settings are
fixed before UDED scoring; no descriptor, bin, radius, orientation, smoothing,
or fusion sweep is allowed.

Within each training fold, fit only the feature's positive membership midpoint,
scale, and singleton weight from edge-versus-hard-texture samples. The feature
is eligible when training AUC is at least `0.56`; otherwise that fold's
candidate equals the control. Eligibility in at least 12 of 15 folds is a
required promotion criterion. This prevents validation labels from deciding
whether or how the feature enters the model.

## Primary endpoint and promotion rule

Aggregate tolerant F1 across all paired outer validation events is primary.
Promote the candidate only if all conditions hold:

1. aggregate F1 delta versus the incumbent is at least `+0.001`;
2. aggregate precision delta is at least `-0.002`;
3. mean paired fold F1 delta is positive;
4. the candidate wins at least 9 of 15 paired fold events; and
5. the texture-distribution feature is training-eligible in at least 12 folds.

Repeated-CV fold events are descriptive, not independent samples. If any
criterion fails, retain the compact incumbent and do not tune this feature
from the result. A pass is development support only and requires separate
confirmation before a new generation is frozen.

## Required outputs

- `summary.json`
- `variant_ranking.csv`
- `fold_results.csv`
- `per_image_metrics.csv`
- `texture_calibration.csv`
- `best_method_preview.png`

The deterministic preview uses the first validation image of the first split.
Columns are conditioned input, ground truth, compact incumbent prediction,
compact-plus-texture-distribution prediction, and retained best. It is
documentary only and cannot affect promotion.
