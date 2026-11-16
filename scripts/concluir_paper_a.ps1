param([switch]$SkipUpdate)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo
$branch = (& git branch --show-current).Trim()
if ($branch -ne "experiment/paper-a-conditional-confirmation") {
    throw "Branch incorreta: $branch"
}
if (-not $SkipUpdate) {
    & git pull --ff-only origin experiment/paper-a-conditional-confirmation
    if ($LASTEXITCODE -ne 0) { throw "Falha no git pull. Nenhum arquivo foi descartado." }
}
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python da venv nao encontrado: $python" }
& $python -u "scripts\continuar_paper_a.py"
$code = $LASTEXITCODE
Write-Host "Resumo em F:\MFI-Edge-Data\MultiCue\paper_a_completion\ONE_COMMAND_STATUS.json"
Write-Host "Pendencias em F:\MFI-Edge-Data\MultiCue\paper_a_completion\NEXT_ACTIONS.md"
Write-Host "Revisao: F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff\REVIEWER_DECISION_REQUIRED.md"
Write-Host "Pacote unico: F:\MFI-Edge-Data\MultiCue\paper_a_completion\PaperA_PRE_FREEZE_REVIEW_ONLY.zip"
if ($code -ne 0) { throw "Erro tecnico: ver ONE_COMMAND_ERROR.json no F:" }
