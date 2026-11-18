# Paper A — reproduzibilidade comunitária experimental

**ATENÇÃO: ESTA CAMADA MODULAR NÃO FOI VALIDADA DE PONTA A PONTA.**

A branch repro/paper-a-end-to-end foi criada a partir do commit
37661abbe16700e780bc3e99027dc1c470c6e44a, da branch
experiment/paper-a-conditional-confirmation. Mantém o código científico
original, os dados numéricos e os registros do congelamento sem
alterações. Os novos módulos em reproduction/ são adaptadores
experimentais e **não** substituem os scripts científicos que geraram o
artigo.

## 1. Instalação: Python, MATLAB e Git

Para Linux, instale Git, Python 3.12, python3-venv, pip e dependências
nativas de NumPy/SciPy e Matplotlib. Para executar a avaliação Berkeley
original, instale MATLAB com **Image Processing Toolbox** e as fontes
e binários MEX/compilador compatíveis do avaliador original. Não é
necessário MATLAB para conferir somente os resultados numéricos
arquivados. Os scripts não instalam MATLAB nem distribuem componentes
proprietários.

Para Windows, instale Git, Python 3.12 com o launcher "py" e MATLAB com
Image Processing Toolbox para as etapas oficiais. O setup usa um
ambiente virtual próprio. Os ambientes congelados originais devem ser
consultados em docs/paper_a_confirmation/successor_vsb100_20261117/environment.json
e nos manifestos de Stage24; a lista de dependências comunitária não
garante a reprodução byte a byte do ambiente de trabalho.

## 2. Clonar e verificar os resultados já arquivados

Linux:

~~~bash
git clone --branch repro/paper-a-end-to-end --single-branch https://github.com/MicamAmorim/MFI-Edge.git
cd MFI-Edge
bash reproduce.sh --mode verify
~~~

Windows PowerShell:

~~~powershell
git clone --branch repro/paper-a-end-to-end --single-branch https://github.com/MicamAmorim/MFI-Edge.git
cd MFI-Edge
powershell.exe -ExecutionPolicy Bypass -File .\reproduce.ps1 --mode verify
~~~

O modo verify executa o verificador de proveniência Stage24
(scripts/verify_stage24gl_repro.py --check-git), verifica o SHA256 de
PAIRED_OUTCOMES.csv, confere 312 unidades primárias e 48 secundárias,
recomputa as correlações Spearman ponderadas e os ganhos médios pareados
a partir das observações arquivadas. Compara o resultado com
EXECUTION_RESULTS.json sem precisar das imagens brutas.

**Importante:** o modo verify padrão somente *lê* os p-valores e
intervalos bootstrap publicados. Para repetir o procedimento de
100.000 permutações e 2.000 reamostragens por hipótese com as sementes
congeladas, use:

~~~bash
bash reproduce.sh --mode verify --deep
~~~

Relatórios são gravados em
reproduction-work/reports/paper_a_reproduction.md e
reproduction-work/reports/paper_a_reproduction.json.

Esse é um **replay de resultados numéricos**; não é uma reprodução de
toda a pesquisa desde a imagem original.

## 3. Pipeline completo proposto (ainda não certificado)

~~~bash
bash reproduce.sh --mode full \
  --uded-root ./reproduction-work/datasets/UDED \
  --bsds-val ./reproduction-work/datasets/BSDS500/data/images/val
~~~

A reprodução foi organizada no código em etapas legíveis:

1. descobrir fontes e verificar integridade;
2. extrair as evidências (Stage23C; 13 descritores);
3. caracterizar complementaridade (Stage23D; 78 pares);
4. comparar operadores (Stage23E; 15 conjuntos × 8 famílias);
5. examinar transferência BSDS500 validation (Stage23F);
6. verificar o arquivo da recertificação Stage24 ou, somente por opt-in,
   executar o runner histórico;
7. comparar H1/H2 com o registro numérico fixado;
8. gerar relatório explícito com conclusões e bloqueios.

A implementação ainda tem limitações específicas:

- Stage23 é reexecutado chamando o código científico histórico, cujos
  caminhos de cache/resultados são relativos à raiz do checkout.
- Stage24 possui dependências antigas de MATLAB, arquivos de entrada
  locais e etapas de publicação que podem preparar mudanças no Git.
  O padrão verifica o arquivo público. A opção
  --allow-legacy-stage24 habilita o runner original e exige que o
  pesquisador inspecione antecipadamente os seus efeitos locais.
  Essa opção não torna o código portátil ou validado.
- O executor original de H1/H2
  (scripts/execute_paper_a_vsb100_successor.py) usa caminhos históricos
  do drive F:, fontes byte-exatas, verificação da revisão independente e
  congelamento científico. A interface nova **não executa essa etapa
  a partir de imagens** e não a substitui por uma implementação não
  autorizada. O modo full deve terminar declarando reprodução parcial,
  nunca sucesso científico completo.
- Se alguma etapa importante falhar, os adaptadores devem parar,
  registrar diagnóstico e nunca inventar resultados ou alterar
  limiares, GT, métricas ou amostras.

## 4. Aquisição das bases

Um registro de fontes está em reproduction/datasets.json. O reprodutor
**só baixa arquivos diretamente de uma URL HTTPS quando existe SHA256
esperado explicitamente configurado**. A ausência de URLs oficiais
fixadas não autoriza adivinhar links, substituir um espelho sem
proveniência ou reutilizar outra divisão do dataset.

| Fonte | Função científica | Aquisição |
|---|---|---|
| UDED | Descoberta e validação cruzada, 14 originais | Distribuição xavysp/UDED; o diretório precisa conter test_pair.lst e seus arquivos associados |
| BSDS500 | Transferência, 100 imagens validation | Dados e avaliador originais Berkeley, inclusive Ground Truth; o diretório de val precisa conter exatamente 100 JPGs |
| MultiCue | 62 capturas primárias | Existe downloader SHA-verificado em scripts/acquire_paper_a_multicue_archive.py; o download completo é grande e requer pacote huggingface_hub |
| NYUDv2 ECCV14 | 153 salas primárias | Requer imagens RGB exatas e os arquivos de anotação do autor |
| VSB100 | 97 vídeos primários | Requer os arquivos General fullres e frames selecionados originais |
| BIPEDv2 | 48 imagens secundárias | Requer distribuição original e os hashes congelados; nunca é domínio principal |

O manifesto de fontes padrão não contém downloads diretos não
verificados. Um pesquisador poderá copiar reproduction/datasets.json
para um arquivo local e fornecer --datasets-config com URLs HTTPS e
SHA256 corretos, ou obter os dados manualmente. Arquivos de terceiros
devem respeitar seus termos de licença e acesso. Os downloads brutos
por si só não reproduzem a seleção das cenas congeladas, seus hashes e
a semântica dos ground truths.

## 5. Interpretação estatística

A confirmação publicada refere-se a 312 unidades principais de
MultiCue, NYUDv2 e VSB100. BIPED48 é somente diagnóstico secundário.
H1 associa a diferença média de evidência entre half-disc e PMI ao
ganho relativo do máximo contra média; H2 associa correlações dos
mapas FH/half-disc/tensor ao ganho relativo de Choquet generalizado
contra média. A conclusão H1 não estabelece ganho médio positivo;
H2 permaneceu não confirmada. O avaliador nativo customizado da
confirmação não é o avaliador oficial Berkeley.

A documentação do protocolo, receitas, hashes, análises e limites da
revisão humana/IA está em
docs/paper_a_confirmation/successor_vsb100_20261117/README.md.

## 6. Issues e contribuições

Abra um issue em https://github.com/MicamAmorim/MFI-Edge/issues
incluindo SO e versão, comando, versão de Python/MATLAB e toolboxes,
commit, estágio, log, hashes e valores esperados/observados. O formulário
recomendado está em .github/ISSUE_TEMPLATE/paper-a-reproduction.md
nesta branch.

Prioridades da comunidade: fixar URLs oficiais e hashes das fontes,
desacoplar os paths legados de Stage24, viabilizar Berkeley+MEX em
Linux, portar o executor de confirmação mantendo o gate de freeze,
adicionar fixtures e testes CI, e medir o grau real de reprodutibilidade.

**Evitar alterações que tornam o pipeline rodável ao custo de mudar
a ciência.** Portabilidade e integridade metodológica são exigências
distintas; toda exceção deve ser documentada no relatório.
