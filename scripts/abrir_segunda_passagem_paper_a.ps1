param(
    [string]$ReconciliationPath = "",
    [string]$ReportPath = ""
)
# Paper A second pass. Reads originals and metadata ONLY; never GT, H5 or F1.
$ErrorActionPreference = "Stop"
$repo=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo
$branch="experiment/paper-a-conditional-confirmation"
$python=Join-Path $repo ".venv\Scripts\python.exe"
$base="F:\MFI-Edge-Data\MultiCue\paper_a_completion"
$signoff=Join-Path $base "scientific_signoff"
$downloads=Join-Path $env:USERPROFILE "Downloads"
if ((git branch --show-current).Trim() -ne $branch) {
    throw "Branch incorreta; faca git pull --ff-only na branch Paper A"
}
if (-not (Test-Path $python -PathType Leaf)) { throw "Python .venv nao encontrado" }
if (-not (Test-Path $signoff -PathType Container)) {
    throw "Pastas scientific_signoff nao encontradas"
}
if (Test-Path (Join-Path $signoff "FINAL_INDEPENDENT_REVIEW.json")) {
    throw "Existe uma decisao assinada: nao regenerar auditoria anterior sem reconciliar"
}
if (Test-Path (Join-Path $base "freeze_approval.json")) {
    throw "Freeze ja existe: nao executar preparacao pre-freeze"
}
if (-not $ReconciliationPath) {
    $list=@(Get-ChildItem -LiteralPath $downloads -File |
        Where-Object { $_.Name -like "PaperA_RECONCILIACAO_*.json" } |
        Sort-Object LastWriteTimeUtc -Descending)
    if ($list.Count -eq 0) {
        throw "Copie o JSON PaperA_RECONCILIACAO_*.json para Downloads ou informe -ReconciliationPath"
    }
    $ReconciliationPath=$list[0].FullName
}
if (-not (Test-Path -LiteralPath $ReconciliationPath -PathType Leaf)) {
    throw "Arquivo de reconciliacao nao encontrado: $ReconciliationPath"
}
$ReconciliationPath=(Resolve-Path -LiteralPath $ReconciliationPath).Path
$revision=Get-Content -LiteralPath $ReconciliationPath -Raw -Encoding UTF8 | ConvertFrom-Json
$reportSha=$revision.source_report_sha256
if ($reportSha -notmatch '^[0-9a-f]{64}$') {
    throw "JSON de reconciliacao sem identidade SHA correta"
}
if (-not $ReportPath) {
    $matches=@(Get-ChildItem -LiteralPath $downloads -File |
        Where-Object {
            $_.Name -like "PaperA_RELATORIO_293_*.html" -or
            $_.Name -like "PaperA_QUIZ_293_*.json"
        } | Where-Object {
            (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower() -eq $reportSha
        })
    if ($matches.Count -ne 1) {
        throw "Nao foi encontrado exatamente um relatorio com SHA $reportSha em Downloads. Indique -ReportPath."
    }
    $ReportPath=$matches[0].FullName
}
if (-not (Test-Path -LiteralPath $ReportPath -PathType Leaf)) {
    throw "Relatorio original nao encontrado: $ReportPath"
}
$ReportPath=(Resolve-Path -LiteralPath $ReportPath).Path
if ((Get-FileHash -LiteralPath $ReportPath -Algorithm SHA256).Hash.ToLower() -ne $reportSha) {
    throw "O relatorio original nao corresponde ao JSON da reconciliacao"
}
$recSha=(Get-FileHash -LiteralPath $ReconciliationPath -Algorithm SHA256).Hash.ToLower()
Write-Host "[1/3] Testes sinteticos da consolidacao visual, sem GT"
& $python -m unittest discover -s tests -p "test_consolidar_reconciliacao_paper_a.py" -v
if ($LASTEXITCODE -ne 0) { throw "Falha nos testes de consolidacao; nao continuar" }
Write-Host "[2/3] Validando as 17 respostas, proveniencia e conflitos remanescentes"
& $python scripts/consolidar_reconciliacao_paper_a.py --report $ReportPath --reconciliation $ReconciliationPath
if ($LASTEXITCODE -ne 0) { throw "Falha na consolidacao: verifique fonte ou erros acima" }
Write-Host "[3/3] Abrindo somente os pares ainda contraditorios"
$out=Join-Path $signoff ("SEGUNDA_PASSAGEM_"+$recSha.Substring(0,12))
$page=Join-Path $out "REVISAR_CONFLITOS_RESTANTES.html"
$audit=Join-Path $out "AUDITORIA_POS_RECONCILIACAO.json"
foreach ($file in @($page,$audit)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Arquivo de segunda passagem ausente: $file"
    }
}
Start-Process -FilePath $page
Write-Host "[OK] Pagina local: $page"
Write-Host "[OK] Auditoria: $audit"
Write-Host "Nenhum acesso a GT confirmatorio, alteracao de coorte ou autorizacao de freeze."
