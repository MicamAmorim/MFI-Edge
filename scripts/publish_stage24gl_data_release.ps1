<#
.SYNOPSIS
  Creates a DRAFT GitHub Release with verified Stage24G-L derived float data.

.EXAMPLE
  .\scripts\publish_stage24gl_data_release.ps1
  .\scripts\publish_stage24gl_data_release.ps1 -PrepareDraft -RightsReviewed
#>
param(
    [string]$Tag = "stage24gl-scientific-data-v1",
    [switch]$PrepareDraft,
    [switch]$RightsReviewed
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
$Bundle = Join-Path $Root "results\local_dev\stage24gl_binary_publication"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) { throw "No project .venv Python found" }
if (-not (Test-Path $Bundle)) { throw "Full binary package missing; run completed campaign/archive first" }
& $Python "scripts\verify_stage24gl_repro.py" --all
if ($LASTEXITCODE -ne 0) { throw "Reproducibility ZIP SHA256 verification failed" }

$Files = @(Get-ChildItem $Bundle -Filter "stage24gl_float_part_*.zip" |
           Sort-Object Name | ForEach-Object FullName)
$Files += (Join-Path $Bundle "binary_deposit_manifest.json")
if ($Files.Count -lt 2) { throw "No scientific ZIP assets to release" }

if (-not $PrepareDraft) {
    Write-Host "Verification OK. Assets prepared for review:" -ForegroundColor Green
    $Files | ForEach-Object { Write-Host "  $_" }
    Write-Host "Nothing uploaded. Inspect licenses, then rerun with -PrepareDraft -RightsReviewed."
    exit 0
}
if (-not $RightsReviewed) {
    throw "Set -RightsReviewed only AFTER checking derivative redistribution rights."
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) missing. Authenticate it or upload ZIPs manually to a Release."
}
& gh auth status
if ($LASTEXITCODE -ne 0) { throw "GitHub CLI is not authenticated" }

$Current = (& git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $Current -ne "mfi-edge-stage24-residual-suppression") {
    throw "Expected research branch; current branch is '$Current'"
}
$Uncommitted = (& git status --porcelain -- "results/paper_a_evidence/stage24gl")
if ($LASTEXITCODE -ne 0 -or $Uncommitted) {
    throw "Commit and push compact evidence first."
}
& git fetch origin "mfi-edge-stage24-residual-suppression"
if ($LASTEXITCODE -ne 0) { throw "Cannot validate remote branch" }
$Local = (& git rev-parse HEAD).Trim()
$Remote = (& git rev-parse "origin/mfi-edge-stage24-residual-suppression").Trim()
if ($Local -ne $Remote) {
    throw "Local HEAD has not been pushed to origin."
}
$Notes = @"
Stage24G-L Paper A complete derived score package.
SHA256 checksums: binary_deposit_manifest.json.
Original input photographs and ground truths are NOT included.
The per-fold checkpoints and Berkeley threshold counts are in commit $Local.
Please verify redistribution rights before publishing this draft.
"@
$ReleaseArgs = @("release","create",$Tag) + $Files + @(
    "--repo","MicamAmorim/MFI-Edge",
    "--target",$Local,
    "--title","Stage24G-L Paper A - derived scientific data",
    "--notes",$Notes,
    "--draft",
    "--latest=false"
)
& gh @ReleaseArgs
if ($LASTEXITCODE -ne 0) { throw "Could not create GitHub release draft" }
Write-Host "Draft ready. Review and publish manually if permitted." -ForegroundColor Green
