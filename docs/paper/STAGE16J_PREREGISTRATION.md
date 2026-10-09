# Stage 16j preregistration — step-profile context evidence

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Nalwa and Binford model an edgel by fitting one-dimensional intensity
surfaces and identify a hyperbolic tangent as an adequate step-edge basis
(`On Detecting Edges`, IEEE TPAMI 8(6), 1986,
DOI `10.1109/TPAMI.1986.4767852`). Their core distinction is between a local
discontinuity model and smoother surface explanations. Elder and Zucker later
showed why natural edge blur varies spatially and why reliable edge evidence
must accommodate more than one blur scale (`Local Scale Control for Edge
Detection and Blur Estimation`, IEEE TPAMI 20(7), 1998,
DOI `10.1109/34.689301`).

Stage 16j tests whether this **local edge-profile shape** supplies positive
context evidence missing from the retained response-amplitude bank. It does
not replace Scharr+NMS. This representation is distinct from failed detector
averaging, image conditioning, component/region gating, and connected-
threshold persistence.

## Fixed candidate

For every pixel, sample the median-conditioned grayscale image along the
incumbent Scharr normal at offsets `[-3,-2,-1,0,1,2,3]` with bilinear
interpolation and reflected boundary extension. Mean-center the seven-sample
profile and fit, by analytic least squares:

- one smooth linear template; and
- three centered `tanh(x / width)` step templates with fixed widths
  `0.75`, `1.5`, and `3.0` pixels.

The new scalar cue is

`max(linear_SSE - best_step_SSE, 0) / profile_total_energy`,

clipped to `[0,1]`. The three widths are a closed scale set fixed before
results; they are not a search. The implementation is a repository-specific
bounded surrogate of one-dimensional surface-model selection, not an exact
reproduction of Nalwa and Binford's complete detector.

The cue's positive logistic membership and singleton weight are fitted only
from each outer UDED-selection training fold, using the existing Stage-14j
calibration rule. It is eligible only when training edge-versus-texture AUC is
at least `0.56`. When eligible, it is appended as a sixth positive membership
to the retained distorted-Choquet context. The five retained memberships,
gamma `0.55`, gate strength `2.0`, floor `0.10`, median conditioning,
grayscale Scharr+NMS localizer, and fold-fitted operating thresholds are
unchanged.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Feature
  calibration, singleton weight, and operating threshold are fit inside each
  outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations,
  99 thresholds, `maxDist=0.0075`, thinning enabled, native resolution, and
  direct 8-bit soft PNG export without per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and other protected data are not
  read.
- The local Windows matcher remains stochastic and reference-uncertified; the
  fixed-seed diagnostic matcher is forbidden for dataset scoring.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is at least `-0.002`.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The cue is training-eligible in at least `12/15` folds.
6. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are both nonnegative versus the unchanged
   incumbent.
7. The deterministic preview and finite/bounded cue checks complete.

Failure of any condition rejects this fixed realization. Do not tune profile
extent, offsets, widths, interpolation, eligibility, membership calibration,
Choquet parameters, gate, localizer, or threshold grid from the result.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `step_profile_calibration.csv`,
`best_method_preview.png`, `official_eval_manifest.json`, and the controller's
official-evaluation summary. The preview uses fixed UDED-selection positions
1, 8, and 15 with columns: input, ground truth, incumbent out-of-fold
prediction, candidate out-of-fold prediction, and step-profile preference.
