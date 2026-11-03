# Stage24G-L — Complete Scientific Reproducibility Package

The scientific results are stored in **two interoperable tiers**. The code
does not automatically publish third-party images/GTs, derived detector maps,
or an external DOI. A successful experiment followed by a commit is **not**
the same as completion of the external public data deposit.

## Tier A: GitHub code and complete numeric evidence

Directory: results/paper_a_evidence/stage24gl/

- All summary/fold/per-image CSV, model/threshold parameters, final claim audit,
  exact environment lock, math contract checks and SHA256 source provenance.
- Full per-group and per-fold checkpoint JSONs, including inner CV candidate
  trials, serialized model parameters and selected recipe details, packed as
  reproducibility/cv_part_*.zip.
- Original Berkeley per-image evaluation text/CSV/JSON (not just aggregate
  metrics), packed as reproducibility/berkeley_original_part_*.zip.
- Per-file SHA256 and archive SHA256 in
  reproducibility/source_to_archive.csv and reproduction_manifest.json.
- Independent verification: python scripts/verify_stage24gl_repro.py --check-git.
- Individual Git ZIP parts limited to 24 MiB uncompressed; full compressed
  archive capped at 180 MiB to avoid large Git history.

These are safe to stage for commit if the campaign is complete and the
archive verifier passes. The original UDED/BSDS photos and their GTs are
NOT included.

## Tier B: large, reproducible data deposit

Directory (LOCAL / ignored by Git):
results/local_dev/stage24gl_binary_publication/

- stage24gl_float_part_001.zip and subsequent parts, plus
  binary_deposit_manifest.json.
- All cached Stage24 scientific float descriptor NPYs and their metadata
  (for the complete campaign, including BSDS validation where materialized).
- All cached official evaluator prediction PNGs found at
  automation/runtime/official_eval_cache/experiments/
  stage24_paper_a_recertification/.
- Manifest with SHA256 for every source file and ZIP part, byte count,
  source path, and class of artifact.
- No original UDED/BSDS input images, GT files or third-party detector
  author-native float assets unless separately authorized and archived.
- Independent verification:
  python scripts/verify_stage24gl_repro.py --check-binary.

The tier B manifest SHA256 and ZIP hashes are recorded in the Git archive's
reproducibility/external_data_reference.json. The external bundle is
**prepared locally but NOT automatically uploaded or published**.
Review licenses/redistribution rules for derived score maps and representative
figures before publishing.

If predictions or float caches are missing, do not claim full image-level
reproducibility merely because the archive is valid. Read the actual file
counts; missing caches and predictions may require regenerating exports.

## Windows execution and archival

After synchronizing the research branch, run preflight, then the full campaign:

    .\run_stage24_paper_a_recertification.bat --phase preflight
    .\run_stage24_paper_a_recertification.bat --phase all

When the full scientific run finishes successfully, its launcher automatically
calls the archival script with --stage --replace. The new archiver creates both
tiers, verifies their SHA256/CRC, and stages only the compact Git package.

Review the archive and checksums before committing:

    .\.venv\Scripts\python.exe scripts\verify_stage24gl_repro.py --all
    Get-Content .\results\paper_a_evidence\stage24gl\archive_manifest.json -Raw
    git --no-pager diff --cached --stat
    git commit -m "results: Stage24G-L full numeric reproducibility evidence"
    git push origin HEAD

If the binary bundle is too large for available disk, there is an explicit
archiver option --no-binary-bundle. **That creates only Tier A** and marks
Tier B as pending. Do not claim complete public preservation.

## Prepare a GitHub Release draft for Tier B

Using an authenticated GitHub CLI after commit/push:

    .\scripts\publish_stage24gl_data_release.ps1

This is a dry-run inventory/verification and uploads nothing.

After inspecting redistribution rights, you may prepare an unpublished draft:

    .\scripts\publish_stage24gl_data_release.ps1 -PrepareDraft -RightsReviewed

The draft is not publicly released automatically. Review its assets,
then publish using the GitHub interface if rights allow. The resulting
release link should be recorded with the Git compact manifest and
optionally cross-linked to a separate Zenodo dataset record.

Do not invent a DOI. A DOI is issued only after the deposit is genuinely
published. A GitHub repository release archived by Zenodo can provide a
software DOI; the scientific dataset may need its own separately deposited
record with related identifiers.

## Independent reanalysis

A member of the scientific community should be able to:

1. Clone the pinned source commit and install the documented environment.
2. Download Tier A numerical evidence and verify each checkpoint and all
   original Berkeley threshold counts without the images/GTs.
3. Recompute pair rankings, heldout F1, ablations, image-level bootstrap
   and statistical summaries from this numerical evidence.
4. Acquire UDED/BSDS source images and GT under their original licenses,
   download Tier B prediction/descriptor score maps if licensed to share,
   verify SHA256, and reproduce image-level figures and matching.
5. Report limitations clearly: the UDED has 14 unique images and reused
   outer folds; external BSDS val is development, not a protected blind test;
   theoretical equivalence and independent evaluator reference certification
   remain separate scientific gates.

## Important distinction: reproducibility is not confirmation

Publishing every intermediate artifact prevents avoidable data loss and
allows third parties to question choices. It cannot convert a post-hoc
result into a blind confirmatory one, or grant licenses over third-party
data. Do not treat "all ZIP files valid" as a license to claim SOTA.
