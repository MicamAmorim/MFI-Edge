# Paper A219 - run exact inferential ENGINE on 219 SYNTHETIC captures.
# NEVER opens protected original images, H5, GT, F1 or real X/Y.
# NEVER attempts scientific freeze or writes an approval.
$ErrorActionPreference="Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python=Join-Path $root ".venv\Scripts\python.exe"
if(-not(Test-Path -LiteralPath $python -PathType Leaf)){
    throw "Missing virtualenv Python"
}
Set-Location $root
$branch=(git branch --show-current).Trim()
if($LASTEXITCODE -ne 0 -or $branch -ne "experiment/paper-a-conditional-confirmation"){
    throw "Wrong branch; select Paper A independent analysis branch"
}
$active=Get-Content -LiteralPath (Join-Path $root "docs\paper_a_confirmation\protocol.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if($active.status -ne "draft_not_frozen" -or $active.confirmatory_outcomes_opened -ne $false){
    throw "Current protocol state requires human review before running pre-freeze dry-run"
}
Write-Host "[1/2] Verify statistical engine with small SYNTHETIC blocks only"
& $python -B -m unittest discover -s tests -p "test_testar_motor_estatistico_a219_sintetico.py" -v
if($LASTEXITCODE -ne 0){throw "Synthetic inference tests failed"}
Write-Host "[2/2] Invoke EXACT Paper A Spearman/100000 blocked permutations/Holm/2000 bootstrap, on synthetic N219"
& $python -B (Join-Path $root "scripts\testar_motor_estatistico_a219_sintetico.py") --permutations 100000 --bootstrap 2000
if($LASTEXITCODE -ne 0){throw "Synthetic inference executable failed"}
$out="F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff\TESTE_SINTETICO_MOTOR_INFERENCIAL_A219_SEM_GT.json"
if(-not(Test-Path -LiteralPath $out -PathType Leaf)){throw "Statistical synthetic report missing"}
$state=Get-Content -LiteralPath $out -Raw -Encoding UTF8 | ConvertFrom-Json
if($state.sample.N -ne 219 -or
   $state.permutations_per_hypothesis -ne 100000 -or
   $state.bootstrap_replicates_per_hypothesis -ne 2000 -or
   $state.real_GT_images_or_F1_read -ne $false -or
   $state.freeze_authorized -ne $false -or
   $state.H1_H2_confirmatory_executed -ne $false){
    throw "Unexpected scientific status in synthetic-only report"
}
Get-FileHash -LiteralPath $out -Algorithm SHA256
Write-Host "[OK] Synthetic-only statistical engine tested. No observed H1/H2 inference. Scientific freeze remains pending."
Write-Host "REPORT: $out"
