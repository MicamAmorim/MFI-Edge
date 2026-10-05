# MFI-Edge

MFI-Edge is a research project on **multiscale fuzzy edge detection, adaptive aggregation and context-aware spatial localization**.

The project began with functional-information-guided multiscale edge detection and has since expanded into the CH-MFI research line.  The repository intentionally keeps stable/promoted work separate from broad exploratory sweeps.

## Branches

| Branch | Purpose |
|---|---|
| `main` | stable/reproducible promoted line |
| `mfi-edge-local-dev` | active CH-MFI-v2 research and workstation benchmarking |
| `mfi-edge-webui` | local Next.js/FastAPI inference and model-comparison interface |
| `experiment/uded-railway` | server-side UDED experiment lineage |

For the current project checklist and next milestones, see **[`ROADMAP.md`](ROADMAP.md)**.

> The active experimental architecture is ahead of `main`.  Do not interpret the `main` branch as automatically containing the best exploratory configuration; candidates move here only after validation/promotion.

## Stable historical core

The original MFI-Edge line uses:

1. local multiscale descriptors;
2. generalized Choquet-style fuzzy aggregation (`CF`, `CF1F2` and related operators);
3. fuzzy measures over descriptor evidence;
4. functional-information/surprisal maps;
5. coarse-to-fine refinement;
6. classical spatial localization, NMS and topology/linking experiments;
7. synthetic and natural-image benchmark infrastructure.

The repository preserves early stages instead of deleting them because they provide the ablation/history required to explain later CH-MFI designs.

## Current research direction

Active development in `mfi-edge-local-dev` tests **CH-MFI-v2**, where contextual fuzzy evidence controls a spatial localizer rather than being assumed to work best as a direct additive score.

The current research families include hierarchical multiscale aggregation, context-conditional operators, SWAFED, restricted-dissimilarity d-Choquet families, distorted/regularized capacities, Shapley gating, scale-specific measures, uncertainty control and topology competition.

See the branch documentation:

```text
README.md
LOCAL_DEV_V2.md
ROADMAP.md
docs/paper/
```

on `mfi-edge-local-dev`.

## Repository highlights on `main`

- `src/` — descriptor, fuzzy-integral, pipeline, evaluation and visualization code;
- `datasets/sintetics/test/` — fixed synthetic diagnostic cases;
- `synthetic_demo.py` — reproducible small synthetic smoke benchmark;
- `synthetic_v2.py` — robust deterministic synthetic benchmark generator;
- `benchmark_stage4.py` — conditioning/linking/held-out synthetic benchmark lineage;
- `prototype.py` — BSDS500 development runner/operator sweeps;
- `results/synthetic/` — preserved early-stage result reports.

The directory name `sintetics` is retained for repository compatibility.

## Mathematical base

### CF

`CF_m^F(x) = min(1, sum_i F(x_(i)-x_(i-1), m(A_(i))))`

### CF1F2

`CF_m^(F1,F2)(x) = min(1, x_(1) + sum_{i=2}^n [F1(x_(i),m(A_(i))) - F2(x_(i-1),m(A_(i)))])`

With product-like choices these connect back to the classical discrete Choquet integral; the project also explores broader aggregation/pre-aggregation families.

The historical operator bank includes:

`TP, TM, TL, AVG, THP, TDP, OB, OmM, ODiv, GM, HM, S, CF, CL, ORS, FGL, FBPC, FNA, FNA2, FIM, FIP`.

Numerical admissibility checks are engineering screens, not mathematical proofs.

## Basic installation

```bash
pip install -r requirements.txt
```

Verify the original mathematical implementation:

```bash
python test_math.py
```

Run the small synthetic diagnostic set:

```bash
python synthetic_demo.py
```

## Active development checkout

For the current CH-MFI-v2 workstation experiments:

```powershell
git fetch
git switch mfi-edge-local-dev
git pull
python smoke_local_architecture_v2.py
```

Then follow `LOCAL_DEV_V2.md` on that branch.

## Web interface

For qualitative single-model and 2–4 model side-by-side comparison:

```powershell
git fetch
git switch mfi-edge-webui
git pull
.\run_webui.bat
```

The WebUI is an inspection surface, not the source of official benchmark rankings.

## Methodological caveats

- development F1/ODS/OIS/AP currently includes a tolerant boundary matcher that is **not the official Berkeley bipartite evaluation**;
- final publication claims require a frozen training/validation/test protocol and official benchmark evaluation;
- UDED is small and should be treated as a development/generalization dataset rather than the sole source of capacity-learning claims;
- held-out/test performance must never be used to retrospectively rank a large exploratory search;
- paper-inspired experimental operators must be distinguished from faithful reproductions and from new generalizations.
