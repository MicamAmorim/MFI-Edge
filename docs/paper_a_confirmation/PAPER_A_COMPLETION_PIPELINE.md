# Paper A — resumable end-to-end completion pipeline

Run once on your Windows development workstation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_finish_paper_a.ps1
```

This program checkpoints the research state and preserves all historical
Stage24 results. It reuses an existing verified 56/56 development-cache
audit **when scientific code is unchanged**, otherwise runs only the
read-only prefreeze audit (never recreates the descriptor arrays). It
inspects the incomplete H1/H2 recipe, performs no GT/F1 lookups before
freeze, and produces the current scientific-gates report on F:.

## Main outputs

- `F:\MFI-Edge-Data\MultiCue\paper_a_completion\LAST_STATUS.json`
- `F:\MFI-Edge-Data\MultiCue\paper_a_completion\NEXT_ACTIONS.md`
- `F:\MFI-Edge-Data\MultiCue\paper_a_completion\freeze_approval.template.json`
- `F:\MFI-Edge-Data\MultiCue\paper_a_publication\PaperA_repro_preconfirmatory_*.zip`

The approval template contains **false**, never true, for every
authorization. A reviewer must independently verify the training lineage,
capacity/thresholds, GT encoding, scene independence, sample design,
inferential method and exact freeze commit before signing a new
`freeze_approval.json`. These fields cannot be decided retroactively using
confirmatory F1, H1/H2 correlations or outcome-dependent exclusions.

## After scientific sign-off

The **same command** can resume once the following independently reviewed
files are present in the completion directory:

- `frozen_H1_H2_recipe.json` — full H1/H2 calibrated parameters and proofs
- `frozen_cohort_manifest.csv` — all independent source images/captures
- `freeze_approval.json` — signed by reviewer, freeze commit and input SHAs
- `certified_outcomes.csv` — one row per capture with X1,Y1,X2,Y2
- `certified_outcomes_provenance.json` — output SHA, evaluator code provenance

The last two files must be produced by a **separately certified evaluator**
after a valid freeze and the first authorized GT access. The pipeline does
not fake them and does not have an automatically certified GT PNG/H5
decoder. It refuses to open outcomes when any earlier gate fails.

When all gates pass, `scripts/analyze_paper_a_confirmed.py` executes the
preregistered signed, domain-blocked Spearman permutation tests
(100,000 draws, seed 20261115), Holm adjustment across H1 and H2 and
stratified bootstrap intervals. Results are reported whether positive or
negative. It writes a review draft with actual numerical results and
a new hash-manifested analysis ZIP. Journal formatting, independent audit
and author approval remain editorial steps.

## Scientific guarantees and remaining implementation

1. No tuning or selecting on confirmatory GT/F1.
2. No operator substitution if signed H1/H2 are not significant.
3. No padding the sample with correlated frames/annotators.
4. Historical exploratory UDED and BSDS uses are not considered clean
   confirmation.
5. Final frozen model fitting, independent cohort audit, and real GT decoder
   still need separate implementation/validation; the orchestrator will
   identify them rather than falsely claiming an article is complete.

To review the current blockers without waiting for SHA, use:

```powershell
.\.venv\Scripts\python.exe scripts\finish_paper_a.py --no-reaudit
```

## Optional supervised fit on known DEVELOPMENT data

After scientific authorization to read only the 14 UDED development GT
masks, run `python scripts/fit_paper_a_development_uded14.py
--authorize-uded-development-gt`. This uses verified cached float maps,
fits the exact operators, and writes an **UNATTESTED** recipe with no
confirmatory-overlap approval. It cannot be frozen without independent
image-source and training-data lineage certification.
