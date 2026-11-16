# Paper A — preparar a revisão científica prospectiva v2 (SEM freeze)
# Execute no PowerShell Windows a partir da raiz do repo, apos git pull.
# Não acessa GT confirmatório, não treina, não aprova e não cria commit freeze.
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo
$branch = "experiment/paper-a-conditional-confirmation"
$base = "F:\MFI-Edge-Data\MultiCue\paper_a_completion"
$reviewDir = Join-Path $base "scientific_signoff"
$python = Join-Path $repo ".venv\Scripts\python.exe"

if (-not (Test-Path $python -PathType Leaf)) {
    throw "Python .venv nao encontrado"
}
if ((& git branch --show-current).Trim() -ne $branch) {
    throw "Branch incorreta: requer $branch"
}
& git diff --quiet --exit-code
if ($LASTEXITCODE -ne 0) {
    throw "Codigo versionado modificado: nao descartar ou sobrescrever alteracoes locais"
}
& git diff --cached --quiet --exit-code
if ($LASTEXITCODE -ne 0) {
    throw "Ha arquivos staged. Revisar antes de preparar o pacote"
}
if (Test-Path (Join-Path $reviewDir "FINAL_INDEPENDENT_REVIEW.json")) {
    throw "Ja existe uma decisao independente: nao atualizar preview sem examinar a assinatura"
}
if (Test-Path (Join-Path $base "freeze_approval.json")) {
    throw "Ja existe freeze approval: nao reexecutar preparacao pre-freeze"
}

Write-Host "[1/6] Testes sinteticos, sem GT real"
$patterns = @(
    "test_execute_paper_a_frozen_cohort.py",
    "test_freeze_paper_a_from_independent_review.py",
    "test_paper_a_freeze_guard.py",
    "test_paper_a_post_codex_regressions.py",
    "test_paper_a_gt_decoder_candidate_NOT_APPROVED.py",
    "test_check_paper_a_p1_lineage_prefreeze.py",
    "test_export_paper_a_review_bundle.py",
    "test_finish_paper_a.py"
)
foreach ($pattern in $patterns) {
    & $python -m unittest discover -s tests -p $pattern -v
    if ($LASTEXITCODE -ne 0) {
        throw "Teste falhou: $pattern. Nao continuar com o pacote"
    }
}

Write-Host "[2/6] Conferindo auditoria tecnica anterior sem recalcular mapas"
& $python scripts/finish_paper_a.py --no-reaudit --skip-baseline-zip
$finalizerCode = $LASTEXITCODE
if ($finalizerCode -ne 0) {
    throw "Finalizador retornou erro $finalizerCode; preservar log e estado"
}
$status = Get-Content (Join-Path $base "LAST_STATUS.json") -Raw -Encoding UTF8 |
    ConvertFrom-Json
if ($status.technical_audit.status -ne "REUSED_VERIFIED_56_56_WITH_UNCHANGED_SCIENTIFIC_CODE") {
    throw "A auditoria previa de 56 hashes nao pode ser reutilizada legitimamente"
}
if ($status.status -ne "PREFREEZE_SCIENTIFIC_GATES_OPEN" -or
    $status.freeze_certified -ne $false -or
    $status.protected_GT_H5_F1_opened_by_prefreeze -ne $false) {
    throw "Estado cientifico inesperado; nao criar novo pacote pre-freeze"
}

Write-Host "[3/6] Checando documentos de revisao; nenhuma linha aprovada automaticamente"
& $python scripts/prepare_paper_a_final_signoff.py
if ($LASTEXITCODE -ne 0) { throw "Falha ao conferir planilha de revisao" }

Write-Host "[4/6] Validando evidencia GT ja existente e gerando PREVIA, nao freeze"
$cmd = @'
import json, sys
from pathlib import Path
sys.path.insert(0,str(Path("scripts").resolve()))
import freeze_paper_a_from_independent_review as f
samples=f.verified_nonconfirmatory_gt_v2_evidence()
plan=f.prepare()
print(json.dumps({"status":plan["status"],"gt_metadata_sha256":samples,
                  "preview":plan["reviewed_protocol_candidate"],
                  "template":plan["review_template"],
                  "approved":plan["scientific_signoff_issued"]},
                 ensure_ascii=False,indent=2))
'@
& $python -c $cmd
if ($LASTEXITCODE -ne 0) {
    throw "Falha na conferencia GT v2 ou na renovacao segura da previa"
}
$templatePath = Join-Path $reviewDir "FINAL_INDEPENDENT_REVIEW.template.json"
$previewPath = Join-Path $reviewDir "FROZEN_PROTOCOL_BYTES_TO_REVIEW_NOT_ACTIVE.json"
$template = Get-Content $templatePath -Raw -Encoding UTF8 | ConvertFrom-Json
$preview = Get-Content $previewPath -Raw -Encoding UTF8 | ConvertFrom-Json
$format = Join-Path $reviewDir "NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json"
$detail = Join-Path $reviewDir "GT_PIXEL_ENCODING_DETAIL_PRE_FREEZE_v1.json"
$expectedPolicy = "BIPED_UINT8_0_254_255_MULTICUE_UINT16_0_65535_NATIVE_v2"
if ($template.approved_for_first_confirmatory_outcome_access -ne $false) {
    throw "Template indevidamente autorizante"
}
if ($preview.measures.ground_truth_contract.encoding -ne $expectedPolicy) {
    throw "Preview usa politica GT errada"
}
if ($template.nonconfirmatory_gt_format_sha256 -ne
    (Get-FileHash $format -Algorithm SHA256).Hash.ToLower()) {
    throw "Hash do relatorio de formato GT nao corresponde ao template"
}
if ($template.nonconfirmatory_gt_detail_sha256 -ne
    (Get-FileHash $detail -Algorithm SHA256).Hash.ToLower()) {
    throw "Hash do diagnostico GT nao corresponde ao template"
}
if ($null -eq $template.approved_runtime_sources_sha256 -or
    $template.approved_runtime_sources_sha256.PSObject.Properties.Count -lt 10) {
    throw "Hashes das dependencias do executor nao estao completos"
}

Write-Host "[5/6] Exportando apenas metadados, template e protocolo prospectivo"
& $python scripts/export_paper_a_review_bundle.py
if ($LASTEXITCODE -ne 0) { throw "Falha ao exportar pacote de revisao" }
$zip = Join-Path $base "PaperA_PRE_FREEZE_REVIEW_ONLY.zip"
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
try {
    $names = @($archive.Entries | ForEach-Object { $_.FullName })
    foreach ($required in @(
        "review/signoff/FROZEN_PROTOCOL_BYTES_TO_REVIEW_NOT_ACTIVE.json",
        "review/signoff/FINAL_INDEPENDENT_REVIEW.template.json",
        "review/signoff/FREEZE_READINESS_PREVIEW.json",
        "review/signoff/REVIEW_220_IMAGES_PENDING.csv",
        "review/signoff/GT_PIXEL_ENCODING_DETAIL_PRE_FREEZE_v1.json",
        "review/signoff/NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json",
        "review/signoff/P1_LINEAGE_METADATA_CROSSCHECK_NOT_APPROVED.json",
        "MANIFEST.json"
    )) {
        if ($names -notcontains $required) { throw "Falta no ZIP: $required" }
    }
}
finally { $archive.Dispose() }

Write-Host "[6/6] CONCLUIDO: pacote pronto para revisao cientifica EXTERNA"
Write-Host "Status: $($status.status)"
Write-Host "Auditoria: 56/56 (reutilizada)"
Write-Host "Politica GT: $expectedPolicy (APENAS PROPOSTA)"
Write-Host "Nenhum GT confirmatorio aberto; nenhum PASS ou freeze emitido."
Get-FileHash $zip -Algorithm SHA256 | Format-Table -AutoSize
Write-Host "PACOTE: $zip"
Write-Host "PLANILHA PARA REVISAO: $(Join-Path $reviewDir 'REVIEW_220_IMAGES_PENDING.csv')"
Write-Host "TEMPLATE DE DECISAO: $templatePath"
Write-Host "AVISO: nunca assinar sem revisar as 220 cenas, exposicao, sete P1 e semantica GT."
