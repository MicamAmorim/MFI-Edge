# MultiCue vs. UDED 09-MDBD-1C — auditoria dirigida de linhagem (15/11/2026)

## Procedimento efetivamente executado na workstation

1. `tests/test_paper_a_multicue_mdbd_lineage.py`: **1 teste sintético aprovado**.
2. `scripts/review_paper_a_multicue_mdbd_lineage.py --top-k 12`:
   **`UDED_MDBD_LINEAGE_VISUAL_REVIEW_PENDING`**.
3. Imagem histórica: `external/UDED/imgs/09-MDBD-1C.png`,
   SHA256 `639aa076cb9ef7a59e19219f55ed21d930c299e4b8c92cc291251ea3d599bf9c`.
4. Comparação por hashes perceptuais das **100 imagens originais finais esquerdas**
   MultiCue (extraídas e validadas anteriormente), sem abrir H5, GT, predições, F1
   ou outros resultados confirmatórios.
5. Geradas duas pranchas locais para inspeção:
   `F:\MFI-Edge-Data\MultiCue\multicue_uded09_nearest_by_dhash.png` e
   `F:\MFI-Edge-Data\MultiCue\multicue_uded09_nearest_by_phash.png`.
   **A inspeção humana dessas pranchas ainda não foi documentada.**

## Resultado quantitativo — não conclusivo quanto à identidade das cenas

- 100 imagens MultiCue classificadas por proximidade perceptual.
- Nenhuma exclusão automática.
- Melhor distância dHash: **23 / 64 bits** — empates:
  `4113_left_0082`, `4592_left_0020`, `4208_left_0052`.
- Melhor distância pHash: **20 / 63 bits**, em `4638_left_0070`
  (nesse caso dHash = 26).
- Exemplos cruzados:
  `4113_left_2396`: dHash 26, pHash 24;
  `4491_left_0070`: dHash 27, pHash 22.
- Auditoria geral anterior: **0 pares sinalizados** nos limiares
  dHash ≤ 7 ou pHash ≤ 10, ao comparar os 100 originais MultiCue com
  27 originais UDED e 198 candidatos BIPED train. Três originais UDED com
  linhagem BSDS-test foram **intencionalmente excluídos de decodificação
  perceptual**: `03-35028.png`, `10-196062.png`, `22-335094.png`.

**Interpretação:** as distâncias não indicam correspondência evidente entre
`09-MDBD-1C` e as imagens **finais** amostradas do MultiCue. Isso NÃO
descarta origem da mesma cena em outro quadro do vídeo, transformação,
recorte ou outra versão do MDBD/MultiCue, nem comprova independência.

## Gate de confirmação — permanece fechado

- Amostra MultiCue: 100 sequências nominais, 96 grupos conservadores de
  prefixo, com `4108` e `4113` repetidos. Selecionar no máximo uma
  sequência por prefixo até revisão/documentação adicional.
- **Revisão visual ainda pendente:** anexar as duas pranchas para análise,
  comparar a imagem histórica `09-MDBD-1C` e registrar decisões por
  identificador de captura. Se persistir dúvida de linhagem, considerar
  revisão dos demais quadros **somente das sequências suspeitas** antes
  de recorrer a processamento global.
- **Nenhuma** imagem candidata promovida para a coorte, nenhum limiar do
  avaliador/operador alterado, protocolo ainda `draft_not_frozen`,
  nenhuma confirmação de H1/H2 executada.

Os CSV/JSON da auditoria completa ficam **locais** no F:; não incluir
imagens ou dados brutos no GitHub.
