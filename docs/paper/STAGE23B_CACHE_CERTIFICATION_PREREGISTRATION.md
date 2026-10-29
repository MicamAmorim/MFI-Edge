# Stage 23B preregistration - content-addressed cache certification

## Role

Stage 23B is a synthetic-only infrastructure certification. It reads no UDED,
BSDS, BIPED, NYUD, Multi-Cue, protected image, or ground-truth file and scores
no detector. It authorizes Stage 23C only if every cache contract passes.

## Implementation under test

- module: `src/stage23_cache.py`;
- canonical later-stage root: `cache/local_dev/stage23/`;
- disposable certification namespace:
  `cache/local_dev/stage23/_certification/`;
- artifact data: NumPy `.npy` with `allow_pickle=false`;
- per-artifact provenance sidecar: JSON;
- discovery/provenance index: atomic JSONL manifest by artifact type;
- locks: exclusive repository-local lock files;
- writes: temporary file, flush/fsync, atomic replace, then read-back check.

The cache identity contains dataset, split, image id, artifact type/id,
preprocessing id, all scientific parameters, implementation function and
version, code version, source-image hash, representation class, and the
`gt_used` declaration. A scientific change produces a different SHA-256 key.

## Fixed synthetic input

Three in-memory float32 images are used: flat, horizontal ramp, and centered
step. The only extractor accepts an image array and scalar gain; it has no path
or GT argument. Its output is deterministic gradient magnitude. The synthetic
source-byte SHA-256 is part of every identity.

## Required checks

All conditions are conjunctive:

1. The first request for each of the three exact identities calls the extractor
   once and writes an artifact; the second request is a cache hit and does not
   call the extractor.
2. Reloaded arrays and artifact-file SHA-256 values are identical.
3. Changing only an extractor parameter creates a distinct key and computes
   one new artifact.
4. Changing only the preprocessing id creates a distinct key and computes one
   new artifact.
5. Sidecar identity, dtype, shape, source hash and artifact hash match the
   atomic descriptor JSONL manifest record; the expected record count is exact.
   One derived transform is also stored, loaded without recomputation, and
   verified against its separate transform manifest.
6. Appending bytes to one cached array causes a fail-closed
   `CacheCorruptionError`; the extractor is not silently called to repair it.
7. An identity declaring `gt_used=true` is rejected before its compute callback
   can run.
8. The synthetic extractor signature exposes only `image` and `gain`.
9. No temporary atomic-write file remains.

## Decision

- Pass: `summary.json -> status=completed` and every check is true. Register
  Stage 23C with a separate image-experiment preregistration, official BSDS
  attachment if applicable, fixed preview, and the Stage-23A frozen pool.
- Fail: do not extract a benchmark descriptor. Register one harness/cache
  repair that preserves these checks and reruns only Stage 23B.

No cache failure or repair may modify the Stage-23 descriptor or aggregator
shortlists. Corrupt ordinary artifacts must be repaired by an explicit action;
ordinary read-through calls may never overwrite them.

This is infrastructure-only rather than an image-based detector experiment.
There is no candidate prediction, GT, metric, qualitative method output, or
BSDS export, so `best_method_preview.png` and an official-evaluation manifest
are not applicable. The sole required result artifact is `summary.json`.
