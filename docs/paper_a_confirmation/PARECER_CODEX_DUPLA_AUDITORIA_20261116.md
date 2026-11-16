# Paper A — parecer consolidado das duas auditorias Codex (16/11/2026)

**Estado científico: NO-GO para freeze e para consulta do GT da coorte confirmatória.**
Isto não é uma decisão de que H1/H2 sejam falsas: os testes confirmatórios ainda não foram realizados.

## Rastreabilidade dos relatórios locais

- `paper_a_completion/codex_final_audit/codex_round_1_final.md`: SHA-256 `8181712d9130bf9439994f06a126984aba2e0a93fc18b114ef3b51e04c3479f5`.
- `paper_a_completion/codex_final_audit/codex_round_2_final.md`: SHA-256 `36e9e1a3fbb5ba7df67b9639827a74b9342197434ff2d3616f2a3ecb5c62bae5`.
- `paper_a_completion/codex_final_audit/excluded_GT_format_only.log`: SHA-256 `96e54fb64b572b4be01ea56e2bd747a3ee98275896afd16061650039958e3405`.
- `paper_a_completion/codex_final_audit/existing_guarded_pipeline.log`: SHA-256 `e84d6d2466a8fd4c4ce774a3094c68d68ad39f007bddd8397c0e0480677bcb8e`.

Os arquivos integrais permanecem em F: (a cópia detalhada privada não é publicada aqui). O Codex relatou duas rodadas somente leitura e 80 testes técnicos com êxito; esses testes não equivalem a acesso autorizado à coorte protegida.

## Descoberta científica que impede o decoder atual

O relatório `scientific_signoff/NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json` observou:

- 3 GT BIPED **test** (não são os 125 originais BIPED train candidatos): pixels `uint8` com valores `0,254,255`;
- 12 GT de `edges` MultiCue do prefixo `4113` (excluído da confirmação): PNG com dados `uint16`;
- amostras incompatíveis com `STRICT_BINARY_0_1_OR_0_255_NATIVE_v1`.

Isso é **evidência real de incompatibilidade**, não simples ausência de confirmação. Não ajustar automaticamente `>0`, `>=128`, escala de 16 para 8 bits, polaridade, morfologia ou descarte do valor 254. Primeiro é necessário documentar a semântica do exportador/autores, obter revisão independente e versionar política e avaliador *antes* de abrir GT de qualquer imagem/captura selecionada.

A rotina de freeze deve recusar uma tentativa de `PASS` que mantenha o decoder estrito contradito pela amostragem.

## Achados técnicos do Codex e reparos publicados após a auditoria

1. **P0 — SHA do executor não incluía módulos importados:** criado conjunto fechado `RUNTIME_SOURCES`, revisão externa obrigatória de hashes e conferência dos blobs do `freeze_commit` e do checkout antes de qualquer GT.
2. **P1 — SHA P1 LF/CRLF:** vínculo histórico aceita apenas blob Git original ou sua conversão determinística LF→CRLF; não altera hashes nem parâmetros treinados. Prévia do protocolo gravada com newline controlado; backup do rascunho antes da publicação.
3. **P1 — gate técnico perdido:** análise só inicia se auditoria técnica e aprovação científica estiverem válidas, preservando todos os bloqueadores.
4. **P1 — validação incompleta da proveniência:** chamada direta do analisador confere SHA literal, aprovação, hash da fonte executada, responsável, commit verificável e política GT; não depende só do wrapper.
5. **P1 — identidade BIPED:** nome do original deve corresponder ao `image_id` aprovado, assim como MultiCue.
6. **P1 — interrupções:** publicação de outcome CSV e provenance suporta retomada apenas de proveniência já encenada e idêntica por hash; checkpoint por captura tem recibo de SHA separado e valida schema/intervalos.
7. **P2 — alfa/direção:** freeze exige alfa 0,05, alternativas direcionais H1 negativa/H2 positiva, semente definida e teste bloqueado por domínio.
8. **P2 — relatório de formato:** indicador foi alinhado às duas codificações exatas que o decoder `uint8` estrito suporta, sem inventar conversão para máscaras reais.

**Esses reparos ainda requerem execução integral e testes independentes no Windows.** Não foi feita execução de imagens ou GT protegidos por esta manutenção.

## Pendências científicas não substituíveis por código nem Codex

1. **220 cenas:** 125 BIPED e 95 MultiCue ainda sem evidência humana de independência/exposição por cena/captura. Resolver `RGB_221/RGB_222`, `4108`, derivados históricos e limites do bloqueio `4113`. Uma amostra reprovada exige alterar/recongelar N, composição e poder *antes dos resultados*, não forçar `PASS`.
2. **Sete partes P1:** ajuste de membership e limiares H1/H2, capacidade Choquet H2; provar para cada uma treino UDED-14 e não sobreposição por cena (não basta hash de IDs).
3. **Stage13c:** acesso a GT train para checar dimensões constou no código histórico; documentar esse acesso e excluir uso adaptativo, sem afirmar que GT nunca foi aberto.
4. **GT/metric:** justificar tarefa `edges`, anotadores, nível de bits, valor 254, polaridade, máscaras vazias, pareamento e política de missingness/degenerescência e versão do avaliador.
5. **Decisão independente responsável:** registrar fatos primários e assinar `FINAL_INDEPENDENT_REVIEW.json` após revisão real. Essa ação não é suprida pela execução de duas rodadas do Codex.

Só então haverá um freeze genuíno e a execução de H1/H2 produzirá decisão empírica (confirmadas ou não), com Holm e análise de sensibilidade.

## Estado de execução recomendada

Não repetir o pipeline pesado para tentar superar `PREFREEZE_SCIENTIFIC_GATES_OPEN`. Os resultados exploratórios UDED-14 não são confirmatórios. Após aprovação válida e correção prospectiva do contrato de GT, executar o comando existente `concluir_paper_a.ps1` e inspecionar o pacote real de resultados.

**Este documento é um parecer técnico preparatório e NÃO é uma assinatura científica de freeze.**
