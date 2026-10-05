# MFI-Edge local research branch

Branch: `mfi-edge-local-dev`

This branch is the workstation-oriented research branch for the next MFI-Edge architecture experiments. It is intentionally broader than `main`: variants are allowed to compete here without being promoted to the production/reproducible line until they are validated.

## Target workstation

The default launcher is tuned for a desktop with roughly:

- Ryzen 7-class CPU
- 32 GB RAM
- Windows 11
- Python 3.11+

The benchmark shares precomputed feature tensors between worker threads, so the main experiment does **not** duplicate the full UDED feature cache per worker. BLAS/OpenMP inner threading is pinned to 1 to avoid nested oversubscription.

Default worker count is:

```text
min(8, cpu_count - 2)
```

Use `--workers N` if you want to override it.

## First checkout

```powershell
git fetch
git switch mfi-edge-local-dev
git pull
```

## Fastest run

From the repository root:

```powershell
.\run_local_research.bat smoke
```

Then run the normal workstation sweep:

```powershell
.\run_local_research.bat standard
```

For a long overnight exploratory sweep:

```powershell
.\run_local_research.bat wide
```

The launcher creates `.venv` if necessary, installs `requirements.txt`, limits inner BLAS/OpenMP threads and launches `run_local_research.py`.

## Presets

### `smoke`

Small sanity run. It checks the main architectural branches and is intended to reveal import/runtime mistakes quickly.

### `standard`

Current recommended Ryzen 7 / 32 GB experiment. It keeps the major model families alive and currently contains about **292 configurations** before optional Shapley-gated variants.

It crosses:

- power, additive, local-adaptive and distorted-probability capacities;
- flat vs global/local hierarchical MFI;
- fixed vs context-conditional fuzzy operators;
- multiple edge granularities;
- bilateral MFI-to-localizer control vs soft control;
- restricted-dissimilarity d-CF variants;
- adaptive vs uniform localizer controls;
- MFI-only and localizer-only ablations.

### `wide`

Long exploratory grid, currently about **3,892 configurations** before optional Shapley variants. Use checkpoints/resume and preferably let it run overnight.

## New architecture under test

The experimental pipeline is implemented in `src/ch_mfi.py`.

Conceptually:

```text
Image
  |
  +--> Context analyzer
  |      heterogeneity / blur / texture / noise / frequency / coherence
  |
  +--> Fuzzy context branch
  |      multiscale descriptors
  |        -> optional Shapley gating
  |        -> scale-specific fuzzy aggregation
  |        -> optional conditional operator routing
  |        -> hierarchical coarse/fine aggregation
  |        -> MFI attention + uncertainty
  |
  +--> Spatial localization branch
         Scharr / Sobel / DoG(1) / DoG(2)
         -> context-routed localizer bank
         -> oriented NMS

MFI attention + uncertainty
          |
          v
controls/refines the spatial localizer
          |
          v
continuous final edge score
```

The important design change is that MFI is treated primarily as **context/evidence that controls localization**, rather than as a score that must simply be added to Scharr.

## Implemented research ideas

### 1. Context maps

`src/context_maps.py`

Lightweight local maps estimate:

- heterogeneity;
- blur;
- texture;
- high-frequency energy;
- low-frequency structure;
- noise/median residual;
- structure-tensor coherence;
- local orientation.

These maps are router inputs, not calibrated probabilities.

### 2. Hierarchical multiscale MFI

Instead of forcing every scale into one undifferentiated fusion, the `global_local` mode first builds:

```text
coarse = aggregate(25, 13)
fine   = aggregate(7, 5, 3)
```

and then aggregates `coarse` and `fine` at a second level. `granularity` controls the coarse/fine prior.

### 3. Conditional fuzzy operators

The `conditional` mode softly mixes interpretable aggregation experts according to the local regime:

- clean: `CF1F2(CL, CL)`;
- texture: `CF1F2(TM, TM)`;
- blur: `CF1F2(TP, TL)`;
- noise: `CF1F2(TM, FNA)`.

The original fixed operator remains in the competition.

### 4. Distorted-probability capacities

`distorted_probability_capacity()` implements compact capacities of the form:

```text
m(A) = g(sum_i p_i)
```

with power or smooth S-shaped distortion. This is a lower-complexity alternative to a fully free capacity and is included as a candidate rather than a replacement.

### 5. Restricted-dissimilarity variants

The branch includes exploratory d-CF variants using bounded restricted dissimilarities (`abs`, `sqrt`, `quadratic`, `sin`). These are labelled exploratory: they are not claimed to be bit-exact reproductions of a specific published RDF unless the exact published dissimilarity is later plugged in and verified.

### 6. Dynamic localizer bank

`src/dynamic_localizer.py`

A small bank contains:

- Scharr-like derivative magnitude;
- Sobel;
- derivative of Gaussian at sigma 1;
- derivative of Gaussian at sigma 2.

Blur/noise/texture/coherence maps route the localizer weights per pixel. This directly tests whether MFI/context should control the **localizer itself** rather than only its threshold.

### 7. Uncertainty

Scale disagreement and normalized scale-response entropy generate an uncertainty map. Bilateral control uses both MFI evidence and uncertainty:

```text
score = localizer * exp(alpha*(MFI-0.5) - beta*uncertainty)
```

### 8. Shapley descriptor gating

`learn_local_shapley.py` can learn exact descriptor Shapley values on the UDED **selection split only**.

With the current 8 descriptors, exact enumeration requires only 256 coalitions.

Example:

```powershell
python learn_local_shapley.py --target final --workers 8
```

Output:

```text
results/local_dev/shapley_descriptor_importance.json
results/local_dev/shapley_descriptor_importance.coalition_utility.npy
```

To append Shapley-gated candidates to a later sweep:

```powershell
$env:MFI_SHAPLEY_FILE="results\local_dev\shapley_descriptor_importance.json"
python run_local_research.py --preset standard --workers 8 --profile-workers
```

The original non-Shapley candidates remain in the competition.

## UDED protocol

If `external/UDED/test_pair.lst` is missing, the runner downloads the official UDED repository automatically.

The current local research protocol keeps the existing split convention:

```text
selection: items 0,2,4,...
held-out:  items 1,3,5,...
```

Model ranking uses **3-fold inner-CV F1 on the selection split**. A frozen threshold is then fitted on the full selection split and applied to the held-out images.

Only the top `--top-heldout` candidates selected without looking at held-out results are evaluated on the held-out set. Do not re-rank the whole search using held-out performance.

## Parallel execution

The benchmark uses a `ThreadPoolExecutor` across model configurations. This is deliberate:

- NumPy/SciPy/OpenCV release the GIL in the expensive kernels;
- threads share the large precomputed multiscale feature tensors;
- Windows process spawning would otherwise duplicate or serialize a large amount of data.

Measure actual scaling on your machine with:

```powershell
python run_local_research.py --preset smoke --profile-workers
```

This writes:

```text
results/local_dev/ch_mfi/parallel_scaling.csv
```

Start with 6-8 workers on a Ryzen 7. If RAM remains comfortable and scaling is still positive, increase experimentally.

## Checkpoint / resume

`selection_ranking.csv` is rewritten atomically as candidates finish. If the run stops, rerunning the same preset resumes from completed configuration names instead of starting from zero.

Outputs are written under:

```text
results/local_dev/ch_mfi/
```

Key files:

- `run_manifest.json`
- `baseline_scharr.json`
- `selection_ranking.csv`
- `selection_per_image.csv`
- `heldout_top.csv`
- `parallel_scaling.csv` (when profiling)
- `best_contact_sheet.png`
- `summary.json`

The contact sheet contains original image, GT, MFI attention, uncertainty, dynamic localizer, final edge and TP/FP/FN visualization.

## Suggested workflow

1. `smoke` until the branch is stable locally.
2. `standard` without Shapley gating.
3. learn descriptor Shapley values on selection only.
4. `standard` again with `MFI_SHAPLEY_FILE` enabled.
5. inspect family-level behavior and transfer to held-out.
6. run `wide` overnight only after the standard grid is healthy.
7. promote a model to `main` only after the validation protocol is frozen.
8. when a model is promoted, also add it to `mfi-edge-webui` for qualitative desktop comparison.

## Scientific status

This branch is intentionally exploratory. In particular:

- the current tolerant boundary matcher is not yet the official Berkeley bipartite matcher;
- context maps are hand-designed proxies, not learned/calibrated posteriors;
- d-CF variants are generic restricted-dissimilarity experiments until matched exactly to a chosen published formulation;
- UDED is small, so conclusions should later be repeated on BSDS500 and additional real datasets;
- held-out results must remain evaluation, not a source of hyperparameter selection.
