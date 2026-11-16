# Resultado da auditoria MultiCue × 27 UDED históricas — 15/11/2026

## Execução da workstation, confirmada pelo log

- Teste unitário de geometria: **2/2 passando**.
- 100 quadros finais esquerdos MultiCue versus 27 originais UDED historicamente
  acessados: **2.700 pares** concluídos, com cache SIFT no disco F:.
- **25 pares sinalizados** pelo critério SIFT/FLANN + homografia RANSAC.
- **12 originais UDED distintos** e **21 prefixos de captura MultiCue**
  envolvidos nos alertas.
- Referência positiva confirmada:
  `09-MDBD-1C` versus `4113_left_0082`:
  **2.100/2.116 inliers (99,244%)** com FLANN.
  O ensaio anterior BFMatcher produziu **2.101/2.116 (99,291%)**;
  um inlier de diferença entre procedimentos de matching, sem dúvida
  material sobre identidade da cena.
- Três UDED de linhagem BSDS-test (`03-35028`, `10-196062` e
  `22-335094`) não foram decodificadas.
- Nenhum GT/HDF5, mapa, predição, F1 ou inferência confirmatória foi aberto.

## Alertas de maior prioridade de revisão

| UDED histórica | MultiCue | Inliers/matches | Fração |
|---|---|---:|---:|
| 09-MDBD-1C | 4113_left_0082 | 2100/2116 | 99,24% |
| 13-BIPED-1C | 4609_left_0080 | 277/354 | 78,25% |
| 13-BIPED-1C | 4494_left_0070 | 267/313 | 85,30% |
| 13-BIPED-1C | 4580_left_0165 | 195/315 | 61,90% |
| 17-1194 | 4184_left_0048 | 131/188 | 69,68% |

Os **24 alertas adicionais NÃO são sobreposições comprovadas**.
Similaridades geométricas podem resultar de texturas repetitivas ou
estruturas similares. Devem ser avaliadas em pares de imagens originais,
e não resultar em exclusões automáticas.

## Próximo gate: revisão humana de 25 pares, sem reprocessamento

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\tests\test_paper_a_multicue_overlap_review_sheets.py
python .\scripts\render_paper_a_multicue_uded_overlap_review.py
explorer.exe "F:\MFI-Edge-Data\MultiCue\multicue_uded_geometric_visual_review"
```

O renderizador somente lê o CSV/JSON de auditoria, os manifestos
e **as fotos originais correspondentes aos 25 alertas**;
valida novamente SHA256 e usa Pillow para compor cinco pranchas
com cinco pares por página, além do modelo
`human_review_template.csv`. Não refaz SIFT, RANSAC,
dHash/pHash, extração TAR ou leitura de anotação.

### Situação da seleção

- `4113_left_0082` permanece **EXCLUDE_PRIOR_EXPOSURE**.
- Todo o prefixo `4113` permanece em HOLD, incluindo
  `4113_left_2396`, até esclarecimento de dependência.
- Os outros 20 prefixos sinalizados por geometria ficam em
  **REVIEW_PENDING**, sem exclusão automática.
- Se 20 prefixos sinalizados adicionais e o 4113 fossem conservadoramente
  suspensos, **75 grupos MultiCue não sinalizados** permaneceriam em tese
  para posterior verificação, sem implicar independência comprovada ou
  aprovação do protocolo. Não pré-selecionar esses grupos por resultados.

O status segue `draft_not_frozen`. A análise de poder e a definição do
avaliador/GT ainda são pendências antes da execução de H1/H2.
