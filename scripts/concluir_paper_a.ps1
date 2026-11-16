param([switch]$SkipUpdate)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo
$branch = (& git branch --show-current).Trim()
if ($branch -ne "experiment/paper-a-conditional-confirmation") {
    throw "Branch incorreta: $branch"
}
if (-not $SkipUpdate) {
    # PowerShell parses the entire script before git pull. If the pull
    # replaces this launcher, the in-memory script is still the OLD version.
    # Relaunch exactly once, from the newly updated path, without another pull.
    $loadedFileSha = (Get-FileHash -Algorithm SHA256 -Path $PSCommandPath).Hash
    & git pull --ff-only origin experiment/paper-a-conditional-confirmation
    if ($LASTEXITCODE -ne 0) { throw "Falha no git pull. Nenhum arquivo foi descartado." }
    $currentFileSha = (Get-FileHash -Algorithm SHA256 -Path $PSCommandPath).Hash
    if ($loadedFileSha -ne $currentFileSha) {
        Write-Host "[PAPER A] Launcher atualizado pelo git pull; reiniciando a versao NOVA do script sem repetir o pull."
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath -SkipUpdate
        $restartCode = $LASTEXITCODE
        exit $restartCode
    }
}
Write-Host "[PAPER A] Launcher atual carregado: Codex + freeze guard + confirmacao H1/H2."
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python da venv nao encontrado: $python" }
& $python -u "scripts\paper_a_codex_finalizer.py"
$code = $LASTEXITCODE
Write-Host "Resumo em F:\MFI-Edge-Data\MultiCue\paper_a_completion\ONE_COMMAND_STATUS.json"
Write-Host "Pendencias em F:\MFI-Edge-Data\MultiCue\paper_a_completion\NEXT_ACTIONS.md"
Write-Host "Revisao: F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff\REVIEWER_DECISION_REQUIRED.md"
Write-Host "Pacote unico: F:\MFI-Edge-Data\MultiCue\paper_a_completion\PaperA_PRE_FREEZE_REVIEW_ONLY.zip"
Write-Host "Relatorio final: F:\MFI-Edge-Data\MultiCue\paper_a_completion\FINAL_ONE_COMMAND_REPORT.json"
Write-Host "Auditoria Codex: F:\MFI-Edge-Data\MultiCue\paper_a_completion\codex_final_audit"
if ($code -ne 0) { throw "Erro tecnico: ver ONE_COMMAND_ERROR.json no F:" }
