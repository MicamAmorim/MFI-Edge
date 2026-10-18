# Stage 18l preregistration - image-torque closure context

Status: registered before candidate execution or benchmark-result inspection.

## Hypothesis and literature basis

Nishigaki, Fermuller, and DeMenthon, *The Image Torque Operator: A New Tool
for Mid-level Vision* (CVPR 2012, DOI `10.1109/CVPR.2012.6247714`), define
the moment of an oriented edge tangent about a patch center. Contributions
from random texture tend to cancel, while tangents arranged along an extended
closed contour accumulate with a consistent sign. The paper applies this
mid-level closure statistic to boundary strengthening and reports a Berkeley
F-measure gain over Canny. It illustrates square torque maps at `5x5`,
`21x21`, and `45x45` support.

Stage 18l isolates that closure/alignment principle. It is mechanistically
different from Stage 14i endpoint linking, Stage 14r SE(2) diffusion, Stage
16d region stability, Stage 16h threshold persistence, Stage 16l EDPF chain
support, Stage 16x spectral globalization, Stage 18b FH region partitioning,
Stage 18f triangle-curve search, and Stage 18j PMI dependency. It creates no
links, graph, partition, threshold hierarchy, detector fusion, or learned
router. The unchanged Scharr+NMS score is still the only localizer.

## Fixed candidate

1. Use the unchanged median-conditioned grayscale image. Compute fixed
   `3x3` Scharr horizontal and vertical derivatives with reflection.
2. Orient the continuous tangent clockwise to the intensity gradient. Use
   gradient magnitude as a threshold-free edge measure; no Canny threshold,
   binary edge selection, or per-image response normalization is introduced.
3. At every center, compute the paper's signed torque sum over square supports
   `5x5`, `21x21`, and `45x45`. Divide by the radial triangle-inequality bound
   to obtain signed patch coherence in `[-1,1]`.
4. Backproject each signed coherent patch to the oriented gradient samples
   whose moment has the same sign. Divide the positive aligned contribution by
   its radial bound and take the maximum across the three published supports.
   Zero-gradient pixels receive exact-zero evidence. This produces a bounded
   closure-participation map without a fitted coefficient.
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
unchanged. This is an equation-level repository surrogate. It does not use
the paper's learned logistic edge-strengthening coefficients and is not an
exact reproduction of the paper's complete boundary experiment.

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
  field, stronger boundary support for a closed circle than for an open step
  or repeated checker pattern, bitwise repeatability, and polarity-reversal
  invariance.

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
extend the torque supports, patch shape, edge measure, tangent convention,
normalization, coherence, backprojection, polarity handling, calibration,
eligibility, integration, context, gate, localizer, or threshold grid from
the result. Do not advance to disk/elliptic, color/depth/motion, learned
torque, saliency, attention, segmentation, boundary-ownership, multiscale
search, contour-linking, graph, or detector-fusion variants.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `image_torque_calibration.csv`,
`image_torque_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and image-torque closure-support cue.
