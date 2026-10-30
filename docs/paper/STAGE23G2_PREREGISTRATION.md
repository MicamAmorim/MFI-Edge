# Stage 23G2 preregistration — exact PMI detector runtime preflight

## Decision and scope

Stage 23G1 closed the exact-SED / half-disc route after the preregistered
cross-domain conditional-correctness condition failed. Stage 23G2 does not
replace that cue or retune that target. It begins a distinct strong-detector
route by auditing the complete author implementation of Isola, Zoran,
Krishnan, and Adelson's *Crisp Boundary Detection Using Pointwise Mutual
Information* (ECCV 2014, DOI `10.1007/978-3-319-10578-9_52`).

The official repository is pinned before execution:

- repository: `https://github.com/phillipi/crisp-boundaries.git`;
- commit: `ee2d76e98340313a8f92e1b65064a9b4ea90ac77`;
- license: three-clause BSD text in `License.txt`;
- training class: `unsupervised-data-estimated`, with fixed parameters that
  the paper reports were selected on BSDS500 train;
- prospective fidelity label: exact pinned author code under a
  repository-local runtime harness, not yet a benchmark reproduction.

This action is a dataset-free source/build/runtime preflight. It may not read
UDED, BSDS, any annotation, any frozen detector map, or any Stage-23 descriptor
cache artifact. It does not consume or modify the failed Stage-23F cells and
does not alter compact MFI.

## Why this detector is the next target

The author method is a complete non-neural detector rather than the bounded
Stage-18j/Stage-23 descriptor surrogate. Its primary pipeline estimates
image-internal color/variance feature-pair densities, converts them to
`PMI_rho` affinities, and globalizes those affinities through spectral
clustering. The official project describes the method as unsupervised and
ships the end-to-end `findBoundaries` implementation. This makes it a
mechanistically distinct Stage-23G target after SED's biologically inspired
opponency/surround/feedback hierarchy.

The exact author path is audited before any dataset execution because the
2014 package contains MATLAB MEX dependencies and several speed/accuracy
variants. Stage 23G2 freezes the paper-equation path
`MS_algorithm_from_paper`; it does not select a variant from benchmark
outcomes. The repository's faster `speedy`, `accurate_low_res`,
`accurate_high_res`, and approximate-PMI paths remain documentary and are not
alternative candidates.

## Registered checks

The runner must:

1. materialize the ignored external checkout without redistributing it;
2. verify the exact origin, commit, clean tracked state, tracked-file manifest,
   and `License.txt` hash/text class;
3. verify source contracts for color plus local-variance features,
   `rho=1.25`, three image scales, KDE affinity estimation, 100 spectral
   eigenvectors, and the non-approximated `MS_algorithm_from_paper` branch;
4. compile only the author boundary-detection dependencies required by
   `findBoundaries`, without requiring the bundled benchmark matcher or the
   unsupported-on-Windows UCM segmentation path;
5. run the author's `compile_test` path on one fixed synthetic RGB image;
6. run `findBoundaries(..., 'MS_algorithm_from_paper')` on the same fixed
   synthetic image and require finite, nonempty, native-size scalar and
   oriented outputs;
7. record output hashes, ranges, nonzero counts, MATLAB version, build log,
   runtime, and any stochastic/repeatability caveat without editing author
   source bytes.

The synthetic image is fixed before execution: a `36x36` RGB raster combining
one vertical chromatic step, one horizontal chromatic step, and a bounded
deterministic ramp. It is generated in the run-local harness and is not a
benchmark image.

## Pass/fail rule

The preflight passes only if source provenance, every source-contract check,
the dependency build, the compile-test smoke, and the exact paper-path smoke
all pass. A dependency or harness failure permits only a separately registered
repair/retry of this identical preflight. It may not change the author commit,
paper-path setting, synthetic input, parameter values, or scientific target.

A pass may register one exact pinned-author-code development reproduction on
the overlap-clean UDED selection set and BSDS500 validation, with atomic
per-image maps, hashes, runtimes, deterministic fixed previews, and the
standard-Berkeley attachment. That later reproduction must keep the paper's
test headline separate and must not yet add a cue or aggregator. Only after
the baseline is materialized on both development domains may a prospective
missing-family gap diagnosis be designed.

A failure that cannot be repaired without changing author source or the
registered scientific path closes this target as runtime/fidelity unresolved.
It does not authorize a surrogate, parameter search, SED/half-disc reopening,
or incumbent change.

## Artifact exceptions

`best_method_preview.png` and an official-evaluation manifest are not required
for this action because it is a dataset-free build and synthetic smoke test.
Both become mandatory for any later image-dataset reproduction.

## Registered harness-only retry

The first launch verified provenance and source contracts and compiled every
required MEX dependency, but stopped on the fixed synthetic image because
MATLAB R2023a no longer provides the legacy `princomp` entry point called by
the unchanged author `pcaIm.m`. No dataset or benchmark was read. Retry 1 adds
only a result-local centered economy-SVD implementation of the historical
`princomp` score contract ahead of the immutable author tree. The commit,
author bytes, paper path, parameters, synthetic input, and pass rule are
unchanged.

Retry 1 accepted that compatibility entry point and advanced into unchanged
`getLocalPairs`, but stopped because the sparse result-local build surface did
not contain the empty `../caches/ii_jj_caches` directory where the author code
persists its deterministic image-size index cache. MATLAB's later heap-error
exit followed this explicit missing-directory exception and supplies no
detector output. Retry 2 materializes only that expected result-local directory
before repeating the identical smoke test. It does not edit an author byte,
change a parameter or input, or read a dataset.
