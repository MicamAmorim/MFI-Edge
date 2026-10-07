# Stage 14t preregistration — fixed a-contrario meaningfulness gate

Date registered: 2026-10-07, before any Stage-14t metric or qualitative output
was inspected.

## Question and mechanism

Can an image-adaptive statistical test of non-accidental connected support
suppress strong but untrustworthy responses without replacing the incumbent
localizer or learning a domain router?

Desolneux, Moisan, and Morel (2001, DOI
`10.1023/A:1011290230196`) formalize edge detection by the Helmholtz principle:
a contour is meaningful when its expected number of occurrences under a random
background model is small. Tepper, Musé, and Almansa (2013, DOI
`10.1007/s10851-012-0411-6`) extend this line to partially salient level lines
and combined contrast/regularity. Stage 14t does not reproduce either complete
level-line algorithm. It tests one deliberately simpler connected-component
surrogate on the already localized incumbent score.

The compact Choquet-gated Scharr score is quantized on its absolute `[0,1]`
scale to 8-bit levels. At every occupied upper level, 8-connected components
are extracted. For a component of size `L`, the independent sample count is
fixed as `ceil(L/2)`, following the two-pixel sampling rationale used in the
meaningful-boundary literature. Its null tail probability `p` is the fraction
of all image-lattice sites at or above that level. The conservative test-count upper
bound is

`N_tests = 255 * (# nonzero NMS sites)`,

and the component number of false alarms is

`NFA = N_tests * p^ceil(L/2)`.

Each pixel receives the maximum reliability `max(0, 1-NFA)` among containing
upper-level components. The candidate is

`incumbent_score * [0.10 + 0.90 * reliability]`.

Thus `epsilon=1` is the sole meaningfulness cutoff and the retained incumbent
gate floor `0.10` prevents irreversible deletion before fold-fitted thresholding.
There is no new localizer, hard linking, learned router, or parameter search.

## Why this follows Stage 14s

Stages 14r and 14s both improved all official BSDS500-validation headline
metrics while failing UDED, with Stage 14s losing every UDED fold. That pattern
does not justify another derivative or geometry replacement. The common unmet
problem is deciding when a strong response belongs to statistically coherent
support rather than accidental texture/noise. An image-internal a-contrario
null offers adaptive calibration without using dataset identity or ground truth.

The checkpoint also considered Dempster–Shafer ignorance and component-tree
persistence. Dempster–Shafer requires more arbitrary mass assignments for a
first test, while persistence alone lacks the explicit false-alarm calibration
that directly addresses the observed domain discrepancy. Both remain deferred.

## Data, fitting, and fixed protocol

- UDED selection uses the existing 5 repeats × 3 folds.
- Compact membership fitting and each variant's score threshold remain inside
  each outer fold.
- Quantization, connectivity, sampling stride, test-count bound, `epsilon=1`,
  reliability transform, and attenuation floor are fixed before scoring.
- The empirical null is computed independently from each inference image's
  full score lattice without ground truth.
- BSDS500 validation receives native-resolution soft maps exported from a
  context bank fitted on full UDED selection without reading BSDS ground truth.
- The official MATLAB evaluator uses all annotations, 99 thresholds,
  `maxDist=0.0075`, and thinning.
- UDED held-out, BSDS500 test, and BIPEDv2 test are forbidden.
- No quantization, connectivity, sampling stride, NFA, null, floor, context,
  or fusion variant may be tuned after results are observed.

## Promotion rule

All criteria are conjunctive:

1. UDED aggregate F1 delta is nonnegative;
2. UDED aggregate precision delta is nonnegative, because precision/trust is
   the claimed mechanism;
3. mean paired fold-F1 delta is nonnegative;
4. candidate wins at least 9 of 15 folds in F1;
5. official BSDS500-validation evaluation completes with feedback allowed;
6. BSDS-val ODS delta is at least `+0.002`;
7. BSDS-val OIS and AP deltas are both nonnegative.

Failure of the official attachment triggers attachment repair only. A failed
fixed point rejects only this component-support NFA surrogate; it does not
authorize tuning or imply rejection of full level-line a-contrario methods.

## Outputs and qualitative policy

The runner writes aggregate, fold, per-image, and meaningfulness diagnostics,
a repository-local official exporter/manifest, and
`best_method_preview.png`. The fixed preview is the first validation image in
the first deterministic CV split with columns: conditioned input, ground
truth, incumbent prediction, candidate prediction, meaningfulness reliability,
and retained incumbent. It is documentary only.
