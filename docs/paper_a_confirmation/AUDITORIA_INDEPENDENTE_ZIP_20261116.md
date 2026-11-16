# Paper A — auditoria independente de metadados do ZIP (16/11/2026)

**Escopo:** 22 arquivos de metadados entregues no arquivo `PaperA_PRE_FREEZE_REVIEW_ONLY.zip`. Revisão documental, **não** autorização de GT, atestado de independência por cena ou aprovação científica do freeze.

**SHA-256 do ZIP recebido:** `a0146b2d61ba335272b5b94c0b9b7d1ca3b983d0349d891b3d75ae8d4a42d1c9`.

## Verificações concluídas diretamente sobre os 22 arquivos

- **22/22 hashes** internos correspondem ao `MANIFEST.json`, sem diferenças.
- **BIPED**: 198 linhas pós-deduplicação e 198 hashes distintos. `RGB_172` e `RGB_222` excluídas; as 198 restantes continuam `PENDING_HISTORICAL_AND_SCENE_LINEAGE_AUDIT`.
- **MultiCue**: 100 sequências, 96 prefixos de captura (quatro sequências `4108` e duas `4113`). 100 hashes distintos no inventário dos originais. Nomes de 600 GT `edges` e 500 `boundaries`; **pixels e identidade dos anotadores não verificados**.
- **Coorte proposta**: 125 BIPED e 95 MultiCue. Todas as 220 linhas têm ID, hash, caminho e prefixo coerentes com os respectivos manifestos; zero duplicações de hash nos 298 originais BIPED/MultiCue inventariados. **Nenhuma das 220 linhas foi aprovada** para independência ou exposição.
- O prefixo `4113` está fora da proposta. `4108_left_0082` foi escolhida como uma representante única de quatro sequências do prefixo `4108`, que tem `REPEATED_CAPTURE_PREFIX_HOLD` no inventário: **HOLD não pode ser substituído por PASS automaticamente**.
- A amostra inclui `RGB_221`, representante do par visual com `RGB_222` (excluída), e precisa de revisão explícita de exposição histórica.
- **P1**: hash SHA-256 `628d1e345b6d1117c3cbfbc6ecaf75d4cac8db6a7796d328e2ea911ce9891a9c`. O SHA do protocolo de origem registrado em P1 corresponde ao arquivo protocol_DRAFT anexado. A capacidade Choquet H2 é monótona e a reconstrução por Möbius coincide exatamente (erro máximo calculado 0). As **sete** declarações `no_confirmatory_overlap_attested` permanecem `null`. O arquivo P1 original do F: não integra este ZIP, portanto a igualdade com ele é comprovada apenas pelo registro de execução fornecido.
- **Auditoria de histórico BIPED**: 14 referências remotas, 120 referências de código distintas, 40 metadados consultados, zero coincidências de hash/ID entre candidatos e os metadados consultados. Não demonstra não-exposição fora desse escopo. O resumo/log operacional de `stage13c_biped_preflight` **não está no ZIP**.
- **Triagem geométrica MultiCue**: o relatório histórico registra um par de sobreposição UDED no prefixo `4113` em 2.700 pares inspecionados. A triagem perceptual inicial relatou zero alertas, o que não contradiz a geométrica e não prova ausência de outras sobreposições.

## Diferença de protocolo ainda não resolvida

- `protocol.json` está em `draft_not_frozen`, com **N=150**. O relatório de planejamento propõe **N=220** (125+95) e poder conjunto simulado de **82,3% para rho=0,20 homogêneo**. Esse poder é condicionado à elegibilidade de **todos** os 95 prefixos MultiCue; qualquer exclusão exige novo desenho/poder antes do freeze.
- `edges` como tarefa primária, seis GT separados e média de F1 por captura são **propostas**. O ZIP não possui GT/PNG nem evidência suficiente para certificar o decodificador estrito, GT vazio, canais, formato ou equivalência semântica. A implementação **não** deve abrir GT confirmatório para descobrir e corrigir esses detalhes depois do freeze.

## Parecer e decisões restantes

**NO-GO para primeira abertura de GT confirmatório; GO para revisar elegibilidade e semântica sem GT protegido.** As seguintes evidências precisam ser avaliadas antes da aprovação humana:

1. Logs operacionais de Stage13c e outros usos BIPED train, com distinção entre inspeção dimensional e ajuste de parâmetros por GT.
2. Revisão de independência de todas as 125 cenas BIPED, incluindo `RGB_221`, e das 95 MultiCue, incluindo `4108`, com rastreamento histórico além do quadro esquerdo final.
3. Atestar separação do treino UDED-14 e da coorte, de forma fundamentada, para as sete proveniências P1.
4. Certificar codificação dos GT com documentação externa ou amostra de desenvolvimento independente da coorte protegida; definir política para erros/ausências antes de usar GT.
5. Aprovar explicitamente N, composição, permutações bloqueadas por domínio, estatística primária, empates, missingness, limiares já ajustados e hashes do executor.
6. Concluir o freeze legítimo via protocolo, receita, manifesto por captura e `freeze_approval.json` revisados/assinados. Só depois executar F1 e inferência H1/H2.

**Esta auditoria não transforma qualquer status `pending` em `pass`.** O usuário também recebeu o parecer independente em Markdown, um JSON de verificações e um CSV de adjudicação com 220 linhas, com todas as decisões de revisor em `PENDING`. Os artefatos detalhados permanecem locais à conversa; não são uma coorte congelada.
