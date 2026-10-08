# Research agent generation snapshot — through Stage 14u

Snapshot date: 2026-10-07.
Frozen branch: `archive/research-agent-v14u-2026-10-07`.
Snapshot commit: `fd5d060db1bec40e6697141c55e61b616f4d7b28`.
Successor branch: `mfi-edge-stage15`.

## Purpose

This document freezes the scientific state of the autonomous research agent before the Stage-15 reproduction/diagnostic campaign. The archived branch is intended to remain an executable copy of the exploration-first agent generation. Do not rewrite its history. If the project later wants to resume the previous mechanism-search behavior, branch again from the archived ref rather than changing the archive.

## Retained incumbent at freeze

The retained detector is the compact Choquet-gated grayscale Scharr + NMS controller. The Stage-14 program did not produce a candidate satisfying the preregistered conjunctive development criteria strongly enough to replace it.

Key retained compact-context lineage includes positive multiscale edge-signature cues, a compact distorted-capacity Choquet context, context gating, grayscale Scharr localization, and NMS. Exact current implementation details remain authoritative in the repository code and experiment preregistrations; this snapshot is narrative provenance, not a replacement protocol.

## Scientific pattern established by Stage 14

The main result is not merely a list of failures. The sequence established that several mechanistically sophisticated localizer/context alternatives can improve one benchmark while degrading another. In particular, Stage 14r and Stage 14s improved official BSDS500-validation headline metrics but worsened UDED-selection development metrics. That repeated discrepancy motivated a shift from localizer replacement toward trust/reliability mechanisms, followed by the Stage-14t and 14u tests.

This cross-dataset behavior is a central motivation for Stage 15's matched-protocol reproduction and diagnostic campaign.

## Recent experimental record

### Stage 14k — CIELAB color-tensor localizer

Result: not promoted. The fixed Lab vector-gradient replacement failed the preregistered UDED criteria. Grayscale Scharr remained incumbent. The result did not justify a color router or post-hoc color-weight tuning.

### Stage 14l — texture-distribution context feature

Result: not promoted. Aggregate F1 improvement was only about `+0.00031`, below the preregistered margin; mean fold improvement about `+0.00037`; only `6/15` folds won and the feature was eligible in only `7/15` folds. This result does not falsify texture-boundary evidence generally; the tested feature was a specific context construction.

### Stage 14m — fixed linear probability-of-boundary fusion

Result: not promoted. Precision improved by about `+0.00523`, but aggregate F1 fell by about `-0.00497`, mean fold F1 by about `-0.00605`, with only `4/15` fold wins. All models converged, isolating a scientific rather than optimization failure for the fixed realization.

### Stage 14n — shallow edge forest

Result: not promoted. Aggregate F1 changed by about `-0.02493`, precision by `-0.03856`, and only `2/15` folds won. This rejects the bounded shallow surrogate, not the full Structured Forest family.

### Stage 14o — interval-capacity uncertainty

Result: not promoted. UDED aggregate F1 about `-0.00980`, precision `-0.01532`, mean fold F1 about `-0.00798`, `0/15` wins. Official BSDS500-validation later completed after evaluator repairs: ODS/OIS rose slightly, AP fell by about `-0.00100`. The conjunctive rule failed.

The Stage-14o evaluation campaign also exposed multiple MATLAB compatibility/infrastructure failures. Those were documented separately from the scientific result and eventually led to isolated/resumable official evaluation plumbing.

### Stage 14p — MFI-coupled Ambrosio–Tortorelli phase field

Result: not promoted. Large UDED F1/recall loss; official BSDS ODS rose slightly while OIS/AP worsened. The fixed phase-field coefficients were not tuned from the result.

### Stage 14q — anisotropic singularity/shearlet-motivated localizer

Result: not promoted. UDED F1/recall collapsed; BSDS ODS rose slightly while OIS/AP declined. No atom-bank sweep followed.

### Stage 14r — fixed SE(2) orientation-lifted contour enhancement

Result: not promoted. Official BSDS500-validation improved approximately:
- ODS `+0.00381`;
- OIS `+0.00169`;
- AP `+0.00779`.

But UDED worsened:
- aggregate F1 about `-0.00276`;
- precision about `-0.00699`;
- only `5/15` fold wins;
- preregistered largest-component GT coverage also declined rather than improved.

This was the first strong recent signal that a method could help BSDS while hurting UDED.

### Stage 14s — fixed half-order spectral Riesz localizer

Result: not promoted. Official BSDS500-validation improved strongly:
- ODS `+0.01161`;
- OIS `+0.00505`;
- AP `+0.01804`.

UDED failed decisively:
- aggregate F1 about `-0.03599`;
- precision about `-0.02286`;
- mean fold F1 about `-0.03583`;
- `0/15` fold wins.

The project explicitly rejected post-hoc tuning of fractional order, padding, normalization, orientation, or fusion. The result rejects this fixed realization only, not fractional differentiation in general.

### Stage 14t — connected-support a-contrario meaningfulness surrogate

Result: closed without promotion. UDED failed all preregistered conditions:
- aggregate F1 about `-0.01725`;
- precision about `-0.02083`;
- mean fold F1 about `-0.01602`;
- `1/15` fold wins.

After official-evaluation retry, BSDS500-validation also declined:
- ODS about `-0.01257`;
- OIS about `-0.01761`;
- AP about `-0.02830`.

Important scope statement: Stage 14t is a repository-specific upper-level connected-component NFA attenuation. It does **not** reproduce full Edge Drawing / EDPF chain construction and therefore must not be cited as falsifying EDPF.

### Stage 14u — fixed Yager evidential ignorance

Scientific decision at freeze: not promotable from UDED.

UDED result:
- aggregate F1 `-0.00245`;
- mean fold F1 `-0.00171`;
- recall `-0.00781`;
- precision `+0.00072`;
- `3/15` fold wins.

The tiny precision gain did not offset recall/F1 loss. The fixed source partition, masses, Yager conflict handling, pignistic transform, gamma and gate were not to be tuned from this outcome.

Official BSDS500-validation attachment status at snapshot: still documentary/infrastructure work. Two MATLAB native-matching attempts suffered the known intermittent Windows heap-corruption failure. The latest snapshot commit adds resumable per-image Berkeley matching across fresh MATLAB processes without changing predictions, candidate, matcher semantics, or vendor scientific source. Stage 14u remains scientifically rejected from UDED regardless of the eventual documentary attachment.

## Evaluator state at freeze

The repository contains the Berkeley official-evaluation integration with all-annotation matching, 99 thresholds, `maxDist=0.0075`, and thinning. Windows/MATLAB native matching has shown intermittent heap corruption. By commit `fd5d060`, the run-local compatibility layer was modified so that completed nonempty per-image match files are checkpointed and later MATLAB processes resume only missing images before aggregation.

This is an infrastructure repair. It does not change detector predictions or the underlying Berkeley matching semantics and must not be represented as a scientific model modification.

## Deferred ideas at freeze

Examples include threshold/component persistence, uncertainty-controlled PDE conditioning, graph/curvature refinements, and a dynamic/non-neural localizer router. None is automatically selected by the Stage-15 transition.

The dynamic-router idea remains especially constrained: a router is not scientifically justified until Stage-15 per-image/regime diagnostics establish reproducible complementarity using development-only evidence.

## Why this generation was frozen

The exploration-first loop was valuable because it falsified many plausible mechanisms under disciplined preregistration. However, repeated one-shot failures plus the BSDS-positive/UDED-negative pattern mean the information bottleneck is now diagnostic rather than ideational. The project therefore freezes this agent generation and changes to a reproduction-first campaign before designing MFI generation 2.

## Future-paper narrative protection

Do not delete or rewrite this lineage to make the final detector appear inevitable. The future manuscript may legitimately state that:

1. positive multiscale fuzzy edge-signature evidence survived repeated development testing;
2. many plausible replacements/context refinements did not generalize;
3. some mechanisms improved BSDS but harmed UDED, revealing a domain/protocol discrepancy;
4. reliability/ignorance surrogates did not resolve that discrepancy;
5. this evidence motivated a systematic reproduction and error-analysis campaign;
6. the eventual final detector was designed only after that campaign identified genuinely complementary mechanisms.

That sequence is part of the scientific contribution, not noise to be hidden.