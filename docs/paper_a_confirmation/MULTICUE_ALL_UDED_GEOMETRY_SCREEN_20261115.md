# Auditoria geométrica MultiCue × todos os originais UDED históricos

**Apenas triagem pré-dados.** O pipeline de dHash/pHash perdeu o
recorte histórico UDED 09-MDBD-1C ↔ MultiCue 4113_left_0082. A execução
nas imagens originais encontrou 2.101/2.116 inliers (99,291%) e a exclusão
foi registrada antes de abrir GT/F1. Como hashes globais não detectam
necessariamente recortes, todas as demais imagens UDED historicamente
expostas e decodificáveis devem passar por triagem geométrica.

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\tests\test_paper_a_multicue_all_uded_geometry.py
python .\scripts\audit_paper_a_multicue_all_uded_geometry.py
```

O script avalia 27 originais históricos UDED (incluindo 09-MDBD-1C)
contra os 100 originais MultiCue, **2.700 pares**. As três originais UDED
de linhagem BSDS-test protegida permanecem sem decodificação visual.
Não relê TAR, HDF5, anotações, mapas, F1 nem predições.

**Evitar recálculos:** extrai SIFT de cada imagem original uma vez,
armazenando características por SHA-256 no F: em
`F:MFI-Edge-DataMultiCuepredata_sift_cache`.
Também salva resultados completos de cada imagem UDED em
`reference_checkpoints`. Retomadas conferem o SHA256 da
imagem, o conjunto de 100 alvos, versão OpenCV e parâmetros fixados.
Um checkpoint incompatível interrompe a execução.

**Saídas:**
- `F:MFI-Edge-DataMultiCuemulticue_all_uded_geometric_overlap_summary.json`
- `F:MFI-Edge-DataMultiCuemulticue_all_uded_geometric_overlap_pairs.csv`

A evidência positiva conhecida `09-MDBD-1C ↔ 4113_left_0082`
é controle de sanidade: a auditoria **para com erro** caso não a sinalize.
Casos novos são apenas flags para revisão humana. Não excluir cenas
automaticamente, não usar negativos para alegar independência absoluta.
O prefixo 4113 permanece bloqueado para a confirmação.

**Gates após esta auditoria:** revisar novos alertas, certificar dependência
entre capturas e exposição histórica MultiCue/MDBD, concluir análise de
poder, política de GT/avaliador, seleção e congelamento pré-F1 de H1/H2.
