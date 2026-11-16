# P0 — auditoria estática da proveniência dos parâmetros

**Status: pré-freeze, não confirmatório.** Verifica apenas um conjunto explícito de
arquivos Python versionados e o documento protocol.json. Não importa módulos
científicos; não lê imagens, ground truth, H5, mapas, inferências, CSV de F1
nem conteúdo de artefatos históricos. Usa apenas stat() nos três caminhos
históricos de artefatos definidos em código.

## O que estamos investigando

- choquet_generalized_150: capacidade supervisionada treinada com GT de treino
  e transformação de expoente gamma = 1,5; sua capacidade específica de H2
  ainda não foi fixada para o novo experimento.
- legacy_sigmoid: não é uma calibração independente; depende de midpoint e
  scale previamente ajustados em fit_membership no conjunto de treino.
- NMS: thin_score em modo nms_image usa gradient_orientation com sigma=1.0
  e non_maximum_suppression; hashes das fontes serão registrados.
- Limiares: choose_threshold lê GT do conjunto de treino. Os valores exatos
  de H1, H2 e equal_mean devem ser fixados sem recorrer ao GT confirmatório.
- O frozen_models.json histórico pode conter fit_all_UDED_F1_NOT_HELDOUT:
  por isso esta auditoria **não abre nem calcula hash** de seu conteúdo.
- O vencedor automático de Stage24 não é necessariamente o operador Choquet
  e grupo de descritores especificados nas duas hipóteses H1/H2.

## Comandos PowerShell

    git pull --ff-only origin experiment/paper-a-conditional-confirmation
    .\.venv\Scripts\Activate.ps1
    python .\tests\test_paper_a_parameter_provenance_P0.py
    python .\scripts\audit_paper_a_parameter_provenance_P0.py

Relatório: F:\MFI-Edge-Data\MultiCue\paper_a_parameter_provenance_P0.json

Para repetir, use outro nome de arquivo com --output, pois o script recusa
sobrescrever auditoria existente.

## Limites importantes

A ausência de diferenças de assinatura ou source_contract_mismatches=[]
comprova apenas a consistência estrutural esperada do código. Não confirma
que parâmetros de modelo estejam presentes, que o ajuste tenha sido feito
em dados permitidos ou que o protocolo já esteja pronto para congelamento.

Próximo gate P0.1: exportar, com revisão de origem, um manifesto de RECEITAS
de H1/H2 sem F1 ou resultados exploratórios, com valores fixos, SHA256 e
proveniência de desenvolvimento separada da coorte de confirmação.
Não reutilizar modelos automaticamente nem reprocessar Stage24 sem necessidade.
