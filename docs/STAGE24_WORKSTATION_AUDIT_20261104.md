# Auditoria Stage24G–L para o Paper A — 2026-11-04

## Base e alcance

Inspeção da workstation Windows e do histórico de todas as 12 branches remotas;
revisão aprofundada do caminho Stage24G–L, matching, seleção, checkpoints,
controles estatísticos e integração Berkeley. Isso não constitui certificação de
cada função histórica ou de todas as variantes dos estágios anteriores.
Base remota: `3a18eb4`. Cópia da workstation antes da atualização: `565942c`.
Paper A local: `cde7463`, ainda descreve os resultados Stage23C–F.

- main: linha antiga, três commits próprios de documentação/workflow; não contém a recertificação.
- local-dev e archive/research-agent-v14u-2026-10-07: mesmo commit fd5d060, ancestral da Stage24.
- stage15: ancestral 0d5861f; stage23: ancestral 063564b.
- quatro branches stage22-whitespace-fix*: mesmo commit ancestral 8e8b157.
- experiment/uded-railway: ancestral histórico 211aa36.
- webui: 16 commits próprios de interface; não é a base dos experimentos atuais.
- stage24-residual-suppression: linha atual para a recertificação do Paper A.

## Estado local observado

Ryzen 7 5700X, 16 processadores lógicos, Python 3.12.10 na .venv existente.
Inventário científico local registra NumPy 2.5.3 e SciPy 1.18.1; não houve upgrade.
Cerca de 17 GB livres em C: no início da inspeção. MATLAB R2023a está instalado.
Não foram encontrados processos python/MATLAB ativos nas consultas realizadas.

A campanha original possui fingerprint, preflight, pair_screen, geometry_audit e
somente dois de 26 modos individuais de r1_f1: Scharr raw/NMS. Nenhum fold completo
foi encontrado. Existe STOP_STAGE24_PAPER_A. Stage24 anterior está completed, mas
reference_reproduction_verified=false. A causa da saída -1 do terminal não foi
determinada: o trecho fornecido não contém traceback nem diagnóstico nativo.

Os parciais são preservados para auditoria. Como o código científico mudou,
a próxima campanha usa uma pasta canônica nova após arquivamento por renomeação
da antiga; caches float de descritores continuam sujeitos às identidades/hashes.
Não editar fingerprints antigos para forçar reutilização.

## Correções desta auditoria

1. Bootstrap: F1 numérico zero era descartado por teste de truthiness; agora entra
   na média por imagem e no reamostramento, evitando viés de exclusão.
2. Matching exato: relação Euclidiana gerada por sparse_distance_matrix compilado,
   sem listas Python por pixel. Compressão dos vértices ativos dos dois lados e
   busca a partir do lado menor. Mesma cardinalidade máxima; sem matching guloso
   aproximado. Certificados existentes continuam com fallback exato.
3. Fingerprint: inclui implementações transitivas de src e scripts Python da raiz,
   além dos arquivos científicos já registrados. Antes, mudanças em helpers do
   loader/plano dos folds podiam escapar da identidade da campanha.
4. Preflight verifica identidade antes de sobrescrever contratos de uma campanha
   antiga. Monotonicidade de capacidades é verificada de fato, com JSON booleano,
   em vez de registrar apenas normalização sob o nome capacity_monotone.
5. Conclusão exige campanha completa, runtime e avaliação oficial completed;
   --skip-official/--skip-runtime não produzem status completed ou autoarquivo.
6. CLI rejeita all com menos de 15 folds antes do trabalho caro e rejeita contagens
   inválidas. Oficial com --out alternativo é bloqueado porque o backend oficial
   e o arquivador ainda usam a identidade canônica compartilhada.
7. Exportação BSDS float acompanha --out; launcher habilita faulthandler e saída
   sem buffering, e inclui os testes de integridade no gate obrigatório.
8. Manifesto explicita CV interna condicional ao filtro do treino externo.

## Verificação de desempenho e limites

Ensaio local, imagem UDED 01-0843x4, 339x510, fallback exato forçado:
raw 0.1895 -> 0.1279 s; NMS 0.0717 -> 0.0465 s, mesmos TPs 3514/3307.
Tempos são uma observação por caso, não benchmark universal.

Busca raw de sete limiares em três imagens reais, mesmas pertinências:
1 thread 3.918 s; 2 threads 2.276 s; 4 threads 1.732 s.
Limiar selecionado, TP/FP/FN e F1 idênticos em todas as configurações.
Recomendação inicial: STAGE24GL_MATCH_WORKERS=4. Não paralelizar folds por fora:
quatro matchers simultâneos já multiplicam memória de grafos temporários.

## Limites científicos a levar ao manuscrito

- UDED tem 14 imagens únicas; 15 folds repetidos não são 15 amostras independentes.
- Filtro de grupos/finalistas é feito no treino externo antes dos splits internos:
  CV interna é condicional a essa descoberta. Outer held-out permanece separado;
  não descrever como busca conjunta integralmente aninhada e independente.
- Pares históricos já foram escolhidos em campanhas anteriores sobre UDED;
  a recertificação é exploratória, não nova confirmação independente no UDED.
- BSDS val já foi usado no desenvolvimento; uma nova campanha é reavaliação de
  desenvolvimento. Não chamar de confirmação externa intocada ou SOTA.
- Avaliador interno one-to-one não é equivalente ao Berkeley multi-anotador.
- bootstrap por imagem é exploratório: reutilização entre treino/val e seleção
  adaptativa não desaparecem ao promediar repetições.
- Mapas author/native float da literatura e reprodução independente das referências
  continuam pendências; não substituí-los por PNG histórico quantizado.
- Paper A precisa distinguir resultados Stage23 históricos dos novos Stage24G–L,
  com GT nativo, NMS corrigido e operadores matemáticos auditados.

## Execução e acompanhamento

Usar a pasta local MFI-Edge e a .venv existente. Executar o preflight depois de
preservar a saída antiga e atualizar o checkout; iniciar all apenas após passar.

```powershell
$env:STAGE24GL_MATCH_WORKERS = '4'
Remove-Item .\automation\STOP_STAGE24_PAPER_A -ErrorAction SilentlyContinue
.\run_stage24_paper_a_recertification.bat --phase all 2>&1 |
    Tee-Object -FilePath .\results\local_dev\stage24_paper_a_recertification\shell.log -Append
```

Parada cooperativa: `.\stop_stage24_paper_a_safely.bat`. Repetir o comando acima
para retomar sob o mesmo código/ambiente/configuração. Matching nativo em andamento
pode precisar terminar antes da parada. Faulthandler pode registrar falhas nativas
no log, mas encerramento externo do processo pode não deixar diagnóstico Python.

Acompanhar checkpoint e espaço livre. Pacotes float e ZIP de reprodução exigem
espaço adicional; evitar duplicar caches e não remover evidências para liberar disco.
Atualizar Paper A somente depois de conferir claim_status.csv, manifests, tabelas
por imagem e avaliação oficial, preservando limitações e resultados negativos.

## Validação desta revisão

55 testes passaram: matemática histórica (8), recertificação (21), NMS assinado (5),
contratos matemáticos (8), sintéticos com offset (4), pacote de reprodução (4) e
integridade (5). Incluem comparação com um oráculo de grafo independente em
casos aleatórios, identidade serial/paralela, retomada e regressão para F1 zero.

O certificado de matching também foi ampliado para cobrir todos os vértices
não isolados do lado escolhido: vértices sem qualquer vizinho não podem aumentar
a cardinalidade. Se a atribuição gulosa falhar, um matching completo no subgrafo
dos oito vizinhos mais próximos também certifica a mesma cota superior. Se não
cobrir todos os vértices ativos, o grafo de raio completo permanece obrigatório.
Essas otimizações não tornam o matching aproximado.
