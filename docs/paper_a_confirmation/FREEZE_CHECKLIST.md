# Checklist de congelamento (preencher antes de avaliar GT de confirmação)

Estado: **PENDENTE**. Sem assinatura/commit final, o estudo ainda não é confirmatório.

- [ ] Bases, versões, licenças, subdivisões e domínios identificados e registrados em `protocol.json`.
- [ ] Identificado o conjunto de desenvolvimento usado para escolher parâmetros e os respectivos hashes/commit.
- [ ] Auditadas todas as exposições históricas Stage23/Stage24, incluindo UDED descoberta e BSDS500 validation.
- [ ] Duplicatas SHA eliminadas; quase duplicatas e cenas/vídeos correlatos auditados sem usar GT/F1.
- [ ] Manifesto completo de originais confirmado, com hash por imagem, domínio, fonte, tamanho e revisão independente.
- [ ] Análise de poder/sensibilidade realizada sem usar resultados confirmatórios; N final aprovado.
- [ ] Parâmetros, versões e hashes do extrator dos quatro descritores, das funções agregadoras, da NMS, da calibração e do avaliador congelados.
- [ ] Limiar(es) escolhidos apenas no treino ou herdados de configuração de desenvolvimento já congelada; nunca no GT de confirmação.
- [ ] Especificado se a permutação será global ou por domínio, e como lidar com agrupamentos de imagens/cenas.
- [ ] Fixados teste unilateral por H1/H2, Holm, sementes, faltantes e avaliação do sinal.
- [ ] Script de validação executado; erros corrigidos e saída auditada.
- [ ] Atualizado `protocol.json` para `frozen` em commit novo antes de abrir qualquer resultado; hash da lista de imagens registrado.
- [ ] Identificado revisor da conformidade (pode ser auditoria independente por código) e registrado eventual desvio.

**Proibido:** chamar `draft_not_frozen` de pré-registro concluído, executar seleção por GT para decidir amostra ou reportar retrospectivamente p de múltiplas buscas como teste único.

## Condição amostral posterior à simulação (não é freeze)

- [ ] Decidir efeito mínimo relevante (0,20 versus 0,25 ou outro),
  sem usar resultados confirmatórios ou rho exploratório selecionado.
- [ ] Distinguir poder individual H1/H2 de poder conjunto H1+H2.
- [ ] Verificar se o desenho condicional 125+95 é realmente elegível;
  caso contrário simular explicitamente o desenho alternativo escolhido.
- [ ] Documentar por escrito qual estimando é primário: rho global ou
  rho dentro de domínio com pesos n_d-1 e permutação bloqueada.
- [ ] Fixar se MultiCue usa boundaries ou edges e como combina múltiplos
  anotadores antes de qualquer F1 confirmatório.
