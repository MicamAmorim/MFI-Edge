# Fechamento da verificação Stage13c e pré-viabilidade MultiCue — 15/11/2026

## Resultado comprovado do preflight Stage13c

Saída da workstation compartilhada pelo pesquisador:

- `Stage = 13c-biped-preflight`
- `Ready = True`, `Errors` vazio
- `SplitRole = train=unused; test=frozen_external_replication`
- `TrainImages = 200`, `TrainGTFileCount = 200`
- `TestImages = 50`, `TestGTFileCount = 50`

**Interpretação limitada:** o inventário técnico da Stage13c encontrou os 250
pares imagem/anotação esperados. O código existente inspeciona imagens e GTs
para validar nomes e dimensões, de modo que não se deve dizer que o GT train
nunca foi acessado. O preflight não treina nem seleciona agregadores no trecho
de código examinado; a execução histórica Stage13d usa explicitamente BIPED
**test**. Portanto, a alegação sustentável é **nenhuma evidência encontrada
até aqui de uso do BIPED train para selecionar os operadores**, e não prova
de não exposição em todos os estágios.

Continuam em auditoria `198` originais BIPED train após exclusão,
por inspeção visual, de `RGB_172` e `RGB_222`. O restante não está certificado
como independente em termos de cena/seqüência ou uso por outras execuções.

## Segundo domínio proposto — sem baixar dados ainda

A fonte oficial Serre Lab publica
[MultiCue Boundary Detection](https://huggingface.co/datasets/Serrelab/multicue-boundary-detection)
sob licença CC BY 4.0, com 100 cenas, sequências estéreo de 10 quadros e resolução
1280×720. O repositório possui um arquivo único
`multicue-dataset.tar.bz2`, divulgado com aproximadamente 3,4 GB.
Não há estrutura de split acessível diretamente no dataset viewer: a
estrutura interna exata só pode ser certificada ao examinar o tar real.

A literatura descreve a anotação do último quadro esquerdo, com tarefas
distintas de `edges` e `boundaries`. Para o Paper A, usar no máximo uma
observação por cena, mas escolher a tarefa/GT e protocolo de matching
**antes** de examinar F1 ou tentar confirmar H1/H2.

**Sobreposição potencial:** `09-MDBD-1C` consta na exploração UDED histórica.
Não assumir que somente essa cena está contaminada: conferir imagens,
hashes, linhagem e quaisquer outras cenas compartilhadas antes de congelar.

## Próximo comando de baixo custo

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\scripts\preflight_paper_a_multicue_source.py
```

O preflight apenas informa espaço livre no volume de destino, caminhos
locais candidatos e presença/tamanho do arquivo compactado, **sem rede,
download, inspeção de GT, extração, avaliação ou cálculo de F1**.
Nenhum compromisso com baixar 3,4 GB é feito sem verificar o espaço
necessário para arquivo compactado **e conteúdo extraído**.

## Gates ainda pendentes

1. Revisão de dependência entre cenas BIPED train (dHash sozinho não prova
   que 198 são 198 unidades amostrais independentes).
2. Confirmar disponibilidade e estrutura interna do MultiCue, anotações
   compatíveis e exclusões por linhagem UDED/MDBD.
3. Fixar política de limiares/calibração, implementações e avaliador idêntico
   entre candidato e controle.
4. Análise de poder conservadora antes da seleção final de 150 imagens.
5. Pré-registro congelado e commit de coorte **antes** de acessar GT/F1 novos.

**Nenhum resultado confirmatório foi gerado nesta etapa.**
