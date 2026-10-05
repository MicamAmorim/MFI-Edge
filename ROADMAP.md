# MFI-Edge project roadmap

Last updated: **2026-10-05**

This is the project-level roadmap.  `main` remains the stable/reproducible line; active experimental implementation currently lives in `mfi-edge-local-dev`, and qualitative deployment/testing lives in `mfi-edge-webui`.

Legend: 🟢 implemented/completed · 🟡 active/under validation · 🔴 planned.

## Branch map

| Branch | Role |
|---|---|
| `main` | stable/reproducible promoted line |
| `mfi-edge-local-dev` | active CH-MFI-v2 workstation research |
| `mfi-edge-webui` | Next.js/FastAPI inference and model-comparison UI |
| `experiment/uded-railway` | server-side UDED experiment lineage |

## Current direction

The project evolved from MFI-Classic into a context-aware model family:

```text
MFI-Classic
   -> broad fuzzy/operator competition
   -> UDED generalization analysis
   -> CH-MFI-v2
   -> future CH-MFI-Hybrid
```

The active scientific goal is to test whether fuzzy evidence should decide **what to aggregate, how to aggregate, which scale/localizer to trust and how to repair topology**, rather than merely being added to a classical gradient score.

## Immediate CH-MFI-v2 campaign

| Milestone | Status |
|---|:---:|
| v2 code + smoke suite | 🟢 |
| standard search (~519 configs before learned variants) | 🟡 |
| scale-specific capacity learning | 🟢 code / 🟡 results |
| regime-specific Shapley | 🟢 code / 🟡 results |
| learned-bank standard rerun | 🟡 |
| topology competition | 🟢 code / 🟡 results |
| wide search (~4.8k configs) | 🔴 run pending |
| resolution sensitivity | 🔴 |
| official BSDS500 protocol | 🔴 |

Detailed workstation workflow: `LOCAL_DEV_V2.md` on the `mfi-edge-local-dev` branch.

## Research coverage

| Idea | Status |
|---|:---:|
| context analyzer | 🟢 |
| hierarchical multiscale MFI | 🟢 |
| conditional fuzzy operators | 🟢 |
| distorted-probability capacities | 🟢 |
| scale-specific capacities | 🟢 code / 🟡 results |
| global + regime-specific Shapley | 🟢 code / 🟡 results |
| regularized pair interaction | 🟢 |
| SWAFED | 🟢 |
| d-CF / d-CC / d-XC | 🟢 |
| Choquet-inspired aggregation | 🟢 experimental |
| partition-conditioned aggregation | 🟢 experimental |
| dynamic classical localizer | 🟢 |
| MFI/uncertainty bilateral control | 🟢 |
| topology/hysteresis/geodesic repair | 🟢 |
| supervised granularity | 🔴 |
| formal/general k-interactive learning | 🔴 |
| learned router | 🔴 |
| learned dynamic convolution | 🔴 |
| annotator uncertainty | 🔴 |
| ranking loss | 🔴 |
| explicit Fourier branch | 🔴 |
| fuzzy TEED/PiDiNet detector ensemble | 🔴 |

## Validation roadmap

1. Keep synthetic tests for mechanism/failure diagnosis.
2. Use UDED for development/generalization checks without tuning on held-out.
3. Freeze candidate families using training/validation only.
4. Move final claims to BSDS500 train/val/test with official Berkeley boundary evaluation.
5. Add multi-annotator uncertainty instead of immediately collapsing all GTs to binary.
6. Run frozen cross-dataset generalization.
7. Measure resolution and runtime sensitivity.

## Promotion rule

A model is promoted to `main` only after its code/config, validation rule, frozen threshold, held-out result and reproducible outputs are preserved.  After promotion, add the same model to `mfi-edge-webui` for qualitative inspection.

## Future CH-MFI-v3 / Hybrid

Only after v2 ablations identify which interpretable components matter:

- learned router;
- dynamic learned kernels;
- explicit frequency branch;
- annotation-aware uncertainty;
- ranking-based supervision;
- fuzzy ensemble with compact learned detectors (e.g. TEED/PiDiNet);
- optional differentiable fuzzy-capacity layers.

## Documentation discipline

The detailed scientific notebook is maintained on `mfi-edge-local-dev` under `docs/paper/` and contains architecture diagrams, literature matrices, experiment history, manuscript planning and BibTeX.

Update this roadmap whenever a new model family, benchmark, dataset, promotion or literature result changes the project direction.
