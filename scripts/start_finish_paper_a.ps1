# Paper A - ONE COMMAND checkpointed completion controller
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $project
$branch = (git branch --show-current).Trim()
if ($branch -ne 'experiment/paper-a-conditional-confirmation') { throw "Wrong Git branch: $branch" }
git pull --ff-only origin experiment/paper-a-conditional-confirmation
if ($LASTEXITCODE -ne 0) { throw 'Git pull failed' }
$tracked = @(git status --porcelain --untracked-files=no)
if ($tracked.Count -gt 0) { throw "Tracked files have uncommitted modifications: $tracked" }
$python = (Resolve-Path '.\.venv\Scripts\python.exe').Path
$logDir = 'F:\MFI-Edge-Data\MultiCue\paper_a_completion'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$out = Join-Path $logDir "completion_$stamp.stdout.log"
$err = Join-Path $logDir "completion_$stamp.stderr.log"
$p = Start-Process -FilePath $python -ArgumentList @('-u','scripts\finish_paper_a.py') -WorkingDirectory $project -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
Write-Host "Paper A checkpointed completion process PID $($p.Id)"
Write-Host "Log: $out"
Write-Host "Review blockers: $logDir\NEXT_ACTIONS.md"
Write-Host "Final JSON: $logDir\LAST_STATUS.json"
Write-Warning 'This pipeline does NOT auto-freeze science or invent confirmatory results.'
