# Stage 16h preregistration — all-threshold hysteresis persistence boost

Date registered: 2026-10-09, before any Stage-16h metric or qualitative output
was inspected.

## Question and mechanism

Can connectivity across score levels strengthen weak but supported boundary
fragments without replacing the incumbent localizer or causing the recall
collapse seen in recent image-domain/localizer changes?

Canny's original edge detector (TPAMI 1986, DOI
`10.1109/TPAMI.1986.4767851`) uses a high threshold to seed reliable contours
and a lower threshold to retain connected weak responses. Its Figure 7 uses
thresholds `T1` and `2*T1`, providing the fixed 2:1 high/low ratio used here.
Salembier, Oliveras, and Garrido (TIP 1998, DOI `10.1109/83.663500`) show how
upper-level connected components and max-tree representations support
contour-preserving connected transforms.

Stage 16h applies a repository-specific **soft all-threshold extension** of
that principle to the unchanged compact-MFI score. After common 8-bit
serialization, for every high level `h` from 1 through 255, a pixel survives
when it has score at least `ceil(h/2)` and is 8-connected through such pixels
to a seed with score at least `h`. The candidate score is the largest `h` at
which the pixel survives. A descending bucket propagation computes all 255
reconstructions together.

This construction has two enforced invariants:

1. the candidate is pointwise no smaller than the serialized incumbent,
   because each nonzero pixel seeds itself at its own level;
2. candidate support is exactly incumbent support, because zero-score pixels
   cannot enter any positive weak component.

Thus median conditioning, the five retained memberships, distorted-Choquet
gamma `0.55`, gate strength `2.0`, floor `0.10`, grayscale Scharr+NMS, and all
fold fitting remain unchanged. The transform changes only the ranking of
already-localized nonzero responses by connected strong-seed support.

## Why this is a distinct bounded test

- Stage 16f changed the image before localization and destroyed UDED recall.
  Stage 16h leaves the image and Scharr+NMS map untouched and is boost-only.
- Stage 16d attenuated scores using region-boundary shape stability. Stage 16h
  uses no regions, shape test, area, chamfer distance, or attenuation.
- Stage 14i created new geodesic links between endpoints. Stage 16h cannot
  create a response outside incumbent support.
- Stage 14t assigned NFA meaningfulness to connected components at selected
  levels. Stage 16h has no null model, component-size significance, or NFA.
- Stage 16b averaged independent detectors. Stage 16h uses only the incumbent
  score and has no expert weight, learned router, or external method.

This is the deferred threshold-persistence family noted after Stage 14t, not a
parameter revision of any failed mechanism. The 2:1 ratio, 8-connectivity, and
8-bit levels are fixed before results. No alternate ratio, connectivity,
quantization, orientation tracing, or fusion is searched.

## Data and leakage control

- UDED selection only: five repeats of three-fold outer CV. Compact
  memberships and each method's operating threshold are fitted from the outer
  training fold only.
- UDED held-out, BSDS500 test, and BIPEDv2 test are forbidden.
- BSDS500 validation is the second development axis. The exporter fits the
  compact bank from UDED selection only, never reads BSDS ground truth, and
  writes the candidate directly as native-resolution 8-bit PNG.
- The official attachment retains all annotations, 99 thresholds,
  `maxDist=0.0075`, thinning, and the unmodified Windows matcher. The matcher
  remains stochastic and reference-uncertified; the diagnostic fixed-seed
  matcher is forbidden for dataset scoring.

## Promotion rule fixed before results

Promotion requires **every** condition:

1. UDED aggregate F1 delta versus compact MFI is at least `+0.002`.
2. UDED aggregate recall delta is at least `+0.002`, the registered weak-edge
   recovery endpoint.
3. UDED aggregate precision delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative.
5. Candidate F1 exceeds incumbent F1 in at least `9/15` folds.
6. Every candidate map satisfies both pointwise-floor and exact-support
   invariants.
7. The official BSDS500-validation attachment completes.
8. BSDS500-validation ODS delta is at least `+0.002`.
9. BSDS500-validation OIS and AP deltas are both nonnegative.
10. `best_method_preview.png` and all registered numeric artifacts exist.

The rule is conjunctive. A gain on only one dataset, recall bought with a
larger precision loss, or a support-invariant violation rejects the candidate.

## Outputs and qualitative contract

The runner writes `summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `persistence_diagnostics.csv`,
`official_eval_manifest.json`, and `best_method_preview.png`. The preview uses
fixed UDED-selection positions 1, 8, and 15. Columns are input, ground truth,
out-of-fold incumbent prediction, out-of-fold candidate prediction, and the
candidate-minus-serialized-incumbent score. It is documentary only.

## Outcome discipline

If any condition fails, do not tune the high/low ratio, connectivity,
quantization, serialization, propagation, threshold grid, context, gate, or
localizer from Stage-16h outcomes. Retain the compact Choquet-gated
median-conditioned Scharr+NMS controller and escalate to a mechanistically
distinct checkpoint. Failure would apply only to this fixed soft hysteresis
persistence transform, not to Canny hysteresis or connected operators in
general.
