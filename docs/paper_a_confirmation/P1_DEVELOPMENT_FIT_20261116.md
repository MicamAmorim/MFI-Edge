# Paper A — UDED-14 development-only fitted parameters (P1)

**Recorded:** 2026-11-16. **Status:** `FITTED_UNATTESTED`; neither independently certified nor frozen. **Source of values:** workstation PowerShell output of `devfit_20261116T031932_410335Z_recipe_UNATTESTED.json`, as reported by the researcher. The complete source JSON and its SHA256 have **not yet been transferred to this repository**; transcription below is provisional until the source file is checked against the versioned snapshot.

## Execution evidence and scope

- Checkpointed completion log: `F:\MFI-Edge-Data\MultiCue\paper_a_completion\completion_20261116_001902.stdout.log`.
- The submitted completion status reported development fitting `FITTED_UNATTESTED` with subprocess exit code 0 and recipe at `F:\MFI-Edge-Data\MultiCue\paper_a_completion\devfit_20261116T031932_410335Z_recipe_UNATTESTED.json`.
- The 56 UDED-14 cached descriptor maps passed the earlier read-only SHA256 integrity audit; they were reused rather than recomputed.
- Only the already-explored **14 UDED development images** were authorized for supervised fitting. This is not validation against independent BIPED/MultiCue held-out GT.
- The source script is `scripts/fit_paper_a_development_uded14.py`; its calculations use Stage24 membership and aggregation routines. The exact source commit and all fitting-provenance fields must be checked against the complete P1 JSON rather than inferred from this note.
- Subsequent GT access to the independent confirmatory datasets remains blocked by `protocol.json` status `draft_not_frozen`.

## Fixed-order parameters transcribed from workstation

### H1 — maximum versus equal_mean

Cue order: `halfdisc_distribution_contrast`, `pmi_dependency_deficit`.

| Parameter | First cue | Second cue |
|---|---:|---:|
| Sigmoid midpoint | 0.2599221169948578 | 0.08362714946269989 |
| Sigmoid scale | 0.2126612812280655 | 0.10658749751746655 |

- Candidate family: `maximum`; candidate threshold: **0.8604570209980016**.
- Control family: `equal_mean`; control threshold: **0.6064166694879536**.
- Choquet capacity: **not applicable**.

### H2 — generalized Choquet (gamma 1.5) versus equal_mean

Cue order: `fh_region_boundary`, `halfdisc_distribution_contrast`, `structure_tensor_coherence`.

| Parameter | First cue | Second cue | Third cue |
|---|---:|---:|---:|
| Sigmoid midpoint | 0.0 | 0.2599221169948578 | 0.0008532314823241904 |
| Sigmoid scale | 0.05 | 0.2126612812280655 | 0.05 |

- Candidate family: `choquet_generalized_150`; candidate threshold: **0.4981063321232796**.
- Control family: `equal_mean`; control threshold: **0.5953009873628617**.
- H2 capacity indexed by three-bit subset mask `0..7` in Stage24 input order:

| Subset mask | Cue subset | Capacity |
|---|---|---:|
| 0 | empty set | 0.0 |
| 1 | first | 0.2850475022884192 |
| 2 | second | 0.0 |
| 3 | first + second | 0.2850475022884192 |
| 4 | third | 0.3213385800523409 |
| 5 | first + third | 0.6063860823407601 |
| 6 | second + third | 0.7149524977115809 |
| 7 | all three | 1.0 |

The reported capacity has normalized endpoints and is monotone under inclusion at the displayed precision. **The six exact Möbius coefficients were not included in the terminal extract**, so their consistency with the displayed capacity must be checked from the complete P1 file. This note does not replace the machine-readable recipe or the independent scientific review.

## Interpretation and warnings

The exact numerical parameter values above are **development-fitted parameters**, not effect estimates, H1/H2 confirmation, per-image F1 results, p-values or cross-domain generalization evidence. H1/H2 candidate and equal-mean control have separately fitted thresholds under the same membership representation. Threshold differences do not constitute a measured benefit.

For H2, a zero midpoint on the first cue and an exact `scale=0.05` for the first and third cues are consistent with the lower scale floor in the implementation. Under the unchanged `legacy_sigmoid`, zero evidence with zero midpoint yields membership 0.5. This property merits a prespecified development-only numerical sensitivity check, **not post-hoc refitting on confirmatory data**.

## Required independent scientific gates

1. Transfer the **original complete P1 JSON** from the workstation into a small curated versioned path after reviewing its contents; record its SHA256, provenance, full Möbius coefficients and training image/GT hashes. Do not commit any raw source images, GT masks, scientific NPY caches, H5 files or dataset archives.
2. Certify training/confirmatory scene independence and prior exposure; specifically exclude MultiCue capture-prefix `4113`, an exposed UDED overlap.
3. Verify complete 2-additive H2 Möbius/capacity representation, gamma, all four fixed thresholds, common membership calibration and fixed evaluator semantics.
4. Select independently eligible BIPED/MultiCue groups, freeze sampling unit, annotation task/decoder, size and domain-blocked statistical analysis **before opening held-out GT**.
5. Only after independent review, create and sign `frozen_H1_H2_recipe.json`, `frozen_cohort_manifest.csv`, `freeze_approval.json` and a protocol freeze commit. Do not auto-assert approval fields.

**Current conclusion:** successful development fitting; scientific provenance **NOT ATTESTED**; no confirmatory H1/H2 outcomes or journal-ready final Results section.
