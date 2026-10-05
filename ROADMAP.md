# MFI-Edge research roadmap

Last updated: **2026-10-05**

This file is the project-level roadmap for MFI-Edge / CH-MFI.  It is intentionally separate from experiment logs: `EXPERIMENT_HISTORY.md` records what happened, while this file records **what is done, what is active, what is next, and what qualifies a model for promotion**.

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
2. **MFI-Fuzzy++ / Stage 5-7** — broad fuzzy-measure/operator/fusion competition and UDED generalization testing.
3. **CH-MFI-v2** — current active line: context-aware, hierarchical, uncertainty-aware fuzzy evidence that controls spatial localization rather than merely being added to it.

A key Stage-7 lesson is preserved as a design constraint: strong selection-split ranking does **not** automatically transfer to held-out natural images.  CH-MFI-v2 therefore keeps selection/inner-CV, frozen thresholds and held-out evaluation strictly separated.

## Track A — CH-MFI-v2 local workstation campaign

| Milestone | Status | Definition of done |
|---|:---:|---|
| v2 architecture modules | 🟢 | `ch_mfi_v2.py`, `advanced_fuzzy_v2.py`, context/localizer/uncertainty paths import and execute |
| synthetic v2 smoke test | 🟢 code / 🟡 machine validation | all smoke families return finite maps on the target workstation |
| standard screen (~519 configs before learned banks) | 🟡 | complete resumable selection ranking and frozen held-out top-k |
| learn scale-specific capacity bank | 🟢 code / 🟡 results pending | five scale banks learned selection-only and exported |
| learn regime-specific Shapley | 🟢 code / 🟡 results pending | clean/texture/blur/noise Shapley files complete and checkpointed |
| rerun standard with learned banks | 🟡 | learned variants compete without replacing controls |
| topology competition | 🟢 code / 🟡 results pending | none/hysteresis/geodesic/hyst+geo chosen on selection and frozen on held-out |
| wide overnight sweep (~4.8k configs before optional learned variants) | 🔴 run pending | only after standard grid and worker scaling are healthy |
| image-size sensitivity | 🔴 | repeat finalists above the current 256-px development resolution |
| runtime/memory scaling | 🟡 | worker-count curve + per-family runtime reported on the target workstation |

Recommended launcher:

```powershell
.\run_research_campaign_v2.bat quick 8
```

Then, after the baseline screen is healthy:

```powershell
.\run_research_campaign_v2.bat full 8
```

Use `wide` only after the standard campaign is stable.

## Track B — model-family coverage

| Research idea | Status | Current implementation / next action |
|---|:---:|---|
| context analyzer: blur/noise/texture/frequency/coherence/heterogeneity | 🟢 | `context_maps.py` |
| hierarchical coarse/fine multiscale MFI | 🟢 | global/local hierarchy in CH-MFI |
| conditional fuzzy operators | 🟢 | context-routed interpretable operator experts |
| distorted-probability capacities | 🟢 | compact monotone capacity family |
| scale-specific learned capacities | 🟢 code / 🟡 results pending | `learn_scale_capacity_bank.py` |
| global Shapley gating | 🟢 | exact 8-feature coalition enumeration |
| regime-specific Shapley | 🟢 code / 🟡 results pending | clean/texture/blur/noise learner |
| regularized pair interactions | 🟢 | low-complexity 2-additive surrogate |
| formal/general k-interactive learning | 🔴 | implement only if pair model is promising |
| SWAFED local adaptive exponent | 🟢 | image-neighbourhood q(x), multiple operators, repository-literal comparison |
| d-Choquet / d-CF | 🟢 | restricted-dissimilarity family |
| d-CC | 🟢 | restricted-dissimilarity family |
| d-XC | 🟢 | restricted-dissimilarity family |
| Choquet-inspired aggregation | 🟢 experimental | paper-inspired CPU-testable candidates; theorem-level equivalence still to audit |
| partition-conditioned aggregation | 🟢 experimental | paper-inspired hierarchical/partition candidate |
| dynamic classical localizer bank | 🟢 | Scharr/Sobel/DoG routing |
| MFI as bilateral controller of localization | 🟢 | evidence + uncertainty refine localizer response |
| model uncertainty from multiscale disagreement/entropy | 🟢 | current inference uncertainty map |
| granularity control | 🟡 | coarse/fine control exists; supervised multi-granularity GT still missing |
| topology repair / linking | 🟢 | hysteresis, geodesic and combined competition |
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
| UDED development/generalization protocol | 🟢 | selection/held-out convention preserved for development |
| official BSDS500 train/val/test experiment | 🔴 | required before strong publication claims |
| official Berkeley bipartite boundary matching | 🔴 | prototype tolerant matcher must not be presented as official BSDS evaluation |
| multiple-annotator uncertainty experiment | 🔴 | preserve individual BSDS annotations rather than collapsing immediately |
| cross-dataset generalization | 🔴 | train/select on one dataset; evaluate frozen model on another |
| resolution sensitivity | 🔴 | 256 px is a development compromise, not a publication default |

## Track D — CH-MFI-v3 / Hybrid (only after v2 evidence)

Do not mix this track into v2 before we know which non-neural components are actually useful.

Planned components:

- learned context/router network;
- learned dynamic convolution/localizer kernels;
- explicit frequency/Fourier branch;
- annotation-aware uncertainty target;
- ranking loss on boundary confidence;
- detector-level fuzzy ensemble with compact learned detectors such as TEED/PiDiNet;
- optional end-to-end differentiable fuzzy-capacity layer.

The purpose of keeping this as a later generation is scientific attribution: we should know how far the interpretable fuzzy/analytic architecture goes before adding deep learned components.

## Track E — WebUI and promotion

The WebUI is an inspection/deployment surface, not a benchmark.

A model is eligible for the `mfi-edge-webui` registry only when all of the following are recorded:

1. exact code/config identifier;
2. validation protocol and ranking metric;
3. frozen threshold or explicit visualization-only fallback;
4. held-out/test metric reported only after selection;
5. qualitative outputs checked for obvious failure modes;
6. benchmark result committed or otherwise preserved reproducibly.

When a model is promoted:

```text
mfi-edge-local-dev
      -> validated configuration
      -> main
      -> mfi-edge-webui registry
```

## Track F — paper/research record

Already maintained under `docs/paper/`:

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

For every such change, also update the appropriate research record in `docs/paper/` so that roadmap status, experimental evidence and future manuscript claims remain synchronized.
