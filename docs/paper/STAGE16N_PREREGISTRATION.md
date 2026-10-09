# Stage 16n preregistration - SUSAN local-self-similarity context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Smith and Brady's SUSAN principle defines, around every nucleus pixel, a
Univalue Segment Assimilating Nucleus (USAN): the part of a circular
neighbourhood whose brightness is similar to the nucleus. Their initial edge
response increases as this locally similar area falls below a fixed geometric
threshold, without taking an image derivative (*SUSAN - A New Approach to Low
Level Image Processing*, IJCV 23(1):45-78, 1997,
DOI `10.1023/A:1007963824710`). The authors' official technical-report page
fixes the commonly used radius-3.4, 37-pixel circular mask, sixth-power smooth
brightness comparison, and geometric threshold at three quarters of the
maximum USAN area. Its published edge examples use an 8-bit brightness
threshold of `20`.

Stage 16n asks whether this **centre-referenced local self-similarity** adds
positive boundary context that the retained multiscale amplitude/persistence
bank lacks. It is distinct from detector averaging, connected-component or
region gating, image conditioning, threshold persistence, oriented
step-profile fitting, cross-half-disc texture distributions, and exact EDPF
chain support. It does not use dataset identity and does not weaken the joint
UDED/BSDS rule in response to the repeated cross-dataset reversals.

## Fixed candidate

On the unchanged median-conditioned grayscale image, use the integer samples
inside the radius-`3.4` circular mask (exactly `37` pixels). For nucleus value
`I0` and neighbour value `I`, compute

`c = exp(-((I - I0) / (20/255))^6)`.

Sum `c` over the mask to obtain the USAN area `n`, and define the normalized
initial response as

`max(0.75 * 37 - n, 0) / (0.75 * 37)`.

Integer samples use reflected boundary extension. No SUSAN direction estimate,
non-maximum suppression, thinning, binary linking, or subpixel localization is
applied: this is an equation-level implementation of the published initial
response used only as context, not a claim to reproduce the complete author
detector.

The cue's positive logistic membership and singleton weight are fitted only
inside each outer UDED-selection training fold using the existing positive-
feature rule `max(AUC - 0.5, 0) * (1 + mutual_information)`. It is eligible
only when its training edge-versus-texture AUC is at least `0.56`; when
ineligible, the candidate is exactly the compact control for that fold. When
eligible, append it as a sixth membership and renormalize singleton weights
before the unchanged distorted-Choquet aggregation.

The five retained memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
threshold grid are unchanged.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Cue calibration,
  eligibility, singleton weight, compact bank fitting, and operating threshold
  are fit inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native resolution, and direct
  8-bit soft PNG export without per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and other protected data are not
  read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is at least `-0.002`.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The SUSAN cue is training-eligible in at least `12/15` folds.
6. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are both nonnegative versus the unchanged
   incumbent.
7. The deterministic preview and finite/bounded cue checks complete.

Failure of any condition rejects this fixed realization. Do not tune the mask,
brightness threshold, exponent, geometric threshold, boundary handling,
eligibility, membership calibration, Choquet parameters, gate, localizer, or
threshold grid from the result.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `susan_calibration.csv`,
`best_method_preview.png`, `official_eval_manifest.json`, and the controller's
official-evaluation summary. The preview uses fixed UDED-selection positions
1, 8, and 15 with columns: input, ground truth, incumbent out-of-fold
prediction, candidate out-of-fold prediction, and initial SUSAN response.
