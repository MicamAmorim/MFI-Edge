# Stage 23G9 preregistration — exact QFrD overlap-clean materialization

## Decision and scope

The planning-only checkpoint after Stage 23G8 selects Huang, Hu, and Lian's
exact pinned-author Quaternion Fractional Dirac detector (QFrD) as the next
distinct Stage-23 strong-detector target. This action creates only the missing
overlap-clean UDED target surface. It scores no UDED ground truth, chooses no
missing cue or aggregation family, creates no intervention, and cannot promote
a detector.

QFrD is the strongest remaining already reproduced, runnable, soft-output
analytic reference that is mechanistically distinct from the closed SED, PMI,
SCO, and Compass routes. CO is the unsuppressed precursor inside the already
closed SCO lineage; EDPF exposes only a binary operating point; the exact
Structured Edge forest is already closed by its severe UDED transfer failure;
and an exact gPb runtime has not been established on this workstation. This
ordering does not claim that QFrD is the strongest published non-neural method.

## Frozen implementation

- Primary paper: Huang, Hu, and Lian (2026), *Fractional Dirac Operators for
  Edge Detection*, DOI `10.3390/fractalfract10060412`.
- Official repository: `https://github.com/renhu9120/QFrD.git`.
- Pinned sole commit: `8dcc8d846e6dcbe1bc4b931b89f1c814f5f9a245`.
- Frozen tracked-tree manifest SHA-256:
  `49dbc518659eb7a0cd3742c90f040ef93bdb1a4b5ccf3ac6774c7a4fb11c3c72`.
- Training class: parameter-fixed but author-tuned.
- Source notice: no explicit software license was found; the ignored local
  checkout is not redistributed.
- Fixed author path: fractional order `0.8`, full Hilbert rotation, symmetric
  RGB quaternion axis, replicate padding `64`, Gaussian sigma `2.0`, author
  bilinear NMS, and absolute hysteresis defaults.
- Fidelity caveat: the manuscript describes left multiplier application,
  while the pinned code computes `q_mul(Q, M_full)`. The result is an exact
  author-code reproduction, not proof of paper/code algebraic equivalence.

The fourteen overlap-clean inputs are the exact Stage-23 working rasters:
maximum side `256`, bilinear resize, round-to-uint8 PNG. Known protected-lineage
item `03-35028` must be excluded before image or GT byte access.

## Cache and execution contract

For each of the fourteen inputs the runner must:

1. verify the pinned author commit, clean tracked tree, and frozen manifest;
2. verify or atomically create the exact working-raster PNG;
3. fail closed on an unmanifested or provenance-mismatched output;
4. run the unchanged author soft-score path only on a cache miss;
5. serialize by clipping the author soft NMS map to `[0,1]` and direct
   round-to-uint8, without per-image normalization;
6. persist output hash, source/adapter hash, runtime, score range, parameters,
   and the paper/code caveat immediately after each image;
7. complete a second validation traversal with fourteen cache hits and zero
   detector calls.

The fixed preview uses overlap-clean positions `1/7/14` with panels
`input | GT | exact QFrD soft score`. GT is used only for the documentary
preview; it is not available to detector inference, fitting, scoring, cue
selection, or thresholding.

## Standard-Berkeley attachment

The required validation attachment must hash-validate and byte-reuse the 100
frozen Stage-15i QFrD PNGs. It may not invoke QFrD or regenerate a map. The
existing local ODS/OIS/AP baseline is documentary target provenance under the
reference-unverified Windows matcher; no validation result in this stage may
select a cue or intervention.

## Pass/fail rule

Stage 23G9 passes only if all fourteen overlap-clean maps, provenance records,
runtime rows, exact second-traversal cache hits, protected-lineage exclusion,
fixed preview, and frozen-BSDS attachment complete. A harness or dependency
failure permits only an identical materialization retry; it cannot change the
author commit, detector parameters, raster adapter, serialization, or data.

A pass may authorize only a separately preregistered cross-domain frozen-map
gap diagnosis. That later decision must inventory QFrD's quaternion RGB,
fractional spectral, NMS, and hysteresis evidence before choosing exactly one
missing Stage-23 family. It may not assume persistence, reuse the failed
SCO/Compass interventions, or select a fusion from this materialization.
