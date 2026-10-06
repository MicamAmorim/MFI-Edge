# Stage 14j preregistration — phase-congruency context feature

## Status and scientific question

This protocol is registered before Stage 14j result inspection. Stage 14i
falsified fixed geodesic topology repair on natural-image development data, so
Stage 14j moves to a distinct representation mechanism rather than tuning the
linker. The question is whether **cross-scale local phase alignment supplies
positive boundary context not already captured by the retained
Gabor/Hessian-amplitude bank**.

The experiment does not test phase congruency as a replacement localizer.
Scharr+NMS remains responsible for localization; the new signal is contextual
evidence only.

## Literature and fixed mechanism

Morrone and Owens (1987, DOI `10.1016/0167-8655(87)90013-4`) showed that
maxima of local energy correspond to maxima of phase congruency for general
features. Kovesi (1999; 2000, DOI `10.1007/s004260000024`) developed a
noise-compensated, multiscale, multiorientation phase-congruency measure whose
maximum covariance moment indicates edge strength and is normalized against
local contrast.

The candidate uses the long-standing `phasecong3` defaults without a Stage-14j
parameter sweep: four scales, six orientations, minimum wavelength 3, scale
multiplier 2.1, `sigma_on_f=0.55`, noise factor `k=2`, frequency-spread cutoff
0.5, and spread gain 10. The only candidate feature is the maximum
phase-congruency covariance moment.

## Dataset firewall and folds

- Data: the 15 pre-existing UDED selection images only.
- Protocol: five repeats of three-fold outer CV using the established
  deterministic Stage-12d fold generator.
- UDED held-out, BSDS500 test, and BIPEDv2 test are not loaded or consulted.
- The compact feature specifications, phase membership, phase singleton
  weight, phase eligibility, and operating thresholds are fitted using each
  outer training fold only.
- Validation-fold predictions are scored once using the corresponding frozen
  training-fold state.

## Compared variants

1. `compact_incumbent`: the retained five positive features, distorted-Choquet
   gamma 0.55, context gate strength 2.0 and floor 0.10, and Scharr+NMS.
2. `compact_plus_phase`: the identical model with the phase-congruency moment
   appended as a sixth positive membership.

The established positive-bank rule is applied to the phase channel inside the
training fold. It is eligible only when its edge-versus-texture AUC is at least
0.56 in the prespecified positive direction. Its membership midpoint, scale,
and unnormalized singleton weight use the same median/IQR and
`(AUC - 0.5) * (1 + mutual_information)` construction as the existing positive
features. If ineligible, its weight is zero and the candidate equals the
incumbent for that fold. No sign reversal or negative-evidence reinterpretation
is allowed.

## Primary endpoint and promotion rule

The primary endpoint is aggregate tolerant F1 pooled over all outer validation
events. Repeated folds are descriptive rather than independent samples.

Promote the phase feature only if all criteria hold:

1. aggregate F1 delta is at least `+0.001`;
2. aggregate precision delta is at least `-0.002`;
3. mean paired fold F1 delta is positive;
4. the candidate wins at least 9 of 15 folds; and
5. the phase feature is training-eligible in at least 12 of 15 folds.

Failure retains the five-feature compact incumbent. Stage-14j results must not
be used to tune phase-congruency parameters or its eligibility threshold.

## Outputs and deterministic qualitative report

The runner writes `summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `phase_calibration.csv`, and
`best_method_preview.png`. The preview uses the first validation image of the
first deterministic split, never a result-selected example. Columns are:
conditioned input, ground truth, compact incumbent prediction, compact-plus-
phase prediction, and the method retained by the preregistered rule.

The preview is documentary only and is not an optimization signal.
