# Experimental Paper A wrapper; historical scientific code stays unchanged.
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$venv = Join-Path $PSScriptRoot '.venv-paper-a'
$python = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -m venv $venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $venv
    } else { throw 'Python 3.12+ required. Install from python.org.' }
    if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment setup failed' }
}
& $python -m pip install -r reproduction/requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Python requirements installation failed' }
& $python -m reproduction.main @Arguments
exit $LASTEXITCODE
