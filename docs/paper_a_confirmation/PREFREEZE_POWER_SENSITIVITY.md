# Sensibilidade aproximada de poder pré-freeze — não conclusiva

A meta provisória de 150 imagens de duas fontes (mínimo 60 por domínio)
precisa de análise de poder **antes** de congelar o protocolo.
Aproximações baseadas nos rhos exploratórios −0,81 e +0,78 seriam
otimistas, pois essas relações foram selecionadas depois de muitas buscas.

Ferramenta sem leitura de datasets, imagens, anotações ou F1:

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\tests\test_paper_a_power_sensitivity.py
python .\scripts\estimate_paper_a_power_sensitivity.py --output "F:\MFI-Edge-Data\MultiCue\paper_a_power_sensitivity_approx.json"
```

Calcula uma grade para `N = 120, 150, 180, 200` e valores hipotéticos
de `|rho| = 0,15, 0,20, 0,25, 0,30, 0,35, 0,40`. Usa aproximação normal
Fisher-z e alfa unilateral 0,025 por hipótese, limite conservador
antes do ajuste de Holm para a família de duas hipóteses.

**Não substitui a análise formal** do teste de permutação de Spearman:
não incorpora empates, seleção por grupos/cenas, permutação restrita
por domínio, heterogeneidade, distribuição conjunta de H1/H2 ou
pseudorreplicação. Após esse primeiro dimensionamento, será preciso
fixar o efeito mínimo relevante e simular a inferência escolhida
antes do freeze.

Amostra N conta **grupos independentes**, não frames/folds. Misturar
domínios pode produzir correlação global espúria se não houver uma
definição prévia de teste bloqueado ou contribuição dentro de cada
domínio. Status permanece `draft_not_frozen`.
