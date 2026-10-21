# Stage 21A protocol-certification preregistration

## Role and firewall

Stage 21A is infrastructure and methodology certification, not a detector
experiment. It must not run or score a detector, read any BSDS train,
validation, or test image/ground-truth blob, change MFI, or reinterpret the
Stage-20 outcomes. No official-evaluation manifest is required because the
stage uses only source inspection, prior fixture artifacts, and synthetic
binary micro-cases.

## Pinned sources

- Berkeley/BSDS source: BIDS mirror commit
  `a04b7c6c3a9f0ace74bf205c72a43d32e1c72722`.
- Windows-compatible Piotr Dollár matcher binary: `edges` commit
  `94260b5d0fc068202598312e01a37604972dcc9e`.
- Estrada–Jepson primary definition: Estrada and Jepson (2009),
  DOI `10.1007/s11263-009-0251-z`.
- Target fuzzy-literature convention: Amorim et al. (2025),
  DOI `10.3390/app152413273`.
- Public target-literature implementation surface: KITT commit
  `d70bb66ef9ab6f5cea8ead528fe5ac15ac096baf` (GPLv3; runtime-only ignored
  checkout).

## Berkeley certification contract

The standard path must statically and hash-audit all-human-annotation
accumulation, machine-match union, recall accumulation, `nthresh=99`,
`maxDist=0.0075`, `thinpb=true`, and diagonal-scaled one-to-one
`correspondPixels`. The prior five-image Stage-15a fixture and fixed-seed
causal artifacts are reused; the matcher and fixture are not rerun.

`reference_reproduction_verified` remains false unless the shipped public
reference is reproduced under its unmodified code path. Stage 15a already
showed that the source requests a clock seed and consumes randomized `k`-of-`n`
samples, while the shipped fixture does not record its RNG state. A fixed-seed
binary is diagnostic-only and forbidden for dataset scoring. Stage 21A may
therefore close Berkeley certification as explicitly unresolved, but only with
that exact blocker and provenance recorded.

The Berkeley 2.5% sensitivity mode is a separate configuration whose parsed
contents must differ from the standard configuration only at
`max_dist: 0.025`. It remains reference-unverified and cannot promote a model.

## Estrada–Jepson fidelity contract

The primary paper defines directional proximity matching with the
no-intervening-contour and same-side constraints; it expressly does not force
the Berkeley one-to-one bipartite correspondence. The target 2025 fuzzy paper
uses binary detector maps, all human annotations, a tolerance of
`0.025 * sqrt(H^2 + W^2)`, and equal-weight F-measure. Its primary detector
result is a fixed binary operating point; a best-threshold sweep is separate
and exploratory.

KITT's `oneToManyEJBC` supplies the target-literature multi-annotation
convention: a machine pixel matched to any annotation counts for precision,
while recall matches and GT counts accumulate over annotations before the
ratio is formed.

The pinned public KITT tree contains an important reproducibility defect. Its
advertised v1.01 `estradaJepsonMatching.m` calls an absent `isConnected`
helper for displacements beyond its one-pixel bootstrap. The same immutable
tree ships the complete v1.00 implementation as
`estradaJepsonMatching.bckp.m`. Stage 21A executes a byte-identical runtime copy
of that backup, renamed only because MATLAB requires the file name to match
the function name. This is the best public KITT fidelity supported by the
sources, not proof of identity with an unpublished private copy used for any
paper table. Stage 21B must carry that caveat in every fuzzy-comparison row.

## Synthetic micro-cases

At fixed size `64x64` and `maxDist=0.025`, the exact pinned KITT aggregation
surface must pass:

1. exact match;
2. one-pixel offset;
3. two-pixel inside-tolerance and three-pixel outside-tolerance cases;
4. two predictions competing for one GT pixel;
5. two GT pixels competing for one prediction;
6. shifted crossing contours;
7. two-annotation union-precision / accumulated-recall behavior.

The competition cases are expected to document that Estrada–Jepson is not a
one-to-one matcher, not to force Berkeley behavior onto it.

## Stop rule

Stage 21A passes only if:

- the standard Berkeley source/protocol audit passes and the existing
  reference failure is preserved with its exact RNG-provenance blocker;
- the Berkeley `0.025` config is a max-distance-only variant;
- KITT commit and file hashes match;
- every synthetic Estrada–Jepson contract passes; and
- no dataset or detector is read or scored.

Only then may the controller register Stage 21B. A Stage 21A infrastructure
failure permits repair/retry only and is not scientific evidence about MFI.
