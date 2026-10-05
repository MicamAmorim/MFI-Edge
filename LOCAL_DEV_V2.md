# CH-MFI-v2 local workstation workflow

Branch: `mfi-edge-local-dev`

This is the recommended workflow for the second-wave architecture on a Ryzen 7 / 32 GB Windows workstation.  It intentionally separates **learning/attribution**, **model-family screening**, **frozen held-out evaluation**, and **topology search**.

## 1. Checkout

```powershell
git fetch
git switch mfi-edge-local-dev
git pull
```

## 2. Sanity check only

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python smoke_local_architecture_v2.py
```

Every major second-wave branch should print `SMOKE_OK`, ending with:

```text
CH_MFI_V2_SMOKE_DONE
```

Do not start a long sweep if the smoke test fails.

## 3. First screen without learned regime/scale banks

```powershell
.\run_local_research_v2.bat standard 8
```

The current v2 `standard` grid is approximately **519 configurations** before optional learned regime/scale variants. It includes:

- standard CF1F2 contextual/hierarchical models;
- SWAFED image-neighbourhood adaptive power measures;
- d-CF, d-CC and d-XC;
- five core restricted dissimilarities;
- Choquet-inspired aggregation;
- partition-conditioned aggregation;
- compact distorted-probability capacities;
- regularized pair-interaction capacities;
- flat vs hierarchical scales;
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

## 4. Learn scale-specific capacity bank

After the first smoke/standard run is stable:

```powershell
python learn_scale_capacity_bank.py --max-side 256
```

Output:

```text
results/local_dev/scale_capacity_bank.json
```

For each scale 25/13/7/5/3 it stores:

- descriptor-vs-GT ranking AUC;
- additive weights;
- correlation matrix;
- estimated pair complementarity/redundancy;
- additive capacity;
- distorted-probability capacity;
- regularized pair-interaction capacity.

This is learned from the **selection half only**.

## 5. Learn global descriptor Shapley

The original exact global Shapley learner remains useful:

```powershell
python learn_local_shapley.py --target final --workers 8
```

With eight descriptors this enumerates all 256 coalitions.

## 6. Learn regime-specific Shapley

This is substantially heavier because it repeats coalition evaluation for clean/texture/blur/noise regimes.

Start with one regime:

```powershell
python learn_regime_shapley.py --regimes texture --target final --workers 8
```

Then all regimes:

```powershell
python learn_regime_shapley.py --regimes all --target final --workers 8
```

Output:

```text
results/local_dev/regime_shapley.json
results/local_dev/regime_shapley.<regime>.coalitions.npy
```

The `.npy` files are checkpoints. Interrupted attribution runs can resume.

The utility used here is explicitly an **attribution/gating proxy** and is not reported as official ODS/F1.

## 7. Rerun standard with learned regime + scale adaptation

The batch launcher automatically discovers the two files if they are in their default locations:

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

With both learned banks available, the standard grid grows by a small number of explicit learned variants rather than replacing the non-learned controls.

## 8. Topology competition

Only after continuous-score models have been ranked on the selection split:

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

Threshold and topology parameters are fitted on selection only, then frozen on held-out.

Outputs:

```text
results/local_dev/topology_v2/topology_competition.csv
results/local_dev/topology_v2/summary.json
```

In addition to F1, it records:

- edge components overlapping GT;
- largest-component GT coverage;
- endpoint count.

## 9. Wide overnight run

Only after `parallel_scaling.csv` has shown a sensible worker count and standard is stable:

```powershell
.\run_local_research_v2.bat wide 8
```

Without learned optional banks, the current wide family is roughly **4.8k configurations**.  With optional learned variants it is slightly larger.

Do not assume `8` is optimal. On the target PC compare 4/6/8/10/12 workers using the profile output; OpenCV/NumPy kernels, memory bandwidth and thermal limits may make fewer threads faster.

## 10. RAM / CPU expectations

The runner uses threads so large precomputed feature tensors are shared rather than serialized to separate Windows processes. BLAS/OpenMP inner thread counts are pinned to one to avoid nested oversubscription.

With 32 GB RAM we can later increase image size beyond the current development default of 256 px, but do that as a **separate experiment** rather than silently changing resolution mid-ranking.

## 11. Scientific interpretation rules

1. Selection / inner-CV chooses models.
2. Held-out estimates generalization; it never reorders the full search.
3. UDED is only 30 images and is not sufficient for final capacity learning.
4. Final claims should be rerun on BSDS500 train/val/test with the official boundary matcher.
5. The current context maps are handcrafted proxies, not learned/calibrated probabilities.
6. `regularized_pair_capacity` is a low-complexity interaction surrogate, not yet an exact implementation of every formal k-interactive learning method in the literature.
7. Choquet-inspired and partition-conditioned variants are research implementations of the architectural idea; theorem-level equivalence to a particular paper must be verified before manuscript wording calls them exact reproductions.

## 12. Paper planning files

See:

```text
docs/paper/ARCHITECTURE_MAP.md
docs/paper/BIBLIOGRAPHY_MATRIX.md
docs/paper/EXPERIMENT_HISTORY.md
docs/paper/PAPER_WRITING_PLAN.md
docs/paper/references.bib
```

Treat these files as part of the research record, not just documentation.
