# Stage 18b preregistration - FH adaptive-region boundary context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Felzenszwalb and Huttenlocher, *Efficient Graph-Based Image Segmentation*
(IJCV 59(2):167-181, 2004, DOI
`10.1023/B:VISI.0000022288.19776.77`), define evidence for a boundary between two
components by comparing the minimum between-component edge weight with each
component's maximum internal minimum-spanning-tree edge plus
`tau(C)=k/|C|`. The criterion therefore asks whether a local transition is
large relative to variation already accepted inside an adaptively grown
region. The primary paper fixes an eight-neighbour image grid, absolute gray
difference, Gaussian sigma `0.8`, and uses `k=300` for its 320-by-240 or larger
natural-image examples.

Stage 18b tests whether boundaries of that fixed adaptive region partition
provide useful mid-level support to MFI. This is mechanistically different
from Stage 16x's spectral-Pb surrogate, which globalized an existing response
through intervening-contour affinities and normalized-Laplacian eigenvectors;
Stage 16d's response-component stability gate; and Stage 17x/17z's
piecewise-constant scanline and adaptive-polynomial representation failures.
The new cue comes from an image-region partition whose stopping predicate
explicitly normalizes external contrast by each component's internal
variation.

The implementation uses scikit-image `0.26.0` as an equation-level
realization of the published grayscale grid-graph algorithm. It is not an
exact author-code reproduction or an image-segmentation benchmark. The
paper's optional color-plane intersection and feature-space nearest-neighbour
graph are not run.

## Fixed candidate

For every unchanged median-conditioned grayscale image in `[0,1]`:

1. Smooth internally with Gaussian sigma `0.8`, then construct the published
   eight-neighbour pixel graph with absolute gray-level edge weights.
2. Run the Felzenszwalb-Huttenlocher sorted-edge merge with fixed
   `tau(C)=300/|C|`. Set `min_size=1`, thereby disabling implementation-level
   minimum-size postprocessing not present in the paper's core Algorithm 1.
3. Rasterize a binary cue by marking both endpoints of every eight-neighbour
   adjacency whose final component labels differ. Apply no dilation,
   thinning, distance transform, confidence weighting, or segment selection.
4. Fit one positive logistic membership only inside each outer UDED-selection
   training fold. The midpoint is the mean of training edge and texture
   medians; the scale is the pooled training interquartile range with a
   `1e-9` floor. The singleton weight is
   `max(AUC-0.5,0)*(1+mutual_information)`. Eligibility requires training AUC
   at least `0.56`; an ineligible fold is exactly the compact control.
5. When eligible, append the membership to the retained five and renormalize
   singleton weights before the unchanged distorted-Choquet integral.

The retained five memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
threshold grid are unchanged. There is no graph, scale, sigma, connectivity,
component-size, rasterization, calibration, integration, or threshold search.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, cue calibration, eligibility, singleton weight, and operating
  threshold are fit only inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native-resolution 8-bit soft
  output without export-time per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all protected data are not
  read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.
- A fixed synthetic contract must verify finite binary output, one region and
  zero boundary on a flat field, bitwise repeatability, additive-offset
  invariance, and localization of a clean vertical step relative to its flat
  exterior. Fixed checkerboard and seed-18002 small-noise diagnostics are
  recorded without becoming performance gates.

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
8. Synthetic, finite/binary, repeatability, runtime, and deterministic preview
   contracts complete.

Failure of any condition rejects this fixed realization. Do not tune or
extend Gaussian smoothing, `k`, graph connectivity, edge weights, grayscale
handling, minimum-size processing, boundary rasterization, region selection,
feature-space graphs, color-plane intersection, hierarchical segmentation,
calibration, eligibility, integration, context, gate, localizer, or threshold
grid from the result. Do not combine the cue with rejected mechanisms.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `fh_region_boundary_calibration.csv`,
`fh_region_boundary_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and FH region-boundary cue.
