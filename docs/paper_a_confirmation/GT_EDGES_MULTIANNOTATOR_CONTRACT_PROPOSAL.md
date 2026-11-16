# Proposta de contrato de anotação e F1 — BIPEDv2 × MultiCue (pré-freeze)

**Status: CANDIDATA, NÃO CONGELADA.** Não modificar a implementação
confirmatória nem acessar GT/F1 antes da revisão científica.

## Justificativa da tarefa primária

A documentação oficial do BIPEDv2 descreve uma tarefa de detecção de
**edges**, com um GT supervisionado por imagem e revisão por especialistas.
Mély et al. (Vision Research 120, 2016, pp. 93–107) distinguem
**object boundaries** de **low-level edges** no MultiCue. Os índices
de nomes do TAR local mostram 6 arquivos `edges` e 5 `boundaries`
por último quadro esquerdo anotado. A origem documental identifica
anotações humanas separadas; **nomes do TAR não certificam a identidade
de cada anotador nem o conteúdo da imagem**.

Recomenda-se escolher como tarefa primária **low-level edges**, não
`boundaries`, para aproximar a semântica do BIPED. `boundaries`
pode figurar em análise secundária/exploratória, não influenciando
tamanho amostral, limiares, seleção de operador ou conclusões primárias.

Referências:
- https://github.com/xavysp/MBIPED
- https://huggingface.co/datasets/Serrelab/multicue-boundary-detection
- https://serre-lab.clps.brown.edu/wp-content/uploads/2016/11/2016_Mely_VR.pdf

## F1 proposto: média de resultados pareados por anotador

Para imagem `i`, candidato `c`, controle `b` e anotação `k`:

```text
f_i,k(c) = 2 TP_i,k(c) / (2 TP_i,k(c) + FP_i,k(c) + FN_i,k(c))
F_i(c)   = (1/K_i) * sum_k f_i,k(c)
Y_i      = F_i(candidate) - F_i(equal_mean)
```

- **BIPED:** `K_i = 1` (um GT), se a auditoria da anotação confirmar.
- **MultiCue edges:** `K_i = 6`, se a auditoria de conteúdo confirmar.
- Uma imagem/captura rende **uma observação**, nunca seis casos.
- Cada GT é avaliado **separadamente**, com matching de cardinalidade
  máxima um-a-um da `src/stage24_integrity.py` e tolerância `0.0075`
  da diagonal nativa; jamais unir, somar ou dilatar GTs.
- Usar exatamente mesma predição, tamanho, threshold, pré-processamento
  e pós-processamento no contraste candidato-versus-controle,
  exceto diferenças próprias dos operadores já definidos.
- Na imagem MultiCue, a média dos seis valores F1 é obtida **depois**
  da avaliação um-a-um; não é um F1 de uma suposta máscara média.
- Limiar, pesos e capacidade de `choquet_generalized_150` devem ser
  aprendidos apenas de desenvolvimento, fixados por commit e artefato.
  Nenhum ajuste individual de limiar com GT de confirmação.
- A métrica customizada **não é a avaliação Berkeley oficial** nem
  permite comparação numérica direta com ODS/OIS/AP publicados.
- O uso de seis referências MultiCue versus uma BIPED altera
  dispersão/distribuição dos F1. Reportar efeitos de H1/H2 dentro
  dos domínios e justificar o estimando conjunto *antes do freeze*.

## Pontos que exigem aprovação prévia

1. Confirmar que todos os nomes `edges` realmente se referem a
   máscaras de linha no último quadro esquerdo e que seus pixels são
   binários/codificados de forma compatível; isso exige **auditoria
   controlada de GT em conjunto de desenvolvimento** ou documentação
   inequívoca, não acesso a resultados da coorte.
2. Fixar como tratar imagens sem anotação válida, máscaras vazias e
   diferenças de resolução/codificação, **antes** de qualquer resultado.
   Política recomendada: falhar de modo explícito e escalar ao
   protocolo, sem exclusões silenciosas por desempenho.
3. Registrar sem ambiguidade como os parâmetros são calibrados em
   treino prévio independente, especialmente os operadores Choquet.
4. Fixar N e o teste (Spearman dentro de domínio, ponderado por
   `n_d - 1`, permutação bloqueada, Holm, ou alternativa justificada).
5. Auditar independência de grupos/cenas e exposição histórica
   (incluindo quadros além do final esquerdo); `4113` permanece
   em HOLD.

## Verificação somente de nomes já inventariados

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\tests\test_paper_a_multicue_gt_task_names.py
python .\scripts\check_paper_a_multicue_gt_task_names.py
```

O programa verifica o resumo de nomes de 100 sequências já gerado no F:,
o vínculo dos caminhos de anotação ao último quadro esquerdo, índices
distintos por tarefa, e a retenção de `4113`. Não relê TAR, H5, GT PNG,
originais, scores ou F1. Saída:

`F:\MFI-Edge-Data\MultiCue\multicue_annotation_task_name_contract_predata.json`

**Aviso:** verificar 1.100 nomes não significa validar as 1.100
anotações nem autoriza sua leitura antes do freeze.
