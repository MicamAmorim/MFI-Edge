# Stage 17f preregistration - photometric quasi-invariant context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Van de Weijer, Gevers, and Geusebroek derive photometric quasi-invariant
derivatives from the dichromatic reflection model (*Edge and Corner Detection
by Photometric Quasi-Invariants*, IEEE TPAMI 27(4):625-630, 2005, DOI
`10.1109/TPAMI.2005.75`). For an RGB image vector `f` and one spatial
derivative `f_x`, their equations (5)-(6) remove the projection of `f_x` onto
the unit RGB direction `f_hat`. The residual is insensitive to the derivative
component attributable to achromatic shadow/shading changes while avoiding the
low-intensity instability of derivatives of fully normalized color invariants.
The paper uses Gaussian derivatives at sigma `1` in its edge experiments.

Stage 17f tests whether the combined horizontal/vertical L2 energy of that
residual supplies transferable positive boundary context. It targets a
physical cause of false boundaries rather than another grayscale texture,
rank, random-field, orientation, topology, persistence, or profile statistic.
It is also distinct from Stage 14k: that stage replaced the localizer with a
CIELAB Di Zenzo tensor magnitude, while Stage 17f leaves grayscale Scharr+NMS
unchanged and introduces only a photometrically decomposed RGB context cue.

## Fixed candidate

Apply the incumbent `3x3` reflection-padded median conditioning independently
to the three RGB channels. RGB samples are scaled by their fixed storage range
to `[0,1]`; no gamma linearization, white balancing, or per-image normalization
is applied. Compute reflection-padded horizontal and vertical Gaussian
derivatives at the paper's fixed sigma `1`. For each derivative vector `d`, compute

`d_c = d - dot(d, f_hat) * f_hat`,

with `f_hat=0` only when the conditioned RGB norm is at machine zero. The cue
is `sqrt(||d_c,x||^2 + ||d_c,y||^2)`. No per-image normalization, illuminant
estimate, color-space conversion, channel weight, threshold, or fitted image
parameter is used.

Fit one positive logistic membership only inside each outer UDED-selection
training fold. Its midpoint is the mean of the training edge and texture
medians and its scale is the pooled training interquartile range, with only a
`1e-9` numerical floor. Fit its singleton weight by the established rule
`max(AUC-0.5,0) * (1+mutual_information)`. The cue is eligible only when
training edge-versus-texture AUC is at least `0.56`; an ineligible fold is
exactly the compact control. When eligible, append it as a sixth membership and
renormalize singleton weights before the unchanged distorted-Choquet integral.

The retained five memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, grayscale median conditioning, grayscale Scharr+NMS localizer, and
fold-fitted threshold grid are unchanged. The implementation is an
equation-level repository realization of the selected published derivative,
not an exact reproduction of a complete author detector.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, cue calibration, eligibility, singleton weight, and operating
  threshold are fit only inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native-resolution 8-bit soft
  output without per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all other protected data are
  not read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.
- A fixed synthetic contract must verify finite nonnegative repeatable output,
  a stronger response to an equal-RGB-norm red/green step than to an achromatic
  intensity step, zero response on a constant color field, and numerical
  orthogonality of each residual derivative to the local RGB direction.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is nonnegative.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The cue is training-eligible in at least `12/15` folds.
6. Candidate and incumbent soft scores have exactly the same positive support
   in every evaluated fold image.
7. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are both nonnegative versus the unchanged
   incumbent.
8. The synthetic contract, finite/nonnegative checks, runtime diagnostics, and
   deterministic preview complete.

Failure of any condition rejects this fixed realization. Do not tune or vary
the RGB conditioning, derivative scale, projection, energy norm, illuminant
assumption, eligibility, calibration, context integration, Choquet parameters,
gate, localizer, or thresholds from the result. Do not advance to full
invariants, specular/hue quasi-invariants, alternative color spaces,
multiscale/color-localizer mixtures, or learned photometric variants from the
outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `photometric_calibration.csv`,
`photometric_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and photometric quasi-invariant cue.
