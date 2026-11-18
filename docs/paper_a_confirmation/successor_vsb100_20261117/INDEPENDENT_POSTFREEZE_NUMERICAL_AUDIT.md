# RevisÃ£o numÃ©rica independente pÃ³s-freeze â€” MFI-Edge

**DecisÃ£o:** auditoria numÃ©rica passou; decisÃµes H1/H2 abaixo foram recalculadas independentemente e nÃ£o presumidas positivas.

Revisor: Codex independent agent /root/independent_vsb100_review. UTC: 2026-11-18T00:56:38.508356+00:00
Freeze local: `3faff3660043ee0b063f423c0801b0fc740568d7`. O snapshot foi congelado antes do GT; nÃ£o foi um prÃ©-registro pÃºblico.

Conferi as360identidades, a partiÃ§Ã£o312primÃ¡rias/48secundÃ¡rias, os360checkpoints/caches, hashes de fontes GT, todos os arrays, X1/X2 reconstruÃ­dos dos mapas congelados e mÃ©dias/deltas por anotador. NÃ£o ajustei modelo, limiar, populaÃ§Ã£o nem fontes congeladas.

| HipÃ³tese | rho ponderado | p unilateral | p Holm | IC95% bootstrap | deltaF1 mÃ©dio | DecisÃ£o |
|---|---:|---:|---:|---|---:|---|
| H1 | -0.137910168 | 0.0075199248 | 0.0150398496 | [-0.242751, -0.032544] | -0.011570 | Confirmada no teste fixado |
| H2 | -0.040302807 | 0.761092389 | 0.761092389 | [-0.151612, 0.072342] | 0.010899 | NÃ£o confirmada |

Reproduzi100.000permutaÃ§Ãµes bloqueadas por domÃ­nio,2.000bootstraps estratificados por hipÃ³tese e a correÃ§Ã£o Holm. O cÃ¡lculo independente usou SciPy Spearman como nÃºcleo e reproduziu contagens de permutaÃ§Ãµes extremas, p-valores e intervalos nos limites numÃ©ricos declarados.

Conferi tambÃ©m48F1 em quatro amostras nativas (uma por fonte, menor SHA RGB prÃ©-fixado antes de examinar resultados), usando construÃ§Ã£o de grafo por query_ball_point e matching Hopcroftâ€“Karp, diferente do solver Dinic congelado. Todas as quatro prediÃ§Ãµes e todos os anotadores dessas amostras concordaram. Isso Ã© auditoria amostral do pareamento, nÃ£o reavaliaÃ§Ã£o independente de todos os pixelsGT dos360casos.

A BIPED permaneceu secundÃ¡ria e nÃ£o contribuiu aos p-valores primÃ¡rios. Confirmar a associaÃ§Ã£o direcional nÃ£o exige deltaF1 mÃ©dio positivo, nÃ£o prova superioridade universal e nÃ£o valida um seletor adaptativo. Persistem limites de independÃªncia operacional de cenas/salas e de generalizaÃ§Ã£o entre fontes/granularidades de anotaÃ§Ã£o.

Hash do resultado auditado: `0e4ff50a6eb1538bf0d7f7c2279ad6dbccbe658b4a8072fb6c2fe3f419fa2868`. Hash da tabela pareada: `f3cee6cf14451d3e2815b17e75859893a5e37dbfe9e64587c2fab29d55acae7f`. Detalhes e contagens nativas no JSON independente anexo.
