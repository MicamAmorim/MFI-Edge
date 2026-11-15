# Isolated, reproducible downloader environment on F: for MultiCue.
# Does NOT download or inspect the MultiCue dataset.
param(
    [string]$DataRoot = "F:\MFI-Edge-Data"
)
$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw ("Command failed with exit code {0}: {1}" -f $LASTEXITCODE, $Executable)
    }
}

$absoluteRoot = [System.IO.Path]::GetFullPath($DataRoot)
$targetDrive = [System.IO.Path]::GetPathRoot($absoluteRoot)
$systemDrive = [System.IO.Path]::GetPathRoot($env:SystemRoot)
if ($targetDrive -ieq $systemDrive) {
    throw "Refusing installation on system drive $systemDrive. Use F:\MFI-Edge-Data."
}
$driveLetter = $targetDrive.TrimEnd('\').TrimEnd(':')
$psDrive = Get-PSDrive -PSProvider FileSystem -Name $driveLetter -ErrorAction Stop
if ($psDrive.Free -lt 15GB) {
    throw "At least 15 GiB free is required on $targetDrive."
}

$tempDir = Join-Path $absoluteRoot "HFTemp"
$cacheDir = Join-Path $absoluteRoot "PipCache"
$venvRoot = Join-Path $absoluteRoot "Venvs\multicue-download"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"
@($absoluteRoot, $tempDir, $cacheDir, (Split-Path $venvRoot -Parent)) |
    ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null }

# Keep temporary downloads/cache out of the nearly full C: volume.
$env:TEMP = $tempDir
$env:TMP = $tempDir
$env:TMPDIR = $tempDir
$env:PIP_CACHE_DIR = $cacheDir
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
$env:HF_HOME = Join-Path $absoluteRoot "HFCache"
$env:HF_HUB_CACHE = Join-Path $env:HF_HOME "hub"
$env:HF_XET_CACHE = Join-Path $env:HF_HOME "xet"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Invoke-Checked -Executable "python" -Arguments @("-m", "venv", $venvRoot)
}
Invoke-Checked -Executable $venvPython -Arguments @(
    "-m", "pip", "install", "huggingface_hub[hf_xet]==1.33.0"
)
Invoke-Checked -Executable $venvPython -Arguments @("-m", "pip", "check")
Invoke-Checked -Executable $venvPython -Arguments @(
    "-c", "from importlib.metadata import version; assert version('huggingface_hub') == '1.33.0'; from huggingface_hub import HfApi, hf_hub_download; print('Hugging Face venv OK: version=' + version('huggingface_hub'))"
)
Write-Host ""
Write-Host "Ambiente isolado pronto, sem download de dataset:" -ForegroundColor Green
Write-Host $venvPython
Write-Host 'Comando de download explicito:'
Write-Host ('& "' + $venvPython + '" .\scripts\acquire_paper_a_multicue_archive.py --destination "F:\MFI-Edge-Data\MultiCue" --download')
