# Paper A — confirmação independente de H1/H2 (rascunho pré-dados)

**Estado: `draft_not_frozen` em 15/11/2026. Não iniciar cálculo de F1 confirmatório.**

Esta branch parte do commit científico [`9957a0c`](https://github.com/MicamAmorim/MFI-Edge/commit/9957a0c1f4fcaadd0159c3c21ad6315f08f891a8) e **não altera** a campanha Stage24 nem os CSVs exploratórios existentes. O objetivo é transformar duas correlações observadas retrospectivamente em hipóteses testáveis em imagens novas e independentes.

- **H1**: para `halfdisc_distribution_contrast|pmi_dependency_deficit`, a amplitude das médias dos mapas sem GT associa-se **negativamente** a `F1(maximum)-F1(equal_mean)`.
- **H2**: para `fh_region_boundary|halfdisc_distribution_contrast|structure_tensor_coherence`, a correlação espacial Pearson média dos três pares de mapas associa-se **positivamente** a `F1(choquet_generalized_150)-F1(equal_mean)`.
- As hipóteses usam quatro descritores únicos, mas a avaliação também requer a construção e calibração **fixada** dos dois operadores e seus controles.
- Testes primários: Spearman unilateral por imagem original, permutação pré-definida, ajuste de Holm para **duas hipóteses** (FWER 5%); indicar também ICs e diagnóstico por domínio.
- Amostra **provisória**: 150 imagens de dois domínios (mínimo 60 por domínio). A análise de poder, os datasets e os IDs devem ser fixados antes de qualquer inspeção confirmatória.
- 100 imagens BSDS500 validation e 14 UDED do desenvolvimento **não** se tornam teste independente apenas por receberem um novo script.

## Sequência operacional

1. Ler [`PREREGISTRATION.md`](PREREGISTRATION.md) e [`protocol.json`](protocol.json).
2. Escolher duas fontes elegíveis, fechar o inventário das exposições históricas, identificar duplicatas e obter manifestos somente a partir dos arquivos e metadados brutos, **sem inspecionar GT/F1**.
3. Preencher `candidate_manifest.csv` a partir do [modelo](candidate_manifest.template.csv) sem inserir imagens antigas ou supostamente novas sem checagem.
4. Rodar `python scripts/check_paper_a_confirmation_manifest.py --manifest CAMINHO\candidate_manifest.csv` para conferir campos, IDs, SHA, contagem e divisões. A verificação é estrutural, **não comprova independência semântica**.
5. Fixar o código gerador de mapas, limiares (somente treino) e avaliador; completar e assinar [`FREEZE_CHECKLIST.md`](FREEZE_CHECKLIST.md); registrar o hash da coorte e criar um **novo commit de congelamento** mudando o status para `frozen`.
6. Só então executar a avaliação confirmatória em saída nova, sem sobrescrever Stage24, e relatar todos os resultados, inclusive negativos.

Para conferir apenas a validade do documento atual:

```powershell
python scripts\check_paper_a_confirmation_manifest.py --protocol-only
```

**Não há coleta, processamento de mapas novos, resultados confirmatórios nem modelo adaptativo em execução por este commit.** O plano inicial propunha cerca de 100–120 imagens; 150 é um alvo conservador preliminar para efeitos moderados, sujeito a análise de poder formal pré-freeze.

## Inventário local de imagens, sem GT (etapa de preparação)

Depois de atualizar esta branch, execute o scanner `scripts/inventory_paper_a_confirmation_images.py`.
Ele procura **somente arquivos de imagem** dentro de diretórios indicados explicitamente,
pula pastas de GT/máscaras/anotações e compara hashes com os dois manifestos UDED
arquivados e nomes com a lista das 100 imagens BSDS500 validation. Não lê
anotações, não gera mapas, não calcula F1 e **não atesta independência**.

Para identificar se há diretórios de datasets no computador:

```powershell
python scripts\inventory_paper_a_confirmation_images.py
```

Para inventariar dois diretórios de imagens escolhidos posteriormente (ajuste os caminhos reais):

```powershell
python scripts\inventory_paper_a_confirmation_images.py --dataset "DOMINIO_A=C:\\dados\\dominio_a\\imagens" --dataset "DOMINIO_B=C:\\dados\\dominio_b\\imagens"
```

A saída é local, em `results/local_dev/paper_a_confirmation_inventory/candidates.csv`,
ignorando o Git; inspecione as estatísticas retornadas pelo terminal. A lista
de candidatos deve ser auditada manualmente por origem/cena, quase duplicatas,
exposição anterior e disponibilidade de anotações `holdout` antes de preencher
o manifesto de confirmação ou congelar o protocolo. Não faça `git add .` em
datasets locais.

## Candidatos à coorte: auditoria preliminar 15/11/2026

Ver [`COHORT_AUDIT_20261115.md`](COHORT_AUDIT_20261115.md).
O inventário da workstation aponta BIPEDv2 train (200 imagens) como candidato local,
mas BIPEDv2 test e BSDS500 test permanecem protegidos por possível uso histórico.
A segunda fonte candidata é MultiCue/MDBD (100 cenas), dependente de nova auditoria
de sobreposição e da disponibilidade de GT por cena. O scanner agora recusa
pastas de GT, outputs e diretórios de teste como raiz.

## Segunda auditoria da BIPEDv2 train (apenas imagens, sem GT)

Após obter 200 linhas `PENDING_MANUAL` no inventário, execute:

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\audit_paper_a_confirmation_predata.py
```

Esse comando confere novamente os SHA-256 das 200 imagens BIPEDv2 train
e compara com manifestos UDED, com imagens UDED de desenvolvimento e com
os arquivos originais BIPED/BSDS test. **As partições test são lidas
apenas como bytes para SHA256, sem decodificação e sem GT**. A inspeção
visual automática por dHash é feita somente nas imagens BIPED train
e nas imagens UDED já expostas. Ela emite **alertas de possível quase
duplicação**, que exigem revisão humana. Não classifica nenhuma imagem
como aprovada. Não acessa F1 nem executa detectores.

Resultados locais: `results/local_dev/paper_a_confirmation_inventory/predata_audit/summary.json`
e `candidate_review.csv`. Não faça `git add .` nem compartilhe imagens
ou anotações protegidas. Caso Pillow não esteja disponível,
`python -m pip install pillow` ou a opção `--no-dhash`
(o segundo caso não detecta quase duplicatas).

## Revisao manual dos pares suspeitos BIPED train

A auditoria identificou os pares `RGB_171` / `RGB_172` e
`RGB_221` / `RGB_222`, apenas por dHash (distancia <= 5).
Para gerar uma prancha de comparacao **local**, usando exclusivamente
originais `BIPEDv2/edges/imgs/train/rgbr/real`:

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\review_paper_a_confirmation_pairs.py
Start-Process ".\results\local_dev\paper_a_confirmation_inventory\predata_audit\biped_train_near_duplicate_review.png"
```

A prancha PNG e o template CSV de decisao sao gerados somente em
`results/local_dev/paper_a_confirmation_inventory/predata_audit/`.
A validacao confere os SHA256 contra `candidate_review.csv`; nenhum GT,
teste, anotacao ou F1 e lido. dHash indica semelhanca, **nao prova**
identidade de cena. Evitar contar quadros da mesma sequencia como
observacoes independentes. Nao excluir automaticamente nem selecionar
as imagens com base no beneficio do agregador.

## Decisão visual humana — 15/11/2026

A comparação original (somente imagens BIPED train) revelou pares da mesma cena,
conforme confirmado visualmente pelo pesquisador em 15/11/2026:
`RGB_171`–`RGB_172` e `RGB_221`–`RGB_222` (dHash 1/64).
O arquivo versionado [`visual_duplicate_decisions.csv`](visual_duplicate_decisions.csv)
mantém as decisões auditáveis. Para evitar pseudorreplicação, mantemos apenas
`RGB_171` e `RGB_221` como representantes potenciais; `RGB_172` e
`RGB_222` não poderão ser sorteados para a coorte H1/H2.

Após atualizar a branch, rode:

```powershell
python .\scripts\apply_paper_a_visual_dedup.py
```

O script verifica que ambos os pares estavam alertados na auditoria, que as
decisões estão corretas e que o inventário inclui 200 originais. Ele
gera um CSV local com **198 imagens candidatas, ainda não certificadas**,
sem ler GT/F1 e sem modificar as imagens originais. Outras duplicações de
cena ou dependências temporais podem existir; não abrir resultados da
coorte antes de concluir auditoria histórica, segundo domínio, análise de
poder e congelamento.

## Auditoria de exposição histórica (sem GT/F1)

Depois da deduplicação visual (198 candidatas), execute:

```powershell
git fetch origin
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\audit_paper_a_confirmation_history.py
```

A ferramenta examina referencias a BIPED nos codigos-fonte versionados
das branches `origin/*` e procura identificadores/hashes das candidatas nos
manifestos de proveniência `results/paper_a_evidence`. Ela **nao** abre
imagens, GT ou CSV de F1, nem roda modelos. Cria localmente
`results/local_dev/paper_a_confirmation_inventory/predata_audit/historical_source_audit.json`.

**Limite essencial:** presença de BIPED em código não prova execução, e
ausência de referências não prova não exposição, sobretudo em logs
locais ignorados, versões não publicadas e decisões feitas fora do
repositório. Nenhuma candidata passa a estar certificada por isso.

## Classificação das referências históricas (sem GT/F1)

Quando a auditoria histórica retornar referências de código, separá-las por
menção explícita ao split train, ao split test, menção genérica ao BIPED e
identificação literal de alguma imagem candidata:

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\summarize_paper_a_confirmation_history.py --max-show 25
```

Lê apenas o JSON já produzido. Escreve
`results/local_dev/paper_a_confirmation_inventory/predata_audit/historical_source_triage.csv`
e imprime a classificação e até 25 trechos relevantes para revisão humana.
Um arquivo que menciona `train` não prova que foi executado;
a ausência de menção não certifica o conjunto. Não abre GT nem F1.

## Adjudicação das 120 referências ao BIPED

A triagem da workstation encontrou 11 referências ao split train: 2 pertencem
à pesquisa histórica e 9 aos scripts criados nesta branch. As duas antigas
afirmam que train não foi usado nos modelos Stage13d; uma delas faz verificação
de resolução de imagens **e GT train** se o preflight foi executado.
Leia [`HISTORICAL_BIPED_ADJUDICATION_20261115.md`](HISTORICAL_BIPED_ADJUDICATION_20261115.md).
Não tratar ausência de matches como certificação de independência.

## Evidências locais de execução histórica — 15/11/2026

Foram localizados arquivos produzidos por Stage13c (preflight técnico em
05/10) e Stage13d (transferência BIPED test em 06/10), bem como saídas UDED
com linhagens `09-MDBD-1C` e `13-BIPED-1C` em estágios subsequentes.
Ver [`LOCAL_EXECUTION_EVIDENCE_20261115.md`](LOCAL_EXECUTION_EVIDENCE_20261115.md).
As 198 candidatas BIPED train **não estão certificadas** e seguem sem F1
confirmatório. Não confundir preflight técnico de dimensões/GT com
seleção de operadores.

## Stage13c concluído; fonte MultiCue em pré-viabilidade

O preflight histórico da workstation retornou `Ready=True`, 200/200
pares train e 50/50 test, sem erros. Esse resultado comprova a integridade
técnica verificada na Stage13c, **não** independência estatística nem
inexistência de acessos ao GT train.

Leia [`STAGE13C_CLOSEOUT_AND_MULTICUE_PREFLIGHT_20261115.md`](STAGE13C_CLOSEOUT_AND_MULTICUE_PREFLIGHT_20261115.md).
Para verificar espaço livre e presença local do MultiCue, sem baixar ou ler GT:

```powershell
python .\scripts\preflight_paper_a_multicue_source.py
```

## MultiCue no volume F: (148,05 GiB livres)

O disco C: tem somente 3,63 GiB livres. Leia
[`MULTICUE_F_DRIVE_PLAN_20261115.md`](MULTICUE_F_DRIVE_PLAN_20261115.md)
para conferir destino `F:\MFI-Edge-Data\MultiCue` e executar o download
**somente mediante `--download`**, com cache/temporários no F:, SHA256,
revisão da fonte e sem extração/GT/F1.

## Falha SSL no cliente MultiCue resolvida por isolamento (15/11/2026)

A atualização global instalada para Hugging Face Hub 2.4.0 conflitou com
tokenizers 0.23.2 e falhou com RecursionError em truststore no Windows.
O arquivo MultiCue não começou a ser transferido na execução informada.

Usar scripts/setup_paper_a_multicue_env.ps1 para criar um venv no F:
com Hub 1.33.0, e executar a aquisição somente pelo Python desse venv.
Procedimento atualizado: [MULTICUE_F_DRIVE_PLAN_20261115.md](MULTICUE_F_DRIVE_PLAN_20261115.md).
Não desativar TLS nem promover coorte antes do congelamento do protocolo.

## MultiCue: inventário de nomes e tamanhos dentro do TAR (sem extração)

A aquisição no F: foi concluída em 15/11/2026, revisão imutável
`f47b14959e9764c8aa854cb7958d54462c46f8ef`, SHA256 oficial e local
`8e5fdb2ff7343e4a55f110e9ffe189b2c81689cd326324e34c6c73562191819e`,
arquivo com 3.575.680.805 bytes. A próxima auditoria não seleciona cenas nem GT.

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\inventory_paper_a_multicue_archive.py
```

O scanner lê cabeçalhos do TAR e seus nomes, tipos e tamanhos, percorre
o BZip2 em streaming (o fluxo comprimido precisa ser internamente descompactado
para alcançar os cabeçalhos posteriores), **não extrai membros**, não chama
`extractfile()`, não decodifica imagens/anotações, não calcula F1,
nem roda modelos. Gera no F: `archive_members_inventory.csv`
e `archive_member_summary.json`. O resumo permite planejar
extração seletiva posterior, nunca autoriza abrir GT antes do protocolo
e da análise de independência. Se quiser verificar o hash inteiro novamente,
adicione `--rehash` (releitura de 3,58 GB).

## Auditoria de correspondência cena/quadros/GT por nomes (MultiCue)

O inventário TAR verificou a fonte SHA256 e os 3.207 membros (3.200 arquivos;
3.100 PNG e 100 H5), sem extração. Com o CSV já gerado, rode:

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\audit_paper_a_multicue_scene_layout.py
```

O script lê **somente** o índice CSV e seu resumo JSON no F:, sem reler o
TAR, decodificar imagens/GT ou abrir H5. Agrupa o identificador de cena,
os frames por vista, o último frame esquerdo e as anotações cujos **nomes**
correspondem ao frame. O resultado detalhado é
`F:MFI-Edge-DataMultiCuemulticue_scene_name_candidates.csv`
e o relatório
`F:MFI-Edge-DataMultiCuemulticue_scene_name_summary.json`.
Nenhum nome de anotação certifica compatibilidade com o avaliador; a
identidade das cenas e o GT devem ser congelados antes de avaliações.

## Correção: 96 prefixos de captura não são 96 sequências MultiCue

O scanner de nomes inicial agrupou por prefixo numérico (p.ex., `4108`),
detectando 96 prefixos e duas anomalias: `4108` tem 40 quadros por vista
(quatro sequências possíveis) e `4113` tem 20 (duas sequências).
O dataset contém 100 H5: usar o stem do H5 como identificador da
sequência e seu quadro esquerdo final, não o prefixo isolado.

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\audit_paper_a_multicue_sequence_units.py
```

O scanner novo **não relê TAR, extrai nem abre imagens, H5, GT ou F1**.
Ele confere, exclusivamente por nomes, cada âncora H5, os dez quadros
anteriores até ela em cada vista, e a disponibilidade nominal de seis
PNG `edges` e cinco PNG `boundaries` por sequência. Emite:
`F:MFI-Edge-DataMultiCuemulticue_h5_anchored_sequence_summary.json`
e `F:MFI-Edge-DataMultiCuemulticue_h5_anchored_sequence_candidates.csv`.

**Unidade conservadora:** nunca contar mais de uma sequência do mesmo
prefixo de captura como independente enquanto não houver prova de
cenas distintas. Portanto, pode haver 100 sequências mas apenas 96
grupos conservadores antes da auditoria de sobreposição UDED.
Os nomes não certificam semântica de GT ou independência de cena.

## Materialização seletiva para auditoria de sobreposição (sem GT)

O scanner H5 verificou 100 sequências, 96 prefixos de captura e 2.000
imagens originais correspondentes a 1.100 nomes de anotações, sem erros.

A próxima etapa é extrair **somente um quadro original esquerdo por
sequência** (100 imagens; não abre GT). O script compara cada nome com
o manifesto H5 ancorado e a lista de membros previamente verificada,
aceita apenas `multicue/images/*.png` e tem limite de 25 MiB
por imagem e 1 GiB no total:

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\materialize_paper_a_multicue_source_frames.py
```

O TAR/BZip2 será percorrido em streaming uma vez. Saídas no F::
`source_frames_only/` (100 originais), `multicue_source_frames_only_manifest.csv`
(hashes por imagem) e `multicue_source_frames_only_summary.json`.
**Não** copia anotações, não abre HDF5/GT, não roda F1. Os 100 arquivos
são usados apenas na auditoria de possível sobreposição de cena/linhagem.
Gravação deliberadamente não permite sobrescrever imagens existentes.

## Auditoria visual MultiCue vs UDED e BIPED (sem anotações)

Após materializar os 100 originais no F:, execute:

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\audit_paper_a_multicue_image_overlap.py
Start-Process "F:\MFI-Edge-Data\MultiCue\multicue_image_only_100_scene_review.png"
```

A ferramenta checa novamente SHA256 de cada original MultiCue, compara
dHash e pHash (Pillow) com os originais UDED previamente usados
e as 198 candidatas BIPED train, e assinala similaridades *dentro* do
MultiCue em prefixos distintos. Os originais UDED com linhagem identificável
do split BSDS test não são decodificados perceptualmente.
Não abre GT, HDF5 nem resultados F1.

Os alertas aparecem em `multicue_image_only_overlap_flags.csv`
e no resumo `multicue_image_only_overlap_summary.json`, ambos no F:.
Uma prancha com as 100 imagens originais e, quando presente, a referência
UDED `09-MDBD-1C` é gerada para revisão humana.

A ausência de flags **não certifica independência**. As sequências
compartilhando prefixos 4108 e 4113 permanecem em hold; usar no máximo
uma unidade por prefixo antes de eventual confirmação documental de
independência. Toda escolha deve preceder F1 e o freeze do protocolo.

## UDED 09-MDBD-1C: auditoria visual direcionada

A auditoria geral encontrou 0 coincidências dHash/pHash **nos limiares fixados**,
mas isso não exclui overlap de cena da imagem UDED `09-MDBD-1C`
com outro quadro do vídeo MultiCue. Antes de congelar, gerar duas pranchas
**usando somente originais** e ranking sem limiar binário:

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\review_paper_a_multicue_mdbd_lineage.py --top-k 12
Start-Process "F:\MFI-Edge-Data\MultiCue\multicue_uded09_nearest_by_dhash.png"
Start-Process "F:\MFI-Edge-Data\MultiCue\multicue_uded09_nearest_by_phash.png"
```

Arquivos CSV/JSON no F: contêm distâncias e rankings de todas as 100
imagens finais esquerdas, não scores F1. **Sem GT/H5 ou inferência.**
Resultados da inspeção humana precisam ser registrados antes de eventuais
exclusões. Não declarar ausência de overlap caso nenhum dos 100 quadros
coincida: uma amostra histórica pode corresponder a outro frame da
mesma sequência, recorte ou uma distribuição MDBD não idêntica.

## Correção da prancha UDED 09-MDBD-1C (KeyError no render)

O primeiro comando da revisão direcionada terminou com KeyError: sequence_id.
O resultado de prepare_targets() usa a chave id para a sequência, e a prancha
agora acessa item["id"], consistente com o CSV de ranking.
A execução anterior gravou o CSV antes de falhar, mas não concluiu
as duas imagens nem o JSON final. A revisão pode ser repetida no mesmo
diretório sem novo download, extração ou auditoria geral.

Teste sintético (sem tocar datasets):

    python .\tests\test_paper_a_multicue_mdbd_lineage.py

Depois, rodar a ferramenta de revisão normalmente.

## Revisão direcionada MultiCue/UDED 09: status real em 15/11

Após corrigir a chave `id` do desenho de prancha, o teste sintético passou
e a revisão das 100 imagens finais esquerdas concluiu. Melhor distância
dHash = 23/64; melhor pHash = 20/63; nenhuma exclusão automática.
**Não há certificação de não sobreposição entre cenas**: as duas pranchas
foram geradas, mas ainda não se registrou uma inspeção visual humana.
Ver [`MULTICUE_UDED09_RANKED_REVIEW_STATUS_20261115.md`](MULTICUE_UDED09_RANKED_REVIEW_STATUS_20261115.md).

## Confirmado: UDED 09-MDBD-1C já aparece no MultiCue 4113

Revisão visual das pranchas detectou a mesma imagem do bicicletário em
`4113_left_0082` (com recorte diferente); SIFT/RANSAC dos thumbnails
confirma forte alinhamento. Isso demonstra falso negativo dos hashes
globais para recortes. **Excluir 4113_left_0082; manter 4113_left_2396
em hold** até revisão de independência da captura. Ver
[`MULTICUE_UDED09_CONFIRMED_OVERLAP_20261115.md`](MULTICUE_UDED09_CONFIRMED_OVERLAP_20261115.md).
Auditoria SIFT dos originais: `python .\scripts\audit_paper_a_multicue_mdbd_geometry.py`
(sem GT/F1; sem exclusões automáticas).

## Confirmado nas imagens originais: 2.101/2.116 correspondências

Auditoria SIFT/RANSAC nos 100 originais MultiCue encontrou **1 sinalização**,
precisamente `4113_left_0082`: 2.101/2.116 inliers = 99,291%. 
Exposição prévia UDED `09-MDBD-1C` comprovada geometricamente; sequência
excluída, prefixo `4113` retido integralmente por prudência.
Máximo de grupos MultiCue antes de demais auditorias: **95**.
Ver [`MULTICUE_UDED09_CONFIRMED_OVERLAP_20261115.md`](MULTICUE_UDED09_CONFIRMED_OVERLAP_20261115.md).

## Próximo gate: SIFT UDED histórico completo (com cache no F:)

Para verificar recortes entre as 27 imagens UDED já usadas no desenvolvimento
e os 100 quadros MultiCue originais, sem GT/F1, use
`python .\scripts\audit_paper_a_multicue_all_uded_geometry.py`.
Há cache de SIFT por SHA-256 e checkpoints por referência para evitar
reprocessamento. O teste com imagens sintéticas é
`python .\tests\test_paper_a_multicue_all_uded_geometry.py`.
Documentação: [`MULTICUE_ALL_UDED_GEOMETRY_SCREEN_20261115.md`](MULTICUE_ALL_UDED_GEOMETRY_SCREEN_20261115.md).

## Revisão de 25 alertas SIFT da UDED histórica

A execução concluiu 2.700 comparações, sinalizando **25 pares**, dos quais
apenas `09-MDBD-1C` ↔ `4113_left_0082` tem identidade de cena confirmada.
Novos alertas não são exclusões; as pranchas de 25 pares são geradas por
`python .\scripts\render_paper_a_multicue_uded_overlap_review.py` no F:
sem repetir SIFT/GT/F1. Ver
[`MULTICUE_ALL_UDED_GEOMETRY_RESULT_20261115.md`](MULTICUE_ALL_UDED_GEOMETRY_RESULT_20261115.md).

## Adjudicação visual dos 25 alertas geométricos — 15/11/2026

A revisão das cinco pranchas identificou 1 par de **mesma cena**
(`09-MDBD-1C` / `4113_left_0082`) e 24 pares **visualmente distintos**.
Isso fecha os alertas no nível das fotos exibidas, **não** certifica a
independência histórica de sequências completas nem autoriza acesso a GT/F1.
Foi identificado falso positivo geométrico sério (277/354 inliers em cenas
visualmente sem relação), exigindo diagnóstico do matcher/homografia.
Ver [`MULTICUE_VISUAL_25_ADJUDICATION_20261115.md`](MULTICUE_VISUAL_25_ADJUDICATION_20261115.md)
e [`multicue_visual_25_decisions.csv`](multicue_visual_25_decisions.csv).

## Diagnóstico de falsos positivos SIFT (cache, pré-F1)

Antes de confiar em correspondências geométricas, execute os testes
`tests/test_paper_a_multicue_sift_false_positives.py` e a análise
`scripts/diagnose_paper_a_multicue_sift_false_positives.py`.
Ela reaproveita `.npz` de SIFT e confere 25 alertas com matching recíproco
e dispersão dos inliers, sem decodificar imagens ou abrir GT/F1.
Ver [`MULTICUE_SIFT_FALSE_POSITIVE_DIAGNOSTICS.md`](MULTICUE_SIFT_FALSE_POSITIVE_DIAGNOSTICS.md).

## Diagnóstico BF e retriagem integral, sem abrir GT/F1

Matching recíproco BF exato preservou 2.100/2.100 inliers do par de
imagem exposta UDED/MultiCue, mas eliminou os falsos alarmes FLANN mais
fortes (277, 267, 195 e 131 inliers anteriores → zero).
Para avaliar 2.675 pares ainda não verificados sem depender de FLANN,
execute `python .\scripts\rescreen_paper_a_multicue_uded_exact_mutual.py`.
Retoma por checkpoint no F: e reutiliza os 25 pares já reavaliados.
Ver [`MULTICUE_EXACT_MUTUAL_FULL_RESCREEN.md`](MULTICUE_EXACT_MUTUAL_FULL_RESCREEN.md).

## Triagem UDED × MultiCue concluída no escopo de 2.700 pares

Retriagem BF recíproca: 2.700/2.700 pares, apenas a correspondência
histórica `09-MDBD-1C` / `4113_left_0082`, nenhuma nova flag.
O prefixo 4113 permanece fora da seleção. Esta é uma conclusão
**somente para os quadros finais e imagens UDED originais auditados**.
Ver [resultado completo](MULTICUE_EXACT_MUTUAL_RESCREEN_RESULT_20261115.md).

## Poder: triagem pré-freeze sem usar GT/F1

Rode `python .\scripts\estimate_paper_a_power_sensitivity.py` para
uma grade de efeitos conservadores. Veja
[sensibilidade de poder](PREFREEZE_POWER_SENSITIVITY.md).
A aproximação Fisher-z não substitui a simulação final do teste Spearman
e da permutação por domínio.

## Próximo gate estatístico: simulação sintética por domínio

Nova simulação com diferenças BIPED/MultiCue, postos de Spearman dentro
de cada domínio, permutação restrita, Holm e poder conjunto H1/H2.
O método é **proposta ainda não congelada**, não substitui o protocolo.
Execute `python .\tests\test_paper_a_domain_blocked_power.py` e
`python .\scripts\simulate_paper_a_domain_blocked_power.py`.
Ver [`PREFREEZE_DOMAIN_BLOCKED_POWER_SIMULATION.md`](PREFREEZE_DOMAIN_BLOCKED_POWER_SIMULATION.md).

## Simulação por domínio: execução concluída (15/11)

5/5 testes passaram; 30 cenários sintéticos gerados. Para N=150,
poder de confirmação simultânea de H1+H2 de 57,6% sob |rho|=0,20,
84,8% sob |rho|=0,25 e 95,4% sob |rho|=0,30 homogêneos.
Não equivale a poder real, nem fixa coorte/estatística. Inspeção de código
identificou decisões pendentes no GT multi-anotador, limiares e
Choquet calibrado. Ver
[`DOMAIN_BLOCKED_POWER_RESULT_AND_EVALUATOR_GATES_20261115.md`](DOMAIN_BLOCKED_POWER_RESULT_AND_EVALUATOR_GATES_20261115.md).

## Escolha amostral preliminar, ainda não congelada

Da tabela completa do usuário: N=220 (125 BIPED+95 MultiCue) tem poder
conjunto sintético de 82,3% em |rho|=0,20 homogêneo; N=180 (90+90)
tem 90,5% em |rho|=0,25, mas só 68,2% em |rho|=0,20.
O desenho 220 é **meta condicional**, depende de todos os 95 grupos
MultiCue ainda não certificados; não substituir automaticamente grupos
perdidos com BIPED sem nova simulação e decisão pré-F1.
Ver [`SAMPLE_SIZE_CONDITIONAL_DECISION_20261115.md`](SAMPLE_SIZE_CONDITIONAL_DECISION_20261115.md).

## Próximo gate: tarefa `edges` e política multi-anotador (proposta)

Recomendação fundamentada nas documentações originais: BIPEDv2 fornece
detecção de bordas (*edges*) e MultiCue tem anotações separadas de
`edges` e `boundaries`. Para comparar H1/H2, a tarefa primária candidata
é `edges`; o F1 de MultiCue seria calculado separadamente para cada uma
das seis referências, depois **média por imagem**. O F1 de BIPED usa
uma referência, se validada. **Nomes não certificam conteúdo.**
Contrato e decisões ainda não congeladas:
[`GT_EDGES_MULTIANNOTATOR_CONTRACT_PROPOSAL.md`](GT_EDGES_MULTIANNOTATOR_CONTRACT_PROPOSAL.md).
Checagem sem GT: `python .\scripts\check_paper_a_multicue_gt_task_names.py`.

## Teste sintético do contrato de F1 multi-anotador (pré-freeze)

Ver [`PAIRED_F1_SYNTHETIC_CONTRACT_PROPOSAL.md`](PAIRED_F1_SYNTHETIC_CONTRACT_PROPOSAL.md).
O módulo [`src/paper_a_confirmation_paired_f1.py`](../../src/paper_a_confirmation_paired_f1.py)
avalia máscaras booleanas sintéticas com 1 GT BIPED ou 6 GT MultiCue
em matching exato um-a-um, sem unir GTs nem multiplicar N. Rejeita
conversões 3D e uint8 implícitas e máscaras de geometria diferente.
Executar `python .\tests\test_paper_a_paired_f1_contract.py`.
**Não abrir GT de coorte real por este módulo antes do freeze.**

## P0 — auditoria estática de proveniência dos parâmetros

Execute no ambiente `.venv`: `python .\tests\test_paper_a_parameter_provenance_P0.py`
e `python .\scripts\audit_paper_a_parameter_provenance_P0.py`.
A ferramenta só lê código-fonte e documento de protocolo; usa `stat()`
para três artefatos históricos sem ler seus conteúdos (podem conter F1).
Ver [`PARAMETER_PROVENANCE_P0.md`](PARAMETER_PROVENANCE_P0.md).

## P0.1 — manifesto saneado das receitas específicas H1/H2

Execute `python .\tests\test_paper_a_h1h2_recipe_P0_1.py` e
`python .\scripts\prepare_paper_a_h1h2_recipe_P0_1.py`.
Cria modelo JSON auditável, *sem F1 nem valores de capacidade/limiares
inventados*, com checksums de código e pendências de proveniência.
Veja [`PARAMETER_RECIPES_P0_1_DRAFT.md`](PARAMETER_RECIPES_P0_1_DRAFT.md).

## P0.2 — auditoria dos metadados de desenvolvimento UDED-14

Os manifestos históricos versionados contêm 14 imagens exploratórias,
13 descritores cada, e metadados dos 56 mapas H1/H2 necessários.
Isso **não** certifica elegibilidade ou parâmetros treinados.
Execute `python .\tests\test_paper_a_development_lineage_P0_2.py` e
`python .\scripts\audit_paper_a_development_lineage_P0_2.py`.
Ver [`DEVELOPMENT_LINEAGE_P0_2.md`](DEVELOPMENT_LINEAGE_P0_2.md).
