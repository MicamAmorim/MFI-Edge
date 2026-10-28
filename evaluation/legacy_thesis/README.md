# Thesis legacy evaluation sources

This directory vendors the exact thesis-era MATLAB path needed for the Stage 22 historical comparison track.

Historical flow:

`continuous aggregated map -> getBoundaries(map, inf) -> binary boundary map -> ComparisonResiduals('ejBCM-F', ..., 0.025)`

`ComparisonResiduals` evaluates the binary candidate separately against each human GT through `ejmBasedConfusionMatrix`, which calls the Estrada–Jepson matcher.

## Provenance

- `getBoundaries.m`, `ComparisonResiduals.m`, `histmedcar.m`: user's thesis-code archive from the supplied Google Drive folder / functions.zip.
- `external/ejmBasedConfusionMatrix.m`: thesis-bundled v1.00 source; its CC-BY-ND header is preserved verbatim.
- `external/estradaJepsonMatching.bckp.m`: complete v1.00 backup matcher; GPL header preserved verbatim.
- other `external/*.m`: exact dependencies retrieved from the thesis Drive
  folder. `SOURCE_MANIFEST.json` records both their Drive file IDs/original
  byte hashes and their repository LF-normalized hashes.

Do not edit third-party vendored files. `SOURCE_MANIFEST.json` pins SHA-256 hashes. Stage 22A creates a run-local filename alias `estradaJepsonMatching.m` from the backup without modifying bytes.

The legacy track is descriptive only. It does not replace standard Berkeley evaluation and cannot promote a detector.
