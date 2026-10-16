# Stage 17r preregistration - directional patch-recurrence context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Xu, Xu, and Quan, *Structure-Texture Image Decomposition Using
Discriminative Patch Recurrence* (IEEE Transactions on Image Processing
30:1542-1555, 2021, DOI `10.1109/TIP.2020.3043665`; author manuscript
`https://csyhquan.github.io/manuscript/21-tip-Structure-Texture%20Image%20Decomposition%20Using%20Discriminative%20Patch%20Recurrence.pdf`),
distinguish cartoon structure from texture by the spatial organization of
recurrent patches. Similar patches near a cartoon contour tend to recur along
one major direction, whereas similar patches in texture tend to recur across
directions. Their fixed implementation uses `5x5` patches, a `51x51` search
window, four bidirectional bands of width `8`, 16 matches per band, and
similarity `exp(-||p-q||^2/0.3)`. Their directional nonlocal operator (Eq. 6)
is the difference between a pixel and a similarity-weighted prediction from
one band.

Stage 17r tests only that nonlocal directional-residual representation as one
positive context membership. It does not run the paper's wavelet/DCT
morphological-component analysis, Bregman iteration, denoising, or
structure-texture decomposition and is therefore a bounded repository cue,
not an exact reproduction. The hypothesis is that a genuine contour will be
poorly predicted from several directional bands while isotropically recurrent
texture will remain predictable across them. This tests nonlocal recurrence
geometry rather than another local activity statistic.

The mechanism is distinct from Stage 16n's centre-pixel SUSAN similarity,
Stage 17b's opposed local ranks, Stage 14l's half-disc LBP distributions,
Stage 16x's image-wide spectral graph, and the closed structural-support and
conditioning families. It neither compares the centre with nearby pixels nor
links, diffuses, segments, smooths, or replaces the localizer.

## Fixed candidate

On the unchanged median-conditioned grayscale image in `[0,1]`, use the
paper's fixed `5x5` patches and `51x51` reflected search window. Rasterize four
bidirectional bands at `0/45/90/135` degrees with width `8`; remove their
common central intersection exactly once. For each band, retain the 16 lowest
patch-SSD matches. Use the paper's `h=0.3` similarity and its normalized
directional prediction. Subtracting the minimum selected SSD before
exponentiation is allowed only as an algebraically neutral underflow guard,
because normalized weights are unchanged.

For direction `d`, let `r_d` be the absolute difference between the centre
intensity and its normalized similarity-weighted directional prediction.
Define positive evidence as

`E = mean_d r_d`.

Input clipping and finite numerical spill clipping keep `E` in `[0,1]`; there
is no per-image normalization, scale selection, learned patch embedding,
search approximation, recurrence threshold, or fitted coefficient. The
finite rasterization is repository-specific because the paper does not fix
pixel inclusion at band boundaries; its realized offset counts are recorded.

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
- A fixed synthetic contract must verify finite bounded output, zero response
  on a constant field, deterministic repeatability, and greater response near
  a clean step than inside a period-two checkerboard and fixed seed-17017
  zero-mean Gaussian perturbations of standard deviation `0.001` around
  mid-gray. It also records all four raster-band offset counts.

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
patch size, search window, bands, directions, band rasterization, match count,
SSD, similarity bandwidth, residual aggregation, boundary handling,
eligibility, calibration, integration, context, gate, localizer, or thresholds
from the result. Do not advance to multiscale, color, rotation-adaptive,
approximate-nearest-neighbour, learned-patch, full-decomposition, smoothing,
or restoration variants from the outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `patch_recurrence_calibration.csv`,
`patch_recurrence_diagnostics.csv`, `best_method_preview.png`,
`official_eval_manifest.json`, and the controller's official-evaluation
summary. The preview uses fixed UDED-selection positions 1, 8, and 15 with
columns: input, ground truth, incumbent out-of-fold prediction, candidate
out-of-fold prediction, and directional patch-recurrence cue.
