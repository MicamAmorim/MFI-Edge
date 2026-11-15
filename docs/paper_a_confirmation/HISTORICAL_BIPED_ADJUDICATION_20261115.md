# Adjudicação das referências ao BIPEDv2 train — 15/11/2026

**Status: auditoria de código CONCLUÍDA; auditoria operacional e independência da coorte PENDENTES.**
Nenhum ground truth confirmatório ou F1 foi examinado para produzir esta adjudicação.

## Entrada recebida do ambiente Windows

- `198` candidatas únicas após duas exclusões confirmadas por inspeção visual.
- `14` branches `origin/*` examinadas.
- `120` referências de código distintas, das quais `11` classificadas como relacionadas a `train`.
- `40` manifestos históricos consultados, **zero identificador/hash coincidente** com as 198 candidatas.
- Triagem: `66` referências ao split test, `39` genéricas, `11` ao train, `4` outras.

## Decisão técnica sobre as 11 referências sinalizadas

| Fonte | Nº | Leitura substancial | Inferência possível |
|---|---:|---|---|
| `run_stage13d_biped_transfer.py` (linha 5) | 1 | Docstring: `The BIPED train split is unused`. O fluxo `load_test_items` consulta `edges/imgs/test` e respectivos GTs | Não há indício **neste script** de usar BIPED train na otimização ou avaliação do Stage13d |
| `automation/stage13c_biped_preflight.py` (linha 23) | 1 | Registra `train=unused; test=frozen_external_replication`. **Contudo**, o script faz `Image.open` das imagens e anotações **train e test** para verificar resoluções/pares | Pode ter ocorrido acesso técnico ao GT train, se executado. Isso **não é o mesmo que** ajuste de parâmetros sobre GT, mas exige verificar logs e execução real |
| `scripts/review_paper_a_confirmation_pairs.py` | 4 | Ferramenta criada **nesta branch** para inspeção visual dos originais BIPED train, sem GT | Preparação da confirmação; não evidencia exposição anterior à formulação das hipóteses |
| `scripts/audit_paper_a_confirmation_predata.py` | 1 | Scanner de hashes/dHash de originais train, sem GT | Preparação da confirmação |
| `scripts/audit_paper_a_confirmation_history.py` | 2 | Pesquisa textual de código, manifests e hashes | Preparação da confirmação |
| `scripts/apply_paper_a_visual_dedup.py` | 2 | Filtragem documentada de duplicatas visuais, sem GT | Preparação da confirmação |

**Total: 2 referências de pesquisa histórica + 9 da própria confirmação = 11.**

A lista é uma triagem estática das linhas que contêm os padrões procurados, e não uma prova de que não existam acessos indiretos por bibliotecas, outras máquinas, cópias de arquivos ou logs não rastreados.

## Conclusão conservadora

**Nenhuma referência antiga apresentada comprova seleção/treinamento de operadores usando resultados BIPED train.**
Entretanto, também não é justificável atribuir o status `eligible`, `holdout` ou `frozen` às 198 imagens.

Além de exposição experimental, o estudo precisa avaliar **dependência de cena e sequência** além dos dois pares visuais detectados pelo dHash. Se duas imagens forem quadros de uma única cena/captura, usar apenas uma como unidade primária, independentemente de seus hashes.

## Procedimento seguinte: inspecionar apenas nomes de arquivos locais

No PowerShell da workstation:

```powershell
Get-ChildItem .\results -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match '(?i)biped|stage13c|stage13d|multicue|mdbd' } |
    Select-Object -First 60 FullName, Length, LastWriteTime |
    Format-Table -Wrap
```

Esse comando **não lê o conteúdo** dos arquivos de resultados; ajuda a localizar
rastros de execução. A existência de um arquivo sinaliza a necessidade de auditoria posterior de
parâmetros/coorte, sem examinar F1 da coorte candidata.

## Possível segundo domínio: MultiCue / MDBD

O MultiCue contém **100 cenas**, cada qual com dez quadros em cada câmera. O estudo
confirmatório usaria **somente o último quadro esquerdo anotado, uma unidade por cena**
e a anotação de `boundaries` (em oposição a `edges`), se a compatibilidade com o
critério de borda do Paper A for sustentada. Verificar a cena histórica `09-MDBD-1C`
na amostra UDED; os demais IDs/linhagens também demandam auditoria.

Fonte oficial: https://huggingface.co/datasets/Serrelab/multicue-boundary-detection

**Decisão sobre o dataset ainda não congelada**: o pacote integral ocupa cerca de
3,4 GB, e nenhuma seleção por resultado pode ser feita após sua abertura.
Amostra-alvo provisória 150 imagens, com dois domínios e análise de poder antes
do congelamento.
