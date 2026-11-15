# Stage 24G-L — status para Paper A

Os GTs nativos foram preservados; as comparacoes de agregadores e suppressors usam os mesmos folds e thresholds ajustados somente no treino.

A recertificacao inclui raw, NMS orientado pela imagem e thinning binario apenas diagnostico UDED. O BSDS continua com thinpb=true oficial; nao equiparar os algoritmos de afinamento.

Os scores Stage23D e Stage24 usam formulas diferentes; G0 isola geometria somente na formula Stage24.

Os testes estatisticos usam medias por imagem entre repeticoes e sao exploratorios; os folds repetidos nao sao 15 observacoes independentes.

O BSDS val e desenvolvimento. Sem reproducao independente de referencia e teste protegido multi-benchmark, SOTA/final claims estao bloqueados.

Consultar claim_status.csv, final_claim_guard.json e literature_transfer_guard.json.
