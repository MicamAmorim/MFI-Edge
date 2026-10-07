# Stage 14r preregistration — fixed SE(2) contour enhancement

Date registered: 2026-10-07, before any Stage-14r metric or qualitative output
was inspected.

## Question and mechanism

Can a fixed orientation-lifted diffusion improve contour continuity without
replacing the incumbent localizer or causing the recall collapse observed in
Stages 14p and 14q?

Duits and Franken (2010, DOI `10.1090/S0033-569X-10-01172-0`) formulate
left-invariant diffusion on `SE(2)` for contour enhancement. Franken and Duits
(2009, DOI `10.1007/s11263-009-0213-5`) show why the position-orientation lift
can preserve crossing structures that ordinary image-plane coherence diffusion
cannot, and Zhang et al. (2016, DOI `10.4208/nmtma.2015.m1411`) compare
numerical realizations of the linear enhancement process.

Stage 14r is a deliberately minimal repository-specific discretization, not a
reproduction of an invertible cake-wavelet orientation score. The retained
compact Choquet-gated Scharr+NMS score is hard-lifted into 32 unoriented tangent
bins. It receives five explicit steps of the fixed linear operator

`0.5 A_tangent^2 + 0.5 A_angle^2`

at `dt=0.2`. The existing compact context gate acts as a fixed local stopping
coefficient. Maximum projection back to the image plane is followed by NMS
using the unchanged grayscale gradient-normal field. Thus the new mechanism
regularizes the incumbent score; it does not replace Scharr, learn a router, or
add endpoints after thresholding.

## Data, fitting, and fixed protocol

- UDED selection uses the existing 5 repeats x 3 folds.
- Compact membership fitting and each variant's score threshold remain inside
  each outer fold.
- The orientation count, lift, coefficients, step count, time step, projection,
  and NMS are globally fixed before scoring.
- BSDS500 validation receives native-resolution soft maps exported from a
  context bank fitted on full UDED selection without reading BSDS ground truth.
- The official MATLAB evaluator uses all annotations, 99 thresholds,
  `maxDist=0.0075`, and thinning.
- UDED held-out, BSDS500 test, and BIPEDv2 test are forbidden.
- No orientation-count, coefficient, time, step, interpolation, projection,
  context-coupling, NMS, or fusion sweep is allowed after results are observed.

## Promotion rule

All criteria are conjunctive:

1. UDED aggregate F1 delta is nonnegative;
2. UDED aggregate precision delta is at least `-0.002`;
3. mean paired fold-F1 delta is nonnegative;
4. candidate wins at least 9 of 15 folds in F1;
5. mean paired fold largest-component GT-coverage delta is at least `+0.005`;
6. largest-component coverage improves in at least 9 of 15 folds;
7. official BSDS500-validation evaluation completes with feedback allowed;
8. BSDS-val ODS delta is at least `+0.002`;
9. BSDS-val OIS and AP deltas are both nonnegative.

The small precision allowance is preregistered because this mechanism claims
continuity rather than sharpening, but it receives no F1 allowance. Failure of
the official attachment triggers attachment repair only. A failed fixed point
does not disprove SE(2) orientation-score theory and does not authorize tuning
this discretization from its outcome; continue to a distinct agenda family.

## Outputs and qualitative policy

The runner writes aggregate, fold, per-image, continuity, and SE(2) numerical
diagnostics, a repository-local official exporter/manifest, and
`best_method_preview.png`. The fixed preview is the first validation image in
the first deterministic CV split with columns: conditioned input, ground
truth, incumbent prediction, candidate prediction, soft SE(2) projection, and
retained incumbent. It is documentary only.
