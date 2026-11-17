# Validate the USER-SELECTED, unsigned N=219 Paper A scenario.
# No protected GT/H5/F1, no training, no freeze, no cohort promotion.
$ErrorActionPreference="Stop"
$repo=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo
$branch="experiment/paper-a-conditional-confirmation"
$python=Join-Path $repo ".venv\Scripts\python.exe"
$base="F:\MFI-Edge-Data\MultiCue\paper_a_completion"
$signoff=Join-Path $base "scientific_signoff"
if ((git branch --show-current).Trim() -ne $branch) {
    throw "Unexpected branch. Check out the Paper A experimental branch first."
}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Missing Python .venv at $python"
}
if (Test-Path -LiteralPath (Join-Path $base "freeze_approval.json")) {
    throw "There is already a freeze approval. Stop prefreeze validations."
}
if (Test-Path -LiteralPath (Join-Path $signoff "FINAL_INDEPENDENT_REVIEW.json")) {
    throw "There is already a signed review. Do not alter its referenced candidate."
}
Write-Host "[1/3] Synthetic no-GT N219 checks"
& $python -m unittest discover -s tests -p "test_validar_coorte_a_219_pre_freeze.py" -v
if ($LASTEXITCODE -ne 0) { throw "Synthetic N219 audit tests failed" }

Write-Host "[2/3] SHA-256 every selected ORIGINAL (125 BIPED + 94 MultiCue)"
& $python -u scripts/validar_coorte_a_219_pre_freeze.py
if ($LASTEXITCODE -ne 0) { throw "A original-image or metadata check failed" }

Write-Host "[3/3] Exact unsigned review output hashes"
$csv=Join-Path $signoff "COORTE_A_N219_PARA_REVISAO_NAO_FROZEN.csv"
$json=Join-Path $signoff "COORTE_A_N219_READINESS_NOT_APPROVED.json"
foreach ($path in @($csv,$json)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required audit output not created: $path"
    }
    Get-FileHash -LiteralPath $path -Algorithm SHA256
}
$metadata=Get-Content -LiteralPath $json -Raw -Encoding UTF8 | ConvertFrom-Json
if ($metadata.scientific_signoff -ne $false -or
    $metadata.freeze_authorized -ne $false -or
    $metadata.GT_accessed -ne $false -or
    $metadata.counts.N -ne 219) {
    throw "Unexpected science approval or wrong cohort size"
}
Write-Host "[OK] Candidate A sources checked; SCIENTIFIC GATES STILL OPEN"
Write-Host "Candidate for review: $csv"
Write-Host "Readiness and blockers: $json"
Write-Host "Do not run H1/H2; legacy freeze still targets N220 until amended and approved."
