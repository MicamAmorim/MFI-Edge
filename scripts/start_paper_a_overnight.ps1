# Paper A overnight Codex/autonomous local launcher.
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$branch = (git branch --show-current).Trim()
if ($branch -ne 'experiment/paper-a-conditional-confirmation') { throw "Wrong Git branch: $branch" }
git pull --ff-only origin experiment/paper-a-conditional-confirmation
if ($LASTEXITCODE -ne 0) { throw 'git pull failed' }
$tracked = @(git status --porcelain --untracked-files=no)
if ($tracked.Count -gt 0) { throw "Tracked/index changes must be reviewed: $tracked" }
Write-Host "Existing untracked scientific evidence will be preserved, never staged or deleted."
$python = (Resolve-Path '.\.venv\Scripts\python.exe').Path
$dir = 'F:\MFI-Edge-Data\MultiCue\paper_a_overnight_codex'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$stdout = Join-Path $dir "overnight_$stamp.stdout.log"
$stderr = Join-Path $dir "overnight_$stamp.stderr.log"
if (-not (Get-Command codex -ErrorAction SilentlyContinue)) { Write-Warning 'Codex not found; audit and package still run.' }
$p = Start-Process -FilePath $python -ArgumentList @('-u','scripts\paper_a_overnight_agent.py') -WorkingDirectory (Get-Location).Path -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
Write-Host "Launched overnight Paper A agent PID $($p.Id)"
Write-Host "Log: $stdout"
Write-Host 'Final: F:\MFI-Edge-Data\MultiCue\paper_a_overnight_LAST_STATUS.json'
Write-Warning 'Keep PC running; do not launch a second instance.'
