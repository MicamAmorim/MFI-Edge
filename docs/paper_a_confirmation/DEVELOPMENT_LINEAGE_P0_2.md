# P0.2 — desenvolvimento UDED: auditoria de metadados de origem (sem GT/F1)

**Estado:** metadados auditáveis; elegibilidade de ajuste ainda NÃO aprovada.

## Evidência antes da execução

O repositório já contém um manifesto histórico Stage24GL com 15 registros
(14 imagens da descoberta, uma original protegida excluída) e uma tabela
de 182 descritores float32 (13 descritores × 14 imagens). O subconjunto
necessário para H1/H2 é formado por 4 descritores × 14 imagens = 56
registros já documentados. Nenhum desses números equivale a um ajuste
aprovado, e a integridade dos bytes de mapas cacheados não é provada
apenas pelo manifesto.

Arquivos-fonte de metadados:

- `results/paper_a_evidence/stage24gl/campaign/native_dataset_manifest.json`
- `results/paper_a_evidence/stage24gl/campaign/descriptor_provenance.csv`
- `docs/paper_a_confirmation/protocol.json`
- Rascunho P0.1 no volume F:

Este script NÃO abre os PNGs, GTs, H5s, NPYs, resultado de F1 ou
`frozen_models.json`. O manifesto de origem contém hashes históricos
de GT, mas o script não reproduz esses campos nem acessa GT real.
Ele verifica apenas IDs, fonte das imagens e metadados de descritores.

## Comandos

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
.\.venv\Scripts\Activate.ps1
python .\tests\test_paper_a_development_lineage_P0_2.py
python .\scripts\audit_paper_a_development_lineage_P0_2.py
```

Saída única: `F:\MFI-Edge-Data\MultiCue\paper_a_development_lineage_P0_2.json`.

## Interpretação do gate

`P0_2_DEVELOPMENT_METADATA_AUDITED_TRAINING_NOT_CERTIFIED` significa:

1. A fonte exploratória UDED-14 está documentada e há metadados de
   todas as quatro espécies de mapas requeridos para H1/H2.
2. Essas mesmas 14 imagens foram usadas para descobrir as relações H1/H2.
   Se forem designadas para calibrar modelos, seu papel será
   **exclusivamente desenvolvimento**, com seleção confirmatória
   estritamente independente e linhagem auditada.
3. Há exposição cruzada conhecida de `09-MDBD-1C` com o prefixo MultiCue
   `4113`, que permanece excluído do conjunto confirmatório.
4. **Ainda NÃO existe prova dos valores ajustados de H1 e H2.**
   O relatório nem fabrica parâmetros, nem promove treino automaticamente.
5. A próxima decisão é conferir se já existe exportação saneada dos
   parâmetros H1/H2 para treino, ou autorizar ajuste limitado sobre um
   conjunto de desenvolvimento designado (nunca sobre BIPED/MultiCue
   candidatos à confirmação).

Não é necessário repetir a triagem 2.700 pares, simulações de poder
nem reconstrução de 14 × 4 mapas sem evidência de cache inválido.

**Não editar `protocol.json` para frozen nesta etapa.**
