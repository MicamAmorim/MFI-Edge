# Paper A — UDED-14 development-only fitted parameters (P1)

**Recorded:** 2026-11-16. **Status:** `FITTED_UNATTESTED`; neither independently certified nor frozen. **Source of values:** workstation PowerShell output of `devfit_20261116T031932_410335Z_recipe_UNATTESTED.json`, as reported by the researcher. The **complete P1 JSON is now versioned** as `P1_DEVELOPMENT_RECIPE_UNATTESTED.json` by commit `2b7be963` (versioned Git blob ID `4be2448b37db6adf79317d1de315b2ee2b155fa4`). The initial attempt to compare SHA256 through PowerShell Get-FileHash failed (the cmdlet was unavailable); **the subsequent Python SHA256 comparison succeeded**. The researcher supplied the command output for the original F: recipe and the versioned Git working-copy recipe: **both SHA256 = `628d1e345b6d1117c3cbfbc6ecaf75d4cac8db6a7796d328e2ea911ce9891a9c`; command printed `IDENTICOS` and returned successfully on 2026-11-16**. This establishes bit-for-bit equality at the time of the reported check. The Git blob ID is not the file SHA256; independent validation of historical training overlap is still outstanding.

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

The reported capacity has normalized endpoints and is monotone under inclusion at displayed precision. **The six Möbius coefficients from the actual versioned P1 recipe** are `(0.2850475022884192, 0.0, 0.3213385800523409, 0.0, 0.0, 0.3936139176592399)`. Reconstructing each subset value by the singleton and pairwise terms agrees with the eight recorded capacities at floating-point precision. This establishes an algebraic consistency check, not independent scientific certification.

## Interpretation and warnings

The exact numerical parameter values above are **development-fitted parameters**, not effect estimates, H1/H2 confirmation, per-image F1 results, p-values or cross-domain generalization evidence. H1/H2 candidate and equal-mean control have separately fitted thresholds under the same membership representation. Threshold differences do not constitute a measured benefit.

For H2, a zero midpoint on the first cue and an exact `scale=0.05` for the first and third cues are consistent with the lower scale floor in the implementation. Under the unchanged `legacy_sigmoid`, zero evidence with zero midpoint yields membership 0.5. This property merits a prespecified development-only numerical sensitivity check, **not post-hoc refitting on confirmatory data**.

## Required independent scientific gates

1. **Source-copy SHA256 check completed**: original F: recipe and Git working-copy recipe matched (`628d1e345b6d1117c3cbfbc6ecaf75d4cac8db6a7796d328e2ea911ce9891a9c`) as reported by the researcher on 2026-11-16. The file includes training image/GT hashes and the six Möbius coefficients, but those metadata fields do **not** constitute independent certification of cohort overlap or training-data history. Keep raw images, GT masks, NPY caches, H5 files and dataset archives outside Git.
2. Certify training/confirmatory scene independence and prior exposure; specifically exclude MultiCue capture-prefix `4113`, an exposed UDED overlap.
3. Verify complete 2-additive H2 Möbius/capacity representation, gamma, all four fixed thresholds, common membership calibration and fixed evaluator semantics.
4. Select independently eligible BIPED/MultiCue groups, freeze sampling unit, annotation task/decoder, size and domain-blocked statistical analysis **before opening held-out GT**.
5. Only after independent review, create and sign `frozen_H1_H2_recipe.json`, `frozen_cohort_manifest.csv`, `freeze_approval.json` and a protocol freeze commit. Do not auto-assert approval fields.

**Current conclusion:** successful development fitting; scientific provenance **NOT ATTESTED**; no confirmatory H1/H2 outcomes or journal-ready final Results section.

## Workstation SHA256 source/copy verification (passed; repeatable)

The earlier blank PowerShell comparison did **not** establish integrity, but the subsequent Python comparison below **did**: the original and Git copy both returned the same SHA256 and `IDENTICOS`. The following read-only command is retained for reproducibility and fails if bytes differ:

```powershell
$src = "F:\MFI-Edge-Data\MultiCue\paper_a_completion\devfit_20261116T031932_410335Z_recipe_UNATTESTED.json"
$dst = "docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json"
.\.venv\Scripts\python.exe -c "import hashlib,sys,pathlib; H=lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(); a,b=map(H,sys.argv[1:]); print('SOURCE_SHA256',a); print('GIT_COPY_SHA256',b); sys.exit(0 if a==b else 2)" "$src" "$dst"
if ($LASTEXITCODE -ne 0) { throw "P1 source-copy SHA256 MISMATCH" }
```

This checksum verifies file identity only. It does not certify training leakage, annotation interpretation or H1/H2 performance.

**Observed verification record (researcher terminal, 2026-11-16):**

```text
Original: 628d1e345b6d1117c3cbfbc6ecaf75d4cac8db6a7796d328e2ea911ce9891a9c
Copia: 628d1e345b6d1117c3cbfbc6ecaf75d4cac8db6a7796d328e2ea911ce9891a9c
IDENTICOS
```

The integrity result does not authorize or imply independent H1/H2 GT evaluation.
