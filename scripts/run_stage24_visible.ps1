$ErrorActionPreference = 'Stop'
$mfiRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $mfiRoot
$Host.UI.RawUI.WindowTitle = 'MFI-Edge | Stage24 | Progresso e retomada'
$env:STAGE24GL_MATCH_WORKERS = '4'
$env:TQDM_DISABLE = '1'
$mfiOutput = Join-Path $mfiRoot 'results\local_dev\stage24_paper_a_recertification'
New-Item -ItemType Directory -Force -Path $mfiOutput | Out-Null
$mfiLog = Join-Path $mfiOutput ('console_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
Start-Transcript -Path $mfiLog
try {
    Write-Host 'MFI-Edge: retomando checkpoints; 4 workers; log sequencial.' -ForegroundColor Cyan
    Write-Host ('Log: ' + $mfiLog)
    Remove-Item -LiteralPath 'automation\STOP_STAGE24_PAPER_A' -ErrorAction SilentlyContinue
    & .\run_stage24_paper_a_recertification.bat --phase all
    Write-Host ('Processo terminou com codigo: ' + $LASTEXITCODE)
} finally {
    Stop-Transcript
}
