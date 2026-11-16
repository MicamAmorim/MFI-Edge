# Paper A — local overnight autonomous controller

Start ONCE in PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_paper_a_overnight.ps1
```

Runs only on the user's computer. Requires a clean confirmation branch
and existing .venv. Automatically calls integrated P0–P0.4 audit, 56
bytewise cache SHA checks and technical tests, then attempts up to two
restricted Codex fixes for errors, reaudits, and optionally performs one
Codex editorial update of the paper. It stages only allowlisted files,
commits and tries to push to the confirmation branch, then creates
the reproducibility ZIP and SHA256 checksum on F:.

Codex must be on PATH and authenticated for autonomous edits.
If missing, audits and packaging still run, but no agent edits occur.
Protected code, protocol, exploratory results, GT/H5, confirmatory F1
and all scientific fits are out of scope. No new result is invented.

Files:
- docs/paper_a_confirmation/PAPER_A_MANUSCRIPT_DRAFT.md
- docs/paper_a_confirmation/NIGHTLY_PROGRESS.md
- F:\MFI-Edge-Data\MultiCue\paper_a_overnight_LAST_STATUS.json
- F:\MFI-Edge-Data\MultiCue\paper_a_overnight_codex\overnight_*.stdout.log
- F:\MFI-Edge-Data\MultiCue\paper_a_publication\PaperA_repro_preconfirmatory_*.zip

The controller requests Windows remain awake during its process;
do not shut the computer down. Overnight completion does not imply
scientific protocol freeze or H1/H2 confirmation.

## CI baseline reproducibility fallback

On pushes to this branch, GitHub Actions runs a lightweight Python
smoke test and builds a **preconfirmatory** ZIP artifact. It does not
connect to local F: caches or run held-out outcomes; the local overnight
controller remains responsible for bytewise checks and Codex editing.
Download the artifact from the latest successful **Paper A prefreeze smoke
checks** GitHub Actions run if the workstation was unavailable.

## Preexisting untracked evidence is protected

The initial checkout may contain untracked Stage24 evaluation folders,
`resultado_analise_condicional.zip`, or other preexisting local artifacts.
These should not be moved, deleted, stashed or ignored. The launcher now
rejects only modified/staged **tracked** files. At the start of the local
controller, it inventories preexisting untracked filenames and `lstat`
metadata (size, timestamp, mode), without reading the file contents.
Original untracked items are excluded from every permitted commit;
unexpected new paths and any changes to the inventory block staging.
Git stages only explicit allowlisted Paper A code and documentation.
