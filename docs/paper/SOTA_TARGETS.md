# MFI-Edge SOTA target ledger

This is the living comparison ledger for the long-horizon goal: an interpretable **non-neural** edge/boundary detector that surpasses the strongest verified neural-network methods under matched official protocols and generalizes across datasets.

Do not copy leaderboard numbers without checking the primary paper/repository and evaluation protocol. Refresh this ledger at literature-escalation checkpoints and immediately before any `goal_reached=true` decision.

## Rules for entries

For each target benchmark, record:

- dataset and exact split;
- official/author-designated evaluator;
- primary metric(s) and tolerance/matching protocol;
- strongest verified neural result found in current literature;
- primary source DOI/URL and publication date;
- date the literature search was refreshed;
- whether code/evaluator is available;
- MFI-Edge frozen-generation result under the same protocol;
- whether that MFI result was obtained without target-test-driven tuning.

Do not compare numerically incompatible protocols as if they were the same benchmark. In particular, the local BSDS tolerant-dilation proxy is not the official Berkeley bipartite/CSA++ evaluation.

## Generalization success gate

The project may set `goal_reached=true` only when all of the following are true:

1. The candidate inference path contains **no neural network or neural feature extractor**.
2. The SOTA literature search has been refreshed from primary sources close to the final evaluation date.
3. A frozen MFI-Edge generation exceeds the strongest verified neural result on the predeclared primary metric for a **multi-benchmark suite of at least three diverse edge/boundary datasets** under matched official or author-designated protocols.
4. At least one benchmark in that final suite is genuinely untouched at the moment the frozen generation is selected.
5. No benchmark/test result in the final suite is used to tune that frozen generation.
6. Results include uncertainty or repeated-run information where the benchmark permits it, plus runtime/complexity reporting.
7. Qualitative output panels are saved for every benchmark so the numerical gain can be visually inspected for boundary quality, localization, texture suppression, continuity, and failure modes.

If a benchmark's strongest neural result cannot be verified under a matching protocol, mark the target `UNRESOLVED` rather than treating a weak or incomparable number as the bar.

## Target table

The autonomous research agent should populate and maintain this table through live literature research.

| Benchmark / split | Official primary metric | Strongest verified neural result | Method / source | Protocol match verified? | Literature refreshed | Frozen MFI-Edge result | Status |
|---|---|---:|---|---|---|---:|---|
| To be refreshed by literature checkpoint | — | — | — | — | — | — | UNRESOLVED |
| To be refreshed by literature checkpoint | — | — | — | — | — | — | UNRESOLVED |
| To be refreshed by literature checkpoint | — | — | — | — | — | — | UNRESOLVED |

## Historical external diagnostics that are **not** final SOTA gates

- BSDS500 local proxy evaluation: useful transfer evidence only; not official Berkeley metric.
- BIPEDv2 already-inspected test: useful historical frozen-transfer evidence only; unavailable for new model selection and not a genuinely untouched final benchmark anymore.
- UDED held-out: historically inspected; unavailable for optimization and not a fresh final external benchmark.

These can be reported in the paper history, but they cannot by themselves satisfy the final generalization gate.

## Visual evolution record

Each future image-based experiment should save `best_method_preview.png` using fixed/predeclared examples. When an incumbent is promoted, preserve the old preview and add the new one rather than overwriting historical evidence. The paper record should reference the qualitative artifacts for important generations.