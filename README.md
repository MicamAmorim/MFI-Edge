# MFI-Edge / CH-MFI

MFI-Edge is an experimental edge-detection research project centered on **multiscale fuzzy aggregation, context-aware evidence fusion and precise spatial localization**.  The project started from functional-information-guided multiscale edge detection and has evolved into **CH-MFI (Contextual Hierarchical MFI)**.

> This checkout is the **`mfi-edge-local-dev`** research branch.  It is intentionally broader than `main`: many competing variants live here before promotion.

## Project status

The current active model family is **CH-MFI-v2**.

Conceptually:

```text
Image
  |
  +--> Context analyzer
  |      blur / noise / texture / frequency / coherence / heterogeneity
  |
  +--> Fuzzy evidence branch
  |      multiscale descriptors
  |        -> optional Shapley gating
  |        -> scale-specific/adaptive fuzzy capacities
  |        -> standard / SWAFED / d-Choquet / Choquet-inspired families
  |        -> coarse/fine hierarchical aggregation
  |        -> MFI attention + uncertainty
  |
  +--> Spatial localization branch
         Scharr / Sobel / DoG bank
         -> context-routed localizer
         -> oriented NMS

MFI attention + uncertainty
          |
          v
controls/refines localization
          |
          v
continuous edge score
          |
          v
threshold / hysteresis / geodesic topology repair
```

The central design change from the early MFI-Edge prototype is that fuzzy evidence is no longer assumed to be best used by simply adding it to a gradient score.  CH-MFI explicitly tests whether it should **select evidence, choose an aggregation behavior, choose scale, control a localizer and guide topology**.

## Branches

| Branch | Purpose |
|---|---|
| `main` | stable/reproducible promoted line |
| `mfi-edge-local-dev` | active model research and workstation sweeps |
| `mfi-edge-webui` | local Next.js/FastAPI qualitative comparison interface |
| `experiment/uded-railway` | historical/server-side UDED experiments |

See **[`ROADMAP.md`](ROADMAP.md)** for the current project-wide checklist and next milestones.

## Quick start on the target Windows workstation

Target environment: Ryzen 7-class CPU, ~32 GB RAM, Windows 11, Python 3.11+.

```powershell
git fetch
git switch mfi-edge-local-dev
git pull
```

Fast v2 smoke test:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python smoke_local_architecture_v2.py
```

Expected final marker:

```text
CH_MFI_V2_SMOKE_DONE
```

Recommended first research run:

```powershell
.\run_research_campaign_v2.bat quick 8
```

The full local campaign, including learned scale capacities, regime-specific Shapley and topology competition:

```powershell
.\run_research_campaign_v2.bat full 8
```

Use the `wide` mode only after the standard screen and worker-scaling profile are healthy:

```powershell
.\run_research_campaign_v2.bat wide 8
```

Detailed workstation instructions: **[`LOCAL_DEV_V2.md`](LOCAL_DEV_V2.md)**.

## CH-MFI-v2 experimental families

The current `standard` grid contains roughly **519 configurations before optional learned regime/scale variants**.  The wide grid is roughly **4.8k configurations** before those optional variants.

Implemented families include:

- flat and coarse/fine hierarchical multiscale aggregation;
- fixed and context-conditional fuzzy operators;
- power, additive, local-adaptive and distorted-probability capacities;
- regularized pair-interaction capacities;
- image-neighbourhood SWAFED adaptive exponents;
- d-Choquet / d-CF / d-CC / d-XC restricted-dissimilarity variants;
- Choquet-inspired input-dependent aggregation;
- partition-conditioned aggregation;
- global and regime-specific Shapley gating;
- scale-specific learned capacity banks;
- adaptive classical localizer bank;
- MFI/uncertainty bilateral and soft localizer control;
- topology competition: none, hysteresis, geodesic and hysteresis+geodesic.

Research implementations inspired by recent papers are labelled as such; they must not be described as theorem-level or bit-exact reproductions unless separately verified.

## Main v2 files

```text
src/ch_mfi_v2.py
src/advanced_fuzzy_v2.py
src/research_grid_v2.py
src/context_maps.py
src/dynamic_localizer.py
src/linking.py
learn_scale_capacity_bank.py
learn_regime_shapley.py
run_local_research_v2.py
benchmark_topology_v2.py
run_research_campaign_v2.bat
```

The older `src/ch_mfi.py`, `run_local_research.py` and `LOCAL_DEV.md` remain as first-wave research history; use the `*_v2` path for new experiments.

## Datasets and current protocol

### Synthetic

- `datasets/sintetics/test/` — small fixed diagnostic set with exact masks.
- `synthetic_v2.py` — deterministic robust synthetic benchmark with multiple primitive/degradation families.

The spelling `sintetics` is preserved for repository compatibility.

### UDED

The local development protocol currently uses alternating images as selection and held-out subsets.  Model ranking is selection/inner-CV based; held-out results must never be used to reorder the whole search.

UDED is small and is a development/generalization dataset, **not sufficient for final publication claims**.

### BSDS500

BSDS500 remains a required publication-stage target.  Final reporting must use the official boundary evaluation protocol rather than relying only on our development tolerant matcher.

## Historical experimental line

The repository preserves the progression rather than hiding obsolete approaches:

- Stage 1-4: synthetic MFI, orientation, conditioning and linking;
- Stage 5-7: fuzzy-measure/fusion competition and UDED generalization;
- Stage 8: contextual server-side prototype lineage;
- current local line: CH-MFI-v2.

Stage-7 evidence is particularly important: a configuration can rank well on selection yet fail to establish a held-out advantage.  This is why all current v2 experiments preserve frozen selection/held-out separation.

## Mathematical base

Two central historical generalized Choquet forms remain in the codebase.

### CF

`CF_m^F(x) = min(1, sum_i F(x_(i)-x_(i-1), m(A_(i))))`

### CF1F2

`CF_m^(F1,F2)(x) = min(1, x_(1) + sum_{i=2}^n [F1(x_(i),m(A_(i))) - F2(x_(i-1),m(A_(i)))])`

The repository also contains the original operator bank:

`TP, TM, TL, AVG, THP, TDP, OB, OmM, ODiv, GM, HM, S, CF, CL, ORS, FGL, FBPC, FNA, FNA2, FIM, FIP`.

Numerical admissibility screens are useful engineering checks, not mathematical proofs.

## Research notebook for the future paper

The long-term research record is under `docs/paper/`:

- `ARCHITECTURE_MAP.md` — global and model-specific editable diagrams;
- `BIBLIOGRAPHY_MATRIX.md` — current architecture-driving literature;
- `LEGACY_REVIEW_CORPUS.md` — historical SLR literature corpus;
- `EXPERIMENT_HISTORY.md` — stage-by-stage scientific history;
- `PAPER_WRITING_PLAN.md` — claims, figures, ablations and manuscript evidence plan;
- `references.bib` — working bibliography.

The roadmap and paper notebook should be updated whenever a new model family, paper, dataset or benchmark result changes the project direction.

## Important methodological caveats

- the current tolerant boundary F1/ODS/OIS/AP implementation is a **development proxy**, not the official Berkeley bipartite matcher;
- 256-px resizing is currently a development/runtime choice and must receive a resolution-sensitivity study;
- UDED is too small for strong capacity-learning claims;
- handcrafted context maps are router features, not calibrated probabilities;
- held-out/test performance is evaluation only, never a source of post-hoc model selection;
- paper-inspired experimental operators must be clearly distinguished from faithful reproductions and from our own generalizations.
