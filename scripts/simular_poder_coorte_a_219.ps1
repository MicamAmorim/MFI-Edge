# Paper A Candidate A (125 BIPED + 94 MultiCue) — power sensitivity ONLY.
# No images/GT/H5/F1, no changes to the cohort, scientific protocol or freeze.
$ErrorActionPreference="Stop"
$repo=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo
$branch="experiment/paper-a-conditional-confirmation"
$python=Join-Path $repo ".venv\Scripts\python.exe"
$base="F:\MFI-Edge-Data\MultiCue\paper_a_completion"
$signoff=Join-Path $base "scientific_signoff"
if ((git branch --show-current).Trim() -ne $branch) {
    throw "Wrong branch: run from experimental Paper A branch"
}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Missing local .venv Python"
}
if ((Test-Path -LiteralPath (Join-Path $base "freeze_approval.json")) -or
    (Test-Path -LiteralPath (Join-Path $signoff "FINAL_INDEPENDENT_REVIEW.json"))) {
    throw "Scientific review already signed/frozen; do not regenerate planning estimates"
}
Write-Host "[1/3] Testing planning math on synthetic observations"
& $python -m unittest discover -s tests -p "test_simular_poder_coorte_a_219.py" -v
if ($LASTEXITCODE -ne 0) { throw "Synthetic power tests failed" }
Write-Host "[2/3] 10000 Monte Carlo scenarios per assumed absolute Spearman rho"
& $python -u scripts/simular_poder_coorte_a_219.py --replicates 10000
if ($LASTEXITCODE -ne 0) { throw "Power simulation failed; do not infer approval" }
Write-Host "[3/3] Verifying unsigned planning report"
$out=Join-Path $signoff "PODER_A_N219_SENSIBILIDADE_NAO_APROVADA.json"
if (-not (Test-Path -LiteralPath $out -PathType Leaf)) {
    throw "Power report missing"
}
$status=Get-Content -LiteralPath $out -Raw -Encoding UTF8 | ConvertFrom-Json
if ($status.scientific_power_approval -ne $false -or
    $status.freeze_authorized -ne $false -or $status.GT_opened -ne $false -or
    $status.H1_H2_executed -ne $false) {
    throw "Unexpected power approval or confirmatory access"
}
Get-FileHash -LiteralPath $out -Algorithm SHA256
Write-Host "[OK] Planning-only power sensitivity; scientific freeze is still blocked."
Write-Host "REPORT: $out"
