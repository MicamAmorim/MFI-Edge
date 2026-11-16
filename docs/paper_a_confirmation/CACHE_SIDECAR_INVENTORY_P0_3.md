# P0.3 — inventário de sidecars dos 56 mapas já cacheados

**Somente metadados.** Não relê `.npy`, imagens, GT/H5 ou resultados F1.
Verifica os registros JSON de identidade em
`cache/local_dev/stage24/descriptors/{descriptor_id}/`, e confere
presença/tamanho do `.npy` correspondente usando apenas `stat()`.

Para cada um dos 56 pares de 14 imagens UDED × 4 descritores, compara
o `artifact_sha256` declarado no sidecar com o hash do manifesto
`results/paper_a_evidence/stage24gl/campaign/descriptor_provenance.csv`.
Isto **não recalcula o hash do `.npy`** e não prova integridade dos bytes.

Se 56/56 corresponderem, a disponibilidade do cache fica documentada
e podemos considerar uma verificação de hash de leitura autorizada,
antes de qualquer ajuste limitado de desenvolvimento.
Se houver ausentes ou versões ambíguas, o relatório aponta a ausência;
não reprocessa automaticamente e não altera a campanha.

## Executar

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
.\.venv\Scripts\Activate.ps1
python .\tests\test_paper_a_uded14_cache_sidecars_P0_3.py
python .\scripts\audit_paper_a_uded14_cache_sidecars_P0_3.py
```

Relatório: `F:\MFI-Edge-Data\MultiCue\paper_a_uded14_cache_sidecars_P0_3.json`.

**Importante:** as 14 imagens pertencem à fase exploratória.
Se usadas para ajuste supervisionado, contam apenas como desenvolvimento;
nunca poderão ser observações confirmatórias.
Aprovar a origem do treino e o método de ajuste, congelar os valores
e certificar a coorte independente são etapas posteriores.
