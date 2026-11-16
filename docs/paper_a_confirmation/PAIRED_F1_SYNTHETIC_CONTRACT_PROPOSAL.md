# Pré-freeze: contrato sintético para F1 pareado multi-anotador

**Estágio:** unidade de teste sintética. **Não** é código avaliador
confirmatório liberado. O GT real dos 100 frames MultiCue permanece fechado;
a simulação não valida a decodificação de rótulos reais.

O módulo `src/paper_a_confirmation_paired_f1.py` implementa
somente a última etapa, **depois** de obter as predições binárias com
limiares já congelados e máscaras GT booleanas nativas previamente
validadas. Ele NÃO abre arquivos, lê imagens, produz mapas, calibra
operadores, escolhe limiares nem converte máscaras de múltiplos canais.

- BIPED: exige 1 GT booleano independente por imagem.
- MultiCue: exige 6 GT booleanos separados da tarefa candidata `edges`.
- Avalia candidato e controle separadamente com
  `src.stage24_integrity.one_to_one_boundary_counts`,
  em geometria nativa e tolerância de 0,0075 da diagonal.
- Calcula média de F1 **depois** das avaliações por anotador;
  `delta_F1 = mean(F1_candidato,k) - mean(F1_controle,k)`.
- Exige dimensões idênticas, `dtype=bool`, ao menos 1
  pixel de linha em cada GT; rejeita rótulos vazios/malformados
  sem decidir como excluir a imagem.
- Toda imagem produz **uma** linha de saída estatística,
  nunca seis réplicas independentes.
- Não é o avaliador oficial Berkeley; o comportamento não
  afirma equivalência entre os dois datasets.

## Testes sintéticos somente (seguros antes do freeze)

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\tests\test_paper_a_paired_f1_contract.py
```

O teste verifica 1/6 anotações, equivalência de predidores,
média em GTs distintos, diferença positiva, geometria nativa,
rejeição de PNG não decodificado (uint8), de canal 3D, e GT vazio.
Nenhum script de execução sobre as bases reais é oferecido nesta etapa.

## Gates científicos que continuam abertos

1. Auditoria controlada da **codificação** do GT de MultiCue edges
   e BIPED em uma fonte de desenvolvimento apropriada/documentação
   oficial; não ler máscaras da coorte confirmatória antes do freeze.
2. Escolha irrevogável do método de binarização de máscaras GT,
   inclusive significado de valores em escala de cinza e canais.
   **Nunca** importar silenciosamente `exact_binary_gt` sobre
   PNG multi-canal: a função existente usa o primeiro canal.
3. Escolha/registro de threshold(s) calculados **somente** em treino
   independente, calibração `legacy_sigmoid`, NMS e
   parâmetros `choquet_generalized_150` fixos por
   hash antes da análise das imagens elegíveis.
4. Confirmar unidades amostrais por captura e resolver linhagens
   para além do quadro final; 4113 continua bloqueado.
5. Decidir o estimando primário dentro-domínio versus global,
   os testes com permutação e o tamanho N antes de congelar.

**Importante:** a política de GT vazio deve ser aprovada antes do freeze.
O código apenas para com erro e **não** remove/filtra a imagem para
evitar seleção dependente de resultados.
