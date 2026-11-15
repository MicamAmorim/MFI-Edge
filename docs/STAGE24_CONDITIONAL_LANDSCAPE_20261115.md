# MFI-EDGE — análise exploratória do landscape condicional

**Data da leitura:** 15/11/2026  
**Fonte científica:** branch `mfi-edge-stage24-residual-suppression`, HEAD `435e557`  
**Natureza:** reanálise de resultados arquivados; **não** é uma nova campanha nem uma validação confirmatória.

## 1. Pergunta científica

Em vez de decidir qual agregador tem melhor F1 **médio**, investigamos se existem subconjuntos de imagens nos quais a mesma combinação descritor–agregador apresenta ganhos ou perdas em relação a um controle idêntico. Depois examinamos, exploratoriamente, características dos mapas de descritores que possam estar associadas a esses regimes.

Para um grupo de descritores `g`, operador `a` e imagem `i`, calculamos

\[
\Delta_{i,g,a}=\overline{F1}_{i,g,a}-\overline{F1}_{i,g,\mathrm{equal\_mean}}.
\]

Cada média corresponde aos cinco resultados *held-out* da mesma imagem nos folds repetidos. **A amostra é de 14 imagens, não 70 observações independentes**. Comparações aqui incluídas preservam conjunto de descritores, `nms_image`, supressor `identity` e calibração `legacy_sigmoid` na UDED. O resultado de uma configuração selecionada retrospectivamente por imagem é apenas um *oráculo descritivo*.

## 2. Inventário verificado

- 14 imagens UDED distintas, com cinco resultados de avaliação externa por imagem.
- 13 descritores individuais e sete grupos de descritores presentes em todas as imagens.
- 195 candidatos de cobertura comum, incluindo os 13 individuais; 26 nomes de operadores ao longo dos grupos.
- Aliases algébricos foram reunidos: por exemplo, mediana de duas entradas e média aritmética, `owa_optimistic` e `maximum`. Conferi que as diferenças observadas entre as implementações equivalentes eram zero nos dados comparados.
- As tabelas consolidadas derivam de `common_candidate_scores.csv` e `image_features.csv`, já presentes no pacote arquivado.

## 3. Resultados: ganhos e perdas coexistem

| Conjunto de descritores | Agregador | Controle | Ganhos/perdas (imagens) | ΔF1 médio | Mín. / Máx. ΔF1 |
|:--|:--|:--|--:|--:|--:|
| Gabor persistente + half-disc | Máximo | Média | 7 / 7 | −0,0094 | −0,2490 / +0,1548 |
| Gabor persistente + half-disc | Logística não negativa | Média | 11 / 3 | +0,0290 | −0,1123 / +0,1624 |
| Half-disc + Hessiana s7 | Choquet 2-aditivo assinado | Média | 11 / 3 | +0,0329 | −0,0410 / +0,0930 |
| Gabor persistente + PMI + coerência | Mediana | Média | 12 / 2 | +0,0158 | −0,0297 / +0,0752 |
| FH + half-disc | Média | **Melhor componente retrospectivo por imagem** | 11 / 3 | +0,0490 | −0,1152 / +0,1746 |

A última linha usa um **controle diferente** das demais. O melhor componente por imagem é escolhido após observar seu desempenho, portanto é um limite descritivo, não um comparador prospectivo treinado de forma equivalente.

### Inversão particularmente informativa

Para o mesmo par Gabor persistente + half-disc, mantendo a média como referência:

- Na imagem `01-0843x4`, o **máximo perde 0,2490 F1** e a logística **ganha 0,0934**.
- Na imagem `23-img_011_SRF_2_HR`, o **máximo ganha 0,1548 F1** e a logística **perde 0,1123**.

Isso é uma inversão considerável da preferência entre operadores **sem trocar o conjunto de descritores**. É evidência descritiva de heterogeneidade do desempenho por imagem, não evidência de que uma propriedade específica dos mapas já explique a inversão.

## 4. Estabilidade da ordenação dos operadores entre imagens

Foram comparadas, para cada grupo fixo, as ordenações dos operadores nas 14 imagens, reunindo aliases matemáticos e computando as 91 correlações entre pares de rankings de imagens. Valores negativos indicam inversões relativas de preferência entre operadores.

| Grupo | Nº operadores distintos | Modal retrospectivo | % de imagens em que foi vencedor | Spearman médio | % pares de imagens com Spearman negativo |
|:--|--:|:--|--:|--:|--:|
| FH + half-disc | 21 | Łukasiewicz | 50,0% | 0,652 | 0,0% |
| FH + half-disc + coerência | 22 | Choquet generalizado 1,5 | 35,7% | 0,842 | 0,0% |
| **Gabor persistente + half-disc** | 21 | Łukasiewicz* | 35,7% | **0,244** | **36,3%** |
| Gabor persistente + PMI + coerência | 22 | Mediana | 57,1% | 0,618 | 0,0% |
| Gabor persistente + coerência | 21 | GCF CL/CL | 42,9% | 0,399 | 17,6% |
| Half-disc + Hessiana s7 | 21 | GCF TP/TL | 28,6% | 0,434 | 20,9% |
| Half-disc + PMI | 21 | Mínimo | 28,6% | 0,665 | 0,0% |

\* O primeiro lugar no par Gabor persistente + half-disc está empatado entre Łukasiewicz e GCF CL/CL, com cinco imagens para cada. A tabela apresenta um deles. Essas modas são resultados de seleção retrospectiva, não de uma política validada.

**Interpretação:** alguns conjuntos exibem ordenações bastante estáveis, outros apresentam inversões expressivas. Logo, não seria correto sustentar que todo landscape é instável; a própria **intensidade da dependência da imagem parece variar conforme o conjunto de descritores**.

## 5. Primeira busca de padrões nas características já extraídas

No caso Gabor persistente + half-disc, a correlação de Spearman entre ΔF1 do **máximo vs média** e a **média da magnitude do gradiente dos dois mapas** foi cerca de **+0,50** (14 imagens). Para FH + half-disc, o ganho da **média vs melhor descritor individual retrospectivo** apresentou correlação de aproximadamente **−0,73** com a média das respostas dos dois mapas.

São apenas **associações exploratórias pós-hoc** examinadas entre múltiplas características disponíveis, sem correção por multiplicidade. Podem ser influenciadas por observações extremas e por propriedades do controle escolhido. Não permitem afirmar que maior gradiente *cause* ganho do máximo nem que a intensidade média seja uma regra preditiva.

O ponto fundamental é que os 78 atributos pré-extraídos descrevem principalmente **cada mapa individualmente**. Ainda faltam variáveis diretamente relacionadas à interação espacial, como coativação e exclusividade das respostas fortes, concordância ponto a ponto e correlação entre mapas. Esse é o passo analítico que melhor testa a motivação científica do Paper A.

## 6. Verificação adicional do BSDS500 por imagem (concluída)

Foi possível recuperar integralmente o blob textual de `per_image_threshold_counts.csv` (Git SHA `a25e5a66ff0b465b0c0592ca50add383f5b8d368`) e analisar suas **79.200 contagens Berkeley**: oito métodos, 100 imagens, 99 limiares por imagem/método. A reconstrução usa precisão `cntP/sumP`, revocação `cntR/sumR` e sua média harmônica.

Cada método é avaliado no limiar discreto **mais próximo do seu próprio ODS registrado**. Como ODS veio do mesmo split validation, estes são contrastes por imagem para investigação, não avaliação prospectiva e **não equivalem aos deltas de ODS agregado**.

| Comparação | Nº imagens favoráveis | Nº desfavoráveis | ΔF1 médio por imagem | Intervalo dos ΔF1 observados |
|:--|--:|--:|--:|--:|
| `identity` contra incumbent Choquet | **90** | 10 | **+0,0378** | −0,1396 a +0,1316 |
| `winner` contra incumbent Choquet | 38 | 62 | −0,0230 | −0,2569 a +0,1004 |
| **`winner` contra `identity`** | **9** | **91** | **−0,0608** | −0,2629 a +0,0600 |
| `best_single` contra incumbent Choquet | 70 | 30 | +0,0218 | −0,2219 a +0,2069 |
| Par 04 logística contra Par 04 média ponderada | 54 | 46 | −0,00004 | −0,0064 a +0,0087 |

Para `winner – identity`, as maiores **vantagens** por imagem ocorreram em `302008` (+0,0600), `69040` (+0,0255), `227092` (+0,0209). As maiores **perdas** ocorreram em `196073` (−0,2629), `65033` (−0,1729), `78004` (−0,1559). Esses IDs são bons casos para inspeção espacial posterior, mas foram selecionados **após** observar os resultados.

A perda com supressão não está concentrada em um único conjunto de imagens: particionando em três faixas de `sumR` (volume de anotações humanas na avaliação Berkeley), `winner` perdeu para `identity` em **32/33**, **28/33** e **31/34** imagens. Essa estratificação usa uma quantidade derivada das anotações, e não uma característica GT-free do mapa; é só um diagnóstico de distribuição do efeito.

**Interpretação importante:** a hipótese de compensações entre ganhos e perdas se aplica claramente a certas comparações UDED. Já no contraste BSDS entre `winner` e `identity`, o efeito desfavorável é disseminado (91/100), não apenas uma média anulada por alguns poucos casos. Mesmo assim, nove imagens favorecem o `winner` e podem ser inspecionadas para buscar um regime de supressão útil, sem generalizar esses casos retrospectivos.

O repositório ainda registra **700 mapas float** de sete variantes finais no BSDS. O script acompanhante verifica SHA256 dos `.npy` existentes e mede dispersão, gradiente, fração positiva e alterações de score entre `winner` e `identity`. Esses mapas são **predições agregadas finais**: não substituem necessariamente os **13 mapas de descritores individuais** por imagem. Não devemos declarar características da complementaridade espacial interna no BSDS sem esses mapas de entrada.

## 7. Arquivos de análise e execução sem reprocessar

O script `analisar_landscape_condicional.py`:

1. Reconstrói todos os contrastes **modelo × imagem** a partir dos dados já consolidados.
2. Exporta rankings e instabilidade das preferências por imagem.
3. Correlaciona os ganhos com os atributos marginais já extraídos, explicitamente como análise exploratória.
4. **Quando disponível no PC**, lê apenas os 182 mapas UDED `.npy` existentes, verifica SHA256 e calcula concordância/exclusividade espacial das ativações superiores, sem carregar GT ou rodar detectores.
5. **Quando disponível no PC**, analisa as 79.200 contagens Berkeley preexistentes por método/imagem/limiar e também os 700 mapas de predição float finais para examinar regimes favoráveis e desfavoráveis no BSDS.

Comando na raiz do projeto:

```powershell
python "<CAMINHO_DO_SCRIPT>\analisar_landscape_condicional.py" --research-root . --out .\analise_condicional
```

Opcionalmente, `--no-maps` permite executar somente a análise tabular; `--no-bsds` omite a etapa de contagens Berkeley. O script escreve em uma pasta de saída separada e **não altera os resultados originais**.

## 8. Próxima inferência científica defensável

A etapa que faltava não era escolher o vencedor do landscape: era examinar a **distribuição condicional dos ganhos**. A análise inicial encontrou inversões reais no conjunto de dados arquivado e também mostrou que a intensidade das inversões depende do grupo de descritores.

Ainda **não demonstramos** que as características dos mapas expliquem essas inversões. Para sustentar tal alegação serão necessárias: (i) análises espaciais dos mapas float congelados; (ii) inspeção de estabilidade a pontos extremos; (iii) definição de hipóteses explícitas antes de examinar novas imagens; e (iv) validação separada caso se pretenda fazer previsões.

Não é necessário recalcular modelos para obter as análises descritivas restantes, desde que os caches científicos originais estejam acessíveis.

## Fontes rastreáveis

- [Resultados da Stage24 — grupos de imagens](https://github.com/MicamAmorim/MFI-Edge/tree/mfi-edge-stage24-residual-suppression/results/paper_a_evidence/stage24_image_groups)
- [Manifesto Stage24G–L](https://github.com/MicamAmorim/MFI-Edge/blob/mfi-edge-stage24-residual-suppression/results/paper_a_evidence/stage24gl/archive_manifest.json)
- [Protocolo de recertificação](https://github.com/MicamAmorim/MFI-Edge/blob/mfi-edge-stage24-residual-suppression/docs/STAGE24G_L_RECERTIFICATION_PLAN.md)