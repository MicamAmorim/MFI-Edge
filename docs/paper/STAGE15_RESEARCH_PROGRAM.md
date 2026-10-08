# Stage 15 research program — reproducibility, diagnosis, then redesign

Status: preregistered research program before Stage-15 result inspection.
Created: 2026-10-07.
Base scientific lineage: `fd5d060db1bec40e6697141c55e61b616f4d7b28`.
Archived previous agent generation: `archive/research-agent-v14u-2026-10-07`.
Active Stage-15 branch: `mfi-edge-stage15`.

## Why Stage 15 exists

Stages 14k–14u tested a long sequence of bounded, preregistered non-neural mechanisms while preserving the compact Choquet-gated grayscale Scharr+NMS controller as incumbent. None earned promotion. Several localizer/context variants produced a repeated cross-dataset pattern: some improved official BSDS500-validation metrics while worsening UDED-selection repeated CV. Stage 14t then showed that a simplified connected-support a-contrario attenuation did not resolve the discrepancy, and Stage 14u showed that a fixed Yager evidential-ignorance fusion did not improve UDED either.

This is enough evidence to stop the automatic cycle `new mechanism -> one-shot falsification -> new mechanism` temporarily. Stage 15 changes the research mode from invention-first to **reproduction, protocol audit, error diagnosis, and only then redesign**.

The historical Stage-14 record is not superseded or erased. It remains evidence for the future manuscript and must be cited when Stage-15 decisions depend on it.

## Mandatory scientific rules for Stage 15

1. **No new MFI architecture before Stage 15p.** Stages 15a–15o are benchmark, reproduction, protocol-audit, or diagnostic stages. They may implement external non-trained methods faithfully, but may not use their outcomes to opportunistically redesign the MFI candidate before the diagnostic phase is complete.
2. Every reproduced method must be classified as: strictly untrained; parameter-fixed but author-tuned; weakly data-calibrated; or trained. Only the first two may be candidates for the non-neural reference frontier. Trained methods may appear only as context/SOTA targets.
3. Every Stage-15 implementation decision materially driven by literature must record the paper, DOI/URL, code repository if any, exact methodological role, evaluation protocol, and whether the source is primary/official/secondary in `docs/paper/STAGE15_LITERATURE_LEDGER.md` and, when appropriate, `docs/paper/BIBLIOGRAPHY_MATRIX.md`.
4. Prefer exact author code or faithful reproduction before repository-specific approximations. If exact reproduction is impossible, label the implementation as a surrogate and state the missing elements.
5. Never compare headline numbers across incompatible protocols as though they were directly comparable. Store reported literature metrics and our re-evaluated metrics separately.
6. Use the repository's official Berkeley evaluator for comparable BSDS500 development attachments. Preserve all annotations, 99 thresholds, `maxDist=0.0075`, thinning, and the pinned matcher unless a protocol-audit stage explicitly documents a compatibility issue.
7. UDED selection remains development-only with leakage-free repeated CV. UDED held-out, BSDS500 test, and BIPEDv2 test remain unavailable for Stage-15 architecture selection.
8. Do not micro-tune a reproduced method after inspecting its Stage-15 benchmark outcome. If the paper specifies several published variants, preregister which one is being reproduced and why.
9. Keep deterministic qualitative previews and per-image outputs wherever feasible. Stage 15k onward depends on per-image complementarity analysis.
10. Preserve negative results. A faithful failure is scientifically useful and must stay in the paper history.

## Central questions

Stage 15 must answer, in order:

1. What is the strongest **verified, non-trained** edge/boundary detector under our matched official protocol?
2. Which published high numbers survive re-evaluation under the same protocol?
3. Which mechanisms explain the gap between local-gradient methods and stronger contextual methods?
4. Why do some Stage-14 mechanisms improve BSDS500 while worsening UDED?
5. Which errors of the incumbent are genuinely complementary to external non-trained methods?
6. Only after those answers: which mechanism deserves integration into MFI-Edge generation 2?

---

# Phase I — matched-protocol reproduction campaign

## Stage 15a — evaluator and protocol audit

Goal: establish the measurement floor before comparing algorithms.

Required work:
- verify Canny and the repository Scharr/incumbent through the exact Stage-15 BSDS evaluation path;
- verify image sizing, soft-map conventions, NMS/thinning interaction, annotation handling, threshold sweep, and `maxDist`;
- document reference-reproduction status and any remaining MATLAB compatibility differences;
- produce a protocol matrix separating official Berkeley-compatible results from proxy/incompatible literature metrics.

This stage does not modify MFI architecture.

## Stage 15b — exact SED reproduction

Reference: Akbarinia & Párraga, *Feedback and Surround Modulated Boundary Detection*, IJCV 2018, DOI `10.1007/s11263-017-1035-5`.

Goal: establish a strong bio-inspired, non-trained contextual baseline under our evaluator.

Priority: highest.

## Stage 15c — vector co-occurrence morphology audit

Reference: Lu et al., *Vector co-occurrence morphological edge detection for colour image*, IET Image Processing 2021, DOI `10.1049/ipr2.12290`.

Goal: test whether the reported high BSDS performance survives our matched evaluator. The paper's comparison table contains protocol/implementation signals that make independent reproduction mandatory before treating its headline numbers as frontier evidence.

Priority: highest, but result must be treated as a reproduction claim, not accepted a priori.

## Stage 15d — exact Edge Drawing / EDPF reproduction

References:
- Topal & Akinlar, *Edge Drawing: A Combined Real-Time Edge and Segment Detector*, DOI `10.1016/j.jvcir.2012.05.004`.
- Akinlar & Topal, *EDPF: A Real-time Parameter-free Edge Segment Detector with a False Detection Control*, DOI `10.1142/S0218001412550026`.
- Author code: `https://github.com/CihanTopal/ED_Lib`.

Goal: test the full chain-first Helmholtz/a-contrario method. Stage 14t was a connected-upper-level surrogate and must **not** be interpreted as falsifying EDPF.

## Stage 15e — CO/SCO contextual color baselines

Core reference for CO: Yang et al., *Efficient Color Boundary Detection with Color-Opponent Mechanisms*, CVPR 2013, DOI `10.1109/CVPR.2013.362`.

Goal: decompose the value of color opponency and contextual/sparseness mechanisms under a matched protocol.

## Stage 15f — Compass distribution-gradient baseline

Reference: Ruzon & Tomasi, *Color Edge Detection with the Compass Operator*, CVPR 1999, DOI `10.1109/CVPR.1999.784624`.

Goal: test half-disc distribution contrast as a boundary cue that can detect distribution changes even when mean luminance gradients are weak.

## Stage 15g — texture gradients + surround modulation reproduction

Reference: Yang, Peng & Wu, *Edge Detection Using Texture Gradients and Surround Modulation*, Signal, Image and Video Processing 2025, DOI `10.1007/s11760-025-04339-6`.

Goal: distinguish **texture inside a region** from **texture-distribution change across a boundary**. This is a central Stage-15 hypothesis because the latter is positive boundary evidence, not merely anti-texture evidence.

## Stage 15h — adaptive multiscale surround modulation

Reference: Zhang et al., *Contour detection model inspired by V1 surround modulation*, Signal, Image and Video Processing 2025, DOI `10.1007/s11760-024-03634-y`.

Goal: test whether image-internal adaptive surround behavior helps explain the UDED/BSDS discrepancy without using dataset identity.

## Stage 15i — modern fractional reference audit

Reference: *Fractional Dirac Operators for Edge Detection*, Fractal and Fractional 2026, DOI `10.3390/fractalfract10060412`.

Goal: provide a contemporary analytic/fractional reference under our evaluator. This is a **benchmark stage**, not permission to restart fractional-order micro-tuning after Stage 14s.

## Stage 15j — high-number protocol audit

Goal: investigate recent non-trained papers reporting unusually high F/F1 values and determine whether those values correspond to Berkeley ODS/OIS/AP, another threshold policy, or another matching protocol. No paper's headline number is accepted as an official-protocol target until verified.

---

# Phase II — error and complementarity diagnosis

No new MFI feature may be promoted during this phase.

## Stage 15k — per-image oracle matrix

For every reproducible Stage-15 method and the incumbent, store per-image precision/recall/F1 and official BSDS contributions where possible. Build pairwise win/loss and oracle-complementarity matrices.

## Stage 15l — image-regime characterization

Predeclare measurable image properties, including at minimum:
- texture density;
- local/global contrast;
- edge-map density;
- contour length/fragmentation;
- curvature/orientation complexity;
- scale distribution;
- GT density and annotator agreement where available.

Test which properties explain method deltas. Avoid dataset labels as router features.

## Stage 15m — pixel/segment complementarity

Measure which true positives are unique to each strong method, which false positives are shared, and whether gains come from localization, weak-boundary recovery, texture suppression, or structural continuity.

## Stage 15n — UDED versus BSDS discrepancy audit

Directly test the Stage-14 observation that SE(2)/fractional/context variants can help BSDS while hurting UDED. Compare dataset distributions and matched error regimes without using protected test splits for design.

## Stage 15o — texture evidence decomposition

Separate at least:
- interior texture/activity evidence;
- cross-boundary texture-distribution contrast;
- local gradient strength;
- multiscale persistence;
- structural/chain support.

This stage decides whether a Stage-16/MFI-generation-2 feature integration is scientifically justified.

---

# Phase III — hypothesis-led MFI generation 2

These stages are conditional. They are **not** automatically run simply because their letters exist. Stage 15o must justify them from development-only evidence.

## Stage 15p — positive texture-boundary membership

Candidate idea: a preregistered half-disc distribution-distance membership representing change between texture distributions across a candidate boundary. Do not conflate it with generic texture suppression.

## Stage 15q — surround-modulation membership

Candidate idea: retain the incumbent localizer while exposing contextual surround evidence as an explicit fuzzy membership rather than replacing Scharr.

## Stage 15r — distributional half-disc cue

Candidate idea: Compass-like distribution contrast integrated as an interpretable cue, only if 15f/15m establish complementarity.

## Stage 15s — Edge-Drawing structural support

Candidate idea: use edge-chain support as a structural membership or confidence cue without automatically replacing the MFI score.

## Stage 15t — chain-level a-contrario confidence

Conditional on 15s. Test EDPF-like chain meaningfulness as a structural confidence cue. Do not reuse the failed Stage-14t component attenuation and do not claim Stage 14t tested this mechanism.

## Stage 15u — fixed expert mixture

Only if 15k–15o establish complementary regimes. First test a fixed, interpretable combination; do not jump immediately to a learned router.

## Stage 15v — analytic image-adaptive router

Only if development evidence proves regime complementarity and the routing variables are image-internal, interpretable, and preregistered. Dataset identity is forbidden.

## Stage 15w — robustness campaign

Run frozen candidates against preregistered perturbation families such as Gaussian noise, blur, compression, illumination shifts, texture clutter, and compound corruption.

## Stage 15x — freeze, ablation, efficiency, and final-transfer readiness

Freeze the retained generation; produce full ablations, complexity/runtime accounting, qualitative panels, bibliography/protocol ledger, and a final-test plan. Protected external/test datasets remain untouched until the final protocol permits them.

---

# Promotion discipline

For architecture-changing stages (15p onward), the exact numerical promotion margins must be preregistered before results are viewed. At minimum the decision must be conjunctive across:
- UDED-selection repeated leakage-free CV non-collapse/stability criteria;
- official BSDS500-validation ODS/OIS/AP criteria when applicable;
- no material failure of a preregistered mechanism-specific endpoint;
- deterministic qualitative output present;
- no protected-test feedback.

A reproduction stage does not 'promote' the reproduced external method into MFI. Its purpose is to establish a verified baseline and a mechanistic diagnostic.

# Required records for every Stage-15 decision

Every stage must leave enough provenance to reconstruct the future paper narrative:

- hypothesis/question;
- preregistered mechanism and parameters;
- source papers and code;
- DOI/URL and access date when relevant;
- dataset role and evaluation protocol;
- implementation fidelity: exact / faithful reimplementation / surrogate;
- results and failure modes;
- interpretation, clearly separated from raw results;
- decision: reproduce further / retain as baseline / reject as MFI integration / justify next diagnostic;
- deterministic preview path for image-based experiments;
- commit SHA linking the decision to code/results.

The purpose of Stage 15 is not to hide the exploratory path. It is to turn that path into a traceable scientific argument for the final detector and manuscript.