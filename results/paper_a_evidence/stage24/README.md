# Stage 24 — evidencias para Paper A

Pacote gerado localmente sem rodar novamente a campanha.
Verifique archive_manifest.json e source_provenance.csv.

Arquivos principais:
- pair_scores_stage24_ranked.csv: ranking dos 78 pares com media, dispersao e frequencia.
- pair_scores_all_15_folds.csv: 1170 scores de treino por fold.
- folds/: 15 pair screens originais e 15 checkpoints.
- official_bsds/: resumo oficial e contagens Berkeley por imagem/threshold.
- stage24_additional/: manifest da geometria nativa e checkpoint.
- descriptor_cache_metadata/: identidade e SHA dos mapas float (sem .npy).
- preflight/: relatorios de integridade Stage24R0, se presentes.
- historical_stage23_NOT_CORRECTED/: registros antigos, identificados como legado.
- historical_stage23_OFFICIAL_validation_summaries/: summaries Berkeley antigos, se presentes.
- paper_a_evidence_gaps.json: metricas/ablacoes que AINDA NAO EXISTEM.

Os sete arquivos originais da Stage24 estao no commit 0c9af74 em
results/local_dev/stage24_residual_suppression.

ATENCAO: os scores Stage23D e Stage24 nao usam a mesma formula.
Nao calcule deltas numericos entre eles. Os dados Berkeley presentes
sao do split validation; a reproducao da referencia permanece pendente.
A consolidacao exclui os GTs, mapas float, PNGs, datasets e arquivos
temporarios. Os hashes ligam os registros aos arquivos originais locais.
