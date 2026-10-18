# Stage 18n preregistration - sloped-facet structural-break context

Status: registered before candidate execution or benchmark-result inspection.

## Hypothesis and literature basis

Haralick, *Edge and Region Analysis for Digital Image Data* (Computer
Graphics and Image Processing 12, 1980, DOI
`10.1016/0146-664X(80)90004-0`), models an image region as a sloped plane and
defines edge strength through an F statistic testing whether the parameters
of planes fitted to opposing neighborhoods differ significantly. The paper's
central point is that the statistic normalizes apparent edge strength by an
estimate of within-region noise. Chow, *Tests of Equality Between Sets of
Coefficients in Two Linear Regressions* (Econometrica 28, 1960, DOI
`10.2307/1910133`), supplies the fixed nested-regression F statistic used here.

Stage 18n tests whether noise-normalized local surface-model change is more
transferable than another unnormalized activity cue. It is mechanistically
different from Stage 16j's one-dimensional step-template advantage, Stage
17d's globally fitted GMRF innovation, Stage 17p's median/MAD gradient
outlier, Stage 17x's semi-global piecewise-constant scanline partition, Stage
17z's single adaptive-polynomial reconstruction residual, and Stage 18l's
oriented closure moments. It does not segment the image, alter conditioning,
replace localization, or combine a rejected cue.

## Fixed candidate

1. Use the unchanged median-conditioned grayscale image in `[0,1]`.
2. At each pixel, evaluate four fixed undirected axes: horizontal, vertical,
   and the two diagonals. For each axis, take two disjoint `3x3` square
   neighborhoods whose centers are exactly two integer direction-vector steps
   to either side of the candidate pixel. Reflection is fixed at image
   boundaries.
3. Fit the planar model `I=a+b*y+c*x` by ordinary least squares. Compare one
   shared plane over all 18 samples with two separate planes, one per
   neighborhood. With three parameters per plane, compute
   `F=((RSS_pooled-RSS_separate)/3)/(RSS_separate/12)`.
4. Map finite nonnegative statistics to `[0,1]` by `F/(1+F)`. If the separate
   residual is numerically zero under the fixed relative-energy tolerance
   `1e-12*(sum(I^2)+1)`, assign one only when the pooled model has a positive
   structural-break residual above that tolerance; otherwise assign zero.
   Take the maximum across the four axes. There is no p-value threshold,
   fitted scale, orientation interpolation, per-image normalization, or
   model-order search.
5. Fit one positive logistic membership only inside each outer UDED training
   fold. Its midpoint is the mean of edge and texture medians and its scale is
   the pooled IQR with a `1e-9` floor. Its singleton weight is
   `max(AUC-0.5,0)*(1+mutual_information)`. Eligibility requires training AUC
   at least `0.56`; an ineligible fold exactly reduces to compact control.
6. When eligible, append the membership to the five retained memberships,
   renormalize singleton weights, and run the unchanged distorted-Choquet
   integral.

The compact bank, gamma `0.55`, gate strength `2.0`, floor `0.10`, median
conditioning, grayscale Scharr+NMS localizer, and fold threshold fitting are
unchanged. This is a bounded equation-level repository surrogate, not an
exact reproduction of Haralick's iterative facet-region procedure or its
complete edge detector.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, cue calibration, eligibility, singleton weight, and operating
  threshold are fit only inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment using all
  annotations, 99 thresholds, `maxDist=0.0075`, thinning, native-resolution
  8-bit soft output, and no export-time normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all protected data are not
  read.
- The unmodified Windows Berkeley matcher remains stochastic and reference-
  uncertified; the fixed-seed diagnostic matcher is forbidden for scoring.
- The synthetic contract requires finite bounded maps, exact zero on a flat
  field, zero in the interior of an affine ramp, stronger registered-boundary
  evidence than checkerboard and fixed noise, bitwise repeatability, polarity
  invariance, and positive-affine photometric invariance.

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
   least `+0.002`, and OIS and AP are nonnegative versus the incumbent.
8. Synthetic, finite/bounded, repeatability, runtime, and deterministic-
   preview contracts complete.

Failure of any condition rejects this fixed realization. Do not tune or
extend the facet size or placement, axes, plane coordinates or order,
regression loss, structural-break statistic, residual tolerance, evidence
mapping, boundary handling, calibration, eligibility, integration, context,
gate, localizer, or threshold grid. Do not advance to iterative facets,
higher-order or robust surfaces, multiscale/color/texture facets, adaptive
windows/orientations, alternative change tests, segmentation, calibration,
fusion, or learned variants from the result.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `facet_break_calibration.csv`,
`facet_break_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and sloped-facet structural-break cue.
