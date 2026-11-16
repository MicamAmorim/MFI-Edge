# Paper A — H1/H2 inferência pré-GT (implementação incremental)

**Status: ENGENHARIA DE PRÉ-CONFIRMAÇÃO, NÃO CONGELADO.**
A implementação em `src/paper_a_h1h2_inference_core.py` conecta a receita
P1 já validada por SHA256 às rotinas existentes de pertinência, agregação,
supressão NMS por gradiente da imagem e limiares ajustados *exclusivamente*
no desenvolvimento UDED-14. A função `predict_from_native_maps` recebe,
em memória, **quatro mapas float32 de mesma geometria da imagem de origem**;
não abre arquivos, imagens de bases externas, GT, F1 ou resultados.

## Contrato implementado e testes

- H1: X1 = diferença absoluta entre médias dos mapas originais halfdisc e PMI;
  candidato `maximum` versus `equal_mean`.
- H2: X2 = média dos três Pearson espaciais calculados nos mapas originais
  FH, halfdisc e structure tensor; candidato
  `choquet_generalized_150` (gamma 1.5) versus `equal_mean`.
- O código aplica *as mesmas funções Stage24 existentes*, com pertinência
  `legacy_sigmoid`, capacidade e limiares provenientes da P1 **sem refit**.
- A saída é X1/X2 e quatro predições booleanas (dois candidatos, dois controles);
  não há Y, GT, F1, p-valor ou conclusão confirmatória.
- Verificação estrutural da receita P1: identificadores, ordem dos descritores,
  famílias, escalas positivas, quatro limiares, e coerência de 8 capacidades /
  6 coeficientes Möbius.
- Valores degenerados ou não finitos, mapas quantizados e divergência
  dimensional abortam explicitamente. Política de X2 constante não é
  improvisada: **aborta**, aguardando uma decisão pré-freeze.

Executar apenas testes sintéticos e de predição (sem GT):

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
.\.venv\Scripts\python.exe .\tests\test_paper_a_h1h2_inference_core.py
if ($LASTEXITCODE -ne 0) { throw "Falha no core H1/H2" }
.\.venv\Scripts\python.exe .\scripts\preflight_paper_a_h1h2_core.py
```

## Quatro entregas restantes até a confirmação definitiva

1. **Adapter de imagens e descritores**: obter os originais aceitos da coorte
   BIPED/MultiCue, computar uma vez os quatro mapas com as funções Stage23
   na resolução de pré-processamento (histórico: máximo 256), registrar o
   hash do código, inspecionar geometria nativa e cachear/checkpointar. Não
   modificar parâmetros com base em resultados confirmatórios. O preditor
   deste commit exige mapas previamente registrados à imagem **sem usar GT**.
2. **Contrato de GT validado em desenvolvimento/documentação**: fixar o
   decodificador dos arquivos reais BIPED e MultiCue *edges*, política
   de máscaras vazias e de múltiplos anotadores, sem abrir GT protegido.
3. **Manifesto final e freeze assinado**: 4113 excluído; verificar
   exposição histórica e a independência das capturas; N/domínios;
   escolha para mapas constantes; garantir assinaturas/SHAs e commit
   de congelamento **anterior** ao primeiro acesso a qualquer GT
   confirmatório.
4. **Executor de outcomes**: após (3), carregar dados GT autorizados,
   aplicar `src/paper_a_confirmation_paired_f1.py` para cada predição
   das hipóteses, emitir um único registro X1/Y1/X2/Y2 por unidade
   independente e proveniência verificável. Então executar o
   `scripts/analyze_paper_a_confirmed.py` existente (permutações
   por domínio + Holm), relatar os resultados mesmo negativos.

**Não confundir:** implementação da inferência GT-free não certifica GT,
N, independência amostral nem estatística; não é resultado científico.

## Correção do preflight real Stage23 (16/11/2026)

A primeira execução no PC passou nos 9 testes sintéticos do adaptador, mas
`--real-stage23` falhou em `Constant/degenerate X2 descriptor correlation`
sobre uma imagem artificial de 48 × 52 pixels. Isso não é um resultado de
BIPED/MultiCue nem prova um defeito de H2: o estimador Pearson é
matematicamente indefinido se um dos três mapas é constante.

A fixture do **teste**, e somente ela, foi substituída por uma imagem RGB
sintética determinística de 160 × 192 pixels, com várias regiões e textura.
O preflight agora imprime mínimo/máximo, média/desvio, quantidade de
valores únicos e número de pixels não nulos **por descritor**.
O método científico não foi alterado: um verdadeiro X2 indefinido
continua abortando, sem atribuir correlação zero nem escolher outro operador.

Executar:

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
.\.venv\Scripts\python.exe .\tests\test_paper_a_prefreeze_map_adapter.py
if ($LASTEXITCODE -ne 0) { throw "Falha nos testes" }
.\.venv\Scripts\python.exe .\scripts\preflight_paper_a_prefreeze_map_adapter.py --real-stage23
if ($LASTEXITCODE -ne 0) { throw "Diagnostico Stage23 pendente; enviar saida JSON" }
```

Se o preflight ainda falhar, ler os diagnósticos de todos os descritores
antes de modificar o pipeline; não relaxar o contrato de Pearson ou
ajustar limiares sem decisão científica pré-freeze.
