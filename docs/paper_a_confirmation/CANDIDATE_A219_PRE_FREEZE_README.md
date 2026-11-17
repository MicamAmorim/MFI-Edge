# Paper A — caminho seguro para a coorte A219

Status: **pré-freeze; não aprovado; resultados confirmatórios ainda protegidos**.

## Seleção e proveniência verificadas

- Coorte proposta: **125 BIPED + 94 MultiCue = 219 originais**.
- O roster foi conferido no computador do pesquisador: 219 hashes de imagens
  originais, sem repetições de ID nem de digest. Isso não certifica
  independência de cena nem ausência de exposição anterior.
- 83 BIPED pertenciam à seleção inicial; 42 são alternativas; 16 imagens
  de grupos com contradições visuais seguem fora da seleção.
- MultiCue 4586_left_0080 foi excluída por provável repetição de cena
  com 4582_left_0020; o prefixo histórico 4113 continua excluído.
- Análise de planejamento, **não confirmatória**: modelo sintético Gaussian
  copula, 10.000 simulações por efeito, Spearman por domínio, p unilateral
  aproximado e Holm para H1/H2: poder conjunto estimado 0,4869 para
  |rho|=0,15, 0,8150 para 0,20 e 0,9652 para 0,25. Não equivale à
  análise exata com 100.000 permutações planejada para a confirmação.
- O protocolo ativo permanece draft_not_frozen, originalmente N150.

## Nova infraestrutura de revisão assinável, sem autoaprovação

O módulo scripts/paper_a_a219_freeze_policy.py verifica metadados e
identidade SHA-256 do roster e do estudo de poder. Não acessa GT, H5,
resultados ou descritores e não atribui PASS.

O preparador scripts/freeze_paper_a_from_independent_review.py está adaptado
para 219 linhas e a composição 125+94. Antes do freeze, verifica que a
planilha revisada conserva exatamente os 219 IDs, caminhos e hashes do roster
original. Bloqueia agrupamentos de cena não resolvidos, incluindo
NOT_INDEPENDENTLY_ATTESTED_, e exige toda a revisão de proveniência,
GT v2, estatística e exposição histórica assinada, com hashes exatos.

Para produzir **somente** um protocolo congelado em **prévia não ativa**
e um template de signoff **sem aprovações**:

    git pull --ff-only origin experiment/paper-a-conditional-confirmation
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\preparar_freeze_a219_preflight.ps1

Esse script nunca chama attempt_freeze, não emite commit de freeze e
não abre GT/F1/H1/H2. Ele cria no F:\...\scientific_signoff\:

- FROZEN_PROTOCOL_BYTES_TO_REVIEW_NOT_ACTIVE.json
- FINAL_INDEPENDENT_REVIEW.template.json
- FREEZE_READINESS_PREVIEW.json

A prévia contém o status frozen **apenas como bytes sujeitos à aprovação**;
o protocolo versionado principal permanece draft até decisão independente.

## Evidências ainda necessárias

1. **Exposição histórica:** cruzar execução real/logs de Stage13c/Stage23/24
   com as 219 cenas, sobretudo as 42 alternativas; o Stage13c tem preflight
   técnico train com referência a GT e não deve ser representado como ausência
   demonstrada de acesso ao train. Auditorias estáticas e hashes sem colisão
   não provam ausência de influência em ajustes/seleção.
2. **Independência visual:** validar 219 IDs/capturas perante as revisões
   do quiz e grupos, e atribuir identificadores de cena reais. As 219 linhas
   PENDING não podem ser transformadas em PASS por script.
3. **P1:** rever e atestar as sete linhagens de parâmetros, seu fitting
   em desenvolvimento e a exclusão dos exemplos confirmatórios.
4. **GT v2:** conferir semântica e formato BIPED e MultiCue sobre evidência
   não confirmatória; fixar política dos seis anotadores e casos inválidos.
5. **Estatística:** aprovar hipótese de efeito relevante, análise de poder
   e regras prévias para mapas constantes/empates e dados inválidos.
6. **Revisor independente:** documentação explícita por linha/área e decisão
   com responsável, data UTC e SHA do protocolo, código e roster.

O executor scripts/execute_paper_a_frozen_cohort.py consulta o guard antes
de abrir qualquer dado protegido. **H1/H2 não devem ser executadas** antes
do commit de freeze validado e aprovação independente.

**Atenção:** versões antigas dos auxiliares
continuar_paper_a.py e preparar_paper_a_final_signoff.py
ainda podem gerar ou exibir a seleção draft legada N220. Não as use para
revisar ou promover a A219. Utilize somente o novo fluxo A219 até
concluir a migração integral dos comandos de continuação.
