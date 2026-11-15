# Pré-registro H1/H2 — versão candidata 0.1 (não congelada)

## 1. Histórico e separação

O landscape exploratório Stage24 está registrado no commit `9957a0c1f4fcaadd0159c3c21ad6315f08f891a8`, pasta `analise_condicional/`. Os 14 IDs UDED da descoberta e as 100 imagens BSDS500 validation usadas em desenvolvimento não podem contribuir como observações confirmatórias. Os resultados observados, entre centenas de contrastes, motivam **apenas** as duas relações abaixo; os valores exploratórios de rho não são tamanhos de efeito esperados sem viés.

Este documento é um **rascunho pré-dados**: ainda faltam nomes e versões dos datasets confirmatórios, tamanho de amostra justificado por poder, resolução completa da auditoria de exposições e versão congelada da implementação. Os parâmetros em aberto não podem ser preenchidos depois de visualizar resultados confirmatórios.

## 2. Hipóteses primárias fixadas como candidatas

**H1 (sinal negativo)**: para mapas `halfdisc_distribution_contrast` e `pmi_dependency_deficit`, considere
`X1=|mean(D_halfdisc)-mean(D_PMI)|` e `Y1=F1(maximum)-F1(equal_mean)`, em cada imagem. Alternativa `Spearman(X1,Y1)<0`. Na UDED de descoberta, rho = -0.8065934.

**H2 (sinal positivo)**: para `fh_region_boundary`, `halfdisc_distribution_contrast` e `structure_tensor_coherence`, considere `X2` como a média das três correlações de Pearson entre os mapas float correspondentes, e `Y2=F1(choquet_generalized_150)-F1(equal_mean)`, por imagem. Alternativa `Spearman(X2,Y2)>0`. Na UDED exploratória, rho = +0.7802198.

As features são globais por imagem, exclusivamente derivadas dos mapas do detector, sem GT. Preservar geometria e transformação dos mapas (float32, resolução e normalização) é obrigatório. H1 e H2 são relativas a controles pareados de mesmos descritores, não ao melhor descritor individual e não ao oráculo.

## 3. Dados e prevenção de vazamento

Pretendemos dois domínios com 150 imagens distintas (mínimo 60 cada), sendo a decisão final condicionada a uma análise de poder **antes** de observar quaisquer Y1/Y2. O inventário de imagens e a escolha das bases devem ser fixados por hashes SHA256 e commit. Eliminar duplicatas exatas e fazer auditoria de quase duplicatas, casos derivados, sequências de vídeo correlacionadas e exposição prévia ao desenvolvimento. Imagens da mesma sequência, cena, objeto ou origem capturada não são independentes por definição: identificá-las e agrupar/retirar, com política pré-definida. A disponibilidade de anotações não autoriza consultá-las durante seleção da coorte.

## 4. Avaliação e contrastes

Aplicar o mesmo contrato Stage24 em ambos os membros de cada contraste: NMS, supressão identidade, `legacy_sigmoid`, geometria original do GT e matching um-a-um de cardinalidade máxima do avaliador Python (não rotular como Berkeley oficial). Fixar parâmetros de extratores, pesos e limiares em um conjunto de desenvolvimento/treino separado, antes de examinar o GT confirmatório. Em caso de adaptação estratificada por domínio, a política completa deve estar pré-definida e usar somente dados de treino. Nenhum limiar é escolhido individualmente pelo F1 da imagem confirmatória.

O resultado primário de cada imagem é exatamente `F1(operador candidato)-F1(equal_mean)`. Se houver múltiplas repetições/folds, resumir primeiro por imagem. Não reordenar operadores após ver as imagens.

## 5. Inferência e declaração

Duas hipóteses são primárias. Usar Spearman com postos médios, testes de permutação unilaterais na direção fixada, 100.000 permutações, semente 20261115, e Holm para controle de erro familiar a 5%. A forma da permutação (global ou bloqueada por domínio) precisa ser fixada **antes** de abrir resultados; quando houver heterogeneidade importante de domínios, preferir bloqueio pré-especificado. Relatar rho, p unilateral não ajustado, p ajustado de Holm, IC bootstrap por imagem (estratificado por domínio) e estatísticas em cada domínio como diagnóstico secundário.

Critério de confirmação de cada hipótese: sinal esperado **e** p ajustado de Holm < 0.05, sem exclusões condicionadas ao desfecho. Correlação diferente de zero não implica utilidade de seleção, causalidade ou melhora do detector.

## 6. Sensibilidades e análise negativa

Relatar influência leave-one-image-out, distribuição de Y, correlação por domínio, proporção de ganhos/perdas, calibração e qualidade individual. Tudo que surgir depois de observar os dados (novos operadores, outras features, novos recortes) é **exploratório** e deve permanecer fora da família primária. Se o resultado for não confirmatório, isso deve ser reportado, não reinterpretado como confirmação unilateral.

## 7. Política adaptativa, se confirmada

Apenas depois desta confirmação, abrir estudo separado para regra adaptativa. Aprender atributos, parâmetros e seleção somente com dados de treino; avaliar em teste verdadeiramente intocado, comparando com o melhor operador fixo selecionado no treino, `equal_mean` e o melhor descritor individual selecionado sem GT de teste. A margem prática de +0.010 F1 e IC pareado de 95% com limite inferior positivo é **proposta**, não sucesso previamente observado.

## 8. Registro e auditoria

A checagem de manifesto detecta campos ausentes, IDs repetidos, SHA inválidos, contagem por domínio e alguns IDs de descoberta. Ela **não** garante que o conjunto seja independente: a revisão de conteúdo, exclusão por fonte/cena e prova de não exposição histórica exigem procedimento documentado antes do congelamento. Nenhum GT de nova coorte foi lido por este commit.
