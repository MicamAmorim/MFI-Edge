# Stage 16t preregistration - gamma-normalized automatic scale selection

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

The completed generation-2 experiments have mainly changed context cues,
aggregation, conditioning, or post-response structure while retaining a single
localization scale. The recurring BSDS-positive/UDED-weak pattern may instead
reflect different mixtures of sharp, diffuse, noisy, and textured boundaries.
This motivates a local, image-internal scale decision rather than another
dataset-level router or fixed replacement localizer.

Lindeberg (1998, DOI `10.1023/A:1008097225773`) defines a scale-space edge by
the conjunction of a gradient-direction spatial maximum and a maximum of
scale-normalized edge strength over scale. For first-order derivatives,
gamma-normalization with `gamma=1/2` selects fine scales for sharp edges and
coarser scales for diffuse edges. The paper illustrates edge extraction at
variance levels `t=1,4,16`, corresponding to Gaussian standard deviations
`sigma=1,2,4`. Lindeberg's scale-selection review and later discrete-analysis
work preserve the same normalized-derivative rationale and warn that very fine
sampled Gaussian derivatives can be inaccurate.

Stage 16t is a fixed finite-scale repository surrogate of that principle. It
is not a reproduction of the paper's continuous scale-space edge curves,
closed-curve construction, subscale interpolation, or integrated saliency.

## Fixed candidate

Starting from the unchanged median-conditioned grayscale image, compute
first-order Gaussian derivatives at

`sigma in {1, 2, 4}` (`t in {1, 4, 16}`).

At each scale, define normalized strength

`R_sigma = sigma^0.5 * sqrt(L_x^2 + L_y^2)`.

For every pixel, select the scale with greatest `R_sigma`, using the listed
scale order as the deterministic tie rule. Apply the repository's unchanged
four-direction spatial NMS to `R_sigma` at every scale, retain the NMS response
only at the selected scale, and apply the same fixed robust score mapping used
by the incumbent classical localizer. This selected-scale localizer replaces
only grayscale Scharr+NMS before the unchanged compact context gate.

The retained five memberships, outer-fold singleton fitting, distorted-
Choquet gamma `0.55`, gate strength `2.0`, floor `0.10`, median conditioning,
and fold-fitted threshold grid are unchanged. There is no scale search,
response mixture, learned router, dataset identity, target adaptation, or
candidate/incumbent fusion.

## Development protocol

- UDED selection: five repeats by three folds with established seed
  `20261009`. Feature-bank fitting, membership calibration, singleton weights,
  and operating thresholds remain inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment with every
  annotation, 99 thresholds, `maxDist=0.0075`, thinning enabled, native
  resolution, and direct 8-bit soft PNG export.
- UDED held-out, BSDS500 test, BIPEDv2 test, and other protected data are not
  read.
- The unmodified Windows matcher remains stochastic and reference-
  uncertified; the fixed-seed diagnostic matcher is forbidden for dataset
  scoring.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is at least `-0.002`.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are both nonnegative versus the unchanged
   incumbent.
6. Finite/bounded output, exact repeat determinism, fixed-scale membership,
   nonempty spatial maxima, and the predeclared synthetic condition that a
   Gaussian-diffused step selects no finer response-weighted mean scale than a
   sharp step all pass; the deterministic preview is present.

Failure of any condition rejects this fixed realization. Do not tune the
scales, gamma normalization, Gaussian discretization, endpoint/tie handling,
NMS, response mapping, conditioning, context, gate, or threshold grid from the
result.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `scale_diagnostics.csv`,
`best_method_preview.png`, `official_eval_manifest.json`, and the controller's
official-evaluation summary. The preview uses fixed UDED-selection positions
1, 8, and 15 with columns: input, ground truth, incumbent out-of-fold
prediction, candidate out-of-fold prediction, and selected-scale display.
