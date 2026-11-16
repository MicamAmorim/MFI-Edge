# Fechamento da triagem geométrica MultiCue × UDED — 15/11/2026

A execução real na workstation concluiu a retriagem dos **2.700 pares**
(27 imagens históricas UDED × 100 quadros originais finais esquerdos MultiCue)
com `EXACT_BF_Lowe070_BIDIRECTIONAL_MUTUAL_RANSAC4_v1`
e OpenCV `4.11.0`: **2.675 pares novos** e **25 reaproveitados**,
27/27 referências concluídas com checkpoints no disco F:.

**Resultado:** um único par foi sinalizado, já previamente identificado
visualmente: UDED `09-MDBD-1C` × MultiCue `4113_left_0082`,
com **2.100 matches recíprocos e 2.100 inliers**. Nenhum alerta adicional.

**Decisões preservadas:** `4113_left_0082` excluído por exposição
histórica; `4113_left_2396` em HOLD, com todo prefixo `4113`
fora da seleção provisória. Dos 96 prefixos de captura MultiCue, sobram
**até 95 grupos candidatos**, sem certificação completa de independência.

Isso permite **fechar a triagem destes 2.700 pares específicos** sem
repetir o processamento. Não demonstra independência de outros quadros
de vídeo, outras versões MultiCue/MDBD, cenas históricas não indexadas,
ou independência amostral de todos os prefixos.

A auditoria não leu GT/HDF5/F1 ou produziu inferência confirmatória.
O `protocol.json` permanece `draft_not_frozen`.

## Gates restantes

1. Independência entre grupos de captura e exposições históricas de
   cenas/quadros não cobertos, documentadas sem F1.
2. Definir ground truth e semântica *edges* versus *boundaries*,
   calibração e política fixa de matching/evaluação entre domínios.
3. Análise de poder que considere desenho, correlação por domínio,
   permutação e efeito mínimo cientificamente relevante.
4. Fixar seleção/hashes, implementação e freeze explícito, antes de
   abrir resultados H1/H2.
