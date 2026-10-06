# Stage 14f — protocol-resolution note

**Status:** Human methodological resolution after Stage 14f, without changing or re-running the observed experiment.

There is no substantive ambiguity in the Stage-14f promotion rule. Before Stage-14f was executed, `docs/paper/STAGE14F_PREREGISTRATION.md` explicitly superseded the older criterion paragraph in `docs/paper/EXPERIMENT_HISTORY.md`. Therefore the canonical primary criterion for Stage 14f is the dedicated preregistration:

1. mean absolute corrupted-F1 advantage `F1_dCC_corrupt - F1_standard_corrupt >= +0.005` across the 12 predeclared corruption cells;
2. clean mean-image F1 delta `F1_dCC_clean - F1_standard_clean >= -0.01`;
3. positive mean absolute corrupted-F1 advantage in at least three of four corruption families.

The clean-referenced degradation advantage is secondary only.

Stage 14f failed the canonical criterion: mean absolute corrupted-F1 advantage was `-0.00191`, clean mean-image F1 delta was `-0.00280`, and zero corruption families had positive mean absolute advantage. The secondary clean-referenced degradation advantage was `+0.00088`; it does not alter the no-promotion decision.

Scientific conclusion: **the isolated d-CC + FBPC + absolute-RDF aggregation is not supported for promotion under this controlled synthetic robustness protocol.** This does not disprove the whole RDF family and does not justify tuning from external or held-out results.

The earlier history paragraph that named clean-referenced degradation as the primary criterion is historical/superseded. Future agents must treat an experiment-specific preregistration that explicitly says it supersedes a generic history paragraph, and that predates result inspection, as the authoritative protocol record.
