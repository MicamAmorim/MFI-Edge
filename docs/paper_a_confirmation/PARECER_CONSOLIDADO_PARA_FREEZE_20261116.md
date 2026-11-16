# Paper A — Parecer técnico-científico consolidado (16/11/2026)

**Decisão:** **NO-GO para abertura de GT confirmatório nesta data. GO para conclusão da preparação pré-freeze com os artefatos já existentes.** Este é um parecer de análise documental/código, **não** uma certificação independente da execução Windows, das cenas ou de H1/H2. Não foram abertos GT, H5, F1 nem novos mapas experimentais durante esta revisão.

## 1. Objetivo e hipótese operacional

O artigo testa se estatísticas **sem acesso ao ground truth** dos descritores predizem o benefício empírico de um agregador frente ao controle `equal_mean` em imagens inéditas. As hipóteses direcionais são:

- **H1**: X1 = |média(`halfdisc_distribution_contrast`) − média(`pmi_dependency_deficit`)|; alternativa de **Spearman negativo** entre X1 e `F1(maximum) - F1(equal_mean)`.
- **H2**: X2 = média das três correlações espaciais de Pearson entre `fh_region_boundary`, `halfdisc_distribution_contrast` e `structure_tensor_coherence`; alternativa de **Spearman positivo** entre X2 e `F1(choquet_generalized_150) - F1(equal_mean)`.

A seleção original das hipóteses foi exploratória (14 imagens UDED). Os rhos exploratórios não podem ser reclassificados como confirmação nem usados como previsão não viesada do poder.

## 2. Evidência concluída e reaproveitável

| Objeto | Evidência rastreável | Julgamento |
|---|---|---|
| Desenvolvimento P1 | `P1_DEVELOPMENT_FIT_20261116.md`, `P1_DEVELOPMENT_RECIPE_UNATTESTED.json`; SHA256 reportado `628d1e345b6d1117c3cbfbc6ecaf75d4cac8db6a7796d328e2ea911ce9891a9c` coincidente com original do F: à época | Fit finalizado sobre 14 UDED desenvolvimento, com limiares separados e capacidade Choquet internamente coerente; **sem atestado independente de linhagem** |
| Cache UDED desenvolvimento | Auditoria 56/56 SHA256 já executada | Não refazer descritores |
| BIPED | 200 train originais, 2 exclusões `RGB_172` e `RGB_222` conforme revisão visual | 198 candidatos; **independência por cena não certificada** |
| Exposição BIPED train | `HISTORICAL_BIPED_ADJUDICATION_20261115.md`: 14 refs remotas, 120 referências distintas, 40 metadados sem hash/ID coincidente | Ausência de evidência de uso para ajuste não equivale a prova de não exposição. `automation/stage13c_biped_preflight.py` **poderia ter aberto GT train para tamanho**, se executado |
| MultiCue | `MULTICUE_EXACT_MUTUAL_RESCREEN_RESULT_20261115.md`: 27×100=2700 pares testados via BF mútuo/RANSAC | Um par sobreposto UDED `09-MDBD-1C` × `4113_left_0082`; excluir **todo prefixo 4113** (inclusive `4113_left_2396`). No máximo 95 prefixos restantes |
| Anotações MultiCue | 100 âncoras H5, 600 nomes `edges`, 500 `boundaries` | Estrutura nominal correta; não certifica conteúdo, identidade de anotadores, definição de GT |
| F1 pareado | `src/paper_a_confirmation_paired_f1.py`, dez testes sintéticos aprovados na workstation | Um delta por original/captura com seis F1 separados no MultiCue; **não é Berkeley oficial** |
| Poder | `SAMPLE_SIZE_CONDITIONAL_DECISION_20261115.md`: 1000 repetições sintéticas | 125 BIPED + 95 MultiCue, poder conjunto ~82,3% em dois domínios com |rho|=0,20 homogêneo; hipótese do simulador, não resultado real |

## 3. Principal risco na validação GT

`scripts/execute_paper_a_frozen_cohort.py` contém um decodificador **restritivo**, que aceita PNG de máscara nativa 2-D `uint8` com pixels em {0,1} ou {0,255}, ou canais RGB idênticos com alfa opaco. **Não há evidência suficiente no registro para afirmar que todos os 600 PNG `edges` reais seguem esse contrato**, muito menos que a codificação de BIPED é semântica/equivalentemente comparável.

Recomendação: um revisor verifique com **documentação de formato inequívoca ou amostra de desenvolvimento independente da coorte**. Não abrir o GT protegido como "teste rápido" antes do freeze e não usar limiar 128, primeiro canal, união de máscaras, média das máscaras, redimensionamento de GT nem exclusão de máscaras problemáticas sem política prévia. Se o formato real diferir, revisar o protocolo e o decodificador **antes** da confirmação, repetir testes sintéticos e congelar o novo SHA.

Fontes gerais externas de estrutura de dataset, **não de codificação GT**:
- https://huggingface.co/datasets/Serrelab/multicue-boundary-detection
- Mély et al. (2016), *A systematic comparison between visual cues for boundary detection*, Vision Research 120:93–107.
- https://github.com/xavysp/MBIPED

## 4. Decisão amostral e inferência a congelar

**Proposta não vinculante, sob condição de elegibilidade:**
- 125 imagens BIPED independentes + 95 capturas MultiCue independentes = N220.
- Uma imagem original/cena por observação estatística; seis máscaras MultiCue são replicações de anotador, não seis imagens independentes.
- Seleção determinística pelo hash de candidatos *após* certificar independente cena e exposição anterior.
- Medida primaria: efeito Spearman **dentro do domínio**, média ponderada por `n_d-1`.
- Permutações de Y dentro de cada domínio (100000; seed predefinida), unilaterais H1<0 e H2>0; Holm na família de duas hipóteses; bootstrap estratificado, relatório completo de rhos por domínio.
- Se menos de 95 MultiCue aprovados, refazer **somente** a simulação para a composição alternativa, não imputar N220/poder 82,3%.
- Registrar critérios prévios para mapa constante (X2 indefinido), GT vazio, dados inválidos e empates; nenhum descarte pós-resultado por conveniência.

O `protocol.json` atual ainda diz `draft_not_frozen` e N150. O novo `PROTOCOLO_220_PROPOSTA_NAO_CONGELADO.json` (gerado no F: pelo script único) é **apenas proposta** e não altera/autoriza o protocolo principal.

## 5. Riscos e pendências prioritárias com critério de saída

1. **[BLOQUEIO CRÍTICO] Histórico operacional BIPED train:** confirmar em logs/manifestos locais se `stage13c_biped_preflight` foi executado, em que escopo, e se houve uso de GT além de dimensões; atribuir decisão justificada, por captura/cena. *Critério:* tabela por captura com `prior_exposure_review=pass` revisado de fato, ou exclusões explícitas.
2. **[BLOQUEIO CRÍTICO] Independência de cenas:** BIPED além dos dois pares visuais; MultiCue entre prefixos e quadros não finais, além da sobreposição 4113. *Critério:* um ID de captura independente por observação, parecer com justificativa e assinante.
3. **[BLOQUEIO CRÍTICO] GT/decoder:** testar política de codificação fora da confirmação, compatibilidade semântica `edges` com um GT BIPED e múltiplas anotações. *Critério:* documentação/testes, hash do avaliador e regra de erro fixada.
4. **[BLOQUEIO CRÍTICO] P1:** verificar `no_confirmatory_overlap_attested` (ainda nulo nas sete provas de ajuste), hashes da fonte, capacidade/membership, quatro thresholds sem resultados confirmatórios. *Critério:* receita assinada e fixada no freeze.
5. **[BLOQUEIO CRÍTICO] Protocolo / N / teste:** aprovar tamanho/composição, mínimo relevante, agregação por domínio, casos degenerados; atualizar protocolo em um commit de freeze distinto antes de GT. *Critério:* `frozen_cohort_manifest.csv`, `freeze_approval.json` com revisão responsável, hashes e git SHA coerentes.
6. **[PÓS-FREEZE] Executor real e inferência:** com gates verdadeiros, produzir uma linha X1/Y1/X2/Y2 por captura, conferir `certified_outcomes_provenance.json`, executar 100000 permutações/Holm; resultados podem legitimamente **não confirmar H1/H2**.
7. **[EDITORIAL] Manuscrito:** revisar interpretação, método, figuras e limitações; reproduzir tabelas de resultados, inclusive hipóteses negativas, com parecer numérico independente.

## 6. O que foi entregue para diminuir o retrabalho

O comando único `scripts/concluir_paper_a.ps1` reutiliza as auditorias e o controlador de etapas, não refaz mapas nem as 2700 comparações e gera, sem GT:

- `F:\MFI-Edge-Data\MultiCue\paper_a_completion\DOSSIE_CIENTIFICO_PRE_FREEZE.md`;
- `F:\MFI-Edge-Data\MultiCue\paper_a_completion\REVISAO_CIENTIFICA_PRE_FREEZE.json`;
- `F:\MFI-Edge-Data\MultiCue\paper_a_completion\PROTOCOLO_220_PROPOSTA_NAO_CONGELADO.json`;
- `F:\MFI-Edge-Data\MultiCue\paper_a_completion\COHORT_PROPOSAL_220_NOT_CERTIFIED.csv`;
- `F:\MFI-Edge-Data\MultiCue\paper_a_completion\NEXT_ACTIONS.md`.

**Conclusão final deste parecer:** não há falha matemática demonstrada na receita P1 ou nos testes sintéticos. As pendências são de **proveniência científica real, semântica de GT e assinatura prospectiva**. Aprovação automática ou resultados H1/H2 inventados descaracterizariam a confirmação. A revisão documental deixa a decisão pronta para auditoria independente, mas não transforma candidatos em elegíveis.
