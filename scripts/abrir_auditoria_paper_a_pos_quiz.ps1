param([string]$ReportPath = "")

# Metadata-only Paper A post-quiz reconciliation; do not touch GT or freeze.
$ErrorActionPreference = "Stop"
$repo=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo
$branch="experiment/paper-a-conditional-confirmation"
$python=Join-Path $repo ".venv\Scripts\python.exe"
$base="F:\MFI-Edge-Data\MultiCue\paper_a_completion"
$signoff=Join-Path $base "scientific_signoff"

if ((& git branch --show-current).Trim() -ne $branch) {
    throw "Use a branch experimental do Paper A e faca git pull --ff-only"
}
if (-not (Test-Path $python -PathType Leaf)) { throw "Python .venv nao encontrado" }
if (-not (Test-Path $signoff -PathType Container)) { throw "Pacote de revisao nao preparado" }
if (Test-Path (Join-Path $signoff "FINAL_INDEPENDENT_REVIEW.json")) {
    throw "Revisao independente ja existe; nao regenerar pos-quiz sem examinar signoff"
}
if (Test-Path (Join-Path $base "freeze_approval.json")) {
    throw "Freeze ja existe; nao abrir este fluxo pre-confirmatorio"
}

if (-not $ReportPath) {
    $downloads=Join-Path $env:USERPROFILE "Downloads"
    $files=@(Get-ChildItem -LiteralPath $downloads -File -ErrorAction Stop |
        Where-Object {
            $_.Name -like "PaperA_RELATORIO_293_*.html" -or
            $_.Name -like "PaperA_QUIZ_293_*.json"
        } | Sort-Object LastWriteTimeUtc -Descending)
    if ($files.Count -eq 0) {
        throw "Relatorio nao encontrado em Downloads. Passe -ReportPath 'C:\...\PaperA_RELATORIO_293_...html'"
    }
    $ReportPath=$files[0].FullName
}
if (-not (Test-Path -LiteralPath $ReportPath -PathType Leaf)) {
    throw "Relatorio exportado nao encontrado: $ReportPath"
}
$ReportPath=(Resolve-Path -LiteralPath $ReportPath).Path
$hash=(Get-FileHash -LiteralPath $ReportPath -Algorithm SHA256).Hash.ToLower()
Write-Host "RELATORIO INPUT: $ReportPath"
Write-Host "SHA256: $hash"
Write-Host "[1/3] Testes sinteticos sem dados experimentais"
& $python -m unittest discover -s tests -p "test_auditar_paper_a_pos_quiz.py" -v
if ($LASTEXITCODE -ne 0) { throw "Falha nos testes da conciliacao pos-quiz" }

Write-Host "[2/3] Conferencia dos metadados, deteccao de divergencias e matriz historica"
& $python scripts/auditar_paper_a_pos_quiz.py --report $ReportPath
if ($LASTEXITCODE -ne 0) {
    throw "Auditoria pos-quiz bloqueada. Veja os hashes/evidencias divergentes acima."
}

Write-Host "[3/3] Abrindo apenas as pendencias para reconciliacao humana"
$out=Join-Path $signoff ("RECONCILIACAO_POS_QUIZ_"+$hash.Substring(0,12))
$page=Join-Path $out "REVISAR_PENDENCIAS.html"
$matrix=Join-Path $out "MATRIZ_HISTORICA_PENDENTE.json"
$audit=Join-Path $out "AUDITORIA_POS_QUIZ.json"
foreach ($p in @($page,$matrix,$audit)) {
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {
        throw "Artefato da auditoria ausente: $p"
    }
}
Start-Process -FilePath $page
Write-Host "[OK] APENAS PENDENCIAS PARA REVISAO: $page"
Write-Host "MATRIZ HISTORICA: $matrix"
Write-Host "AUDITORIA: $audit"
Write-Host "O historico permanece PENDENTE DE ATESTACAO; nenhum GT ou resultado confirmatorio foi aberto."
