# MFI-Edge — Stage 24G–24L: recertificação do Paper A

**Estado:** implementação publicada; execução científica na workstation pendente.
**Branch:** mfi-edge-stage24-residual-suppression. A Stage 24 encerrada em 36h57min permanece imutável.

## Perguntas centrais

1. Qual o impacto da correção geométrica dos GTs?
2. Quais descritores individuais, pares e triplas são realmente complementares?
3. Quanto cada agregador — OWA, Sugeno, Choquet clássico, Choquet 2-aditivo e variantes — melhora frente a controles sobre as mesmas evidências?
4. A supressão melhora F1 quando testada contra identity no mesmo fold?
5. Qual o efeito de bordas finas por NMS e afinamento?
6. Quais resultados transferem de UDED para BSDS e detectores externos Compass/SCO/SED/QFrD?
7. Que claims do Paper A sobrevivem à recertificação?

## Contratos de integridade

- GT UDED nativo, inalterado, nunca reduzido para treinamento/avaliação.
- Descritores na escala de trabalho max-side 256; score float registrado para geometria nativa.
- Arquivos NPY float32 e SHA-256; PNG somente adaptador da avaliação oficial.
- Matching UDED one-to-one máximo-cardinalidade, distância Euclidiana e tolerância nativa.
- BSDS multi-anotador: Berkeley MATLAB oficial com thinpb=true.
- 15 outer folds (5 repetições, 3 partições). Toda seleção de descritores, memberships, capacidades, gates, threshold, thinning e suppressor acontece em treino; promoção usa 3 inner folds.
- O resultado de cada candidato em outer-heldout é só avaliação. **Não usar o maior F1 held-out para decidir a receita congelada.**
- A receita congelada usa frequência de escolha da inner CV, sem olhar BSDS.
- Os 15 folds repetidos usam apenas 14 imagens distintas. Não tratar folds como observações estatísticas independentes.

## Etapas implementadas

| Etapa | Operação | Artefatos |
| --- | --- | --- |
| 24G0 | Todos os 78 pares pontuados por fold. Auditoria de geometria para pares prioritários com a MESMA fórmula Stage24 na geometria antiga e nova. Baseline held-out individual dos 13 descritores. | geometry_impact_stage24_proxy.csv, individual_descriptors_corrected_*.csv |
| 24G | Landscape de 19 agregadores: mean, min, max, product, logistic, OWA fixos/aprendidos, Choquet aditivo, 2-aditivo positivo e assinado, Choquet distorcido, quasi-arithmetic Choquet, Sugeno. | aggregator_landscape_fold.csv, aggregator_landscape_per_image.csv |
| 24H | Pares candidatos selecionados sem outer labels (top-K + relações históricas); triplas top-K + históricas. | pair_complementarity_*.csv, checkpoints por grupo |
| 24I | Ablações com identity, disagreement (.5/1), local coherence (2/4), compression (1.5) e learned gate (.5/1/2), e inner CV real. | suppressor_ablation_*.csv, inner_cv_trials.csv, receitas selecionadas |
| Thinning | Três tratamentos UDED: raw, nms_image, binary_thin_diagnostic. | Comparação controlada por grupo, agregador e fold |
| 24J | Requer mapas NPY float32 nativos dos detectores da literatura; reavalia baselines e combinações no UDED, exporta BSDS somente com 100 float maps verificados. | literature_transfer_guard.json, resultados de literatura |
| 24K | Congela melhor receita train-only e controle identity, aplica BSDS Berkeley val e incumbent compacto. | frozen_models.json, official_eval_manifest.json, official_bsds_summary.json |
| 24L | Análise pareada por imagem, Wilcoxon/Holm e status dos claims. | statistical_tests_exploratory.csv, claim_status.csv |

### Afinamento incorporado

- **raw:** score agregado (ou suprimido) -> threshold -> one-to-one.
- **nms_image:** score agregado -> Non-Maximum Suppression orientado pelo gradiente da imagem nativa -> threshold -> one-to-one.
- **binary_thin_diagnostic:** score -> threshold -> thinning binário morfológico Python -> one-to-one. É diagnóstico UDED, não método oficial.
- **BSDS:** exportação de score e aplicação do thinpb=true pela rotina oficial Berkeley. Não se deve equiparar o thinning morfológico Python ao Berkeley.

Somente raw e nms_image podem ser escolhidos na receita transferível ao BSDS. O modo binary_thin_diagnostic continua na tabela fatorial como controle.

### Variantes matemáticas e fidelidade ao Paper A

- Choquet positivo 2-aditivo usa Möbius de ordem até 2 não negativo.
- Choquet assinado 2-aditivo usa restrições de monotonicidade e normalização na otimização.
- Choquet distorcido usa capacidade simétrica v(S) = (|S|/n)^0,55.
- Choquet generalized_055/150 usa quasi-arithmetic Choquet com transformação potência e inversa.
- Sugeno opera com capacidade válida.
- OWA median corresponde à mediana exata, particularmente relevante para três evidências.
- **IMPORTANTE:** essas variantes são implementações matemáticas explícitas; não presumir que reproduzem as generalizações originais da tese ou o incumbent histórico sem auditoria equação-por-equação. O incumbent é incluído no Berkeley como referência contextual.

## Comandos Windows PowerShell

Na raiz do projeto:

~~~powershell
git switch mfi-edge-stage24-residual-suppression
git pull --ff-only origin mfi-edge-stage24-residual-suppression
.\.venv\Scripts\python.exe tests\test_stage24_recertification.py
.\run_stage24_paper_a_recertification.bat --phase preflight
.\run_stage24_paper_a_recertification.bat --phase all
~~~

A campanha pode ser custosa. Checkpoints por grupo e fold ficam em results/local_dev/stage24_paper_a_recertification/folds/.

Smoke de um fold, sem alegação científica:

~~~powershell
.\run_stage24_paper_a_recertification.bat --phase g --max-folds 1 --top-pairs 1 --top-triples 0
~~~

Parada segura durante os folds:

~~~powershell
.\stop_stage24_paper_a_safely.bat
~~~

Retomada (mantém os grupos já concluídos):

~~~powershell
Remove-Item .\automation\STOP_STAGE24_PAPER_A -ErrorAction SilentlyContinue
.\run_stage24_paper_a_recertification.bat --phase all
~~~

Execução oficial isolada após freeze:

~~~powershell
.\run_stage24_paper_a_recertification.bat --phase k
~~~

Depois de concluído, arquive resultados científicos curados:

~~~powershell
.\.venv\Scripts\python.exe scripts\prepare_stage24gl_paper_a_archive.py --stage
git --no-pager diff --cached --stat
git status --short
# Confira o manifesto antes do commit.
git commit -m "results: archive Stage24G-L Paper A recertification"
git push origin HEAD
~~~

Evite comandos Git com paginador, especialmente se o terminal não suportar a tecla Q.

## Manifesto opcional de detectores da literatura

Arquivo external/literature_float_manifest.json, uma lista JSON:

~~~json
[
  {
    "dataset": "UDED",
    "split": "selection_overlap_clean",
    "method": "Compass",
    "image_id": "01-0843x4",
    "score_path": "external/float/compass/uded/01-0843x4.npy",
    "sha256": "HASH_REAL_DO_ARQUIVO_NPY"
  },
  {
    "dataset": "BSDS500",
    "split": "val",
    "method": "Compass",
    "image_id": "101085",
    "score_path": "external/float/compass/bsds_val/101085.npy",
    "sha256": "HASH_REAL_DO_ARQUIVO_NPY"
  }
]
~~~

Precisa de todos os 14 UDED e todos os 100 BSDS val para cada detector transferido. O script valida sha, dtype, forma e geometria nativa; dados 8-bit PNG legados são rejeitados como origem científica.

## Outputs e preservação

- results/local_dev/stage24_paper_a_recertification/: resultados da nova campanha, folds e modelos.
- results/official_eval/stage24_paper_a_recertification/: Berkeley MATLAB detalhado.
- results/paper_a_evidence/stage24gl/: pacote curado (gerado pelo arquivador) para commit.

Não comitar dados de imagens, GTs, modelos binários enormes, score caches NPY, temporários MATLAB e fontes vendorizadas. Preserve hashes e manifestos.

## Claims que continuam bloqueados sem evidência adicional

1. A Stage24G0 compara **a fórmula Stage24** no GT antigo vs nativo; não reproduz automaticamente o score Stage23D original. Para claims sobre variação do score Stage23D, portar a fórmula original com os mesmos descritores e condições.
2. Os operadores generalized Choquet devem ser confrontados com as equações exatas do manuscrito antes de reivindicar equivalência.
3. O incumbent BSDS compact Choquet é referência contextual; o retreinamento específico do incumbent no UDED corrigido não está provado por esta comparação.
4. A literatura permanece guardada até chegarem os scores originais author/native float.
5. A avaliação oficial BSDS val é desenvolvimento. Reference reproduction independente e teste multi-benchmark protegido continuam exigidos para claims finais.
6. A escolha de um suppressor não comprova melhoria; somente ablações pareadas held-out e transferência externa podem fazê-lo.

O plano foi implementado para **produzir** evidência científica e relatar ausências de maneira transparente, não para transformar resultados ainda não executados em conclusões.
