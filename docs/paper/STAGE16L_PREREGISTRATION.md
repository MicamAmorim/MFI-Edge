# Stage 16l preregistration - exact EDPF chain support context

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

Topal and Akinlar's Edge Drawing constructs clean, one-pixel-wide contiguous
pixel chains directly from anchors rather than linking an already thresholded
edge map (*Edge Drawing: A Combined Real-Time Edge and Segment Detector*,
JVCIR 23(6), 2012, DOI `10.1016/j.jvcir.2012.05.004`). Akinlar and Topal's
EDPF runs ED with fixed extreme settings and rejects invalid chain segments by
the Helmholtz/a-contrario NFA test (*EDPF: A Real-time Parameter-free Edge
Segment Detector with a False Detection Control*, IJPRAI 26(1), 2012, DOI
`10.1142/S0218001412550026`). The exact MIT-licensed author implementation is
pinned at commit `69b8d081bd6d28192d816ec0ed02aff9186d73c1`.

Stage-15l development diagnosis found that EDPF's relative advantage over MFI
increases as incumbent fragmentation and edge density increase. Stage 16l
therefore tests whether exact chain-level structural support supplies positive
context missing from the retained bank, while leaving MFI localization
unchanged. This is distinct from Stage 14t's upper-level response-component
NFA attenuation, Stage 14i endpoint linking, Stage 14r SE(2) diffusion, Stage
16d region-boundary stability gating, and Stage 16h threshold persistence.

## Fixed candidate

Run the unchanged grayscale author `EDPF(Mat)` path using the already audited
source hashes and pinned OpenCV 3.4.20 build. Preserve its native binary
output. For resized UDED development arrays, serialize the existing image
values to 8-bit by clipping and round-to-nearest without per-image
normalization, then let the author harness perform its registered OpenCV
grayscale decode. Expand the binary map by exactly one pixel with a `3x3` 8-neighbourhood
binary dilation solely to accommodate raster alignment with Scharr NMS. This
alignment adapter is repository-specific and is not attributed to the author
method.

Use the aligned binary support directly as one positive membership. Its
singleton weight is computed only from each outer UDED-selection training fold
with the existing positive-feature rule
`max(AUC - 0.5, 0) * (1 + mutual_information)`. It is eligible only when the
training edge-versus-texture AUC is at least `0.56`; when ineligible, the
candidate is exactly the control for that fold. When eligible, append it to
the five retained memberships and renormalize singleton weights before the
unchanged distorted-Choquet aggregation.

The five retained memberships, gamma `0.55`, gate strength `2.0`, floor
`0.10`, median conditioning, grayscale Scharr+NMS localizer, and fold-fitted
operating thresholds are unchanged. The binary EDPF map does not replace the
localizer and is not averaged with the incumbent score.

## Development protocol

- UDED selection: five repeats by three folds, leakage-free. Eligibility,
  singleton weight, retained compact bank fit, and operating threshold are fit
  inside each outer training fold.
- BSDS500 validation: default official MATLAB attachment, all annotations, 99
  thresholds, `maxDist=0.0075`, thinning enabled, native resolution, and
  direct 8-bit soft PNG export without per-image normalization.
- UDED held-out, BSDS500 test, BIPEDv2 test, and other protected data are not
  read.
- The unmodified Windows matcher remains stochastic and reference-uncertified;
  the fixed-seed diagnostic matcher is forbidden for dataset scoring.
- The prior exact binary EDPF validation metrics are documentary baseline
  evidence only; they do not set the membership weight, alignment rule, or
  operating threshold.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002` versus compact MFI.
2. UDED aggregate precision delta is at least `-0.002`.
3. UDED aggregate recall delta is at least `-0.003`.
4. Mean paired fold-F1 delta is nonnegative and the candidate wins at least
   `9/15` folds.
5. The chain cue is training-eligible in at least `12/15` folds.
6. Mean paired largest-component GT-coverage delta is nonnegative and the
   candidate wins at least `8/15` fold coverage comparisons.
7. The official BSDS500-validation attachment completes, ODS improves by at
   least `+0.002`, and OIS and AP are both nonnegative versus the unchanged
   incumbent.
8. The deterministic preview, exact-author source/hash checks, and
   finite/bounded map checks complete.

Failure of any condition rejects this fixed realization. Do not tune author
EDPF parameters, the one-pixel alignment dilation, eligibility, membership
weighting, Choquet parameters, gate, localizer, or threshold grid from the
result.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `edpf_chain_calibration.csv`, exact UDED EDPF map
hashes and runtimes, `best_method_preview.png`, `official_eval_manifest.json`,
and the controller's official-evaluation summary. The preview uses fixed
UDED-selection positions 1, 8, and 15 with columns: input, ground truth,
incumbent out-of-fold prediction, candidate out-of-fold prediction, and exact
EDPF chain support plus the fixed one-pixel alignment adapter.
