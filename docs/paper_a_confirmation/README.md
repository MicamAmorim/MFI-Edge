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
