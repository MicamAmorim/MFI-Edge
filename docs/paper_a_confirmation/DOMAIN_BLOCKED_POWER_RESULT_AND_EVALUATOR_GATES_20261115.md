# Resultado de poder sintético com bloqueio por domínio — 15/11/2026

## Execução da workstation

Comandos já concluídos:

```powershell
python .\tests\test_paper_a_domain_blocked_power.py
python .\scripts\simulate_paper_a_domain_blocked_power.py --replicates 1000 --null-permutations 20000 --output "F:\MFI-Edge-Data\MultiCue\paper_a_domain_blocked_power.json"
```

- **5/5 testes aprovados.**
- 5 desenhos amostrais × 6 cenários sintéticos = 30 linhas de resultado.
- 1.000 réplicas por cenário e 20.000 permutações nulas
  por desenho; semente `20261115`.
- Não houve leitura de imagens, mapas, H5, GT ou F1 confirmatório.
- A simulação é de **cópula gaussiana artificial**, não representa
  efeitos reais observados nas bases.

## Estatística simulada (PROPOSTA, NÃO CONGELADA)

O simulador usa rho de Spearman **por domínio**, média ponderada
com pesos `n_d - 1`, teste unilateral de permutação bloqueado
por domínio, e Holm para H1/H2 (FWER de 5%).

**Atenção:** o `protocol.json` inicial não fixou essa estatística
estratificada, apenas indicou que a variante seria escolhida antes do
freeze. Não alterar silenciosamente o estimando original: a escolha
de teste deve ser escrita explicitamente no próximo protocolo
pré-congelado, antes de ver resultados novos.

## Resultados efetivamente informados — desenho 75 BIPED + 75 MultiCue

| Cenário simulado | H1 | H2 | Ambas |
|---|---:|---:|---:|
| Nulo com diferença entre domínios | 0,020 | 0,017 | 0,000 |
| Mesma associação rho=0,20 nos dois domínios | 0,717 | 0,765 | **0,576** |
| Mesma associação rho=0,25 nos dois domínios | 0,911 | 0,921 | **0,848** |
| Mesma associação rho=0,30 nos dois domínios | 0,976 | 0,978 | **0,954** |
| Associações 0,30 BIPED / 0,10 MultiCue | 0,752 | 0,759 | **0,584** |
| Associações 0,25 BIPED / -0,10 MultiCue | 0,155 | 0,129 | **0,030** |

No cenário nulo, a frequência de **qualquer rejeição** foi 0,037.
Isso é consistente com controle FWER ≤0,05 no cenário simulado,
sem ser verificação exaustiva de validade sob todos os mecanismos
de dependência/domínio/empates.

**Incerteza Monte Carlo:** com 1.000 réplicas, o erro padrão
máximo de uma frequência é 0,0158 (1,58 pontos percentuais);
as variações de poucos pontos não devem ser superinterpretadas.

## Decisão atual

- **Não congelar N=150 ou N=200 ainda.** A simulação suporta uma
  análise de compromisso; não determina o efeito científico mínimo
  relevante e não certifica a disponibilidade de 95 capturas MultiCue
  ou a independência das 198 candidatas BIPED.
- N=150 (75+75) reserva 20 prefixos MultiCue no teto atual de 95,
  antes de outras exclusões. N=200 (105+95) utiliza todo esse teto;
  qualquer nova exclusão MultiCue inviabiliza essa composição exata.
- Comparar todas as linhas dos desenhos 90+90, 105+95, 125+95 e 145+95
  a partir do JSON **já produzido**; não repetir a simulação.
- Escolher um limiar mínimo cientificamente relevante de `|rho|`
  **antes** de olhar resultados confirmatórios.
- Preferir uma estatística primária pré-especificada **dentro de domínio**
  se a hipótese pretende transferir entre domínios, mas justificar
  que o estimando muda em relação à correlação global.
- O poder de H1, H2 e **ambas** deve ser relatado separadamente:
  controlar a família com Holm não significa ter 80% de poder para
  confirmação simultânea.

## Contrato do avaliador: pontos que ainda precisam de decisão

A inspeção **somente de código-fonte** identificou:

1. `src/stage24_integrity.py`:
   `exact_binary_gt(gt)` aceita **uma máscara 2D**; para array 3D
   seleciona `gt[...,0]`. Não implementar leitura MultiCue
   multi-anotador delegando-lhe um array 3D sem política explícita.
2. `one_to_one_boundary_counts()` exige **mesma geometria** de
   predição e GT, usa matching exato um-a-um com tolerância
   `0.0075` da diagonal e não equivale ao benchmark oficial Berkeley.
3. `src/stage24_recertification_ops.py`:
   `choose_threshold(...)` **usa GT** das imagens que recebe,
   permitido somente para calibração em desenvolvimento/treino
   predefinido — jamais na coorte confirmatória.
4. `choquet_generalized_150` é um agregador com parâmetros de
   capacidade ajustados por `fit_aggregator` sobre dados de treino.
   **Esses parâmetros precisam ser fixados a partir de desenvolvimento
   independente**, com SHA/artefato completo, antes da confirmação.
5. MultiCue tem duas tarefas distintas: `edges` (seis PNG por
   sequência) e `boundaries` (cinco por sequência), enquanto o
   preflight histórico BIPED train confirmou um GT por imagem.
   **Não misturar nem colapsar arbitrariamente anotadores**.
   Decidir qual tarefa é primária, como tratar múltiplos anotadores,
   binarização, tolerância, matching, geometria e limiar
   antes de qualquer F1 confirmatório.

Referências públicas sobre as duas tarefas MultiCue:
- [Serre Lab — MultiCue](https://huggingface.co/datasets/Serrelab/multicue-boundary-detection)
- [Mély et al., 2016](https://serre.lab.brown.edu/resources/the-multi-cue-boundary-detection-dataset)

## Próximo comando, sem reexecutar a simulação

```powershell
$power = Get-Content "F:\MFI-Edge-Data\MultiCue\paper_a_domain_blocked_power.json" -Raw | ConvertFrom-Json
$power.results |
  Where-Object { $_.scenario -in @('homogeneous_rho_020','homogeneous_rho_025','heterogeneous_rho_030_010') } |
  Select-Object BIPED_n,MultiCue_n,total_n,scenario,power_H1,power_H2,power_both |
  Format-Table -AutoSize
```

**Estado permanece `draft_not_frozen`.** O próximo gate não é
novo processamento de mapas; é especificar o contrato da avaliação
e auditar a independência dos grupos, usando só metadados/código
até congelar.
