# Paper A scenario A: review-only N219 science dossier; NEVER freeze or run H1/H2.
$ErrorActionPreference="Stop"
$repo=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo
$branch="experiment/paper-a-conditional-confirmation"
$python=Join-Path $repo ".venv\Scripts\python.exe"
$base="F:\MFI-Edge-Data\MultiCue\paper_a_completion"
$signoff=Join-Path $base "scientific_signoff"
if ((git branch --show-current).Trim() -ne $branch) {
    throw "Wrong branch: switch to the Paper A experiment branch"
}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Python .venv not found"
}
if ((Test-Path -LiteralPath (Join-Path $base "freeze_approval.json")) -or
    (Test-Path -LiteralPath (Join-Path $signoff "FINAL_INDEPENDENT_REVIEW.json"))) {
    throw "Found an earlier signed/frozen artifact; stop and inspect it before another science preview"
}
$gitStatus=@(git status --porcelain --untracked-files=no)
if ($LASTEXITCODE -ne 0 -or $gitStatus.Count -gt 0) {
    throw "Tracked Git worktree has changes. Review before preparing a new scientific preview."
}
Write-Host "[1/3] Synthetic N219 preview tests: no datasets or protected outcomes"
& $python -m unittest discover -s tests -p "test_preparar_revisao_cientifica_a219.py" -v
if ($LASTEXITCODE -ne 0) { throw "N219 science preview tests failed" }
Write-Host "[2/3] Cross-check 219 original IDs, source hashes and prospective power sensitivity"
& $python scripts/preparar_revisao_cientifica_a219.py
if ($LASTEXITCODE -ne 0) { throw "N219 scientific dossier preparation failed" }
Write-Host "[3/3] Preview files and SHA256"
$out=Join-Path $signoff "CANDIDATE_A_N219_SCIENCE_REVIEW_NOT_ACTIVE"
$files=@(
    "PROTOCOLO_N219_PARA_REVISAO_NAO_ATIVO.json",
    "REVIEW_A_N219_ALL_PENDING.csv",
    "FINAL_INDEPENDENT_REVIEW_A219.template_NOT_APPROVED.json",
    "SCIENTIFIC_GATES_A219_PENDING.json"
)
foreach ($name in $files) {
    $target=Join-Path $out $name
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw "Unsigned N219 science document missing: $target"
    }
    Get-FileHash -LiteralPath $target -Algorithm SHA256
}
$state=Get-Content -LiteralPath (Join-Path $out "SCIENTIFIC_GATES_A219_PENDING.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if ($state.scientific_signoff -ne $false -or $state.GT_opened -ne $false -or
    $state.frozen -ne $false -or $state.counts.N -ne 219) {
    throw "Unexpected state: no reviewer approval or confirmatory access permitted"
}
Write-Host "[OK] N219 preview ready. NO scientific signoff, NO freeze, NO GT/H1/H2."
Write-Host "Send the file SCIENTIFIC_GATES_A219_PENDING.json and the exact preview protocol for review."
