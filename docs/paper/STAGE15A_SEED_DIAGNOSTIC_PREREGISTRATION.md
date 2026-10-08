# Stage 15a clock-seed diagnostic preregistration

Status: registered after the source-pinned matcher rebuild result and before
this diagnostic is run. This is a fixture-only causal diagnostic, not an
evaluator replacement or detector experiment.

## Question

Does the pinned matcher's documented clock-seeded global random stream cause
the fresh-process disagreement observed with both the shipped Windows binary
and the repository-built MSVC binary?

The pinned source initializes `Random::rand` through `reseed(0)`, which obtains
a seed from `gettimeofday`, and `kofn.cc` consumes that stream for randomized
sampling. The unmodified source-built matcher differed across two fresh runs
by up to `0.000433` in fixture aggregate tables, so it failed the registered
Stage-15a `1e-4` reproducibility condition.

## Frozen diagnostic

- Copy the exact pinned matcher sources into the result directory.
- In that run-local copy only, replace the global default constructor's
  `reseed(0)` call with the predeclared nonzero seed `1`.
- Record original and controlled `Random.cc` hashes and compiler provenance.
- Build with the already audited MSVC compatibility headers.
- Evaluate the unchanged five shipped fixture PNG maps twice in fresh MATLAB
  processes and compare all aggregate tables.
- Do not score BSDS validation, generate detector maps, edit vendor files,
  alter the `1e-4` tolerance, or use the controlled binary for later metrics.

Seed `1` is a causal control selected before results; it is not searched or
chosen to approach the shipped fixture tables. Agreement with shipped numeric
tables is descriptive only.

## Decision rule

If every repeated table is byte/numerically identical, classify clock-seeded
random sampling as the cause of the repeat drift. Close Stage 15a without
setting `reference_reproduction_verified=true`: the unmodified official path
still failed its preregistered fixture condition, and the controlled binary is
diagnostic only. Proceed to the already ordered Stage-15 reproduction campaign
while reporting official results as stochastic and uncertified until a later
protocol decision is preregistered.

If any fixed-seed repeat differs, retain the classification as unresolved
platform/source behavior and do not proceed to Stage 15b.
