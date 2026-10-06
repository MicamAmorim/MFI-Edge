# MFI-Edge research roadmap

Last updated: **2026-10-06**

Legend: 🟢 completed/implemented · 🟡 active/partial · 🔴 planned · ⚪ parked.

## Branch responsibilities

| Branch | Role |
|---|---|
| `main` | stable/promoted models only |
| `mfi-edge-local-dev` | active workstation research |
| `mfi-edge-webui` | qualitative inference/comparison UI |
| `experiment/uded-railway` | server experiment/infrastructure history |

---

# Scientific trajectory

1. **MFI-Classic** — multiscale fuzzy evidence + classical localizer + NMS/linking.
2. **MFI-Fuzzy++ / Stages 5–7** — broad fuzzy-measure/operator competition and UDED generalization.
3. **CH-MFI-v2 / Stage 10** — context/hierarchy/uncertainty controlling localization; ultimately below Scharr on UDED.
4. **Edge Signature / Stages 11–12** — use GT to discover stable properties that distinguish true boundaries from high-gradient texture, then translate those properties into an interpretable analytical/fuzzy controller while keeping precise localization separate.

Guiding question:

> **Can stable multiscale structural evidence tell a precise edge localizer where to trust or distrust its response, and can positive and anti-texture evidence be represented by a generalizable fuzzy model?**

---

# Latest evidence

## CH-MFI-v2

Best 519-config winner remained below Scharr on UDED held-out:

- CH-MFI-v2 F1: **0.71325**
- Scharr F1: **0.76204**
- delta: **-0.04879**

Later scale-bank/regime-Shapley variants did not replace it.

## Stage 11 / 11b — edge-signature discovery

`oriented_ms` fixed a real implementation artifact:

- historical `oriented`: **22/80** exact duplicate scale/descriptor pairs;
- `oriented_ms`: **0/80**.

Held-out diagnostic discrimination:

| score | AUC | AP |
|---|---:|---:|
| analytical signature | 0.6606 | 0.4257 |
| logistic diagnostic | **0.6992** | **0.5029** |

Main interpretation: the descriptor space contains real information, but exact localization and context/texture rejection are different tasks.

## Stage 12a — fixed Scharr + analytical gate

The large CH-MFI degradation disappeared when Scharr+NMS remained the fixed localizer.

- Scharr held-out F1: **0.76204**
- Stage-12a: **0.76225**
- delta: +0.00020, CI crosses zero.

Conclusion: context should **control** localization, not compete with it.

## Stage 12b — fuzzy positive/dual evidence

A positive distorted-capacity Choquet was the formal selection winner, but several dual positive+anti-texture candidates showed encouraging development-confirmation gains.

This motivated a leakage audit.

## Stage 12c — leakage-free evidence-bank CV

Feature banks and thresholds were rebuilt inside each outer fold.

Selection-only leakage-free CV:

| candidate | CV F1 | delta vs Scharr CV |
|---|---:|---:|
| Scharr | 0.73351 | — |
| positive fuzzy winner | **0.76376** | +0.03024 |
| best dual | 0.76347 | +0.02996 |

The positive winner did not improve the repeatedly inspected UDED held-out split (0.76133 vs 0.76204), but multiple top-ranked dual candidates did. The best inspected dual reached 0.77023, +0.00819 over Scharr with a positive bootstrap CI. **This held-out result is architectural evidence only and must not be used to choose exact hyperparameters.**

Feature-bank stability is encouraging:

- 8 positive features occurred in all 3 folds;
- 3 anti-texture features occurred in all 3 folds;
- positive evidence is dominated by scale-specific Gabor/Hessian responses;
- anti-texture evidence is dominated by scale-centroid / peak-fineness properties of curvature-like responses.

Full note: `docs/paper/STAGE12C_LEAKFREE_RESULTS.md`.

### Validation policy change

The UDED held-out half has now been inspected too many times to serve as a publication test. From Stage 12d onward:

- **do not use UDED held-out for architecture selection**;
- develop/freeze using UDED selection-only repeated leakage-free CV;
- next validation must be external (BSDS/BIPED);
- later publication claims require official untouched test protocols.

---

# Track A — active workstation campaign

| Milestone | Status | Latest decision |
|---|:---:|---|
| CH-MFI-v2 standard screen | 🟢 | negative vs Scharr |
| learned scale-bank / regime-Shapley | 🟢 | no winner replacement |
| Stage 11 signature discovery | 🟢 | reproducible structural signal |
| `oriented_ms` | 🟢 | scale collapse fixed |
| cross-scale relational descriptors | 🟢 | balance/delta/persistence/entropy/centroid/peak |
| Stage 12a fixed-Scharr gate | 🟢 | near-null vs Scharr |
| Stage 12b fuzzy signature | 🟢 | dual family became promising |
| Stage 12c leakage-free bank CV | 🟢 | dual pattern survives leakage correction |
| **Stage 12d repeated bipolar CV** | 🟡 **RUN NOW** | formal separable bi-capacity + repeated CV; no UDED held-out |
| freeze external candidates | 🔴 next | selection-only model specs + thresholds |
| BSDS/BIPED external validation | 🔴 next | first truly external generalization check |
| official BSDS500 evaluation | 🔴 | required for paper claims |
| topology/linking revisit | ⚪ | only after score model is externally competitive |
| dynamic localizer revisit | ⚪ | keep parked until fixed-Scharr line is understood |
| wide sweep | 🔴 blocked | no brute-force expansion before external evidence |

### Run now

```powershell
git fetch
git switch mfi-edge-local-dev
git pull
.\run_stage12d_bipolar_cv.bat
```

Send:

```text
results\local_dev\stage12d_bipolar_cv\summary.json
results\local_dev\stage12d_bipolar_cv\repeated_cv_ranking.csv
results\local_dev\stage12d_bipolar_cv\family_summary.csv
results\local_dev\stage12d_bipolar_cv\bank_stability.csv
results\local_dev\stage12d_bipolar_cv\frozen_candidates.json
results\local_dev\stage12d_bipolar_cv\selection_winner_preview.png
```

---

# Track B — Stage 12 target architecture

Current preferred architecture:

```text
image
  -> oriented_ms descriptors + cross-scale relations
  -> positive boundary memberships -------> C_plus
  -> texture / anti-boundary memberships -> C_minus
  -> bipolar / bi-capacity context

image -> median conditioning -> Scharr -> NMS
     -> context gate
     -> frozen threshold
     -> edge map
```

Stage 12d formalizes a separable bi-capacity:

```text
v(A,B) = mu_plus(A) - lambda * mu_minus(B)

B(x) = C_mu_plus(p(x)) - lambda * C_mu_minus(n(x))
```

with independent distorted-capacity exponents for positive and negative evidence. Positive-only and Stage-12 ratio models remain controls.

The logistic model remains an upper-bound diagnostic only, not the proposed detector.

---

# Track C — model-family coverage

| Research idea | Status |
|---|:---:|
| context analyzer | 🟢 |
| hierarchical coarse/fine MFI | 🟢 tested |
| conditional fuzzy operators | 🟢 tested |
| distorted-probability capacities | 🟢 |
| scale-specific capacities | 🟢 tested |
| global/regime Shapley | 🟡 utility redesign needed |
| SWAFED | 🟢 tested |
| d-CF / d-CC / d-XC / d-Choquet | 🟢 tested |
| Choquet-inspired aggregation | 🟢 experimental |
| partition-conditioned aggregation | 🟢 experimental |
| `oriented_ms` descriptors | 🟢 |
| cross-scale relational signature | 🟢 |
| positive fuzzy signature | 🟢 |
| explicit anti-texture bank | 🟢 |
| separable bipolar / bi-capacity model | 🟡 Stage 12d |
| general non-separable bi-capacity | 🔴 conditional future |
| formal k-interactive learning | 🔴 |
| Fourier/multiband branch | 🔴 |
| dynamic localizer | ⚪ parked |
| uncertainty controller | ⚪ parked/redesign |
| learned router/dynamic convolution | 🔴 v3 |
| annotator uncertainty / ranking loss | 🔴 |
| TEED/PiDiNet fuzzy ensemble | 🔴 hybrid generation |

---

# Track D — datasets and validation

| Dataset/protocol | Status | Role |
|---|:---:|---|
| synthetic v2 | 🟢 | mechanism diagnosis |
| UDED selection 15 | 🟢 | current development/calibration |
| UDED held-out 15 | ⚪ exhausted for final testing | development confirmation only |
| BSDS500 | 🔴 next | external validation + later official test |
| BIPED | 🔴 next | cross-dataset replication |
| official Berkeley matching | 🔴 | publication-grade evaluation |
| multi-annotator uncertainty | 🔴 | preserve individual BSDS annotations |
| higher-resolution rerun | 🔴 | finalist sensitivity check |

---

# Track E — research automation

Planned `automation/research_controller.py`:

- local Python executes long experiments;
- Codex is called only after a result is ready;
- Git is the scientific memory;
- explicit budget / stop file / max-iteration limits;
- no held-out/test feedback inside iterative optimization;
- only allow-listed experiment commands may execute automatically.

This should be implemented after Stage 12d/external-validation scripts are stable.

---

# Track F — promotion

No Stage-12 model is promoted to `main` yet.

Promotion requires:

1. exact frozen config;
2. documented calibration source;
3. untouched external validation/test;
4. reproducible threshold/evaluation protocol;
5. qualitative inspection;
6. runtime/resolution report.

```text
mfi-edge-local-dev -> validated candidate -> main -> mfi-edge-webui
```

---

# Paper/research record

Maintain together:

- `ARCHITECTURE_MAP.md`
- `BIBLIOGRAPHY_MATRIX.md`
- `LEGACY_REVIEW_CORPUS.md`
- `EXPERIMENT_HISTORY.md`
- `STAGE11_EDGE_SIGNATURE.md`
- `STAGE11_EDGE_SIGNATURE_RESULTS.md`
- `STAGE11B_SCALE_SENSITIVE_RESULTS.md`
- `STAGE12A_SIGNATURE_GATE_RESULTS.md`
- `STAGE12B_FUZZY_SIGNATURE_RESULTS.md`
- `STAGE12C_LEAKFREE_RESULTS.md`
- `PAPER_WRITING_PLAN.md`
- `references.bib`

Update this roadmap whenever a result changes the scientific direction.
