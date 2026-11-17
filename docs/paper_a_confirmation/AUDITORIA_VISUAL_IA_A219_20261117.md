# MFI Edge — auditoria ampliada e decisão pré-freeze

**17/11/2026 · Revisor: Codex AI · Versão 2, substitui a leitura de prontidão da primeira rodada.**

**Resultado: a A219 não pode ser congelada como 219 cenas inéditas e independentes.** A revisão computacional/visual encontrou repetição interna e sobreposição com cenas BIPED test já avaliadas no Stage13d. Não houve freeze nem abertura de GT/F1 da coorte confirmatória.

## O que foi feito autonomamente

- Conferidos os 219 originais por SHA256 e o ZIP dos 219 RGB, sem GT.
- Primeira rodada: 12.121 pares ORB intradomínio, 3.066 comparações ORB contra os 14 originais de treino P1 e inspeção visual do atlas de 219 imagens.
- Segunda rodada: **12.121 pares SIFT intradomínio**, a até 800×600, 1.200 keypoints, BF L2 exato, razão 0,72 mútua/bidirecional, RANSAC a 3 px, pelo menos seis inliers e fração 0,50. Dos 34 alertas, a revisão visual por IA julgou **31 relações de cena compartilhada e três falsos positivos**. Essas contagens são por par, não por imagem/cena. A SIFT recuperou relações que a ORB não tinha recuperado.
- **6.250 comparações SIFT** entre os 50 originais BIPED test e os 125 candidatos BIPED train. Dos 50 alertas, a inspeção visual julgou **47 relações claras, uma provável, uma inconclusiva e um falso positivo**.
- As 47 relações históricas atingem **43 candidatos train distintos**; por fechamento dos grupos de cena confirmados, **54 dos 219 originais** são retirados da proposta por sobreposição histórica. Outros **12** entram em quarentena por dúvida visual/histórica.
- Colapsar os grupos remanescentes por representante determinístico de menor SHA deixa um **rascunho de 140 unidades: 56 BIPED + 84 MultiCue**. Os 153 originais não excluídos/não quarentenados são anteriores ao colapso; não são 153 cenas. A proposta não é uma coorte certificada.
- Conferidas as três máscaras BIPED test previamente autorizadas, fora da A219: nos exemplos visuais inspecionados, 254 acompanha traçados de borda. A contagem total foi de 223 pixels 254; 158 estão a um vizinho 255 em janela 3×3, e a distância máxima observada até 255 é cinco pixels. Isso fundamenta operacionalmente tratar exatamente 254/255 como foreground, sem descobrir/otimizar cutoff no GT confirmatório. Não explica a origem do valor no exportador nem certifica máscaras não inspecionadas.
- Refeito o planejamento de poder com 10.000 réplicas por efeito e desenho e **100.000 permutações de referência de postos por desenho**, para o teste direcional bloqueado por domínio e Holm. Apenas dados sintéticos; sem imagens/GT/F1 reais nesse cálculo.

## Por que a história importa

O resumo real Stage13d registra avaliação de 50 imagens BIPED **test**, com limiares herdados e `training_split_used=false`. O código e o resumo não demonstram ajuste nos candidatos train. Entretanto, exemplos como **test RGB_102 × train RGB_101**, **test RGB_059 × train RGB_060** e **test RGB_170 × train RGB_171** mostram praticamente a mesma tomada/cenário. Uma divisão por nomes de arquivos não garante uma divisão por cenas.

A exclusão aplicada segue o critério do protocolo atual de não reutilizar cenas com exposição prévia em desenvolvimento/seleção/avaliação. Ela não é uma acusação de treinamento nos 43 arquivos train nem uma prova de vazamento de GT durante P1. O histórico de preflight Stage13c é distinto: abriu cabeçalhos GT train para dimensões; isso deve ser registrado como contato técnico.

## Poder e critérios do protocolo

| Desenho hipotético | N | Poder conjunto para \|rho\|=0,20 |
|---|---:|---:|
| A219 original (independência suposta, contradita) | 219 | 81,23% |
| Colapso mínimo da primeira rodada (não elegível após história) | 197 | 75,80% |
| Rascunho após história e quarentena (independência ainda suposta) | 140 | **55,69%** |

No rascunho 140, o intervalo Monte Carlo de 95% para 0,20 é 0.5471–0.5666. Para |rho|=0,25, o poder conjunto é 81.16%. Não se alterou o efeito relevante de 0,20 para 0,25 para tornar o estudo aparentemente adequado. A família sob efeito nulo rejeitou pelo menos uma hipótese em 5.04%, 5.59%, 4.81%, próximo do alfa 5% esperado nos três desenhos simulados. A referência de postos pode ser reutilizada sob postos contínuos sem empates; ela não é a execução de 100 mil permutações em cada uma das 10 mil réplicas.

O protocolo ativo ainda é draft, com alvo provisório N150 e mínimo **60 por domínio**; BIPED 56 fica abaixo desse mínimo. A política A219 de transição exige exatamente 125+94 e os hashes do roster original; o rascunho corrigido não satisfaz esse contrato. Forçar PASS ou mudar somente o campo N não constitui revisão científica.

## Evidência preservada e tarefas fechadas

P1 original e cópia C: seguem idênticas; as sete linhagens referem o digest UDED-14 reconstruído. Capacidade H2 monótona e coerente com Möbius. **79 testes técnicos passaram**; o ensaio estatístico artificial com 219 linhas, 100 mil permutações por H e 2 mil bootstraps está separado de qualquer resultado real. Os resultados desta segunda rodada são verificações de dados e desenho, não novas avaliações de detector.

## Próximo protocolo, antes de qualquer resultado

1. Preservar a A219 como proposta rejeitada e os 219 destinos individuais em `all_219_eligibility_dispositions.csv`.
2. Fechar os vínculos restantes e a auditoria operacional no escopo documentado. Não transformar ausência de alerta em garantia universal.
3. Completar uma nova amostra elegível com cenas realmente novas, ou justificar explicitamente outro desenho/poder antes dos desfechos. Não escolher amostra ou hipóteses pelo F1. A política A219 precisa de sucessora versionada e testada; não se deve desativar o guard atual.
4. Fixar GT v2 e casos degenerados, limiares/capacidades P1, composição, unidade de cena, inferência bloqueada e revisão responsável identificada como IA quando for IA.
5. Somente com o novo desenho válido: commit de freeze, primeira abertura de GT, quatro previsões/limiares fixos por unidade, médias de seis F1 MultiCue, 100 mil permutações, Holm e bootstrap; relatar inclusive resultados negativos.
6. Atualizar o manuscrito com a confirmação real; iniciar o modelo adaptativo apenas depois da análise confirmatória prevista.

## Limites e situação de publicação

As auditorias não recuperam execuções ausentes dos registros e não fornecem certificado humano independente. Não se inventou assinatura. O rascunho N140 não é um freeze e não substitui automaticamente o protocolo científico. A publicação dos quatro arquivos no repositório público foi novamente rejeitada pelo controle automático: ele considerou que a resposta genérica do usuário não especificava a divulgação de achados locais naquele destino. Não se tentou contornar a rejeição. As alterações de manuscrito e os payloads completos estão preparados localmente.

## Fontes e rastreabilidade

- [MFI Edge, branch de confirmação](https://github.com/MicamAmorim/MFI-Edge/tree/experiment/paper-a-conditional-confirmation).
- [BIPED, documentação dos autores](https://github.com/xavysp/MBIPED).
- [MultiCue, publicação oficial Serre Lab](https://huggingface.co/datasets/Serrelab/multicue-boundary-detection/blob/main/README.md).

Os resultados anteriores de ORB, a adjudicação inicial e o pacote ZIP original continuam preservados. Os CSVs da segunda rodada e o resumo numérico ficam em `followup/`. Todas as comparações visuais adicionais estão no HTML atualizado.

## Atualização efetiva do manuscrito local

A seção de proveniência do paper local foi atualizada, preservando o conteúdo anterior e um backup por SHA256. A cópia de trabalho LaTeX foi compilada em duas passagens, sem instalação de pacotes, produzindo um rascunho de 37 páginas; as páginas alteradas 34–35 foram renderizadas e conferidas visualmente. Esse PDF é o rascunho local atualizado, não um paper confirmado nem a publicação remota mais recente.
