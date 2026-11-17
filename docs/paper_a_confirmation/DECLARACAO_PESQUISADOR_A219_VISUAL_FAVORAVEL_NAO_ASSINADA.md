# Paper A — declaração do pesquisador sobre a revisão visual da coorte A219

**Data da declaração:** 17 de novembro de 2026  
**Natureza:** manifestação do pesquisador principal; não é parecer de revisor independente, assinatura digital, autorização de GT ou conclusão confirmatória.  
**Status documental:** `PARECER_PESQUISADOR_VISUAL_FAVORAVEL_NAO_ASSINADO`.

## Declaração formalizada

O pesquisador principal manifestou, após consultar o painel de revisão visual,
a opinião de que os itens apresentados foram satisfatórios e solicitou o
prosseguimento imediato à etapa estatística. Essa manifestação é registrada
como **parecer visual preliminar favorável**, sem acrescentar justificativas
específicas ou decisões individuais que não foram efetivamente entregues.

A seleção correspondente é a **proposta A**, composta por **125 imagens BIPED
e 94 capturas MultiCue (N=219)**. Os hashes de origem dos 219 arquivos foram
tecnicamente verificados antes desta declaração. Esse fato atesta integridade
de bytes, **não** independência estatística ou ausência de exposição histórica.

## Escopo e reservas expressas

1. A declaração não substitui a planilha de adjudicação das 219 linhas,
   inclusive as decisões antes divergentes em pares de cenas e os grupos
   visualmente relacionados.
2. O pesquisador não forneceu, nesta manifestação, prova documental de
   ausência de uso prévio em treino, desenvolvimento, calibração, seleção de
   parâmetros ou avaliações anteriores; a exposição ao GT técnico do
   Stage13c deve permanecer explicitamente descrita.
3. Os sete componentes de proveniência P1, o contrato GT v2 e a justificativa
   de poder estatístico aguardam certificação independente.
4. O relatório de poder conjunto estimado 0,815 para |rho|=0,20 é **sintético
   e condicional**, não uma observação de H1/H2.
5. Os arquivos `FINAL_INDEPENDENT_REVIEW.template.json`,
   `REVIEW_A_N219_ALL_PENDING.csv` e
   `FROZEN_PROTOCOL_BYTES_TO_REVIEW_NOT_ACTIVE.json` permanecem sem
   aprovação final. O protocolo versionado continua `draft_not_frozen`.
6. Este documento **não deve ser convertido automaticamente em PASS**, nem
   utilizado como `FINAL_INDEPENDENT_REVIEW.json`, nem como argumento
   para contornar `paper_a_freeze_guard.py`.

## Encaminhamento

O pesquisador solicitou avançar imediatamente para a etapa estatística.
O caminho realizável **sem invalidar a condição confirmatória** é executar
agora os testes sintéticos do próprio motor de inferência do Paper A
(100.000 permutações, Holm e bootstrap), sem abrir GT/F1/XY da A219.
O teste com os **219 resultados observados** requer antes o freeze científico
efetivo, a certificação de independência/exposição/proveniência e a liberação
por revisor independente, vinculada aos hashes.

**Declaração de autoria:** transcrição fiel, preparada pelo assistente a partir
da manifestação do pesquisador. Não representa uma assinatura do pesquisador
nem de terceiros. Se o pesquisador desejar adotar formalmente o texto, deve
revisá-lo e assiná-lo explicitamente.
