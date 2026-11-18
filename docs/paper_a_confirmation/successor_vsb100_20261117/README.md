# Paper A successor — fixed evaluation completed

Freeze LOCAL prospectivo: `3faff3660043ee0b063f423c0801b0fc740568d7`.
312 primary scenes: MultiCue62, NYUD153, VSB10097. BIPED48 is secondary,
excluded from primary N, correlations, permutations and Holm decisions.
The original minimum60 per primary domain was preserved.

H1 directional association confirmed: rho=-0.137910168, Holm p=0.01503985.
H2 directional association NOT confirmed: rho=-0.040302807, Holm p=0.76109239.
Mean paired F1 changes are -0.01157012 and +0.01089884 respectively.
Association confirmation is not positive average gain, universal operator
superiority, causal evidence or validation of an adaptive selector.

The separately authorized Codex reviewer performed independent RGB/code/
lineage review and signed360rows before freeze. Afterward an independent
audit verified360checkpoints/caches/features/per-annotator deltas, repeated
100000permutations+2000bootstraps per hypothesis and Holm, and matched48
native F1 calculations using another exact matching algorithm.
This is AI audit, not represented as human or journal peer review.

`protocol.json`, `cohort.csv`, `recipe.json`, `row_review.csv`,
`INDEPENDENT_REVIEW.json`, `source_pins.json`, `power.json` and environment
remain the exact reviewed bytes. Their outcome-closed flags describe the
freeze instant. `EXECUTION_STATE.json` records current completion.
`EXECUTION_RESULTS.json`/`PAIRED_OUTCOMES.csv` contain the fixed results.

The hypothesis features are GT-free per image, but P1 memberships, capacity
and thresholds were fitted on UDED14 development. No new confirmation GT
was used for fitting. NYUD family appeared in development; only scenes are
new. Room IDs do not identify independent households. Supplied ECCV14 RGBs
remain canonical, including two localized face-region differences from HDF.
The evaluator is custom native paired F1, not official Berkeley/NYUD/VSB.

The original A219 and initialN221 proposals were rejected/revised. Do not
execute the legacy A219 launcher as if it were this successor. The reviewed
runner is scripts/execute_paper_a_vsb100_successor.py and refuses to
overwrite completed results. Its caches are under
F:\MFI-Edge-Data\Paper_A_confirmation_successor\3faff3660043ee0b063f423c0801b0fc740568d7.
The user-facing reproducible ZIP preserves reviewed source bytes, including
their original line endings; automatic Git EOL conversion can change raw
hashes and must not be mistaken for an approved scientific source change.

The new public push was rejected because previous explicit authorization
covered four audit files. No alternate upload channel was attempted.
Public release of this prepared package awaits specific user authorization.
The study is not described as publicly preregistered before GT access.
