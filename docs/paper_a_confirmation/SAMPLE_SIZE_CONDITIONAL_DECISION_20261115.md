# Paper A — decisão amostral condicional pré-freeze (15/11/2026)

**Status: PLANEJAMENTO, NÃO CONGELADO.** Esta nota registra decisões
tomadas exclusivamente a partir de simulações sintéticas
(`paper_a_domain_blocked_power.json`) e dos inventários sem GT/F1.
Não modifica `protocol.json`, que permanece `draft_not_frozen`.

## Dados efetivamente apresentados pela workstation

1. `scripts/estimate_paper_a_power_sensitivity.py`: 4 testes passaram;
   aproximação Fisher-z unilateral, não equivalente ao teste final.
2. `scripts/simulate_paper_a_domain_blocked_power.py`: 5 testes passaram;
   1.000 réplicas × 6 cenários × 5 desenhos, 20.000 sorteios nulos por
   desenho, semente 20261115.
3. Estatística **proposta**, não congelada: média de Spearman **dentro
   de domínio**, ponderada por `n_d - 1`; permutação bloqueada,
   hipóteses unilaterais e ajuste Holm de duas hipóteses. A análise
   confirmatória, se aprovada, ainda requer 100.000 permutações.
4. Nenhum GT/H5/F1, mapa ou resultado confirmatório foi aberto.

## Poder simulado para confirmar H1 e H2 **simultaneamente**

| BIPED + MultiCue | N | rho homogêneo 0,20 | rho homogêneo 0,25 | heterogeneidade 0,30/0,10 |
|---|---:|---:|---:|---:|
| 75 + 75 | 150 | 57,6% | 84,8% | 58,4% |
| 90 + 90 | 180 | 68,2% | 90,5% | 70,8% |
| 105 + 95 | 200 | 73,9% | 93,1% | 77,1% |
| 125 + 95 | 220 | **82,3%** | **96,0%** | **86,5%** |
| 145 + 95 | 240 | 85,6% | 97,3% | 92,2% |

**Atenção:** `power_both` é diferente dos poderes individuais de H1
e H2. A simulação modela apenas duas associações hipotéticas, sem
empates, sem dependências reais entre cenas e sem dados observados.
O pior caso com reversão 0,25/-0,10 teve poder conjunto de 3,0%
para N=150; não se deve presumir transferência entre os domínios.

## Recomendação atual (não vinculante)

- **Alvo preferencial condicional: N=220 (125 BIPED + 95 MultiCue)** se
  a pergunta científica exigir ~80% de probabilidade de confirmar
  AMBAS as hipóteses para `|rho|=0,20` em ambos os domínios,
  e **somente se** 125 grupos BIPED e os 95 grupos MultiCue forem
  independentes/elegíveis e a política de GT for compatível.
- **Plano com margem: N=180 (90 + 90)** se o efeito mínimo de interesse
  for `|rho|=0,25`, aceitando que no caso `|rho|=0,20`
  o poder conjunto simulado foi apenas **68,2%**.
- Se houver menos de 95 grupos MultiCue elegíveis, **não completar
  automaticamente com BIPED e alegar o mesmo poder**. Um desenho
  alternativo, como 130+90, precisa de sua própria simulação explícita
  e de justificativa de domínio/estimando antes do freeze.
- Se menos de 90 MultiCue elegíveis, avaliar alternativa com
  distribuição assimétrica ou domínio adicional, sem olhar F1.
- Não ampliar a amostra após ver p-valores/F1; a regra de elegibilidade,
  contingência e amostragem deve ser fixa ANTES da confirmação.
- Não ajustar tamanho a partir dos rhos exploratórios (|rho|~0,8);
  foram selecionados após múltiplos testes e não são expectativa de efeito.

## Gates prioritários antes da escolha irrevogável

1. **Unidade amostral:** auditar que os 198 BIPED candidatos representam
   capturas/cenas independentes e concluir a genealogia MultiCue/MDBD
   além dos 100 quadros finais. Prefixo 4113 permanece bloqueado;
   o teto atual é 95 *prefixos*, não 95 unidades certificadas.
2. **Anotação/avaliador:** escolher entre `edges` e `boundaries`
   no MultiCue; política de cinco/seis anotações e compatibilidade
   com o único GT BIPED, inclusive limiares, resize de predição
   (nunca de GT), tolerância e matching um-a-um.
3. **Modelo/congelamento:** fixar funções dos quatro descritores,
   calibração e capacidades de `choquet_generalized_150` no
   conjunto de desenvolvimento independente, com hashes, antes de
   calcular ganho F1 para H1/H2.
4. **Inferência:** decidir expressamente se estatística primária será
   global ou within-domain bloqueada (são estimandos diferentes),
   tratamento de empates/ausentes, sensibilidade por domínio,
   reamostragem por cena e poder sob heterogeneidade.
5. **Seleção determinística:** definir regra para caso faltem grupos,
   gerar manifesto com SHA de cada imagem e commit; só depois
   atualizar `protocol.json` e assinar o freeze.

**Próximo trabalho recomendado:** contrato de anotação/avaliação e
auditoria de grupos por captura, em vez de gerar novos mapas ou
recalcular os 30 cenários de poder que já foram produzidos.
