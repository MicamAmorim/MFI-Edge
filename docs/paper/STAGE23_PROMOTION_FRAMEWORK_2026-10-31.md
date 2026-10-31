# Stage 23 — prospective promotion framework amendment (2026-10-31)

## Scope and precedence

This amendment is prospective. It applies only to Stage-23 decisions made after the pause that followed completion of Stage 23G3. It does **not** reinterpret, reopen, retune, or re-score Stage 23F, G1, G2, or G3, and it does not alter the already registered Stage 23G4 gap-diagnosis contract.

The purpose is to prevent a single aggregate criterion from collapsing distinct scientific questions into one binary label. Stage 23F showed that a relationship may preserve an operating-point advantage while failing to preserve global precision–recall ranking. Future Stage-23 intervention decisions must therefore keep these properties separate.

## Four distinct transfer statements

Use the following vocabulary consistently:

1. **Complementarity transfer** — a cue retains nonredundant, GT-supported information relative to a target detector under the preregistered gap diagnostics.
2. **Operational transfer** — an intervention improves the target at useful boundary operating points under the matched evaluator. For Berkeley-style ODS/OIS comparisons, the default Stage-23 operational gate is:
   - `Delta ODS >= +0.002`, and
   - `Delta OIS >= 0`.
3. **Ranking transfer** — the intervention preserves or improves score ordering over the precision–recall sweep. For Berkeley-style evaluation, the default ranking gate is:
   - `Delta AP >= 0`.
4. **Complete transfer** — both the operational and ranking gates pass simultaneously.

Do not use the unqualified phrase `transfers` when only one of these statements is supported.

## Decision ladder for future Stage-23G interventions

For a preregistered matched intervention versus its exact target baseline:

- **Operational fail**: if either `Delta ODS < +0.002` or `Delta OIS < 0`, close that intervention route unless its preregistration already defines another independent criterion. Do not substitute a new cue, aggregator, or target inside the same experiment.
- **Operational pass + ranking pass**: classify as **complete-transfer eligible**. It may be considered for the Stage-23 candidate frontier, subject to all existing provenance, reproducibility, and protected-split rules.
- **Operational pass + ranking fail**: classify as **operational-only transfer**. This is a positive scientific result but not an incumbent replacement and not a Stage-23H freeze candidate. It may authorize at most one separately preregistered, bounded ranking/calibration diagnosis whose purpose is to explain the AP loss while preserving the frozen detector/cue identity. No protected/final split may be used for this diagnosis.

AP is therefore an independent promotion guardrail, not a veto on whether an operationally useful relationship deserves mechanistic follow-up. No post-hoc AP noninferiority margin is introduced.

## No retroactive rescue of Stage 23F

Stage 23F remains exactly as originally preregistered and reported:

- minimum conjunction on persistence + tensor coherence: positive ODS/OIS, negative AP;
- nonnegative logistic addition on persistence + half-disc: positive ODS/OIS, negative AP;
- median OWA on FH + half-disc + tensor coherence: negative ODS/OIS/AP;
- zero complete-transfer promotions under the original conjunctive gate.

Under the vocabulary above, the first two are historical examples of **operational-only transfer**, but this re-labeling is explanatory only and changes no Stage-23F decision, promotion, backfill, or candidate status.

## Dataset roles

Future decisions must preserve dataset-role separation:

- **UDED overlap-clean selection**: heterogeneous, generalization-oriented development surface for evidence structure, complementarity, and bounded mechanism discovery.
- **BSDS500 validation**: canonical natural-image development benchmark for matched Berkeley operating-point and ranking transfer.
- **Protected/final/test splits**: documentary only after freezing; never choose cues, aggregators, parameters, architecture, routing, thresholds, or experiment priority.

A result observed on only one development domain is domain-specific evidence. A cross-domain claim requires the corresponding preregistered criteria to hold on each required domain.

## Relation to Stage 23G4

`stage23g4_sco_persistence_gap_diagnosis` remains frozen exactly as registered. Its four cross-domain gap-support conditions are unchanged. If it fails, SCO/persistence closes as preregistered.

If it passes, it may authorize only the separately preregistered downstream intervention already allowed by the G4 contract. The intervention result must then be interpreted with the decision ladder above:

- operational fail -> close route;
- operational pass + AP pass -> complete-transfer eligible;
- operational pass + AP fail -> operational-only, with at most one bounded ranking/calibration diagnosis before the route is either closed or reaches complete-transfer eligibility.

No weight search, cue substitution, target substitution, Choquet backfill, protected-split feedback, or detector-parameter retuning is authorized by this amendment.

## Stage 23H eligibility

By default, a new method may enter Stage 23H as the proposed improved detector only after complete-transfer eligibility on its matched development track and a frozen software/cache identity. An operational-only result may be reported scientifically but cannot replace the incumbent or trigger protected/final evaluation unless a later preregistered development-only ranking remediation achieves complete-transfer eligibility without sacrificing the operational gate.

## Reporting rule

Every future table or summary that contains ODS/OIS/AP should, where relevant, report the two axes separately:

- operational: ODS/OIS;
- ranking: AP / precision–recall behavior.

The preferred conclusion form is therefore not `pass/fail transfer`, but one of:

- `complete transfer`;
- `operational-only transfer`;
- `ranking-only / no operational promotion` when applicable;
- `no transfer on the preregistered criteria`.
