# Retriação completa de 2.700 pares com matching exato recíproco — 15/11/2026

## Por que esta etapa é necessária

O diagnóstico dos 25 alertas SIFT/FLANN retornou um resultado inequívoco
para as imagens visíveis examinadas: o único par confirmado, UDED
`09-MDBD-1C` × MultiCue `4113_left_0082`, manteve **2.100/2.100
matches recíprocos válidos**, com inliers espacialmente distribuídos.
Os alertas visuais espúrios mais fortes caíram de 277, 267, 195 e
131 inliers FLANN para **zero** após BF exato, Lowe 0,70 em ambas as
direções e teste de reciprocidade.

Isso mostra que **o matching aproximado anterior não é um filtro confiável**,
sem certificar que a causa raiz seja exclusivamente a aproximação FLANN.
Os 2.675 pares não reexaminados anteriormente precisam de retriagem para
controlar possíveis falsos negativos.

## Script com checkpoints e reaproveitamento

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\tests\test_paper_a_full_exact_mutual_rescreen.py
python .\scripts\rescreen_paper_a_multicue_uded_exact_mutual.py
```

A execução usa somente características SIFT já armazenadas no F:,
com SHA256 e versão OpenCV validados, e **não decodifica novamente
imagens ou GT**. Os 25 pares que já passaram pela comparação BF exata
são reaproveitados, sem novo cálculo. Os outros 2.675 passam por
Lowe 0,70 bidirecional + BF exato e homografia RANSAC.

Cada uma das 27 referências UDED tem checkpoint em
`F:\MFI-Edge-Data\MultiCue\predata_exact_mutual_rescreen\`,
atualizado atomicamente a cada 10 pares. Se interrompido, execute
o mesmo comando para retomar sem reprocessar pares salvos.

Opcionalmente, `--reference-limit 1` conclui apenas uma referência
para verificar o fluxo de retomada. Nesse caso o status é explicitamente
`PARTIAL_EXACT_MUTUAL_SCREEN_NO_CONCLUSION`, e o relatório não pode
fundamentar congelamento da coorte.

Resultados completos:

- `F:\MFI-Edge-Data\MultiCue\multicue_all_uded_exact_mutual_summary.json`
- `F:\MFI-Edge-Data\MultiCue\multicue_all_uded_exact_mutual_pairs.csv`

**Gates ainda abertos:** verificação de exposição a outras versões/quadros,
independência por prefixo, compatibilidade de GT para as duas tarefas,
análise de poder e commit de freeze. Nenhum F1 de confirmação será aberto
nesta etapa.
