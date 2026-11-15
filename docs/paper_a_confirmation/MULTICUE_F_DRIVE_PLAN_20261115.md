# Plano de armazenamento da coorte MultiCue no disco F: — 15/11/2026

## Preflight do Windows

Discos informados pelo pesquisador:

- **C:** 3,63 GiB livres — não usar para novo dataset.
- **F:** 148,05 GiB livres — volume selecionado para fonte, cache, arquivos temporários e eventual materialização.
- **G:** 3,45 GiB livres — não usar.

Fonte: [Serrelab/multicue-boundary-detection](https://huggingface.co/datasets/Serrelab/multicue-boundary-detection). Distribuição oficial em arquivo único `multicue-dataset.tar.bz2`, aproximadamente 3,4 GB. A ausência de arquivos por cena impede download seletivo trivial na distribuição atual. O download do pacote **não** significa extração nem utilização de GT.

## Caminho e pré-verificação

```powershell
cd "C:\Users\Windows 11\Documents\MFI-Edge"
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\preflight_paper_a_multicue_source.py --destination "F:\MFI-Edge-Data\MultiCue"
python .\scripts\acquire_paper_a_multicue_archive.py --destination "F:\MFI-Edge-Data\MultiCue"
```

Os dois comandos Python acima **não fazem download**. Verifique que o espaço livre
informado pertence ao F:.

## Correção do erro SSL no Windows (15/11/2026)

A atualização global instalou huggingface_hub 2.4.0, que conflita com
tokenizers 0.23.2 (requer Hub <2). A chamada de metadados falhou com
RecursionError em truststore, antes do download. Não desative verificações
de certificados HTTPS e não faça upgrades globais sem limites.

A nova aquisição utiliza ambiente virtual isolado no F: com a versão exata
huggingface_hub[hf_xet]==1.33.0. O bootstrap não baixa o dataset:

~~~powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_paper_a_multicue_env.ps1
~~~

Depois de confirmar que a instalação retornou sucesso, iniciar o download
explicitamente com o Python isolado:

~~~powershell
& "F:\MFI-Edge-Data\Venvs\multicue-download\Scripts\python.exe" .\scripts\acquire_paper_a_multicue_archive.py --destination "F:\MFI-Edge-Data\MultiCue" --download
~~~

O `--download` é a única opção que permite transferir dados. O script:
(a) exige 15 GiB livres; (b) grava caches e temporários de Hugging Face no F:;
(c) consulta metadados da origem oficial, resolve e congela o commit do dataset;
(d) baixa somente o arquivo compactado via cliente Hugging Face;
(e) confere tamanho e SHA256 local, comparando com o hash LFS oficial **se**
ele estiver disponível nos metadados; (f) registra
`F:\MFI-Edge-Data\MultiCue\archive_provenance.json`.

**Não extrai**, não lê GT, não calcula F1 nem roda detectores. O cliente
Hugging Face pode criar pastas internas `.cache` no destino, sempre no F:.

## Etapas posteriores, ainda bloqueadas

1. Verificar somente a lista de membros do tar, identificar a organização dos
   100 grupos de cenas e as anotações disponíveis.
2. Preparar regra de seleção de uma imagem por cena (último frame esquerdo anotado),
   auditando sobreposição potencial com `09-MDBD-1C` e outros históricos.
3. Extrair **somente o necessário**, sob regras de path-safety e integridade.
4. Fixar política de avaliação, análise de poder, coorte e parâmetros em novo
   commit antes de examinar resultados H1/H2.

Não copiar dados brutos ao GitHub nem usar `git add .` indiscriminadamente.
