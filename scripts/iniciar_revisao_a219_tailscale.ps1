# Paper A219: Windows 11, local-only Python backend plus private Tailscale Serve.
# No Tailscale Funnel, no GT/H5/F1, no automatic freeze or signoff.
param(
    [int]$PortaLocal = 18765,
    [int]$PortaTailscale = 8443,
    [switch]$SomenteLocal,
    [switch]$Verificar
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $repo '.venv\Scripts\python.exe'
$server = Join-Path $PSScriptRoot 'paper_a_mobile_review_server.py'
Set-Location $repo
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Ambiente Python inexistente: $python"
}
if (-not (Test-Path -LiteralPath $server -PathType Leaf)) {
    throw "Servidor de revisão não encontrado: $server"
}
if (($PortaLocal -lt 1024) -or ($PortaLocal -gt 65535) -or
    ($PortaTailscale -lt 1024) -or ($PortaTailscale -gt 65535)) {
    throw 'Escolha portas entre 1024 e 65535.'
}
$branch = (& git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $branch -ne 'experiment/paper-a-conditional-confirmation') {
    throw 'Entre na branch experiment/paper-a-conditional-confirmation antes de executar.'
}
Write-Host '[1/3] Verificando os hashes e o estado pré-freeze da coorte A219'
& $python -B $server --repo $repo --port $PortaLocal --check
if ($LASTEXITCODE -ne 0) { throw 'Pré-verificação interrompida. Nenhum servidor foi exposto.' }
if ($Verificar) { Write-Host '[OK] Somente verificação realizada.'; exit 0 }
if (-not $SomenteLocal) {
    $ts = Get-Command 'tailscale.exe' -ErrorAction SilentlyContinue
    if (-not $ts) { $ts = Get-Command 'tailscale' -ErrorAction SilentlyContinue }
    $tsPath = if ($ts) { $ts.Source } else { 'C:\Program Files\Tailscale\tailscale.exe' }
    if (-not (Test-Path -LiteralPath $tsPath -PathType Leaf)) {
        throw "Tailscale CLI não encontrado em $tsPath. Instale e faça login no PC e celular, ou use -SomenteLocal."
    }
    $statusText = (& $tsPath status --json | Out-String)
    if ($LASTEXITCODE -ne 0) { throw 'Tailscale não está conectado. Entre em sua tailnet primeiro.' }
    $status = $statusText | ConvertFrom-Json
    if ($status.BackendState -ne 'Running') {
        throw "Tailscale precisa estar Running; estado atual: $($status.BackendState)"
    }
    $existing = (& $tsPath serve status | Out-String)
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível inspecionar as portas Tailscale Serve existentes.' }
    if ($existing -match ":$PortaTailscale(\b|/)" -and $existing -notmatch "127\.0\.0\.1:$PortaLocal") {
        throw "Porta Tailscale $PortaTailscale já está ocupada. Não sobrescreveremos outro serviço."
    }
    Write-Host '[2/3] Publicando exclusivamente na tailnet via Tailscale Serve HTTPS'
    & $tsPath serve --bg "--https=$PortaTailscale" "http://127.0.0.1:$PortaLocal"
    if ($LASTEXITCODE -ne 0) {
        throw 'Falha no Tailscale Serve. Pode ser necessário habilitar HTTPS no painel Tailscale.'
    }
    $dns = [string]$status.Self.DNSName
    if ($dns) {
        $dns = $dns.TrimEnd('.')
        Write-Host ''
        Write-Host "NO CELULAR, COM TAILSCALE ATIVO: https://$($dns):$PortaTailscale/" -ForegroundColor Cyan
    } else {
        Write-Host 'Consulte a URL com: tailscale serve status' -ForegroundColor Cyan
    }
    Write-Host 'O celular precisa pertencer à mesma tailnet e ter permissão de acesso.'
} else {
    Write-Host '[2/3] Modo local: não configura Tailscale Serve.'
}
Write-Host '[3/3] Iniciando servidor restrito a 127.0.0.1'
Write-Host 'O código de 12 dígitos será mostrado abaixo. Mantenha o terminal aberto.' -ForegroundColor Yellow
Write-Host 'Ctrl+C encerra o backend. Para desligar também o proxy: tailscale serve --https=8443 off'
& $python -B $server --repo $repo --bind 127.0.0.1 --port $PortaLocal
if ($LASTEXITCODE -ne 0) { throw 'Servidor de revisão finalizado com erro.' }
