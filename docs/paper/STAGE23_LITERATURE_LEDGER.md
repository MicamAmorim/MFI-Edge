# Stage 23 Literature / Code / Protocol Ledger

This ledger is the provenance record for evidence, aggregation, detector, dataset, and evaluator choices in Stage 23.

Every source that materially changes the descriptor shortlist, aggregator shortlist, detector target list, protocol matrix, or implementation strategy must be added here in the same change that preregisters the resulting experiment.

## Required fields

| ID | Source | DOI / official URL | Source type | Method / component | Training class | Dataset / split / metric | Implementation fidelity | Stage-23 decision role | Notes |
|---|---|---|---|---|---|---|---|---|---|

## Training classes

Use one of:

- `fixed-untrained`
- `unsupervised-data-estimated`
- `classical-supervised`
- `neural-reference-only`
- `not-applicable`

## Implementation fidelity

Use one of:

- `author-code-exact`
- `author-code-adapted-protocol-only`
- `faithful-reimplementation`
- `partial-reproduction`
- `conceptual-source-only`

Do not describe a surrogate as an exact reproduction.

## Protocol discipline

Literature-reported and locally re-evaluated metrics must remain separate. Record the exact split, evaluator, matching tolerance, annotation treatment, resizing/thinning/postprocessing, and whether the source number is validation/test/cross-validation whenever these details are available.

## Entries

_No Stage-23 decision-driving sources have been registered yet. Stage 23A must populate this table from primary papers, official repositories, and official benchmark documentation before descriptor/aggregator screening begins._
