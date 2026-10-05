# MFI-Edge research roadmap

Last updated: **2026-10-05**

This is the project-level roadmap for MFI-Edge / CH-MFI. `docs/paper/EXPERIMENT_HISTORY.md` records what happened; this file records **what is done, what is active, what is next, and what qualifies a model for promotion**.

Legend: 🟢 implemented/completed · 🟡 implemented but still under validation / partial · 🔴 planned · ⚪ parked / optional.

## Branch responsibilities

| Branch | Role | Promotion rule |
|---|---|---|
| `main` | stable/reproducible line | only validated models, scripts and frozen benchmark artefacts |
| `mfi-edge-local-dev` | active workstation research | broad model competition; failures and negative results are allowed |
| `mfi-edge-webui` | qualitative inference/comparison UI | only intentionally promoted models should appear in the deployable registry |
| `experiment/uded-railway` | server-side UDED experiments/history | infrastructure/benchmark lineage; not the current primary development line |

## Current scientific position

The project has moved through three conceptual generations:

1. **MFI-Classic** — multiscale fuzzy evidence, ROI/refinement, classical localizer, NMS/linking.
2. **MFI-Fuzzy++ / Stage 5–7** — broad fuzzy-measure/operator/fusion competition and UDED generalization testing.
3. **CH-MFI-v2** — current active line: context-aware, hierarchical, uncertainty-aware fuzzy evidence that controls spatial localization rather than merely being added to it.

### Latest evidence: first local CH-MFI-v2 standard screen

The initial **519-configuration** UDED standard screen is complete on the local workstation. It used 3-fold inner-CV on the 15-image selection half and frozen thresholds on 15 held-out images.

The formal winner was:

`v2_std__distprob_g055__global_local__conditional__g0.75__soft`

but it did **not** beat Scharr:

| Metric | CH-MFI-v2 winner | Scharr |
|---|---:|---:|
| selection CV F1 | 0.71857 | **0.76610** |
| selection ODS | 0.71991 | **0.76642** |
| held-out F1 | 0.71325 | **0.76204** |

Held-out delta F1 was **-0.04879**, with paired-bootstrap 95% CI **[-0.10097, -0.00560]**. All 12 selection-ranked held-out finalists were below Scharr with bootstrap intervals below zero.

This is a **useful negative/diagnostic result**. It means the current unlearned CH-MFI-v2 operating point is not competitive and the wide sweep must remain blocked. The next test is not “more of the same grid”; it is the intentionally planned learned regime/scale adaptation plus stronger ablation diagnosis.

Full compact report: `results/uded/ch_mfi_v2_standard/STANDARD_SCREEN_REPORT.md`.

## Track A — CH-MFI-v2 local workstation campaign

| Milestone | Status | Definition / latest result |
|---|:---:|---|
| v2 architecture modules | 🟢 | `ch_mfi_v2.py`, `advanced_fuzzy_v2.py`, context/localizer/uncertainty paths execute |
| synthetic v2 smoke test | 🟢 | major v2 branches executed before the standard screen |
| first standard screen (519 configs, no learned banks) | 🟢 | complete; negative vs Scharr; compact results preserved in Git |
| learn scale-specific capacity bank | 🟢 code / 🟡 **next run** | learn five scale banks on selection only |
| learn regime-specific Shapley | 🟢 code / 🟡 **next run** | clean/texture/blur/noise Shapley files, checkpointed |
| rerun standard with learned banks | 🟡 **next decision point** | learned variants appended without replacing controls |
| explicit component ablations | 🔴 **add before wide** | localizer-only; MFI-gating-only; dynamic vs Scharr localizer; uncertainty on/off; hierarchy on/off |
| topology competition | 🟢 code / 🟡 deferred | run only after continuous-score finalists close the baseline gap |
| wide overnight sweep (~4.8k configs before optional learned variants) | 🔴 **blocked** | do not run until learned-bank standard rerun shows a credible improvement trend |
| image-size sensitivity | 🔴 | repeat finalists above current 256-px development resolution |
| runtime/memory scaling | 🟢 initial profile | 1/2/4/8 workers measured; 8 workers = 2.58x vs 1 on 8 profile configs |

Recommended next sequence:

```powershell
python learn_scale_capacity_bank.py --max-side 256
python learn_regime_shapley.py --regimes all --target final --workers 8
.\run_local_research_v2.bat standard 8
```

Do **not** launch `wide` yet.

## Track B — model-family coverage

| Research idea | Status | Current implementation / next action |
|---|:---:|---|
| context analyzer: blur/noise/texture/frequency/coherence/heterogeneity | 🟢 | `context_maps.py`; visual diagnosis shows texture leakage still matters |
| hierarchical coarse/fine multiscale MFI | 🟢 | best individual v2 candidate used global/local hierarchy; flat remains important control |
| conditional fuzzy operators | 🟢 | best individual candidate used conditional mode; still below Scharr |
| distorted-probability capacities | 🟢 | gamma 0.55 produced the best initial candidate |
| scale-specific learned capacities | 🟢 code / 🟡 results pending | immediate next experiment |
| global Shapley gating | 🟢 | exact 8-feature coalition enumeration available |
| regime-specific Shapley | 🟢 code / 🟡 results pending | immediate next experiment |
| regularized pair interactions | 🟢 | initial unlearned family not competitive; keep as control |
| formal/general k-interactive learning | 🔴 | implement only if learned interaction models become promising |
| SWAFED local adaptive exponent | 🟢 | initial family underperformed in the 519-config screen; retain for scientific comparison |
| d-Choquet / d-CF | 🟢 | d-CF had competitive selection CV among alternative families but poor held-out finalists |
| d-CC | 🟢 | produced high selection ODS peaks but weaker inner-CV ranking |
| d-XC | 🟢 | highest full-selection ODS peak among v2 families, but weaker inner-CV; do not select post-hoc |
| Choquet-inspired aggregation | 🟢 experimental | interesting ODS behavior; theorem-level equivalence still to audit |
| partition-conditioned aggregation | 🟢 experimental | fast, but not competitive in initial CV screen |
| dynamic classical localizer bank | 🟢 | visually still too texture-sensitive; explicit fixed-Scharr ablation required |
| MFI as bilateral/soft controller of localization | 🟢 | soft gave the best individual candidate; neither controller beat baseline |
| model uncertainty from multiscale disagreement/entropy | 🟢 | visual map is highly texture-responsive; uncertainty ablation is now high priority |
| granularity control | 🟡 | g=0.75 gives highest ODS peaks; g=0.50 better average CV; suggests regime-dependent scale routing |
| topology repair / linking | 🟢 code | do not use topology to hide a weak continuous score; evaluate after learned-bank rerun |
| explicit Fourier/multiband branch | 🔴 | frequency is currently contextual only |
| learned operator/localizer router | 🔴 | current router is hand-designed/contextual |
| learned dynamic convolution | 🔴 | future Mask2Edge-inspired direction |
| annotator/GT uncertainty | 🔴 | planned for BSDS multi-annotator supervision |
| ranking loss / RankED-style supervision | 🔴 | future learned/ranking stage |
| fuzzy detector ensemble (TEED/PiDiNet/etc.) | 🔴 | future `CH-MFI-Hybrid` generation |

## Track C — validation and datasets

| Milestone | Status | Notes |
|---|:---:|---|
| deterministic synthetic primitives | 🟢 | exact GT; useful for mechanism diagnosis |
| robust synthetic benchmark v2 | 🟢 | clean + degradation families |
| UDED development/generalization protocol | 🟢 | selection/held-out convention preserved; first v2 standard result now archived |
| official BSDS500 train/val/test experiment | 🔴 | required before strong publication claims |
| official Berkeley bipartite boundary matching | 🔴 | prototype tolerant matcher must not be presented as official BSDS evaluation |
| multiple-annotator uncertainty experiment | 🔴 | preserve individual BSDS annotations rather than collapsing immediately |
| cross-dataset generalization | 🔴 | train/select on one dataset; evaluate frozen model on another |
| resolution sensitivity | 🔴 | 256 px is a development compromise, not a publication default |

## Track D — CH-MFI-v3 / Hybrid (only after v2 evidence)

Do not mix this track into v2 before we know which interpretable/non-neural components are actually useful.

Planned components:

- learned context/router network;
- learned dynamic convolution/localizer kernels;
- explicit frequency/Fourier branch;
- annotation-aware uncertainty target;
- ranking loss on boundary confidence;
- detector-level fuzzy ensemble with compact learned detectors such as TEED/PiDiNet;
- optional end-to-end differentiable fuzzy-capacity layer.

The purpose of keeping this as a later generation is scientific attribution: determine how far the fuzzy/analytic architecture goes before adding deep learned components.

## Track E — WebUI and promotion

The WebUI is an inspection/deployment surface, not a benchmark.

A model is eligible for the `mfi-edge-webui` registry only when all of the following are recorded:

1. exact code/config identifier;
2. validation protocol and ranking metric;
3. frozen threshold or explicit visualization-only fallback;
4. held-out/test metric reported only after selection;
5. qualitative outputs checked for obvious failure modes;
6. benchmark result committed or otherwise preserved reproducibly.

**No CH-MFI-v2 model from the first 519-config screen is eligible for promotion.**

When a model is promoted:

```text
mfi-edge-local-dev
      -> validated configuration
      -> main
      -> mfi-edge-webui registry
```

## Track F — paper/research record

Maintained under `docs/paper/`:

- `ARCHITECTURE_MAP.md` — editable diagrams;
- `BIBLIOGRAPHY_MATRIX.md` — architecture-driving current literature;
- `LEGACY_REVIEW_CORPUS.md` — historical SLR corpus;
- `EXPERIMENT_HISTORY.md` — chronological evidence/failures;
- `PAPER_WRITING_PLAN.md` — manuscript evidence map;
- `references.bib` — working BibTeX library.

Before manuscript freeze:

- verify all TODO bibliographic metadata;
- resolve the 2026 FSS PII `S0165011426003714` if it is cited;
- label each external-method implementation as **faithful reproduction**, **paper-inspired**, or **our generalization**;
- rerun promoted models under the final official evaluation protocol;
- create publication-quality vector diagrams from the Mermaid source diagrams;
- preserve environment, commit SHA, configs and raw result tables.

## Roadmap maintenance rule

Update this file whenever any of the following happens:

- a new model family is implemented;
- a planned family is dropped or superseded;
- a benchmark changes the scientific direction;
- a model is promoted to `main` or WebUI;
- a new dataset/evaluation protocol becomes canonical;
- a paper introduces a new architectural hypothesis.

For every such change, also update the appropriate research record in `docs/paper/` so roadmap status, experimental evidence and future manuscript claims remain synchronized.
