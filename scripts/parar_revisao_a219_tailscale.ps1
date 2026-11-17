param([int]$PortaTailscale=8443)
$ErrorActionPreference='Stop'
$ts=Get-Command 'tailscale.exe' -ErrorAction SilentlyContinue
if(-not $ts){$ts=Get-Command 'tailscale' -ErrorAction SilentlyContinue}
$exe=if($ts){$ts.Source}else{'C:\Program Files\Tailscale\tailscale.exe'}
if(-not(Test-Path -LiteralPath $exe -PathType Leaf)){throw 'Tailscale CLI indisponível'}
& $exe serve "--https=$PortaTailscale" off
if($LASTEXITCODE -ne 0){throw 'Não foi possível interromper o Tailscale Serve'}
Write-Host 'Proxy Tailscale Serve desligado. Encerre o PowerShell do backend com Ctrl+C, se ainda estiver ativo.'
