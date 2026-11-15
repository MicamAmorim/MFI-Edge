# Reanálise condicional Stage 24G–L (exploratória)

Este pacote reutiliza os resultados já arquivados do Paper A. Não executa detectores, calibração, treinamento ou avaliação MATLAB.

## Executar no PowerShell (raiz do MFI-EDGE)

```powershell
git fetch origin
git switch mfi-edge-stage24-residual-suppression
git pull --ff-only origin mfi-edge-stage24-residual-suppression
python .\analisar_landscape_condicional.py --research-root . --out .\analise_condicional
```

Requisito: Python 3.11+ com NumPy (`python -m pip install numpy` caso não esteja instalado). A execução completa precisa dos caches float `.npy` locais já existentes; nenhum mapa é regenerado. Ausência de caches será indicada no relatório.

Para conferir somente os resultados tabulares sem acessar os mapas float:

```powershell
python .\analisar_landscape_condicional.py --research-root . --out .\analise_condicional --no-maps
```

Para pular também a avaliação por imagem do BSDS: acrescente `--no-bsds`.

Arquivos arquivados: [`STAGE24_CONDITIONAL_LANDSCAPE_20261115.md`](STAGE24_CONDITIONAL_LANDSCAPE_20261115.md), CSVs em `results/paper_a_evidence/stage24_conditional_exploratory/`.

## Cuidados metodológicos

- 14 imagens UDED, não 70 amostras independentes: cinco repetições por imagem.
- Grupos de ganho/perda, operadores vencedores e associações foram identificados retrospectivamente: análise exploratória, não um seletor validado.
- Na BSDS500, os diagnósticos por imagem utilizam limiares próximos dos ODS selecionados na mesma validação; não substituem o ODS/OIS/AP oficial.
- Mapas BSDS congelados são predições agregadas finais, não necessariamente mapas individuais dos descritores.
- O script só escreve em `--out`. Recomenda-se usar um diretório não rastreado para as saídas.

Versão de 15/11/2026. Artefatos de análise existentes não foram alterados ou reexecutados por este commit.
