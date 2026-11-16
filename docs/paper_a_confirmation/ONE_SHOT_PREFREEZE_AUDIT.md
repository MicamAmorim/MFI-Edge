# Auditoria integrada pré-freeze (uma execução)

**Executar uma vez no Windows, sem GT/F1 e sem reprocessamento.**
Após git pull e .venv, executar:

    python .\tests\test_paper_a_prefreeze_one_shot.py
    python -u .\scripts\run_paper_a_prefreeze_one_shot.py

O programa executa seis grupos de testes já existentes, as verificações
P0, P0.1, P0.2, P0.3, o inventário MultiCue e o SHA256 byte a byte dos
56 arquivos NPY de desenvolvimento. **Não chama np.load**, não treina
modelos, não consulta dados confirmatórios, GT, H5 ou F1. O consumo de
leitura de NPY é limitado a 16 MiB por arquivo; compara cada SHA256 ao
valor declarado simultaneamente no CSV histórico e no sidecar P0.3.

Os relatórios recebem nome exclusivo no diretório
F:\MFI-Edge-Data\MultiCue\paper_a_prefreeze_combined_audit.
Uma falha em SHA ou source-contract produz status TECHNICAL_REVIEW_REQUIRED.
Um resultado TECHNICAL_AUDITS_OK_SCIENTIFIC_GATES_STILL_OPEN confirma
integridade técnica, NÃO autorização para fitting nem congelamento.

Para deixar rodando sem precisar manter a janela de PowerShell aberta:

    $folder = 'F:\MFI-Edge-Data\MultiCue\paper_a_prefreeze_combined_audit'
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    Start-Process -FilePath (Resolve-Path '.\.venv\Scripts\python.exe').Path -ArgumentList @('-u','scripts\run_paper_a_prefreeze_one_shot.py') -WorkingDirectory (Get-Location).Path -RedirectStandardOutput "$folder\ultima.stdout.log" -RedirectStandardError "$folder\ultima.stderr.log" -PassThru

Não desligar nem suspender/hibernar o Windows durante a execução.
Os resultados científicos pendentes continuam: receitas H1/H2,
calibração, GT edges real, independência das cenas e freeze formal.