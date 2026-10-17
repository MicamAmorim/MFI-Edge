# Stage 18j preregistration - image-internal PMI dependency context

Status: registered before candidate execution or benchmark-result inspection.

## Hypothesis and literature basis

Isola, Zoran, Krishnan, and Adelson, *Crisp Boundary Detection Using Pointwise
Mutual Information* (ECCV 2014, DOI
`10.1007/978-3-319-10578-9_52`), start from a grouping principle different
from gradient magnitude: features belonging to the same object should have
higher statistical dependency than features separated by an object boundary.
Their image-internal model estimates the joint distribution of nearby feature
pairs, corrects it by the feature marginals with `PMI_rho`, and thereby keeps
frequent within-object texture transitions more affine than rarer cross-object
pairs. The primary paper, official project page, and BSD-licensed author code
at commit `ee2d76e98340313a8f92e1b65064a9b4ea90ac77` were checked live on
2026-10-17. The author code fixes `rho=1.25`, learns each image's probability
model internally, and then uses spectral clustering for its full detector.

Stage 18j isolates only that statistical-dependency principle. It does not run
or reproduce the author's KDE, random-forest approximation, multiscale graph,
spectral clustering, OWT, or UCM. This prevents the test from revisiting Stage
16x's rejected spectral-globalization integration. It also differs from
Compass and Stage 14l/15o: the candidate does not compare two half-disc
histograms. Instead, an image-wide co-occurrence model asks whether the two
intensity labels straddling each pixel occur together more or less often than
their marginals predict.

## Fixed candidate

1. Use the unchanged median-conditioned grayscale image and serialize it once
   to 256 uniformly spaced 8-bit levels. Do not normalize per image.
2. At every pixel, form centered endpoint pairs in four fixed axes with
   offsets `(0,1)`, `(1,0)`, `(1,1)`, and `(1,-1)`. Reflection is fixed at
   raster boundaries. Accumulate all endpoint labels into one symmetric
   image-internal `256x256` joint table.
3. Add a fixed Laplace pseudocount of `1` to every joint bin. Convert joint and
   marginal probability masses to densities on the unit intensity interval,
   then compute the paper/code exponent
   `PMI_rho(a,b)=log(p(a,b)^1.25/(p(a)p(b)))`.
4. Convert dependency deficit to bounded positive evidence with
   `1-exp(-max(-PMI_rho,0))` and take the maximum across the four axes. This
   contains no fitted scale or response normalization. A flat image receives
   exact-zero evidence.
5. Fit one positive logistic membership only inside each outer UDED training
   fold. Its midpoint is the mean of edge and texture medians and its scale is
   the pooled IQR with a `1e-9` floor. Its singleton weight is
   `max(AUC-0.5,0)*(1+mutual_information)`. Eligibility requires training AUC
   at least `0.56`; an ineligible fold exactly reduces to the compact control.
6. When eligible, append the membership to the five retained memberships,
   renormalize singleton weights, and run the unchanged distorted-Choquet
   integral.

The compact bank, gamma `0.55`, gate strength `2.0`, floor `0.10`, median
conditioning, grayscale Scharr+NMS localizer, and fold threshold fitting are
unchanged. The discrete table is a bounded equation-level surrogate, not an
exact author-code reproduction or an independent PMI detector.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, cue calibration, eligibility, singleton weight, and operating
  threshold are fit only within each outer training fold.
- BSDS500 validation: default official MATLAB attachment using all
  annotations, 99 thresholds, `maxDist=0.0075`, thinning, native-resolution
  8-bit soft output, and no export-time normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all protected data are not
  read.
- The unmodified Windows Berkeley matcher remains stochastic and reference-
  uncertified; the fixed-seed diagnostic matcher is forbidden for scoring.
- The synthetic contract requires finite bounded maps, exact zero on a flat
  field, a localized step response exceeding fixed repeated-checker and
  low-amplitude-noise responses, bitwise repeatability, and exact invariance
  when the two step intensity labels are reassigned without changing their
  co-occurrence structure.

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
extend the intensity levels, pair geometry, co-occurrence scope, smoothing,
pseudocount, density convention, PMI exponent, deficit mapping, calibration,
eligibility, integration, context, gate, localizer, or threshold grid from the
result. Do not advance to color, variance-feature, KDE, learned affinity,
multiscale, graph/spectral, OWT/UCM, approximate-PMI forest, half-disc,
patchwise, conditional-PMI, or detector-fusion variants.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `pmi_dependency_calibration.csv`,
`pmi_dependency_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and PMI dependency-deficit cue.
