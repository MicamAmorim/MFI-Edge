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

## Stage 14b â€” spatial polarity mechanism ablation

On UDED selection only (5 repeats × 3 folds), the spatial negative-evidence ratio
scored CV F1 0.75669, below positive-only (0.75889) and marginally below the
image-mean-negative control (0.75922). Its mean fold delta against the image-mean
control was −0.00213; the preregistered criterion for spatial anti-texture support
was not met. This does not establish that negative evidence is universally
useless, but it removes spatial negative localization as a supported mechanism
for the current candidate. The next Stage-14 step prunes the positive feature
bank before any conditional combination is considered.

The positive-only controller narrowly wins. The separable bi-capacity remains very close and occupies **12 of the global top 20** configurations, versus 8 positive controls, but current repeated-CV evidence does not support claiming that negative evidence adds performance beyond the positive bank.

The positive bank is very stable: `gabor4_s5`, `hessian_s7`, `gabor4_s13`, `hessian_s13`, and `gabor4_scale_persistence` appeared in all 15 splits. The strongest anti-texture feature, `steered_hessian_scale_centroid`, also appeared in all 15 splits.

### Stage 14a/14c research checkpoint

The Stage-14 checkpoint compared three directions: RDF aggregation under
controlled corruption (retained as a later robustness question because prior
UDED inner-CV did not beat the standard family), positive-bank pruning
(selected now based on Stage-12d feature stability and Stage-14b results), and
conditional expert routing (deferred until development ablations show
complementary regimes). The registered Stage-14c test compares the full and
five-feature stable positive banks under identical repeated leakage-free CV on
UDED selection. External test results and UDED held-out are excluded.

Stage 14d tested the compact bank without `gabor4_scale_persistence`. The
four-feature variant scored CV F1 0.75473 versus 0.75889 for the five-feature
bank, with mean paired fold delta -0.00322 (3 wins, 12 losses). Retain
persistence and the five-feature compact bank under the predeclared pruning
rule. Fold events are descriptive only.

Stage 14f is registered as a synthetic-validation-only robustness
falsification: standard positive distorted-Choquet versus d-CC/FBPC/absolute
RDF, with identical frozen compact features, Scharr+NMS, gate, and clean-fit
threshold procedure. It reports absolute F1 and clean-referenced degradation
by Gaussian-noise, blur, texture, and compound family at three predeclared
severities. The comparison changes only the aggregation layer; external sets
and UDED held-out remain unavailable for design or feedback.

Stage 14f completed and did not support d-CC promotion. Its absolute mean
corrupted-F1 advantage was -0.00191; clean mean-image F1 changed by -0.00280;
there were zero corruption families with positive absolute advantage. The
descriptive clean-referenced degradation advantage was +0.00088 (positive in
three families), below the +0.01 threshold in the history. The runner summary
instead labels absolute corrupted F1 with a +0.005 threshold as primary. This
preregistration/reporting mismatch is recorded in `docs/paper/EXPERIMENT_HISTORY.md`;
both criteria failed, so d-CC is not retained. RDF robustness remains an
unsupported hypothesis on this protocol. No external or UDED held-out result
informed the interpretation.

Stage 14g compared three mechanistically distinct follow-ups. Further RDF
operator tuning is deferred; conditional experts remain blocked pending
development-only complementary errors; the d-CC paper's gravitational
preprocessing result motivates one isolated test of that conditioning step.
Stage 14h is registered on synthetic validation only: replace the median
prefilter with the fixed grayscale gravitational smoother before both the
feature and Scharr branches, with the compact positive controller frozen. The
source result is a hypothesis for this different multiscale system, not
evidence of transfer. The experiment must pass its preregistered criteria and
then receive a separate development confirmation before any retention.

Stage 14h completed without promotion. Gravitational smoothing produced mean
corrupted-F1 advantage `+0.00534`, but clean F1 fell by `-0.27231` and only
the texture family improved (`1/4` families), so two mandatory criteria failed.
Median conditioning remains incumbent. The texture-only benefit is a useful
complementarity observation but does not yet define a valid observable router;
known synthetic corruption labels cannot be used at inference. Further
gravitational/RDF tuning is deferred, and the repeatable autonomous literature
checkpoint is next to select one mechanistically distinct development test.

The literature checkpoint selected Stage 14i as that distinct test. Current
crisp-edge work makes contour continuity an explicit concern, and this
repository already has independent Stage-4 synthetic evidence for fixed
MFI-guided geodesic linking. Stage 14i transfers exactly that linker
(`max_gap=8`, `max_mean_cost=0.60`) to UDED-selection repeated leakage-free CV,
with no parameter sweep and no score-model change. Promotion requires
predeclared F1/precision noninferiority and natural-image connectivity gains.

Stage 14i completed without promotion. Fixed geodesic linking changed
aggregate F1 by `-0.01519` and mean fold F1 by `-0.01134` with no fold wins.
Its mean paired largest-component GT-coverage gain was only `+0.00156`, far
below the predeclared `+0.03`, even though precision remained within its
noninferiority margin and coverage improved in 12/15 fold means. The no-link
compact positive controller remains incumbent. Linker micro-tuning is blocked;
the autonomous literature/mechanism escalation was used to choose a distinct
representation test.

That checkpoint selected Stage 14j: append one fixed-default Kovesi PC2 maximum
phase-congruency moment to the retained positive context bank. The mechanism is
cross-scale phase alignment normalized by local response energy, rather than a
new smoother, fuzzy increment, or topology rule. Stage 14j keeps median
conditioning, distorted-Choquet gamma 0.55, the gate, and Scharr+NMS fixed. It
uses UDED-selection 5x3 repeated leakage-free CV, fits phase membership and
weight only within training folds, and permits no phase-parameter sweep. A
conditional phase/gradient localizer is deferred until this single-feature
test establishes complementarity.

Stage 14j completed without promotion. Compact-plus-phase changed aggregate F1
by `-0.000361` and mean fold F1 by `-0.000251`, with 6/15 fold wins. The phase
feature was training-eligible in every fold and precision remained within its
allowed margin, but the three F1 criteria failed. The compact five-feature
controller remains incumbent. Phase-parameter tuning and the conditional
phase/gradient router are not justified by this result; the repeatable
autonomous literature escalation is next and must select a mechanistically
distinct development-only test.

The live checkpoint selected Stage 14k as a direct localizer-information test.
The incumbent converts RGB to grayscale before Scharr, so it cannot detect a
chromatic discontinuity with little luminance contrast. Stage 14k changes only
the localizer to a fixed CIELAB Di Zenzo tensor built from channel-wise Scharr
derivatives; the compact fuzzy context, gate, conditioning footprint, repeated
CV splits, and fold-fitted threshold policy remain fixed. The candidate is a
replacement, not a tuned grayscale/color fusion or router. Promotion requires
the preregistered aggregate F1 and precision margins, positive mean fold delta,
and at least 9/15 fold wins on UDED selection only.

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
| BIPEDv2 external replication | 🟡 preflight registered | test split frozen; author-provided download requires human license acceptance |
| official BSDS500 evaluation | 🔴 | requires official Berkeley MATLAB/CSA++ benchmark tooling; Stage 13a remains a proxy |
| topology/linking revisit | 🟢 Stage 14i completed | fixed linker not promoted; F1 and coverage-effect criteria failed |
| post-topology mechanism search | 🟢 completed | selected phase congruency as a distinct representation mechanism |
| Stage 14j phase context | 🟢 completed | eligible in 15/15 folds but no incremental F1; not promoted |
| post-phase mechanism search | 🟢 completed | selected fixed CIELAB vector-gradient localization |
| Stage 14k color-tensor localizer | 🟡 registered | UDED-selection repeated CV; one fixed analytical localizer replacement |
| dynamic localizer revisit | ⚪ | learned/routed localizers remain parked; Stage 14k is fixed and non-routed |
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

Stage 13c targets author-designated BIPEDv2: 250 outdoor RGB/edge-map pairs at 1280×720, with 200 train and 50 test. Train is not used for fitting or calibration; test is a frozen replication. The author distribution carries terms that must be accepted by a human, so the registered read-only preflight validates the locally supplied canonical layout before any inference. Preserve native resolution and frozen Stage-12d settings. The Berkeley project recommends submitting soft, thinned score maps to its official benchmark code; that code uses multi-annotator matching through CSA++ and requires MATLAB, so it should be run as a separate publication-grade evaluation when the compatible toolchain is available.

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
