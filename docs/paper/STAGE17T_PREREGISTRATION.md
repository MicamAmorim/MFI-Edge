# Stage 17t preregistration - Frei-Chen patch-subspace context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Frei and Chen, *Fast Boundary Detection: A Generalization and a New
Algorithm* (IEEE Transactions on Computers C-26(10):988-998, 1977, DOI
`10.1109/TC.1977.1674733`), represent every `3x3` image patch in a fixed
orthogonal basis. The first four basis vectors span an edge subspace, the
next four span a line subspace, and the ninth represents average intensity.
Their edge criterion is the angle between the patch vector and its projection
onto the edge subspace. This supplies an analytic local shape test: evidence
depends on how much of a patch is explained by edge-like basis elements, not
only on derivative amplitude.

Stage 17t tests the cosine of that published projection angle as one positive
context membership. It does not apply the paper's binary threshold or
sequential edge/line processing and is therefore an equation-level soft use
of the basis, not an exact reproduction of the complete detector. The
hypothesis is that edge-subspace occupancy adds boundary-shape evidence not
already captured by the retained marginal Gabor/Hessian strengths.

This mechanism is distinct from Stage 17r's nonlocal patch recurrence,
Stage 16z's spatially averaged gradient outer-product tensor, Stage 16j's
normal-profile model selection, Stage 14l's half-disc LBP distributions, and
the closed graph, topology, structural-gating, conditioning, aggregation,
fusion, and localizer-replacement families. It uses a complete fixed local
patch basis and changes neither the image nor the localizer.

## Fixed candidate

On the unchanged median-conditioned grayscale image in `[0,1]`, correlate
each reflected `3x3` neighborhood with the nine published normalized
Frei-Chen masks. If `r_i` is the response to normalized basis vector `i`, set

`E = sqrt(sum_{i=1..4}(r_i^2) / sum_{i=1..9}(r_i^2))`.

A zero-energy patch receives zero evidence. There is no threshold, per-image
normalization, orientation choice, scale, search, learned coefficient, or
fitted transform in the raw cue. The basis normalizations are fixed at
`1/sqrt(8)` for masks 1-4, `1/2` for masks 5-6, `1/6` for masks 7-8, and
`1/3` for mask 9.

Fit one positive logistic membership only inside each outer UDED-selection
training fold. Its midpoint is the mean of training edge and texture medians,
and its scale is the pooled training interquartile range with a `1e-9`
numerical floor. Its singleton weight is
`max(AUC-0.5,0)*(1+mutual_information)`. The cue is eligible only when the
training edge-versus-texture AUC is at least `0.56`; an ineligible fold is
exactly the compact control. When eligible, append it as a sixth membership
and renormalize singleton weights before the unchanged distorted-Choquet
integral.

The retained five memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
threshold grid are unchanged.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, cue calibration, eligibility, singleton weight, and operating
  threshold are fit only inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native-resolution 8-bit soft
  output without per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all protected data are not
  read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.
- A fixed synthetic contract must verify orthonormality of the nine masks,
  finite bounded output, zero response on a zero field, deterministic
  repeatability, positive-intensity-scale invariance, greater response for a
  canonical edge-basis patch than a canonical line-basis patch, and greater
  response near a clean step than inside a period-two checkerboard and fixed
  seed-17018 small Gaussian perturbation around mid-gray.

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
8. The synthetic, finite/bounded, repeatability, runtime, and deterministic
   preview contracts complete.

Failure of any condition rejects this fixed realization. Do not tune the
basis, mask normalization, edge-subspace membership, denominator, support,
boundary handling, zero-energy rule, eligibility, calibration, integration,
context, gate, localizer, or thresholds from the result. Do not advance to
larger, rotated, multiscale, color, learned, selected, weighted, line-subspace,
or sequential Frei-Chen variants from the outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `frei_chen_calibration.csv`,
`frei_chen_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and Frei-Chen edge-subspace cue.
