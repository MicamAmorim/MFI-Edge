# MFI-Edge local research branch — legacy first-wave workflow

Branch: `mfi-edge-local-dev`

> **Status: superseded for new experiments.** This document describes the first local CH-MFI research wave (`src/ch_mfi.py`, `run_local_research.py`).  It is retained as development history because those experiments motivated CH-MFI-v2, but new workstation runs should use **[`LOCAL_DEV_V2.md`](LOCAL_DEV_V2.md)** and **[`run_research_campaign_v2.bat`](run_research_campaign_v2.bat)**.

The project-wide status and next milestones are maintained in **[`ROADMAP.md`](ROADMAP.md)**.

## Historical purpose

The first-wave local branch introduced the architectural shift from simply adding MFI confidence to a classical gradient toward a two-branch model:

```text
context / fuzzy evidence branch
           +
spatial localization branch
           |
           v
MFI evidence controls/refines localization
```

It established the following ideas that remain in v2:

- context maps for blur, noise, texture, frequency, coherence and heterogeneity;
- coarse/fine hierarchical MFI;
- context-conditional fuzzy operators;
- distorted-probability capacities;
- an adaptive Scharr/Sobel/DoG localizer bank;
- multiscale uncertainty;
- bilateral MFI-to-localizer control;
- exact global descriptor Shapley experiments;
- resumable selection/held-out workstation benchmarks.

## Why v2 replaced this workflow

CH-MFI-v2 expands the experimental space with:

- regime-specific Shapley;
- scale-specific learned capacity banks;
- SWAFED image-neighbourhood adaptive exponents;
- d-CF, d-CC and d-XC restricted-dissimilarity families;
- Choquet-inspired aggregation;
- partition-conditioned aggregation;
- regularized pair-interaction capacities;
- explicit topology competition among none/hysteresis/geodesic/combined post-processing;
- a dedicated smoke suite and campaign launcher.

## Current commands

Use:

```powershell
python smoke_local_architecture_v2.py
.\run_research_campaign_v2.bat quick 8
```

Then follow `LOCAL_DEV_V2.md` for learned-bank, topology and wide experiments.

## Historical outputs

First-wave outputs, when present, remain under:

```text
results/local_dev/ch_mfi/
```

Current v2 outputs use:

```text
results/local_dev/ch_mfi_v2/
results/local_dev/topology_v2/
```

Do not mix first-wave and v2 rankings when reporting results.
