# CH-MFI-v2 local workstation workflow

Branch: `mfi-edge-local-dev`

This is the **current recommended workflow** for the second-wave CH-MFI architecture on a Ryzen 7 / 32 GB Windows workstation.  It separates learning/attribution, model-family screening, frozen held-out evaluation and topology search.

Project-wide status and future milestones: **[`ROADMAP.md`](ROADMAP.md)**.

## 1. Checkout

```powershell
git fetch
git switch mfi-edge-local-dev
git pull
```

## 2. One-command campaign modes

The preferred launcher is:

```powershell
.\run_research_campaign_v2.bat <mode> <workers>
```

Modes:

- `smoke` — synthetic architecture sanity test only;
- `quick` — smoke + baseline v2 standard screen;
- `full` — quick + scale-specific capacities + regime Shapley + learned-bank rerun + topology competition;
- `wide` — full campaign + wide overnight model search.

Examples:

```powershell
.\run_research_campaign_v2.bat smoke 8
.\run_research_campaign_v2.bat quick 8
.\run_research_campaign_v2.bat full 8
.\run_research_campaign_v2.bat wide 8
```

Start with `smoke`, then `quick`.  Do not launch `wide` until the standard grid and worker profile are healthy.

## 3. Manual smoke test

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python smoke_local_architecture_v2.py
```

Every major second-wave family should print `SMOKE_OK`, ending with:

```text
CH_MFI_V2_SMOKE_DONE
```

The smoke grid covers at least:

- standard CH-MFI-v2;
- SWAFED;
- d-CF;
- d-CC;
- d-XC;
- Choquet-inspired aggregation;
- partition-conditioned aggregation;
- regularized pair-interaction capacity.

## 4. First screen without learned regime/scale banks

```powershell
.\run_local_research_v2.bat standard 8
```

The current v2 `standard` grid contains approximately **519 configurations** before optional learned regime/scale variants.

It includes:

- standard CF1F2 contextual/hierarchical models;
- flat vs global/local hierarchical scale fusion;
- fixed vs context-conditional operators;
- power, additive, local-adaptive and distorted-probability capacities;
- SWAFED image-neighbourhood adaptive power measures;
- d-CF, d-CC and d-XC;
- five core restricted dissimilarities;
- Choquet-inspired aggregation;
- partition-conditioned aggregation;
- regularized pair-interaction capacities;
- multiple coarse/fine granularity settings;
- bilateral vs soft context/localizer control.

Outputs:

```text
results/local_dev/ch_mfi_v2/
```

Key files:

```text
selection_ranking.csv
selection_per_image.csv
heldout_top.csv
parallel_scaling.csv
best_contact_sheet.png
summary.json
run_manifest.json
```

The experiment is resumable: completed configuration names are read back from `selection_ranking.csv`.

## 5. Learn scale-specific capacity bank

After the first smoke/standard run is stable:

```powershell
python learn_scale_capacity_bank.py --max-side 256
```

Output:

```text
results/local_dev/scale_capacity_bank.json
```

For each scale `25/13/7/5/3` it stores:

- descriptor-vs-GT ranking AUC;
- additive relevance weights;
- descriptor correlation matrix;
- estimated pair complementarity/redundancy;
- additive capacity;
- distorted-probability capacity;
- regularized pair-interaction capacity.

The bank is learned from the **selection subset only**.  It is exploratory and should later be relearned on a larger training split such as BSDS500 train/val before publication claims.

## 6. Learn global descriptor Shapley

The original exact global Shapley learner remains useful:

```powershell
python learn_local_shapley.py --target final --workers 8
```

With eight descriptors this enumerates all 256 coalitions.

## 7. Learn regime-specific Shapley

The v2 learner estimates descriptor contributions separately for:

```text
clean
texture
blur
noise
```

Start with one regime:

```powershell
python learn_regime_shapley.py --regimes texture --target final --workers 8
```

Then all regimes:

```powershell
python learn_regime_shapley.py --regimes all --target final --workers 8
```

Outputs:

```text
results/local_dev/regime_shapley.json
results/local_dev/regime_shapley.<regime>.coalitions.npy
```

The `.npy` files are checkpoints, so interrupted attribution runs can resume.

The regime utility is an **attribution/gating proxy**, not an official ODS/F1 benchmark metric.

## 8. Rerun standard with learned regime + scale adaptation

The batch launcher automatically discovers the default learned files if present:

```powershell
.\run_local_research_v2.bat standard 8
```

Equivalent explicit execution:

```powershell
$env:MFI_REGIME_SHAPLEY="results\local_dev\regime_shapley.json"
$env:MFI_SCALE_CAPACITY_BANK="results\local_dev\scale_capacity_bank.json"
python run_local_research_v2.py `
  --preset standard `
  --workers 8 `
  --profile-workers `
  --out results\local_dev\ch_mfi_v2
```

Learned candidates are appended to the competition; they do **not** replace the non-learned controls.

## 9. Topology competition

Only after continuous-score models have been ranked on the selection subset:

```powershell
$env:MFI_REGIME_SHAPLEY="results\local_dev\regime_shapley.json"
$env:MFI_SCALE_CAPACITY_BANK="results\local_dev\scale_capacity_bank.json"
python benchmark_topology_v2.py `
  --ranking results\local_dev\ch_mfi_v2\selection_ranking.csv `
  --preset standard `
  --top 8 `
  --bootstrap 5000
```

The topology stage competes:

- no topology repair;
- hysteresis;
- MFI-guided geodesic linking;
- hysteresis + geodesic linking.

Threshold and topology parameters are fitted on selection only and then frozen on held-out.

Outputs:

```text
results/local_dev/topology_v2/topology_competition.csv
results/local_dev/topology_v2/summary.json
```

In addition to F1, the stage records continuity-oriented diagnostics such as edge components overlapping GT, largest-component GT coverage and endpoint count.

## 10. Wide overnight run

Only after `parallel_scaling.csv` has shown a sensible worker count and the standard campaign is stable:

```powershell
.\run_local_research_v2.bat wide 8
```

Without optional learned banks, the current wide family is approximately **4,839 configurations**.  Learned regime/scale variants add only a small number of explicit candidates.

Do not assume `8` workers is optimal.  Compare 4/6/8/10/12 workers on the target machine; NumPy/OpenCV kernels, memory bandwidth and thermal limits may make fewer workers faster.

## 11. RAM / CPU behavior

The runner uses threads so the large precomputed feature tensors are shared rather than serialized into multiple Windows processes.  BLAS/OpenMP inner thread counts are pinned to one to avoid nested oversubscription.

With 32 GB RAM we can later raise image resolution beyond the current 256-px development default, but resolution must be treated as an explicit experiment rather than silently changed during a ranking campaign.

## 12. Scientific interpretation rules

1. Selection/inner-CV chooses models.
2. Held-out estimates generalization; it never reorders the full search.
3. UDED is only 30 images and is insufficient for final capacity-learning claims.
4. Final claims should be repeated on BSDS500 train/val/test with the official boundary matcher.
5. Handcrafted context maps are router features, not calibrated posterior probabilities.
6. `regularized_pair_capacity` is a low-complexity interaction surrogate, not a complete implementation of every formal k-interactive learning method.
7. Choquet-inspired and partition-conditioned variants are research implementations of architectural ideas; theorem-level equivalence to a particular paper must be verified before manuscript wording calls them faithful reproductions.
8. The current 256-px resize is a development compromise and requires sensitivity analysis before publication.

## 13. Research record

See:

```text
ROADMAP.md
docs/paper/ARCHITECTURE_MAP.md
docs/paper/BIBLIOGRAPHY_MATRIX.md
docs/paper/LEGACY_REVIEW_CORPUS.md
docs/paper/EXPERIMENT_HISTORY.md
docs/paper/PAPER_WRITING_PLAN.md
docs/paper/references.bib
```

Treat these files as part of the research record, not merely documentation.  When a new paper or experiment changes the architecture, update the roadmap and the corresponding paper notebook entry in the same development cycle.
