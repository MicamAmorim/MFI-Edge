# Paper A — Manuscript draft: Predicting fusion benefits from ground-truth-free edge-descriptor statistics

**Manuscript status:** METHODS, EXPLORATORY EVIDENCE AND REPRODUCIBILITY DRAFT; NOT A CONFIRMATORY RESULT. Technical-audit update: 2026-11-16.
**Authors, journal, final title and affiliations:** to be confirmed. This text is an evidence-grounded working manuscript.

## Abstract

Fusion of edge evidence maps may benefit some images while impairing others. We investigate two prespecified, image-level diagnostic hypotheses linking simple ground-truth-free statistics of classical descriptors to the performance difference between a candidate aggregation rule and an equal-mean control. H1 concerns the absolute difference of mean evidence between half-disc distribution contrast and PMI dependency deficit, predicted to correlate negatively with the advantage of maximum fusion. H2 concerns average pairwise map correlation among FH region boundary, half-disc contrast and structure-tensor coherence, predicted to correlate positively with the advantage of generalized Choquet fusion (gamma 1.5). Historical Stage24 exploratory data motivate these hypotheses but cannot constitute independent confirmation. A prospective analysis plans independent BIPEDv2/MultiCue capture groups, a common native-geometry one-to-one F1 evaluator, training-only model calibration and domain-blocked permutation tests. Preliminary metadata and geometric-overlap audits established up to 198 BIPED candidates and 95 MultiCue capture prefixes after the known collision of MultiCue capture 4113 with an earlier UDED discovery image was withheld; these counts are **not independently certified samples**. Simulations suggest that joint power to detect two homogeneous within-domain associations of magnitude 0.20 may be approximately 82.3% at a hypothetical composition of 125 BIPED and 95 MultiCue groups, conditional on strong simplifying assumptions. No held-out confirmatory F1 or hypothesis test has been performed. This manuscript reports the scientific design, existing technical audits, and what is still required to execute the preregistration.

**Keywords:** edge detection; non-additive aggregation; Choquet integral; descriptor complementarity; preregistration; image-level correlation; domain-blocked inference; reproducibility.

## 1. Introduction

Classical edge detectors provide complementary evidence about local intensity variation, regional boundaries, texture and contextual dependencies. A scalar fusion operator combines these maps, but the choice of operator may interact with the distribution and dependence of input evidence. A single aggregate benchmark score cannot establish whether an inexpensive pre-outcome image statistic predicts when a fusion rule will help. This paper therefore separates *prediction of relative operator benefit* from *maximizing detector F1*, and separates retrospective discovery from independent confirmation.

Exploratory Stage23/24 development covered descriptor and aggregation landscapes and motivated two narrowly stated signed hypotheses. The Stage24 evidence and numerical reproducibility assets are versioned under `results/paper_a_evidence/stage24gl/`; they are **development/exploratory**, not blind confirmation. The archived experimental literature and further scientific context are tracked in `docs/paper/`.

## 2. Prespecified scientific questions

For image i, let D_h, D_p, D_f, and D_s be the float32 descriptor maps for `halfdisc_distribution_contrast`, `pmi_dependency_deficit`, `fh_region_boundary`, and `structure_tensor_coherence`, respectively. The predictors require no edge ground truth.

**H1, signed negative.** X1_i = |mean(D_h,i) − mean(D_p,i)|, and Y1_i = F1_i(maximum[D_h,D_p]) − F1_i(equal_mean[D_h,D_p]). The directional hypothesis is Spearman(X1,Y1) < 0.

**H2, signed positive.** X2_i is the mean of the three pairwise spatial Pearson correlations among D_f,i, D_h,i, and D_s,i, with a prespecified policy for degenerate/constant maps still required. Y2_i = F1_i(choquet_generalized_150[D_f,D_h,D_s]) − F1_i(equal_mean[D_f,D_h,D_s]). The directional hypothesis is Spearman(X2,Y2) > 0.

The exploratory UDED-14 values rho(H1) ≈ −0.8066 and rho(H2) ≈ +0.7802 were obtained after examining many contrasts. These selected retrospective associations are *not* unbiased confirmatory effect estimates and are *not* used as power-analysis effect sizes.

## 3. Data roles and leakage prevention

The source exploration comprises 14 UDED original images, all barred from independent confirmation. Historical exposure additionally includes BSDS500 validation and other Stage23/24 development and external-test uses, requiring documented provenance screening. A BIPEDv2 training split produced 198 deduplicated preliminary candidate images, with capture independence and prior exposure still subject to audit. The MultiCue indexed source contains 100 last-left annotated sequences and 96 capture prefixes; four sequences share prefix 4108 and two share prefix 4113. Geometric comparison of 27 historically exposed UDED images against 100 selected MultiCue frames yielded 2,700 comparisons. An exact reciprocal feature-matching rescreen strongly flagged `09-MDBD-1C` against `4113_left_0082`, and the entire 4113 capture group is withheld. Up to 95 MultiCue capture-prefix groups remain candidates. These counts are not proof of 95 independent eligible units; other frames and lineages remain to be audited.

No GT from the proposed confirmatory images is to be used for image selection, operator selection, descriptor tuning, threshold selection, or capacity fitting. Cohort membership, exclusions, dataset version, N and inference must be signed in a separate freeze commit before outcome access.

## 4. Descriptor processing and controlled aggregation

All four descriptor maps are generated as float32 maps with fixed source-code hashes and pre-processing identities. Historical Stage24 maps were calculated at a maximum side of 256 pixels before native-image registration. The exact preprocessing and resolution at which X1/X2 are measured must be frozen for the new cohort. Stage24 uses sigmoid membership maps with parameters `midpoint` and `scale` fitted on development GT. The `legacy_sigmoid` option leaves these already-fitted memberships unchanged; it is not itself a universal calibration parameter. H2's generalized Choquet operator transforms memberships with gamma = 1.5 and uses a *supervised, fitted* monotone capacity. H1 maximum and each matched `equal_mean` control use the same underlying descriptor group and membership parameters. Their operator-specific binary thresholds must be fitted and fixed using permitted development data. Identity suppression and image-oriented NMS are candidate fixed choices. None of these fitted values has yet been independently certified for this confirmatory study.

## 5. Edge-reference semantics and per-image evaluation

BIPED and MultiCue differ in annotation structure. MultiCue provides distinct low-level `edges` and object `boundaries` tasks, with six and five indexed annotation files per annotated last-left frame, respectively. The proposed primary task is low-level `edges` for closest semantic alignment with BIPED; it is *not yet frozen*. The synthetic-only evaluator tests use one BIPED GT mask or six separate MultiCue `edges` masks. For each proposed MultiCue image and operator, compute F1 separately for each annotator using the existing one-to-one maximum-cardinality matcher at tolerance 0.0075 of the native image diagonal, then average F1 across references. Candidate and control are evaluated against exactly the same individual references and give one paired delta per original capture group. No annotator counts as an independent sample.

The Python evaluator is a custom native-geometry matcher, **not the official Berkeley benchmark**. Decoder semantics, empty-GT behavior, multi-channel images and annotator validity must be established on documentation or permitted development data before F1 of the confirmatory cohort is calculated.

## 6. Prospective inferential analysis

The proposed test statistic is a weighted mean of Spearman correlations *within each dataset domain*, weighted by (n_domain−1), with directional one-sided domain-blocked permutations and Holm adjustment across H1/H2 (family-wise alpha 0.05; final planned 100,000 permutations). A global pooled Spearman test would target a different estimand and must not be silently substituted. Stratified image-level bootstrap confidence intervals, within-domain estimates, signed gain/loss distributions and leave-one-unit-out sensitivity are planned. The final tied-rank handling, sampling unit and inference code require preregistration. Scientific confirmation requires the prespecified sign and Holm-adjusted p < 0.05 for each tested hypothesis.

## 7. Pre-freeze results: technical evidence, not confirmatory findings

Metadata-only controls verified the filenames of 100 MultiCue annotated sequences, the existence of 600 `edges` and 500 `boundaries` annotation files, and the 4113 hold. The UDED-14 development inventory contains 13 descriptor types for each of 14 originals, with the 56 source-metadata entries needed for H1/H2 present. Sidecar audits matched all 56 cached descriptor identities, geometries and historical SHA256 declarations. **The integrated workstation audit on 16 November 2026 additionally streamed and verified the bytes of all 56 development-cache NPY files: 56/56 SHA256 matches** against the versioned provenance metadata. The audit returned TECHNICAL_AUDITS_OK_SCIENTIFIC_GATES_STILL_OPEN with zero reported failures, documented in local report prefreeze_20261116T023522_659579Z.json. This establishes cache-integrity consistency, **not** that the fitted operator achieves a better F1, that GT annotations are valid, or that H1/H2 have been confirmed.

Pre-freeze Monte Carlo simulation with 1,000 replicates per scenario and 20,000 reusable null draws per candidate design produced the following *synthetic joint* probabilities of rejecting both H1 and H2:

| BIPED + MultiCue (N) | Both when homogeneous |rho|=0.20 | Both when homogeneous |rho|=0.25 | Both when heterogeneous 0.30/0.10 |
|---|---:|---:|---:|
| 75+75 (150) | 57.6% | 84.8% | 58.4% |
| 90+90 (180) | 68.2% | 90.5% | 70.8% |
| 105+95 (200) | 73.9% | 93.1% | 77.1% |
| 125+95 (220) | 82.3% | 96.0% | 86.5% |
| 145+95 (240) | 85.6% | 97.3% | 92.2% |

These are conditional Gaussian-copula model outputs, not empirically estimated power and not a guarantee that 95 MultiCue capture groups will qualify. For N=150 under a synthetic null with a between-domain shift, the estimated family-wise frequency of any rejection was 3.7%. Joint-power Monte Carlo standard error is at most approximately 1.6 percentage points for 1,000 replicates. A target of 220 is **conditional**, while a sample of 180 has high modeled joint power for effects of 0.25 but insufficient joint power for two effects of 0.20. No irrevocable N is chosen.

**Confirmatory outcomes for H1/H2: NOT MEASURED.** Do not insert a numerical rho, p-value, F1 gain, confidence interval, or significance declaration here until a versioned protocol freeze precedes outcome access.

### 7.1. Technical audit-trail summary (observed, not confirmatory)

| Gate | Evidence established on 16 November 2026 | What remains unproven |
|---|---|---|
| UDED development metadata | 14 original images, 13 descriptor kinds, 182 provenance entries | Independent confirmation from the discovery set |
| H1/H2 map inventory | 56 of 56 required UDED image/descriptor cache identities match metadata | No image-level benefit established |
| Bytewise development-cache integrity | 56 of 56 NPY SHA256 values equal versioned provenance hashes | No fitted H1/H2 model parameter certified |
| MultiCue prospective candidate triage | 100 indexed annotated sequences, 96 capture prefixes, historical prefix 4113 withheld | Full capture independence and annotation decoding |
| BIPED prospective triage | 198 preliminary deduplicated candidate images | Final eligibility, absence of historic exposure and independent scenes |
| Confirmatory H1/H2 | NOT EVALUATED | All signed hypotheses and primary outcome tests remain pending |

The machine audit report is stored on the workstation data volume as paper_a_prefreeze_combined_audit/prefreeze_20261116T023522_659579Z.json, separately from the versioned source tree. The end-of-run status recorded no confirmatory GT/H5/F1 access, no model training and no descriptor recomputation. These are technical traceability statements rather than evidence of predictive discrimination.

### 7.2. Explicit per-capture analysis and prespecified evaluation

For image or independent capture group i, the outcome of hypothesis h is Y(h,i) = F1(candidate(h),i) - F1(equal_mean(h),i). For annotations k=1,...,K(i), compute F1(a,i,k) = 2 TP(a,i,k) / [2 TP(a,i,k) + FP(a,i,k) + FN(a,i,k)] under the fixed native-geometry one-to-one boundary matcher. The image-level score is the arithmetic mean over annotators, calculated independently for candidate and control. MultiCue's proposed six edge annotations, if validated, yield **one** averaged response per independent capture; annotator masks are not replicated samples.

The proposed primary test computes within-domain Spearman correlations rho(h,d), then their n(d)-1 weighted mean T(h) = [sum_d (n(d)-1) rho(h,d)] / [sum_d (n(d)-1)]. Permuting paired outcomes within each domain, not globally, defines the one-sided null distribution. The two resulting p-values will be adjusted by Holm at family-wise alpha=0.05. The original protocol draft still requires amendment and a separate freeze to adopt this estimand; it is not retrospectively assumed to be frozen.

Before outcome inspection the study also needs deterministic rules for constant evidence maps (undefined Pearson), identical ranks, missing data, zero-denominator F1, invalid annotation pixels and shared captures. None may be chosen because it improves held-out p-values.

## 8. Reproducibility and independent audit

Code, the signed protocol draft, synthetic unit tests, data-lineage assessments and the existing Stage24GL Tier-A numeric evidence archive are recorded in the GitHub repository. A local reproducibility ZIP generated by `scripts/package_paper_a_repro.py` includes the manuscript, preregistration, source scripts, reproducibility instructions, evidence metadata, a manifest of checksums and the latest safe overnight audit report if present. It excludes source images, GT/H5, original dataset files, heavy map caches and unreviewed protected test outputs. The archived Stage24GL evidence is explicitly exploratory; its extensive per-fold/official evaluation archives do not convert post-hoc discoveries into independent confirmation.

The staged package is **not an independent laboratory replication**. For final replication, investigators must obtain datasets under applicable licenses, verify source and cache hashes, fix H1/H2 fitted parameters on authorized development data, preregister independent groups and evaluate untouched GT only after the freeze. A paper describing successful pre-freeze checks but no held-out outcomes must be labeled methodological or preliminary; it cannot claim confirmed hypotheses or superior performance.

### 8.1. Reproducibility procedure and output provenance

A third-party audit should (i) check out a pinned code commit and the declared environment, (ii) review the protocol draft and freeze checklist without relabeling historical development as confirmation, (iii) run the synthetic evaluator tests and metadata checks, (iv) compare actual UDED development cache SHA256 values with their declared versioned hashes, and (v) read the Stage24GL numerical evidence archive as exploratory provenance only. It must then wait for independently fitted and signed H1/H2 recipes, the approved cohort and an immutable preregistration before opening new confirmatory GT or running either signed hypothesis test.

The local package PaperA_repro_preconfirmatory_20261116T023603_855866Z.zip was generated after the successful integrated audit, with a SHA256 sidecar and a manifest for 37 included files. Its recorded hash is c45c87dc34a1674f769e46cc5432e4fe5e63318f5b4c12e9eec4778fe5848e37. **That package predates these manuscript revisions**; a new reproducibility ZIP must be generated before distributing the updated draft.

### 8.2. Planned figures and tables (not fabricated outcomes)

- Figure 1: separation of historical hypothesis discovery, permitted development calibration, technical preflight, independent-cohort freeze and untouched outcome evaluation.
- Figure 2: fixed H1 and H2 descriptor groups, shared membership calibration and paired candidate-versus-equal-mean aggregation paths.
- Figure 3: sample lineage and known cross-dataset hold for capture prefix 4113; graph explicitly labels preliminary versus independently certified groups.
- Figure 4: joint synthetic power sensitivity for alternative sample mixes, with the model assumptions and Monte Carlo error made visible.
- Figure 5 (reserved): confirmatory X-versus-delta-F1 relationships by domain, inserted only after genuinely independent outcomes exist.

Every publication figure, table and sentence that would imply observed H1/H2 significance remains reserved rather than synthesized from exploratory F1.

## 9. Limitations and next decision gates

The 14 discovery images are small and retrospectively selected; MultiCue scenes may be temporally correlated beyond prefix grouping; the two domains differ in annotation multiplicity and scene statistics; fixed threshold training must use valid independent development data; the Choquet capacity must be fitted under a documented training lineage. The principal remaining gates are GT-encoding verification on allowed data, training-only parameter provenance, independent-scene certification, preregistered sample size, and a formal source/parameter/frozen-cohort commit. A failed signed hypothesis is a publishable negative result if reported without post-selection.

## References and source provenance

- Primary project evidence and study plan: `docs/paper_a_confirmation/PREREGISTRATION.md`, `docs/paper_a_confirmation/SAMPLE_SIZE_CONDITIONAL_DECISION_20261115.md`, `docs/paper_a_confirmation/GT_EDGES_MULTIANNOTATOR_CONTRACT_PROPOSAL.md`, `docs/paper_a_confirmation/DEVELOPMENT_LINEAGE_P0_2.md`, `docs/paper_a_confirmation/CACHE_SIDECAR_INVENTORY_P0_3.md`.
- Stage24GL numerical evidence and archive description: `results/paper_a_evidence/stage24gl/` and `docs/STAGE24G_L_FULL_REPRODUCIBILITY.md`.
- Bibliographic starting point: `docs/paper/references.bib`. Complete DOI-level citation review is pending; no unverified reference is invented here.
- Foundational evaluation concepts: Martin, Fowlkes and Malik (Berkeley boundary evaluation); Arbelaez et al. (BSDS); Mély et al. (MultiCue). Full bibliography to be checked against originals before submission.

**Scientific gate:** `docs/paper_a_confirmation/protocol.json` remains `draft_not_frozen`; the manuscript may be revised editorially overnight, but its confirmatory Results section must remain pending until a valid prospective study is executed.
