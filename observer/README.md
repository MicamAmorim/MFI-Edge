# MFI-Edge Research Console V2

Observador externo do MFI-Edge. Não altera o MFI.

## Instalar
```powershell
cd "C:\Users\Windows 11\Documents\MFI-Edge"
.\.venv\Scripts\python.exe -m pip install -r .\observer\requirements.txt
```

## Rodar
```powershell
.\.venv\Scripts\python.exe .\observer\app.py
```

Local: `http://127.0.0.1:8765`

Tailscale:
```powershell
tailscale ip -4
```
Depois abra `http://SEU_IP_TAILSCALE:8765`.

## Monitora
- processos Python/MATLAB/Codex/PowerShell relacionados ao MFI
- árvore pai-filho
- comando ativo
- arquivos recentes em results/, automation/ e docs/
- `.partial.json` para progresso
- melhor F1 quando houver `f_measure`
- etapa/experimento inferidos
- Git (branch, HEAD, dirty, ahead/behind)
- stream de eventos
