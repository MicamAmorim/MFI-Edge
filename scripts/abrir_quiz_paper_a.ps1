# Paper A local quiz launcher: builds local SHA-verified image-only assets.
# Does not read GT, train models, compute F1, create freeze, or upload data.
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo
$branch = "experiment/paper-a-conditional-confirmation"
$python = Join-Path $repo ".venv\Scripts\python.exe"
$work = "F:\MFI-Edge-Data\MultiCue\paper_a_completion"
$signoff = Join-Path $work "scientific_signoff"
$report = Join-Path $signoff "QUIZ_VISUAL_LOCAL_293\index.html"

if ((git branch --show-current).Trim() -ne $branch) {
    throw "Branch incorreta; use a branch experimental e faca git pull --ff-only"
}
if (-not (Test-Path $python -PathType Leaf)) { throw "Python da .venv nao encontrado" }
if (-not (Test-Path $signoff -PathType Container)) {
    throw "Dados de revisao ainda nao preparados: $signoff"
}
if (Test-Path (Join-Path $signoff "FINAL_INDEPENDENT_REVIEW.json")) {
    throw "Ja ha assinatura: nao abrir ferramenta de revisao pre-freeze sem conferir estado"
}
if (Test-Path (Join-Path $work "freeze_approval.json")) {
    throw "Ja ha freeze_approval: esta ferramenta e apenas pre-freeze"
}

Write-Host "[1/3] Testes locais do gerador sem GT real"
& $python -m unittest discover -s tests -p "test_build_paper_a_review_quiz.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testes do quiz falharam" }

Write-Host "[2/3] Preparando 198 BIPED + 95 MultiCue dos originais verificados"
& $python scripts/build_paper_a_review_quiz.py
if ($LASTEXITCODE -ne 0) { throw "Falha ao montar o quiz local; nenhum freeze foi alterado" }

Write-Host "[3/3] Abrindo o HTML offline em seu navegador"
if (-not (Test-Path $report -PathType Leaf)) {
    throw "Pagina HTML gerada nao encontrada"
}
Start-Process -FilePath $report
Write-Host "[OK] Quiz local aberto: $report"
Write-Host "As respostas nao alteram o protocolo: use Exportar JSON para salvamento."
