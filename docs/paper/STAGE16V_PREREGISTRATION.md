# Stage 16v preregistration - exact Structured Edge forest replacement

Status: registered before candidate execution or result inspection.

## Hypothesis and literature basis

The completed Stage-14 through Stage-16 sequence has tested many fixed cues,
gates, conditioning operators, localizers, and aggregators without promoting a
generation-2 candidate. Several candidates improved BSDS500 validation while
remaining neutral or harmful on UDED selection. Stage 16v therefore tests a
larger but still bounded and interpretable non-neural hypothesis: predicting a
structured local edge mask may capture junctions and short contour geometry
that cannot be represented by either a scalar local response or the shallow
pixel classifier tested in Stage 14n.

Dollár and Zitnick's Structured Forests method maps each image patch to a local
edge mask with a random decision forest after discretizing structured labels
for information-gain training (ICCV 2013; TPAMI 2015, DOI
`10.1109/TPAMI.2014.2377715`). The official author repository
`https://github.com/pdollar/edges` is pinned at commit
`94260b5d0fc068202598312e01a37604972dcc9e`. Its shipped `modelBsds.mat` is
SHA-256 `9b0f2af485516c89549d4050a7d29fe789c315a4632d16cf29a07796b54c1a6b`
(22,640,640 bytes) and is trained from
`BSDS500/data/{images,groundTruth}/train` by the fixed `edgesTrain.m` contract.
The required official Piotr MATLAB toolbox is pinned at commit
`e87332637bbe8e8b92dd487c87567d9628404523`.

This mechanism is not Stage 14n repeated at a different tree count. Stage 14n
predicted a scalar pixel probability from retained MFI channels with a shallow
forest. The author model predicts a structured 16-by-16 edge mask from each
32-by-32 RGB patch using author color, gradient, and self-similarity channels,
then aggregates and sharpens overlapping patch predictions. It is also not a
neural model.

## Fixed candidate

The candidate is the exact pinned author `modelBsds` inference path:

- eight learned structured trees, with four evaluated per location;
- stride `2`, sharpening `2`, single-scale inference, and the model's fixed
  author features and learned thresholds/masks;
- detector NMS enabled exactly as in the author `edgesEval.m` path;
- one MATLAB thread as a runtime-only determinism control;
- direct 8-bit serialization of the bounded author score without per-image
  normalization.

No forest is retrained and no candidate parameter is selected on UDED or BSDS
validation. The fixed model is explicitly classified as a **non-neural
supervised** detector trained on BSDS500 train. It is not described as
strictly untrained, and its literature scores are not used as experiment
feedback.

The candidate replaces the complete compact MFI score for this falsification.
There is no fusion, routing, MFI-context addition, score mixing, calibration
mapping, or parameter search. Compact Choquet-gated Scharr+NMS remains the
incumbent unless every promotion condition passes.

## Development protocol

- UDED selection: the fixed forest produces one score map per image. The
  established five-repeat by three-fold split with seed `20261009` fits only
  each method's operating threshold on the outer training images. The
  incumbent still refits its compact bank inside each outer fold. The forest
  receives no UDED label or parameter fitting.
- BSDS500 train: training provenance of the immutable author model only. The
  repository does not retrain or alter the forest.
- BSDS500 validation: default official MATLAB attachment with all annotations,
  99 thresholds, `maxDist=0.0075`, thinning, native resolution, and direct
  8-bit soft PNG export. Validation annotations are not read by the exporter.
- UDED held-out, BSDS500 test, BIPEDv2 test, and other protected data are not
  read.
- The unmodified Windows matcher remains stochastic and reference-
  uncertified. The fixed-seed diagnostic matcher is forbidden for scoring.

## Promotion rule

All conditions are conjunctive:

1. UDED aggregate F1 improves by at least `+0.005` over compact MFI.
2. UDED aggregate precision and recall deltas are each at least `-0.003`.
3. Mean paired fold-F1 improves by at least `+0.002`, and the candidate wins at
   least `10/15` fold comparisons.
4. The official BSDS500-validation attachment completes, and ODS, OIS, and AP
   each improve by at least `+0.02` over the unchanged incumbent.
5. Both pinned commits and the model hash verify; a fixed synthetic input is
   bitwise repeatable; every score is finite and bounded; per-image maps,
   hashes, runtimes, model-complexity metadata, and the deterministic preview
   are present.

Failure of any condition rejects the exact author model as the generation-2
replacement. Do not tune tree count, depth, evaluated trees, stride,
multiscale mode, sharpening, NMS, channels, training samples, UDED threshold
grid, score calibration, MFI fusion, or routing from the result. A failure does
not falsify structured prediction or other structured-forest variants.

## Required artifacts

`summary.json`, `variant_ranking.csv`, `fold_results.csv`,
`per_image_metrics.csv`, `per_image_runtime.csv`, `map_hashes.json`,
`best_method_preview.png`, `official_eval_manifest.json`, the frozen map and
provenance directories, and the controller's official-evaluation summary.
The preview uses fixed UDED-selection positions 1, 8, and 15 with columns:
input, ground truth, incumbent out-of-fold prediction, Structured Forest
out-of-fold prediction, and Structured Forest soft score.
