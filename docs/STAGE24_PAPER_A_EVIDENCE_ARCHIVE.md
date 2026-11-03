# Stage 24 — preservação de evidências para o Paper A

## Por que isto existe

O commit de encerramento da campanha, 0c9af74, contém apenas sete arquivos
resumidos em results/local_dev/stage24_residual_suppression/. O Git ignora
results/local_dev/; os arquivos abaixo ficaram disponíveis apenas na máquina
em que a campanha de 36h57min foi executada.

Esta ferramenta **não** roda novamente a Stage 24, não altera resultados
originais, não treina detectores e não reexecuta MATLAB. Ela apenas copia ou
consolida evidências para results/paper_a_evidence/stage24/, uma pasta que
não está excluída pelo .gitignore.

## Inventário da evidência ausente

| Fonte local | O que recuperar | Saída curada |
| --- | --- | --- |
| Stage24/folds/r*_f*_pair_screen.csv (15 arquivos) | 78 scores de complementaridade por fold, 1.170 resultados | folds/ + pair_scores_all_15_folds.csv + pair_scores_stage24_ranked.csv |
| Stage24/folds/r*_f*.json (15 arquivos) | Receita, IDs de validação, TP/FP/FN e hash dos modelos selecionados | folds/ |
| Stage24/native_dataset_manifest.json | IDs, hashes e geometrias nativas UDED, exclusão deliberada de um caso | stage24_additional/ |
| Stage24/checkpoint.json | Estado final/resume da execução | stage24_additional/ |
| Stage24R0 preflight (relatórios de texto/CSV/JSON) | Testes de GT, matching e integridade | preflight/ |
| cache/local_dev/stage24/descriptors/**/*.json | Identidade, dtype, parâmetros, dimensões e hashes dos scores float | descriptor_cache_metadata/ + descriptor_float_cache_manifest.csv |
| cache/local_dev/stage23/manifests/*descriptor*.jsonl | Proveniência do cache anterior reutilizado, quando disponível | stage23_descriptor_cache_manifests/ |
| results/official_eval/stage24_residual_suppression/summary.json | Resultado separado do avaliador Berkeley | official_bsds/summary.json + method_metrics.csv |
| results/official_eval/stage24_residual_suppression/matlab/<método>/official_summary.json | Métricas originais de cada método | official_bsds/method_summaries/ |
| results/official_eval/stage24_residual_suppression/matlab/<método>/*_ev1.txt | Contagens por imagem/threshold, inclusive multi-anotador | official_bsds/per_image_threshold_counts.csv + per_image_source_manifest.csv |
| results/local_dev/stage23*/ (CSV/JSON pequenos selecionados) | Rankings e baselines históricos para comparação **rotulada como não corrigida** | historical_stage23_NOT_CORRECTED/ |
| Todos os itens copiados/consumidos | Hashes SHA-256 e caminhos de origem | source_provenance.csv, archive_manifest.json |

O script valida que existem **15 pair screens com 78 relações cada**; consolida
os 1.170 scores com média, desvio, mediana, mínimo, máximo, rank e frequência
de seleção. Para o Berkeley, valida o número de arquivos por método e os
**99 thresholds** esperados por imagem, com cinco colunas originais
(threshold, cntR, sumR, cntP, sumP). A evidência MATLAB original é
representada por seus valores numéricos e hashes; os arquivos binários
temporários não são adicionados ao Git.

## Lacunas que NÃO se resolvem apenas arquivando

A Stage 24 não produziu a seguinte evidência; o script sinaliza isso em
paper_a_evidence_gaps.json e **não inventa métricas**:

1. Tabela individual dos 13 descritores sob GT nativo + held-out matching.
   A Stage 23C tem avaliações individuais antigas, mas no protocolo anterior.
2. TP/FP/FN **por imagem** dentro dos folds, não apenas contagens totais.
3. Ablação held-out pareada da mesma receita com identity vs suppressor.
4. Comparação antiga/nova da mesma fórmula de complementaridade isolando GT.
5. Landscape completo Choquet/Sugeno/OWA e melhores triplas.
6. Rematerialização float/transferência dos detectores da literatura.
7. Reprodução independente registrada da referência Berkeley.
8. Gate final protegido de múltiplos benchmarks / BSDS test.

Os scores Stage 23D e Stage 24 **não** são diretamente comparáveis em magnitude,
pois são funções de pontuação diferentes. Também não se deve confundir a
frequência de seleção de pares com o score de complementaridade.

## Uso em Windows PowerShell

No checkout e na branch da campanha:

~~~powershell
git status
git pull --ff-only origin mfi-edge-stage24-residual-suppression
python scripts/prepare_stage24_paper_a_evidence.py --stage
git diff --cached --stat
git status
~~~

Inspecione pelo menos estes arquivos antes de commitar:

~~~powershell
Import-Csv .\results\paper_a_evidence\stage24\pair_scores_stage24_ranked.csv |
    Select-Object -First 15 | Format-Table -AutoSize

Get-Content .\results\paper_a_evidence\stage24\archive_manifest.json -Raw
Get-Content .\results\paper_a_evidence\stage24\paper_a_evidence_gaps.json -Raw
~~~

Depois do exame, publique somente o pacote curado:

~~~powershell
git commit -m "results: archive Stage24 pair screens, BSDS counts and Paper A provenance"
git push origin HEAD
~~~

O comando --stage executa apenas git add da pasta curada. Ele **não**
executa commit, push ou stage de outros arquivos. Se faltarem fontes
obrigatórias, o script cria um manifesto parcial e encerra com código 2,
sem efetuar stage, salvo quando --allow-incomplete for explicitamente usado.

Se o pacote curado já existir e você quiser gerá-lo novamente, passe
--replace; a ferramenta não apaga uma pasta anterior sem essa opção.

Para não arquivar os relatórios antigos da Stage 23, use --no-legacy.
A cópia da Stage 23 tem limite de 100 arquivos e 20 MiB; o inventário
informa eventuais itens que ultrapassarem o limite.

**Não adicione manualmente:** datasets, GTs, cache .npy de scores,
imagens PNG exportadas, pastas MATLAB de compatibilidade, binários MEX,
vendor sources ou outros dados volumosos. Mantenha os originais na
máquina e preserve backups externos apropriados.
