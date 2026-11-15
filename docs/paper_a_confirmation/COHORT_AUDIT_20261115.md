# Auditoria pré-dados dos candidatos a coorte (15/11/2026)

**Status: candidatos, não imagens confirmatórias.** Este documento não acessa GT nem métricas. Nenhuma amostra foi congelada ou aprovada.

## Inventário informado pela workstation

| Fonte local | Imagens | Situação | Ação pré-dados |
|---|---:|---|---|
| `datasets/BSDS500/images/test` | 200 | **Proteger**: existe pipeline histórico `run_stage13_bsds_transfer.py` que usa `--split test` por padrão; não foi auditado se todas foram efetivamente avaliadas ou usadas para decisões | Não examinar agora; não incluir automaticamente |
| `datasets/BIPEDv2/edges/imgs/test/rgbr` | 50 | **Exposição potencial forte**: `run_stage13d_biped_transfer.py` explicitamente carrega este split com GT para transferências antigas | Excluir provisoriamente, até auditoria documental |
| `datasets/BIPEDv2/edges/imgs/train/rgbr/real` | 200 | **Candidato A**: o protocolo Stage13d informa que não utilizou BIPED train; outras campanhas/artefatos ainda precisam ser auditados | Inventariar originais com hashes, sem abrir GT |
| `datasets/BIPEDv2/edges/edge_maps/train/rgbr/real` | 200 | Anotações, **não imagens candidatas** | Nunca inventariar como imagens |
| `datasets/BIPEDv2/edges/edge_maps/test/rgbr` | 50 | Anotações, **não imagens candidatas** | Nunca inventariar como imagens |
| `datasets/sintetics/benchmark_v2/validation/images` | 40 | Superfície sintética de desenvolvimento; não substitui população natural de domínio independente | Excluir dos testes primários |
| `external/UDED/imgs` | 30 | Inclui 14 imagens de descoberta Stage23/Stage24; contém linhagem anteriormente protegida de BSDS test (`35028`) | Não tratar como confirmação; auditar cada linhagem |
| `external/bsr_source`, `external/crisp-boundaries` | poucas | Arquivos de ferramentas/testes, sem coorte suficiente identificada | Descartar neste estágio |

**Importante:** a existência do pipeline de avaliação não prova por si só que foi executado nem que todos os dados influenciaram decisões; a classificação conservadora evita contaminar o teste. Uma partição denominada `train` pelo fornecedor pode servir de holdout **para este estudo específico** somente se demonstrarmos que não foi usada, direta ou indiretamente, para desenvolver os métodos ou suas hipóteses.

## Candidato B externo: MultiCue/MDBD

O conjunto [Multi-Cue Boundary Detection](https://huggingface.co/datasets/Serrelab/multicue-boundary-detection) é publicado pelo Serre Lab e contém 100 cenas naturais em 100 sequências estéreo de dez quadros (720p). Há anotações de bordas em quadros específicos; **cada cena, não cada quadro**, deve contar como uma unidade. O pacote completo da distribuição é de cerca de 3,4 GB. A escolha das imagens deve verificar disponibilidade exata de pares imagem/anotação e protocolo comparável.

Há imagem `09-MDBD-1C` na descoberta UDED; o conjunto novo **não pode ser considerado automaticamente independente**. Antes da escolha, conferir hashes, identificação de cena, correspondência perceptual e exposição histórica no MFI-EDGE. Excluir a cena já utilizada e quaisquer outras coincidências. Não presumir que as 99 cenas restantes sejam elegíveis sem auditoria.

## Desenho preliminar, ainda não congelado

Propor dois domínios: (A) BIPEDv2 train; (B) MultiCue/MDBD. Após validação de elegibilidade, considerar cerca de **75 imagens independentes por domínio** (total 150) mediante seleção determinística a partir dos hashes, com ao menos 60 por domínio. A escolha final depende da análise de poder prévia e das verificações de não exposição histórica.

Não realizar exploração de F1, seleção de limiar, ajuste de pesos ou cálculo de relações H1/H2 na nova coorte antes do congelamento; tampouco alterar o conjunto após ver resultados. Se MultiCue for inviável, buscar outro domínio realmente independente com anotações compatíveis, em vez de substituir silenciosamente pelo BSDS500 test.

## Primeiro comando seguro na workstation

Na raiz do repositório e com a branch de confirmação atualizada:

```powershell
python .\scripts\inventory_paper_a_confirmation_images.py --dataset "BIPEDv2_train=.\datasets\BIPEDv2\edges\imgs\train\rgbr\real"
```

Saída local: `results/local_dev/paper_a_confirmation_inventory/candidates.csv` com hashes e marcadores de possível exposição. **Nenhuma linha com `PENDING_MANUAL` está aprovada:** os hashes apenas facilitam revisão. Pastas `test`, `edge_maps`, `gt` ou `results` serão recusadas caso sejam passadas como raiz.

## Próximas decisões bloqueantes

1. Demonstrar com manifestos/logs que a fração de BIPED train destinada ao experimento não foi usada em campanhas passadas.
2. Obter/revisar MultiCue, remover sobreposições com UDED, identificar uma cena por unidade.
3. Fixar avaliação e limiares de acordo com as anotações existentes; não transportar sem verificação o avaliador tolerante Python para protocolos de múltiplos anotadores.
4. Realizar análise de poder com hipótese de efeito mínimo relevante, **sem usar o rho pós-hoc como estimativa não enviesada**.
5. Congelar coorte, fonte, software e regra de multiplicidade por commit separado. Somente depois abrir GT confirmatório.
