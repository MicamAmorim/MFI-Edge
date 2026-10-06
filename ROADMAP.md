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
5. **External transfer / Stage 13** — freeze the UDED-development representatives and test whether the learned structural signature transfers unchanged to other edge datasets.

Guiding question:

> **Can stable multiscale structural evidence tell a precise edge localizer where to trust or distrust its response, and can that controller transfer across datasets without re-fitting?**

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

## Stage 12b / 12c — fuzzy positive and anti-texture evidence

Stage 12b suggested that explicit anti-texture evidence could help. Stage 12c repaired feature-bank leakage by rebuilding positive/negative banks inside each outer fold. Several dual models looked promising on the already-inspected UDED held-out half, but that split is now development confirmation only.

## Stage 12d — repeated leakage-free bipolar CV

Stage 12d used only the 15 UDED selection images, with **5 repeats × 3 folds = 15 outer validations**. UDED held-out was not used.

| candidate | repeated CV F1 | delta vs Scharr |
|---|---:|---:|
| Scharr | 0.75095 | — |
| positive distorted-Choquet | **0.75889** | **+0.00794** |
| separable bi-capacity | 0.75811 | +0.00715 |
| ratio control | 0.75669 | +0.00573 |

The positive-only controller narrowly wins. The separable bi-capacity remains very close and occupies **12 of the global top 20** configurations, versus 8 positive controls, but current repeated-CV evidence does not support claiming that negative evidence adds performance beyond the positive bank.

The positive bank is very stable: `gabor4_s5`, `hessian_s7`, `gabor4_s13`, `hessian_s13`, and `gabor4_scale_persistence` appeared in all 15 splits. The strongest anti-texture feature, `steered_hessian_scale_centroid`, also appeared in all 15 splits.

Scientific conclusion:

> **Positive multiscale edge-signature evidence is reproducibly useful on UDED development. Anti-texture evidence is stable and interpretable, but its incremental value is unresolved. External transfer must decide whether either mechanism generalizes.**

Full note: `docs/paper/STAGE12D_REPEATED_BIPOLAR_RESULTS.md`.

### Validation policy

- **do not use UDED held-out for further architecture selection**;
- Stage-12d candidates are frozen from UDED selection only;
- Stage 13 must apply them unchanged to external datasets;
- official paper claims still require official dataset-specific evaluation protocols.

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
| Stage 12c leakage-free bank CV | 🟢 | leakage fixed; UDED held-out retired |
| Stage 12d repeated bipolar CV | 🟢 | positive wins narrowly; bi-capacity remains close |
| freeze external candidates | 🟢 | exact banks/configs/thresholds frozen on UDED selection |
| **Stage 13a BSDS frozen transfer** | 🟡 **RUN NOW** | no BSDS tuning; first external check |
| BIPED external replication | 🔴 next | second cross-dataset confirmation |
| official BSDS500 evaluation | 🔴 | required for literature-comparable paper claims |
| topology/linking revisit | ⚪ | only after score model is externally competitive |
| dynamic localizer revisit | ⚪ | keep parked until fixed-Scharr line is understood |
| wide sweep | 🔴 blocked | no brute-force expansion before external evidence |

### Run now

```powershell
git fetch
git switch mfi-edge-local-dev
git pull
.\run_stage13_bsds_transfer.bat
```

By default this attempts the complete BSDS500 **test** split at max side 256. Do not pass `--limit` for the real frozen transfer run. The script downloads missing BSDS files automatically.

Send:

```text
results\external\stage13a_bsds_transfer\summary.json
results\external\stage13a_bsds_transfer\external_metrics.csv
results\external\stage13a_bsds_transfer\per_image_metrics.csv
results\external\stage13a_bsds_transfer\preview_positive_control.png
results\external\stage13a_bsds_transfer\preview_separable_bicapacity.png
results\external\stage13a_bsds_transfer\preview_ratio_control.png
```

---

# Track B — current candidate architecture

```text
image
  -> oriented_ms descriptors + cross-scale relations
  -> positive boundary memberships -------> C_plus
  -> texture / anti-boundary memberships -> C_minus

image -> median conditioning -> Scharr -> NMS

positive control:
  C_plus -> context gate -> frozen threshold -> edge map

separable bi-capacity control:
  B(x) = normalize(C_plus - lambda*C_minus)
  -> context gate -> frozen threshold -> edge map
```

Stage 12d froze three unique representatives for transfer:

1. `positive__gp0.55__a2__floor0.1`;
2. `bicap__gp0.55__gm1.75__l0.35__a2__floor0.1`;
3. `ratioctl__gp0.55__gm1__l1__a2__floor0.1`.

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
| positive fuzzy signature | 🟢 stable development signal |
| explicit anti-texture bank | 🟢 stable features, incremental value unresolved |
| separable bipolar / bi-capacity model | 🟢 implemented/tested |
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
| UDED selection 15 | 🟢 | completed development/calibration source |
| UDED held-out 15 | ⚪ exhausted for final testing | development confirmation only |
| BSDS500 consensus transfer proxy | 🟡 **Stage 13a** | external frozen generalization check |
| BIPED | 🔴 next | cross-dataset replication |
| official Berkeley matching | 🔴 | publication-grade evaluation |
| multi-annotator BSDS uncertainty | 🔴 | preserve individual annotations |
| higher-resolution rerun | 🔴 | finalist sensitivity check |

Stage 13a intentionally reports a **consensus-thresholded BSDS + tolerant-dilation proxy**, not official Berkeley bipartite matching. ODS/OIS on BSDS are descriptive only; the primary external transfer metric uses thresholds frozen before BSDS.

---

# Track E — research automation

Planned `automation/research_controller.py`:

- local Python executes long experiments;
- Codex is called only after a result is ready;
- Git is the scientific memory;
- explicit budget / stop file / max-iteration limits;
- no held-out/test feedback inside iterative optimization;
- only allow-listed experiment commands may execute automatically.

Implement after the Stage-13 external-validation runners are stable.

---

# Track F — promotion

No Stage-12/13 model is promoted to `main` yet.

Promotion requires:

1. exact frozen config;
2. documented calibration source;
3. untouched external validation/test;
4. reproducible threshold/evaluation protocol;
5. qualitative inspection;
6. runtime/resolution report;
7. external evidence that the controller improves or robustly matches the fixed localizer.

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
- `STAGE12D_REPEATED_BIPOLAR_RESULTS.md`
- `PAPER_WRITING_PLAN.md`
- `references.bib`

Update this roadmap whenever a result changes the scientific direction.
