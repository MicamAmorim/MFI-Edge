# Stage 15a source-matcher diagnostic

Status: registered after the fixture path-equivalence retry, before inspecting
any source-rebuild output.

The fixture comparison found that two fresh MATLAB processes running the same
pinned Windows `correspondPixels` binary produced different raw integer match
counts and aggregate tables. The repeat drift is larger than the registered
`1e-4` fixture tolerance, so the result does not satisfy the path-equivalence
decision rule and does not isolate the mismatch to historical fixture
provenance.

This diagnostic compiles `correspondPixels` from the exact C++ sources in the
pinned BSDS500 commit with the workstation's selected MATLAB C++ compiler. The
binary is written under the experiment result directory; no vendored source or
binary is edited. The shipped five prediction PNGs are then evaluated twice in
fresh MATLAB processes through the unchanged Berkeley wrapper, five thresholds,
all fixture annotations, `maxDist=0.0075`, and thinning enabled.

The registered `1e-4` tolerance is unchanged. If the rebuilt matcher is
repeatable and every shipped aggregate table agrees within that bound, its
source commit, compiler, MATLAB version, and binary hash will become explicit
Stage-15a evaluator provenance. Otherwise Stage 15a remains open and the
remaining discrepancy is recorded as unresolved platform/source behavior.
This test uses no BSDS validation image, detector output, or architecture
feedback, and therefore needs neither an official-evaluation manifest nor a
qualitative preview.
