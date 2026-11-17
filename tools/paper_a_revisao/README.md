# Paper A — Quiz visual local de revisão pré-freeze

O código do quiz é versionado no Git. As 293 imagens são lidas apenas do disco local, com verificação SHA-256; as fotos e os GT não são enviados ao Git.

## Executar no Windows (PowerShell, pasta MFI-Edge)

1. Execute: git pull --ff-only origin experiment/paper-a-conditional-confirmation
2. Execute: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\abrir_quiz_paper_a.ps1

A rotina exige .venv, executa teste sintético e abre o HTML offline.

Local do HTML:
F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff\QUIZ_VISUAL_LOCAL_293\index.html

## Conteúdo

- 198 candidatas BIPED train (125 na seleção inicial, 73 alternativas).
- 95 capturas MultiCue da proposta.
- 22 grupos ORB/RANSAC de possível repetição visual, sem decisão automática.
- 7 questões de proveniência P1 e 10 de GT, histórico e estatística.
- Decisões por captura, com fundamentação textual.
- Autosalvamento no navegador quando possível, exportação HTML/JSON/CSV,
  importação JSON para retomar respostas.

As exportações ficam na pasta Downloads do navegador. Faça cópias de segurança
do JSON, sobretudo se mudar de navegador ou limpar o armazenamento local.

## Escopo científico e privacidade

Não acessa GT, H5, F1, descritores, métricas, resultados confirmatórios, nem
faz treino, signoff ou freeze. Não modifica planilha, protocolo ou evidências
históricas. A inspeção visual não demonstra ausência de exposição anterior;
essa pergunta requer também fontes documentais. Os grupos geométricos
são alertas de triagem, não certificação exaustiva.

O quiz não é FINAL_INDEPENDENT_REVIEW.json e nunca aprova H1/H2.

## Fontes locais utilizadas

- results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv
- F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff\REVIEW_220_IMAGES_PENDING.csv
- F:\...\scientific_signoff\P1_LINEAGE_METADATA_CROSSCHECK_NOT_APPROVED.json
- F:\...\scientific_signoff\FINAL_INDEPENDENT_REVIEW.template.json
- datasets/BIPEDv2/edges/imgs/train/rgbr/real/ (somente originais)
- F:\MFI-Edge-Data\MultiCue\source_frames_only\ (somente originais)

O HTML usa CSS/JS locais e não exige rede, servidor, serviços externos ou login.
Se o inventário mudar, o gerador bloqueia reutilizar o mesmo diretório de
revisão com metadados distintos. Exporte suas respostas antes de arquivar
a revisão anterior e gerar outra versão.


## Como responder ao quiz simplificado

- **Grupos 02:** olhe edifícios, postes, rua e paisagem. Responda se todas as
  fotos mostram o mesmo lugar, apenas algumas, nenhuma, ou se não sabe.
  Se todas forem uma cena, indique um original representativo; não exclui nada.
  Se apenas algumas forem uma cena, marque quais se parecem com a primeira.
- **Capturas 03:** use a comparação lado a lado. Para cada par respondido,
  marque "mesmo lugar", "lugares diferentes" ou "não consigo decidir".
  O resultado da comparação fica registrado no JSON, com os IDs das fotos.
  O quiz também separa a pergunta sobre histórico de desenvolvimento:
  **olhar a imagem não é evidência de ausência de exposição**.
- **P1 04 e GT/método 05:** cada questão mostra o que o pipeline já registrou
  e o que ainda falta provar documentalmente. Você NÃO precisa aprovar sem
  conhecer a fonte: selecione "Não consegui conferir / não sei" quando for
  esse o caso. Essa resposta fica registrada como pendência, não signoff.
- **Relatório:** exporte HTML e JSON. Os grupos, referências comparadas,
  critérios visuais e respostas P1/GT são incluídos. O JSON permite retomar
  a revisão sem fabricar aprovação.

**Segurança:** nenhuma resposta de "sim" altera automaticamente o protocolo,
substitui o parecer do revisor independente ou autoriza GT confirmatório.
