# Auditoria de linhagem visual MultiCue × UDED 09-MDBD-1C — revisão 15/11/2026

## Evidência de sobreposição confirmada na revisão visual

Os dois PNGs de revisão enviados pelo pesquisador exibem a imagem histórica
`UDED 09-MDBD-1C` e os 12 vizinhos mais próximos por dHash e pHash.

A imagem **`MultiCue 4113_left_0082` mostra o mesmo conteúdo fotográfico**
da imagem histórica: bicicletário junto a um muro claro, calçada principal,
faixa de grama e árvore ao fundo. O registro MultiCue é mais largo que a
referência UDED, que apresenta recorte vertical.

**Validação geométrica adicional:** recortes das *pranchas renderizadas*
produziram, em teste SIFT + homografia RANSAC, **86 inliers entre 88
matches** (97,7%); ORB + RANSAC, **214 inliers entre 217 matches**
(98,6%). A transformação majoritária é uma redução de escala, consistente
com o mesmo registro visual recortado. Estes números foram calculados
**sobre thumbnails renderizados nas pranchas**, não sobre PNGs de origem.
O script de confirmação por características locais nas imagens originais
foi adicionado para obtenção de evidência primária.

## Por que a auditoria anterior deu zero alertas

A comparação dHash/pHash global foi realizada com imagens de proporções
diferentes (referência vertical versus quadro original horizontal). Para
`4113_left_0082`, os hashes globais diferiram em dHash 23/64 e pHash
26/63. Esses valores ultrapassavam os limiares de triagem dHash ≤ 7 e
pHash ≤ 10. Isso constitui **falso negativo demonstrado por inspeção
visual e alinhamento geométrico** para a regra de triagem global.

## Deliberação pré-F1

- **`4113_left_0082`: EXCLUDE_PRIOR_EXPOSURE.** A imagem/reprodução da
  mesma cena entrou na UDED de desenvolvimento exploratório; não pode ser
  tratada como amostra confirmatória independente.
- **`4113_left_2396`: HOLD_SHARED_CAPTURE_PREFIX.** Aparenta outra
  cena pela prancha, mas o identificador 4113 é compartilhado. Não
  declarar que seja a mesma cena; mantê-la fora da seleção provisória
  até revisão de proveniência da captura.
- **Demais MultiCue:** `PENDING_HISTORY_AND_VISUAL_REVIEW`. Não
  transformar ausência de alertas em certificação. A prudência de
  no máximo uma sequência por prefixo permanece, inclusive 4108.

Estas decisões não foram influenciadas por GT ou F1. Nenhuma coorte está
congelada; o arquivo de decisões é
[`multicue_predata_exclusion_decisions.csv`](multicue_predata_exclusion_decisions.csv).

## Próximo teste: verificar os 100 originais com SIFT + RANSAC

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\tests\test_paper_a_multicue_mdbd_geometry.py
python .\scripts\audit_paper_a_multicue_mdbd_geometry.py
```

Dependência: `cv2` e `numpy` no Python que executa a auditoria. Se
`cv2` não estiver disponível, **não atualizar indiscriminadamente o
ambiente global**: preparar ambiente isolado apropriado.

O script lê apenas originais RGB já materializados no F:, confirma
novamente SHA-256 de seus manifestos e avalia correspondências locais
com RANSAC. Relatório em
`F:\MFI-Edge-Data\MultiCue\multicue_uded09_geometric_overlap_summary.json`.
Não lê ground truth, H5, mapas, predições nem F1. Não exclui
automaticamente nenhuma imagem. Um SIFT negativo não descarta
cenas de outros quadros ou grandes mudanças de aparência.

**Próximo gate pendente:** auditoria por cena e captura dos demais
originais históricos, verificação de tarefa/GT e análise de poder
antes do freeze de H1/H2.
