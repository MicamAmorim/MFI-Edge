# Stage 23G6 preregistration - exact Compass overlap-clean materialization

## Scientific role

Stage 23G6 materializes the unchanged Ruzon-Tomasi Compass detector on the
14-image overlap-clean UDED-selection working raster. It is a baseline
reproduction and artifact-preparation stage, not a gap diagnosis, detector
intervention, cue selection, aggregation test, or promotion experiment.

Compass is the strongest remaining exact strictly untrained Stage-15 reference
with a distinct evidence architecture after the closed SED, PMI, and SCO
routes. The primary paper and official project model opposed image regions as
adaptive color distributions and compare them by Earth Mover's Distance while
rotating the dividing orientation. The official project explicitly identifies
integration across scales as unresolved future work. This observation is a
mechanistic reason to retain Compass as a target, not permission to choose a
scale cue or fusion rule before its exact cross-domain surface exists.

Stage 15F already pinned and reproduced the complete author code at the fixed
published sigma-4 setting on native-resolution BSDS500 validation. Under the
common reference-unverified Berkeley path it obtained ODS/OIS/AP
`0.630841/0.656565/0.518359`. Those existing development results select no
parameter here. The Stage-23F/G1/G2/G5 negative evidence remains binding; in
particular, Stage 23G5's failed SCO/persistence equal mean is not reinterpreted
and this stage selects neither persistence nor equal-mean fusion.

## Frozen detector contract

- Official archive: `https://ai.stanford.edu/~ruzon/compass/ruzon.tar.gz`,
  SHA-256 `43e2ab843af620f5b6405843be0c5478b6953039c36b1e32b2a3ac725ddce7ea`.
- Every reachable author-source byte must match the Stage-15F source manifest.
- Detector call: `compassmex(input, 4, 1, 1, 180, 6, 10)`.
- Fixed parameters: sigma `4`, radius `12`, spacing `1`, 180-degree edge
  model, six wedges per quadrant, 15-degree orientation steps, and at most ten
  color clusters.
- The author's CIE-Lab conversion, randomized clustering, and
  `srand(clock())` behavior remain unchanged. There is no seed intervention,
  repeat selection, or averaging. Each persisted map is the one authorized
  draw for that image.
- Author-valid response centers are zero-padded at the radius-12 border and
  serialized directly as `round(255 * strength)` without per-image
  normalization.
- Training class: strictly untrained, fixed, and non-neural.
- Fidelity label: exact author detector on the declared Stage-23 working
  raster adapter, not an exact native-resolution UDED reproduction.
- The archive has no explicit software license; it remains an ignored local
  dependency and is not redistributed.

## Dataset and raster contract

- Domain: UDED selection, development only.
- Known protected BSDS-test-lineage item `03-35028` is excluded by filename
  before image or GT bytes are read.
- The retained fourteen images use exactly the Stage-23C overlap-clean loader
  and maximum-side-256 bilinear raster.
- The working RGB array is rounded once to an 8-bit result-local PNG before
  MATLAB; its hash is recorded.
- GT is used only for the fixed qualitative preview. It is not exposed to the
  detector, scored, fitted, thresholded, or used to choose a later cue.

## Checkpoint, cache, and provenance contract

Each image is an atomic resumable unit. Before processing it, the runner
validates source-image, raster-adapter, author-source-bundle, parameter,
shape, output, and output-hash identity. A valid record causes `skip complete`;
a missing record causes one `compute new`; any mismatch or unmanifested output
fails closed. Temporary PNGs are atomically moved into place, and valid maps
are never regenerated despite the author's stochastic clustering.

The mandatory BSDS500-validation attachment must hash-validate and byte-reuse
the 100 frozen Stage-15F Compass maps. It cannot invoke Compass or regenerate a
map. Standard Berkeley settings remain 99 thresholds, `maxDist=0.0075`,
thinning, and all annotations. The Windows matcher remains stochastic and
reference-unverified, so this attachment is documentary target-baseline
provenance and cannot promote a detector.

## Required outputs and pass rule

The experiment must emit:

- `summary.json`;
- `overlap_clean_dataset_manifest.json`;
- `map_provenance.jsonl`;
- `map_hashes.json`;
- `per_image_runtime.csv`;
- fourteen persisted Compass PNGs;
- `best_method_preview.png` at fixed overlap-clean positions 1, 7, and 14,
  with panel order input / GT / exact Compass maximum-EMD score;
- `official_eval_manifest.json` whose exporter reuses frozen Stage-15F maps.

The stage passes only if all source hashes match, the protected-lineage item
was excluded before byte access, all fourteen maps are finite, bounded,
single-channel, and working-raster-sized, every identity/hash agrees, and a
second traversal records fourteen exact cache hits with zero detector calls.
An output is complete only after the MATLAB completion marker, a valid atomic
PNG, and its provenance record exist. A post-marker MATLAB heap-corruption exit
may be recorded but cannot invalidate a fully validated output, matching the
already documented Stage-15F platform behavior.

A pass authorizes only a separately preregistered cross-domain target-gap
diagnosis. No cue or aggregator is preselected. A failure permits only a
harness repair that leaves author bytes, stochastic behavior, parameters,
raster, dataset role, and output convention unchanged.

## Forbidden adaptations

- no Compass scale, cluster, wedge, spacing, orientation, NMS, hysteresis, or
  seed tuning;
- no repeated Compass draws, draw selection, averaging, or regeneration of a
  valid cached map;
- no UDED GT scoring, detector threshold fit, gap cue, aggregation, fusion, or
  intervention;
- no reopening or substitution inside the closed SED/half-disc, PMI, or
  SCO/persistence routes;
- no descriptor extraction or silent Stage-23 cache recomputation;
- no protected/test access or documentary test feedback for design.
