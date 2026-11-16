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
frozen. Um avaliador real, auditado, de GT e imagens ainda precisa produzir
os dois últimos arquivos. Nomes de 600 anotações MultiCue não garantem sua
codificação. Nenhum script deve forjar esse passo.

A confirmação estatística, quando autorizada e com dados certificados, usa
100.000 permutações, Holm e bootstrap e reporta inclusive hipóteses
não confirmadas. O manuscrito ainda exige revisão científica independente.
