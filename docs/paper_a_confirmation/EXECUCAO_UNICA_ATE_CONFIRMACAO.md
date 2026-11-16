# Paper A — execução única, retomável e protegida

Na raiz do repositório, executar uma única linha no PowerShell:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\concluir_paper_a.ps1

A rotina atualiza a branch por fast-forward, reutiliza a auditoria BIPED 198,
confere o inventário MultiCue 100/96/95, valida a estrutura da receita P1,
executa testes sintéticos e integração Stage23 somente em imagem sintética,
e aciona o controlador já existente finish_paper_a.py.

Ao retomar, os inventários prontos não serão refeitos. A rotina nunca refaz
o fit UDED-14, cálculos de descritores originais, download TAR, SIFT/RANSAC,
nem abre GT antes de um freeze válido. Ela não fornece aprovação científica.

Relatórios: F:\MFI-Edge-Data\MultiCue\paper_a_completion\
- ONE_COMMAND_STATUS.json
- NEXT_ACTIONS.md
- ONE_COMMAND_ERROR.json (somente em erro técnico)
- one_command_logs\ (quando um comando falhou ou foi executado)

Se o protocolo ainda estiver em rascunho ou não houver assinatura válida,
a rotina para no gate científico e gera o NEXT_ACTIONS.md, sem adulterar
dados ou registrar hipóteses como confirmadas. A mesma linha deve ser usada
novamente após resolver os requisitos.

Para executar efetivamente a confirmação, o controlador existente requer
frozen_H1_H2_recipe.json, frozen_cohort_manifest.csv, freeze_approval.json,
certified_outcomes.csv, certified_outcomes_provenance.json e protocolo
frozen. Um executor de GT real agora está implementado em
scripts/execute_paper_a_frozen_cohort.py e será chamado automaticamente
pelo mesmo launcher, mas somente APÓS aprovação independente de seu código e
da política binária 0/1 ou 0/255 (nenhum threshold arbitrário), expressas
no freeze_approval.json, além dos outros seis gates científicos:
- approved_executor_source_sha256: SHA256 exato do arquivo executor revisado;
- executor_contract_independently_reviewed: true, se efetivamente revisado;
- gt_binary_decoding_contract: STRICT_BINARY_0_1_OR_0_255_NATIVE_v1.

O executor acessa originais e GT somente após o freeze, extrai do TAR apenas
os GT edges aprovados em F:, reutiliza checkpoints SHA por captura, gera
certified_outcomes.csv e provenance a partir da revisão independente e permite
que o controlador rode Spearman, 100.000 permutações e Holm. Não considera
falha de geometria/GT um motivo para exclusão posterior ou ajuste de limiar.

IMPORTANTE: a aprovação do decoder exige evidência PRÉVIA independente do
formato real dos GTs; não preencher os campos como verdadeiros apenas para
fazer o software passar. Se os GTs não tiverem codificação binária estrita,
o executor bloqueia sem alterar o protocolo. Nomes de 600 anotações MultiCue
não comprovam sua codificação e não autorizam antecipar sua inspeção.

A confirmação estatística, quando autorizada e com dados certificados, usa
100.000 permutações, Holm e bootstrap e reporta inclusive hipóteses
não confirmadas. O manuscrito ainda exige revisão científica independente.


## Proposta de coorte gerada automaticamente (não aprovada)

O launcher cria, se não existir, um CSV conservador com 125 imagens BIPED
e uma sequência por cada um dos 95 prefixos MultiCue não bloqueados:
F:\MFI-Edge-Data\MultiCue\paper_a_completion\COHORT_PROPOSAL_220_NOT_CERTIFIED.csv

A escolha é determinística por hash, sem consultar GT/F1. As 220 linhas
permanecem com independência e exposição = pending; a revisão do pesquisador
e a alteração explícita do protocolo de N=150 para N=220 (se justificadas)
são obrigatórias ANTES de gerar frozen_cohort_manifest.csv.


Atualização de 16/11: corrigido o caminho de importações Python em execução
Windows por arquivo, com testes de regressão usando python -I, sem acesso a GT.


## Dossiê científico automático (metadata-only)

O mesmo comando único chama o auditor consolidado e produz também:

- `F:\MFI-Edge-Data\MultiCue\paper_a_completion\DOSSIE_CIENTIFICO_PRE_FREEZE.md`
- `F:\MFI-Edge-Data\MultiCue\paper_a_completion\REVISAO_CIENTIFICA_PRE_FREEZE.json`
- `F:\MFI-Edge-Data\MultiCue\paper_a_completion\PROTOCOLO_220_PROPOSTA_NAO_CONGELADO.json`

A proposta do protocolo não altera `docs/paper_a_confirmation/protocol.json`
original nem configura um congelamento. Registra 125+95 como desenho
condicional a verificação de independência, os requisitos de anotação
`edges` e a estatística ponderada dentro dos dois domínios. O dossiê
preserva pendências como não aprovadas, inclusive a verificação de GT real.


## Pacote único para revisão independente (sem GT)

O mesmo comando único agora gera:

`F:\MFI-Edge-Data\MultiCue\paper_a_completion\PaperA_PRE_FREEZE_REVIEW_ONLY.zip`

O ZIP contém somente CSV/JSON/Markdown listados explicitamente no código
(índices de nomes, IDs, SHA256 de fontes, proposta ainda não aprovada,
parecer e relatório de gates). Nunca contém imagens originais, arquivos
GT, HDF5, TAR, máscaras, descritores nem métricas confirmatórias. Pode
ser anexado para um revisor checar históricos/linhagens sem acessar GT.


## Folha de revisão científica e rastreio Stage13c

No mesmo comando PowerShell, enquanto o protocolo estiver em
\`draft_not_frozen\`, o controlador também escreve:

- \`F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff\REVIEW_220_IMAGES_PENDING.csv\`
- \`F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff\REVIEWER_DECISION_REQUIRED.md\`
- \`F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff\SIGNOFF_READINESS_NOT_APPROVAL.json\`

A planilha preserva as decisões do revisor em reruns, valida que os 220
originais/hash não foram substituídos e não aprova nenhuma linha.
O relatório verifica a existência do resumo Stage13c somente por metadados.
Na ausência de logs, mantém a pendência aberta; jamais declara
independência/ausência de exposição. O review ZIP inclui os três arquivos
(captura estática, antes da primeira leitura de dados confirmatórios).


## Evitar repetição das 100.000 permutações após aprovação

Quando e somente quando houver protocolo frozen, aprovação independente
válida e resultados reais certificados, \`resume_paper_a_confirmation.py\`
registra assinatura com SHA256 do protocolo, receita, amostra, aval,
CSV de outcomes, provenance e versões do avaliador/estatística. Caso
os mesmos arquivos sejam encontrados numa execução posterior, o
resultado estatístico anterior é verificado por hash e reaproveitado.
O ZIP de análise também não é sobrescrito; seus membros são conferidos
contra o MANIFEST interno antes do reaproveitamento.
A própria revalidação do freeze precede qualquer leitura de outcome.


## Execução integral do pré-freeze com uma linha

O comando único executa os testes sintéticos do avaliador, inferência, guard,
runner, pacote de evidência e revisão (11 arquivos de teste), além do
preflight de Stage23 com imagem sintética. Em seguida gera a planilha
científica e o ZIP, registra as pendências e encerra normalmente quando o
freeze não está aprovado. **Ausência do resultado confirmado não é falha
técnica.** Após aprovação independentemente fundamentada dos GT, coorte,
receita, prova de não sobreposição, teste estatístico, hash do avaliador e
commit do protocolo, o mesmo comando continua para a etapa pós-freeze.


### Proveniência original da receita P1

A verificação da receita compara os hashes aos blobs versionados do commit histórico de ajuste P1, e não aos arquivos alterados no checkout de freeze. A implementação atual continua exigindo aprovação independente de seu SHA256.


## Um comando: revisão externa assinada → freeze Git → confirmação H1/H2

O comando \`concluir_paper_a.ps1\` prepara o arquivo
\`F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff\FINAL_INDEPENDENT_REVIEW.template.json\`
e o protocolo byte-exato \`FROZEN_PROTOCOL_BYTES_TO_REVIEW_NOT_ACTIVE.json\`.
O revisor *independente* precisa preencher a planilha de 220 cenas com
decisões \`PASS\` fundamentadas, depois copiar o template para
\`FINAL_INDEPENDENT_REVIEW.json\` e assinar conscientemente as sete
proveniências P1, os seis gates, os cinco relatos de evidência e os SHA256
dos arquivos efetivamente revistos.

Nenhum \`PASS\` é criado automaticamente; um review ausente ou incompleto
produz \`AWAITING_INDEPENDENT_SCIENTIFIC_SIGNOFF\` ou
\`SIGNED_REVIEW_NOT_AUTHORIZED_YET\` sem abrir GT. Com decisão completa
e coerente, o MESMO comando pode criar o protocolo congelado no Git,
\`git commit\` e \`git push\` com a versão revisada, registrar receita
e coorte assinadas no F:, executar guard e, se o hash exato do avaliador
tiver sido aprovado, seguir aos GTs e F1 de H1/H2.

**A decisão externa é necessária**: nenhum software pode inferir a
independência científica por declarar que 220 amostras estão disponíveis.
O preenchimento não pode ser delegado ao mesmo script, pois seria
autorização circular. O estado de revisão e a exposição Stage13c são
necessariamente registrados para o revisor antes da primeira abertura de GT.


### Escopo real da inspeção Stage13c

A versão histórica `automation/stage13c_biped_preflight.py` efetivamente contém código que abre imagens e GT **train** do BIPED para conferir dimensões (sem calcular F1 ou fazer ajuste nesse módulo). O relatório operacional existente deve ser revisado: afirmar que 'nenhum GT train foi aberto' é incorreto se o Stage13c executou esse bloco. A aprovação da independência deve distinguir inspeção de dimensões de uso de resultados para treinar/calibrar/selecionar.


### Fontes científicas versionadas no freeze

Após uma aprovação externa legítima, o commit de freeze passa a incluir também:

- `docs/paper_a_confirmation/FROZEN_H1_H2_RECIPE_P1.json` (parâmetros P1 aprovados);
- `docs/paper_a_confirmation/FROZEN_COHORT_IDS_PUBLIC.csv` (IDs/SHA256 com notas pessoais omitidas);
- `docs/paper_a_confirmation/FROZEN_FREEZE_INPUTS_MANIFEST.json` (hashes SHA256 das fontes locais, decisão externa, protocolo, avaliador e evidências).

O guard valida os hashes contra os arquivos congelados no F: antes de qualquer GT. O texto detalhado de adjudicação, com nomes e justificativas do revisor, **não é publicado no Git**, apenas vinculado por hash para proteger a confidencialidade.


### Retomada e testes após publicação

O executor recupera tentativas interrompidas de publicação de freeze mediante a mesma decisão externa e comparação de SHA dos arquivos de revisão e do commit Git. Após o freeze, os testes específicos do rascunho deixam de ser exigidos; o guard continua obrigatório. A pipeline CI também não exige a presença de protocolo draft quando o status estiver corretamente congelado.
