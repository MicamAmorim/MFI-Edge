# Paper A N219 — prepare final hash-bound freeze REVIEW, without freeze/approval.
# No GT/H5/F1/maps, no outcome access, no new descriptor computation.
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root
$branch="experiment/paper-a-conditional-confirmation"
$python=Join-Path $root ".venv\Scripts\python.exe"
$signoff="F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff"
if ((git branch --show-current).Trim() -ne $branch) {
    throw "Use a branch experimental Paper A"
}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {throw "Missing .venv"}
if (Test-Path -LiteralPath "F:\MFI-Edge-Data\MultiCue\paper_a_completion\freeze_approval.json") {
    throw "Existing freeze approval; do not prepare a different cohort"
}
if (Test-Path -LiteralPath (Join-Path $signoff "FINAL_INDEPENDENT_REVIEW.json")) {
    throw "Signed decision already exists; do not mutate its reviewed inputs"
}
$changed=@(git status --porcelain --untracked-files=no)
if ($LASTEXITCODE -ne 0 -or $changed.Count -gt 0) {
    throw "Tracked files changed since the last reviewed commit"
}
Write-Host "[1/3] Synthetic source-hash and unsigned-scene prefreeze checks"
& $python -m unittest discover -s tests -p "test_paper_a_a219_freeze_policy.py" -v
if ($LASTEXITCODE -ne 0) {throw "A219 source policy tests failed"}
Write-Host "[2/3] Synthetic independent-review and freeze-invariant checks"
& $python -m unittest discover -s tests -p "test_freeze_paper_a_from_independent_review.py" -v
if ($LASTEXITCODE -ne 0) {throw "Legacy-to-A219 freeze tests failed"}
Write-Host "[3/3] Generate ONLY a pending freeze preview and an unsigned human signoff template"
# Native Windows process argument quoting can strip quote characters from
# python -c; execute a dedicated script with a normal filesystem path instead.
$entrypoint=Join-Path $PSScriptRoot "gerar_preview_freeze_a219.py"
if (-not (Test-Path -LiteralPath $entrypoint -PathType Leaf)) {
    throw "Missing standalone A219 preview entrypoint"
}
& $python -B $entrypoint
if ($LASTEXITCODE -ne 0) {throw "N219 reviewed-freeze preflight blocked"}
$template=Join-Path $signoff "FINAL_INDEPENDENT_REVIEW.template.json"
$preview=Join-Path $signoff "FROZEN_PROTOCOL_BYTES_TO_REVIEW_NOT_ACTIVE.json"
foreach($f in @($template,$preview)){
    if(-not(Test-Path -LiteralPath $f -PathType Leaf)){throw "Missing review artifact: $f"}
    Get-FileHash -LiteralPath $f -Algorithm SHA256
}
$t=Get-Content -LiteralPath $template -Raw -Encoding UTF8|ConvertFrom-Json
$p=Get-Content -LiteralPath $preview -Raw -Encoding UTF8|ConvertFrom-Json
if($t.approved_for_first_confirmatory_outcome_access -ne $false -or
   $p.cohort.target_n_independent_images -ne 219 -or
   $p.status -ne "frozen" -or
   $p.confirmatory_outcomes_opened -ne $false -or
   $null -ne $p.freeze_commit){
    throw "Unexpected signed/live protocol state. Review inputs manually."
}
# The frozen STATUS is only inside an inactive preview, not protocol.json.
$active=Get-Content -LiteralPath ".\docs\paper_a_confirmation\protocol.json" -Raw -Encoding UTF8|ConvertFrom-Json
if($active.status -ne "draft_not_frozen"){throw "Active protocol was unexpectedly frozen"}
Write-Host "[OK] A219 exact prospective freeze PREVIEW ONLY. No signed approval, no GT/H1/H2."
Write-Host "Unsigned review template: $template"
Write-Host "Inactive frozen protocol bytes for external reviewer: $preview"
