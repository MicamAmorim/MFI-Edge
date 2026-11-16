# Paper A — proposta prospectiva de decodificação GT (v2, NÃO APROVADA)

**Status:** `DRAFT_NOT_APPROVED`. Não libera freeze, GT da coorte, F1, H1 ou H2. O módulo experimental `scripts/paper_a_gt_decoder_candidate_NOT_APPROVED.py` **não é importado pelo executor confirmatório** e não substitui a política vigente `STRICT_BINARY_0_1_OR_0_255_NATIVE_v1`.

## Base empírica anterior à confirmação

Fonte: `F:/MFI-Edge-Data/MultiCue/paper_a_completion/scientific_signoff/GT_PIXEL_ENCODING_DETAIL_PRE_FREEZE_v1.json`, verificada contra os SHA-256 anteriores e exportada no ZIP de revisão de 30 evidências, criado em 2026-11-16.

| Conjunto permitido na auditoria | GTs amostrados | dtype | valores de pixel | contagens totais |
|---|---:|---|---|---|
| BIPED **test** (não train 125) | 3 | uint8 | {0, 254, 255} | 0: 2.654.723; 254: 223; 255: 109.854 |
| MultiCue prefixo **4113 excluído** | 12 | uint16 | {0, 65535} | 0: 10.809.640; 65535: 249.560 |

Esses números descrevem *somente* as 15 máscaras analisadas e NÃO autorizam pressupor a mesma distribuição nas 220 unidades propostas. Os 223 pixels de valor 254 constituem ~0,20% dos 110.077 pixels não nulos das três amostras BIPED.

Os autores do BIPED descrevem ground truth de edges supervisionado e revisado por especialistas; literatura de implementação descreve GT binário {0,255}, mas não resolve a presença observada de 254 nos arquivos locais. Ver:
- https://github.com/xavysp/MBIPED
- https://www.ipol.im/pub/art/2022/423/article_lr.pdf

Mély et al., *Vision Research* 120 (2016), distinguem anotações de *physical boundaries* e *lower-level edges* no MultiCue; o material documental não especifica inequivocamente a codificação PNG local uint16:
- https://serre-lab.clps.brown.edu/wp-content/uploads/2016/11/2016_Mely_VR.pdf
- https://huggingface.co/datasets/Serrelab/multicue-boundary-detection/blob/main/README.md

## Codificações candidatas, estritas e reversíveis apenas em termos de classe

1. BIPED: **hipótese ainda não certificada**: background `0` e edges `254` ou `255`. Exigir PNG uint8, cinza 2-D, geometria idêntica à imagem e exclusivamente os valores permitidos. Rejeitar toda outra intensidade. A origem do valor 254 requer documentação ou decisão explícita fundamentada em GT **não confirmatório**.
2. MultiCue edges: **hipótese ainda não certificada**: background `0` e edges `65535`, PNG uint16 2-D `I;16`. Rejeitar 255, 65280 e quaisquer outros valores não documentados. Sem conversão genérica de 16 para 8 bits.
3. Rejeitar máscaras integralmente vazias ou integralmente positivas antes de qualquer métrica, preservando falha fechada e posterior análise de causa. Não realizar redimensionamento, segmentação, interpolação ou limiar adaptativo.
4. Fixar a política de múltiplos anotadores: seis GT separados por último quadro esquerdo do MultiCue `edges`, média dos seis F1 por captura, nunca seis observações independentes.
5. Os parâmetros P1, capacidades de Choquet, limiares e a inferência H1/H2 não se alteram com esta proposta.

## Pendências obrigatórias para promover esta proposta

- Evidência primária ou autorização metodológica responsável para interpretar 254 como foreground e 65535 como foreground, com rastreio da versão dos arquivos BIPED/MultiCue e referência ao exportador.
- Escolha prospectiva da política e revisão independente dos testes, geometria, validez das máscaras e tratamento de degenerescências.
- Caso aprovada, integração revisada no **executor** pós-freeze, testes sintéticos e de amostras **não confirmatórias**, hash SHA-256 atualizado e inclusão nos hashes do código aprovado. Não atualizar o executor silenciosamente.
- Auditoria independente dos 220 registros de cena/exposição e sete atestações P1; aprovação responsável com evidências primárias antes do commit de freeze.
- Só depois emitir autorização legítima por `freeze_paper_a_from_independent_review.py` e executar o controlador existente.

**Este documento não é uma assinatura científica.** Nenhum resultado confirmatório foi aberto na preparação desta proposta.
