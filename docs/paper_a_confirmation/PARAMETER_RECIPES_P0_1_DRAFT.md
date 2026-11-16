# P0.1 — manifesto H1/H2 sem F1, ainda não congelado

## Resultado esperado

Este passo monta um **rascunho rastreável** para H1 e H2,
respeitando as definições existentes de grupos, operadores e sentido
das duas hipóteses. Não lê resultados históricos nem o conteúdo de
`frozen_models.json`; nenhuma capacidade, limiar ou calibração é inventada.

Cada hipótese tem um único conjunto compartilhado de parâmetros
de membership `legacy_sigmoid` (midpoint/scale) usado pelo candidato
e pelo controle `equal_mean`. São documentados limiares separados
para candidato e controle, ajustáveis apenas em desenvolvimento.
A H2 exige ainda uma capacidade de Choquet 2-aditiva válida
(8 coeficientes de capacidade e 6 de Möbius), gamma 1,5 fixo.

O manifesto registra SHA256 de códigos científicos e do protocolo,
além do commit Git. Os campos desconhecidos ficam `null`.
Documentos antigos contendo F1 de desenvolvimento **não são abertos**.

## Executar em PowerShell

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
.\.venv\Scripts\Activate.ps1
python .\tests\test_paper_a_h1h2_recipe_P0_1.py
python .\scripts\prepare_paper_a_h1h2_recipe_P0_1.py
```

Rascunho gerado em:
`F:\MFI-Edge-Data\MultiCue\paper_a_H1_H2_recipe_P0_1_DRAFT.json`

Para verificar o próprio rascunho:

```powershell
python .\scripts\prepare_paper_a_h1h2_recipe_P0_1.py `
  --check "F:\MFI-Edge-Data\MultiCue\paper_a_H1_H2_recipe_P0_1_DRAFT.json"
```

A verificação inicialmente reportará `P0_1_DRAFT_INCOMPLETE_NOT_FROZEN`
e campos ausentes, **comportamento esperado e seguro**.
A revisão de schema rejeita campos F1 inesperados, mudança de hipótese
ou de hash de código, capacidade não monotônica e escala não positiva.

## Próximo gate, sem reprocessamento automático

Localizar uma exportação **independente de F1** dos parâmetros
ajustados exclusivamente sobre dados permitidos de desenvolvimento:
membership de cada grupo, capacidade H2 e os quatro limiares.
Verificar hashes de dados e processo de ajuste antes de preencher
valores. Um manifesto completo não é automaticamente certificado:
a verificação independente de proveniência e o freeze formal
continuam obrigatórios.

**Nenhuma leitura de GT/H5/mapas/F1 ou cálculo confirmatório ocorre
neste script.** O `protocol.json` permanece `draft_not_frozen`.
