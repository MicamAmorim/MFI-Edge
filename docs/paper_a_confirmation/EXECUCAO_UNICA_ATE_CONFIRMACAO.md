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
