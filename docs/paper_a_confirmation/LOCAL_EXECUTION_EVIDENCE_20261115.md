# Evidência local de execução histórica — 15/11/2026

**Escopo:** metadados de nomes de arquivos, tamanhos e datas apresentados pelo pesquisador; nenhum conteúdo de métricas F1 da coorte confirmatória foi aberto e nenhuma imagem/GT foi reprocessada nesta etapa.

## 1. Artefatos históricos observados na workstation

| Evidência de caminho relativo a `results/` | Última modificação informada | Significado limitado |
|---|---|---|
| `automation/stage13c_biped_preflight/summary.json` | 05/10/2026 23:39:20 | Saída persistida do preflight Stage13c; inspecionar campos `checks`, `errors`, `ready` |
| `external/stage13d_biped_transfer/external_metrics.csv` | 06/10/2026 00:29:41 | Saída de métricas da transferência BIPED test; **não abrir para selecionar candidatos confirmatórios** |
| `external/stage13d_biped_transfer/per_image_metrics.csv` | 06/10/2026 00:29:41 | Métricas históricas por imagem BIPED test; **não usar para definir H1/H2** |
| `external/stage13d_biped_transfer/summary.json` | 06/10/2026 00:29:41 | Saída persistida da transferência, que o código existente executa sobre BIPED test |

Os arquivos existem na máquina; datas de modificação não são prova absoluta de quando
cada função científica foi executada. O script `automation/stage13c_biped_preflight.py`
contém `Image.open` para conferir dimensão de imagem **e anotação** em ambos os splits
`train` (200) e `test` (50). Essa etapa não ajusta modelos ou limiares no
código revisto, porém dá evidência de que o split train **pode ter sido inspecionado tecnicamente**.
O script `run_stage13d_biped_transfer.py` carrega o split `test` por sua
função `load_test_items` e documenta `train=unused` para ajuste/avaliação.

## 2. Artefatos de linhagem UDED observados

Diretórios `results/local_dev/stage16*`, `stage23*` e
`stage24_paper_a_recertification/float_predictions_uded/` contêm arquivos com
nomes `09-MDBD-1C` e `13-BIPED-1C`. São imagens da coorte UDED já
utilizadas, **não provas de que as 198 imagens BIPED train foram usadas**.
Esses nomes reforçam a necessidade de detectar sobreposição de **cena e
linhagem**, não somente de hashes exatos, com o segundo domínio MultiCue/MDBD.

## 3. Status metodológico

- Candidatas BIPED train: 198 após 2 exclusões visuais documentadas.
- 14 branches de código e 40 manifestos científicos auditados; zero identificador/hash
  das 198 candidatas nos manifestos examinados.
- Código antigo relacionado a `train`: duas referências, consistentes com
  declaração de não utilização experimental pelo Stage13d e preflight com
  leitura técnica de dimensões no Stage13c.
- **Não certificado**: ainda faltam revisão dos campos do resumo Stage13c,
  possíveis outros acessos locais não rastreados e avaliação de independência
  entre cenas/sequências, além do segundo domínio.
- Protocolo `draft_not_frozen` permanece inalterado. Não abrir novos GTs, não
  computar F1 confirmatório e não ajustar hipóteses por resultados.

## 4. Próxima leitura restrita: apenas integridade do preflight

Executar no PowerShell na raiz do repositório:

```powershell
$pf = Get-Content '.\results\automation\stage13c_biped_preflight\summary.json' -Raw | ConvertFrom-Json
[pscustomobject]@{
    Stage = $pf.stage
    Ready = $pf.ready
    SplitRole = $pf.split_role
    TrainImages = $pf.checks.train.images
    TrainGTFileCount = $pf.checks.train.ground_truth
    TestImages = $pf.checks.test.images
    TestGTFileCount = $pf.checks.test.ground_truth
    Errors = ($pf.errors -join '; ')
} | Format-List
```

**Atenção:** esse comando acessa somente um resumo técnico histórico. Não
abre `external_metrics.csv`, `per_image_metrics.csv`, imagens ou anotações.
Ele não é uma certificação de independência. A presença de `TrainGTFileCount`
documenta a verificação de arquivos, não uma avaliação de performance.
