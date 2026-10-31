# Stage 23G3 preregistration — exact SCO overlap-clean materialization

## Scientific role

Stage 23G3 materializes the unchanged author SCO detector on the 14-image
overlap-clean UDED-selection working raster. It is a baseline-reproduction and
artifact-preparation stage, not a detector intervention, cue selection, or
promotion experiment.

The target is Yang et al.'s double-opponent color-boundary detector with the
published modified spatial-sparseness constraint (SCO). The primary paper
(DOI `10.1109/TIP.2015.2425538`) describes oriented chromatic/achromatic
double-opponent responses followed by local spatial-sparseness texture
suppression. The institutional author archives were already hash-pinned and
reproduced exactly on native-resolution BSDS500 validation in Stage 15E.
Under the common local official path, exact SCO obtained ODS/OIS/AP
`0.656582/0.682564/0.694939`. Those existing development results selected no
new parameter and remain separate from the paper's documentary test numbers.

SCO is the next distinct Stage-23 target because it is the strongest remaining
exact deterministic strictly untrained reference after the closed SED and PMI
routes, and its color-opponent plus response-sparseness architecture is not a
variant of either closed target. No missing evidence family or aggregator is
selected at this stage. That decision requires the exact cross-domain baseline
surface first.

## Frozen detector contract

- Author source: the already pinned institutional `SCOboundary.rar` archive,
  SHA-256 `01f928da7c9ecacfd3b0ebc0ce5a095fb561d2366745eee6e72e56234a6c9071`.
- Reachable MATLAB source hashes must match the Stage-15E manifest exactly.
- Detector call: `SCOBoundary(input, 1.1, 8, -0.7, 5)`.
- Parameters: Gaussian scale `1.1`, eight orientations, cone weight `-0.7`,
  and modified-spatial-sparseness window `5`.
- Author output: intrinsically normalized, NMS-suppressed soft score in
  `[0,1]`; serialization is fixed `round(255*score)` without adapter
  normalization.
- Training class: fixed at inference and strictly non-neural; the published
  constants were author-selected on BSDS300 train.
- Fidelity label: exact author detector on a declared fixed raster adapter,
  not an exact native-resolution UDED reproduction.

## Dataset and raster contract

- Domain: UDED selection, development only.
- The known BSDS-test-lineage item `03-35028` is excluded by filename before
  image or GT bytes are read.
- The retained 14 images use exactly the Stage-23C overlap-clean loader and
  maximum-side-256 bilinear image raster. This keeps future target-gap
  diagnostics aligned with the immutable Stage-23 descriptor cache.
- The resized RGB array is rounded once to an 8-bit result-local PNG adapter
  before MATLAB. Its hash is recorded. This declared raster quantization
  changes no detector equation or parameter.
- GT is used only in the deterministic preview and is not read by MATLAB,
  scored, fitted, thresholded, or used to choose the target.

## Checkpoint and provenance contract

Each image is an atomic unit. Before computation, the runner validates a
per-image record containing source, adapter, author-source-bundle, parameter,
shape, output, and output-hash identity. A complete valid record causes a
`skip complete`; a missing record causes one `compute new`; an identity or hash
mismatch fails closed. The author detector is never rerun for a valid unit.
Records and the aggregate manifest are written atomically.

The mandatory BSDS500-validation attachment must reuse the 100 frozen exact
Stage-15E SCO PNGs after verifying their registered hashes. It may copy those
bytes into the evaluator workspace but may not rerun SCO or regenerate a map.
The default standard Berkeley settings remain 99 thresholds, `maxDist=0.0075`,
thinning, and all annotations. The Windows matcher remains stochastic and
reference-unverified, so the attachment is documentary baseline provenance and
cannot promote a detector.

## Required outputs and pass rule

The experiment must emit:

- `summary.json`;
- `overlap_clean_dataset_manifest.json`;
- `map_provenance.jsonl`;
- `map_hashes.json`;
- `per_image_runtime.csv`;
- 14 persisted SCO PNGs;
- `best_method_preview.png`, using fixed overlap-clean positions 1, 7, and 14
  with panel order input / GT / exact SCO score;
- `official_eval_manifest.json` whose exporter reuses the frozen Stage-15E SCO
  maps.

The stage passes only if all author-source hashes match, the protected-lineage
item was excluded before byte access, all 14 outputs are finite/native-to-the-
working-raster/single-channel/bounded, every atomic record and artifact hash
agrees, and a second traversal obtains 14 cache hits with zero detector calls.

A pass authorizes only a later separately preregistered target-gap diagnosis.
A failure permits a harness-only retry when it does not change source bytes,
parameters, raster, dataset role, or output convention. This stage cannot
select a cue, aggregator, threshold, intervention, or new incumbent.

## Forbidden adaptations

- no SCO/CO parameter tuning or variant selection;
- no native-versus-working-raster comparison selected from outcomes;
- no descriptor extraction or Stage-23 cache recomputation;
- no GT scoring, target threshold fitting, gap cue, aggregation, fusion, or
  intervention;
- no SED/half-disc or PMI-route repair/substitution;
- no protected/test access and no use of documentary test metrics for design.
