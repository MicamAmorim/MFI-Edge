# Stage 17d preregistration - local GMRF Fisher-information context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Levada derives local type-I and type-II observed Fisher information for an
isotropic pairwise Gaussian Markov random field using Besag's conditional
pseudo-likelihood (*Learning from Complex Systems: On the Roles of Entropy and
Fisher Information in Pairwise Isotropic Gaussian Markov Random Fields*,
Entropy 16(2):1002-1036, 2014, DOI `10.3390/e16021002`, arXiv `1108.4973`).
The paper interprets high type-I information as a local configuration that is
unexpected under the field's global spatial dependence and explicitly shows
such informative patterns at region boundaries. It defines local
L-information as the type-I/type-II ratio.

For the paper's Gaussian conditional model, equations (4), (6), (10), and
(12) algebraically reduce that ratio to the squared standardized conditional
innovation

`(x_i - mu - beta * sum_j(x_j - mu))^2 / sigma^2`.

Stage 17d tests whether this local information-geometric surprise supplies
transferable positive boundary context. It differs from Stage 17b's opposed-
sample ordering statistic, Stage 16z's spatially averaged gradient tensor,
Stage 16x's image-wide spectral graph, and the closed profile, self-similarity,
conditioning, topology, persistence, and localizer families. It is an
equation-level repository realization of the cited GMRF measure, not a
reproduction of a complete published edge detector.

## Fixed candidate

On each unchanged median-conditioned grayscale image, use the paper's
second-order isotropic eight-neighbour system. Reflection supplies the fixed
boundary extension needed to retain a regular neighbourhood at the raster
edge. Estimate the conditional intercept and spatial dependence `beta`
jointly by the ordinary-least-squares form of the paper's Gaussian maximum
pseudo-likelihood equations, then estimate conditional variance `sigma^2`
from those residuals. The cue is the nonnegative local L-information
expression above.
A numerically constant image maps to zero; the only floor is machine epsilon
scaled by pixel count for detecting that degenerate case. No clipping,
per-image normalization, fitted spatial model, scale, orientation, or window
parameter is introduced.

Fit one positive logistic membership only inside each outer UDED-selection
training fold. Its midpoint is the mean of the training edge and texture
medians and its scale is the pooled training interquartile range, with only a
`1e-9` numerical floor. Fit its singleton weight by the established rule
`max(AUC-0.5,0) * (1+mutual_information)`. The cue is eligible only when
training edge-versus-texture AUC is at least `0.56`; an ineligible fold is
exactly the compact control. When eligible, append it as a sixth membership and
renormalize singleton weights before the unchanged distorted-Choquet integral.

The retained five memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
threshold grid are unchanged. There is no neighbourhood, parameter-estimator,
boundary-extension, evidence transform, membership, fusion, or threshold
search.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Compact-bank
  fitting, cue calibration, eligibility, singleton weight, and operating
  threshold are fit only inside each outer training fold. The per-image GMRF
  parameters use image pixels without labels.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native-resolution 8-bit soft
  output without per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and all other protected data are
  not read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.
- A fixed synthetic contract must verify finite nonnegative repeatable output,
  stronger mean response at a vertical step than in remote constant regions,
  zero response on a flat field, and invariance to a positive affine intensity
  transform.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is nonnegative.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The GMRF cue is training-eligible in at least `12/15` folds.
6. Candidate and incumbent soft scores have exactly the same positive support
   in every evaluated fold image.
7. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are both nonnegative versus the unchanged
   incumbent.
8. The synthetic contract, finite/nonnegative checks, runtime diagnostics, and
   deterministic preview complete.

Failure of any condition rejects this fixed realization. Do not tune or vary
the neighbourhood, GMRF parameter fit, boundary handling, evidence transform,
eligibility, calibration, context integration, Choquet parameters, gate,
localizer, or thresholds from the result. Do not advance to multiscale,
anisotropic, color, mixture-GMRF, or learned-random-field variants from this
outcome.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `gmrf_calibration.csv`, `gmrf_diagnostics.csv`,
`best_method_preview.png`, `official_eval_manifest.json`, and the controller's
official-evaluation summary. The preview uses fixed UDED-selection positions
1, 8, and 15 with columns: input, ground truth, incumbent out-of-fold
prediction, candidate out-of-fold prediction, and local GMRF L-information.
