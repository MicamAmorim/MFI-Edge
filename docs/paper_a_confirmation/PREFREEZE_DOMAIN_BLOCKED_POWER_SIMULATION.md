# Simulação de poder estratificada por domínio — proposta, não congelada

## Por que precisamos disso

A aproximação Fisher-z anterior projetou 80% de poder com aproximadamente
124 observações independentes se a correlação real tivesse magnitude 0,25.
Ela não considerou os dois domínios, a dependência de H1/H2 e a correção
de Holm em conjunto.

A simulação seguinte usa **somente dados sintéticos** gerados por uma
cópula gaussiana. Nenhuma imagem, GT, arquivo H5, F1 ou resultado da
campanha confirmatória é aberto.

## Estatística primária candidata (ainda NÃO registrada como frozen)

Spearman calculado dentro de cada domínio; média ponderada dos dois rho
com pesos n_domínio - 1. H1 testa o sinal negativo, H2 o sinal positivo.
As permutações são restritas ao mesmo domínio. Essa escolha evita que
mudanças entre a média dos domínios, sozinhas, induzam a correlação
primária — mas **altera/precisa especificar** o teste preliminar de
correlação de Spearman global descrito no rascunho `protocol.json`.
Nenhuma mudança no protocolo foi feita automaticamente.

Com ranks contínuos sem empates, a distribuição nula condicional de
permutações depende dos tamanhos dos grupos e pode ser pré-calculada
em Monte Carlo e reutilizada para os cenários sintéticos. Isso
**não** substitui as 100.000 permutações sobre os valores observados
previstas para a confirmação verdadeira.

## Como rodar

```powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\tests\test_paper_a_domain_blocked_power.py
python .\scripts\simulate_paper_a_domain_blocked_power.py `
  --replicates 1000 --null-permutations 20000 `
  --output "F:\MFI-Edge-Data\MultiCue\paper_a_domain_blocked_power.json"
```

Testa tamanhos de desenho **75+75, 90+90, 105+95, 125+95 e 145+95**
(BIPED+MultiCue). Todos respeitam os tetos de candidatos atuais
no nível de contagem, **não** constituem seleção nem garantia de
independência. Cenários: nulidade com diferenças entre domínios,
associações hipotéticas 0,20/0,25/0,30, heterogeneidade 0,30 versus 0,10,
e reversão entre domínios 0,25 versus −0,10.

Relata separadamente a probabilidade de confirmar H1, H2,
**ambas** e ao menos uma sob Holm/FWER de 5%, além do erro Monte Carlo.

## Resultado de verificação local sintética (não resultado experimental)

Na execução inicial sintética de desenvolvimento com 1.000 réplicas,
20.000 sorteios nulos e semente 20261115:

| Grupos (BIPED + MultiCue) | Cenário | Poder H1 | Poder H2 | Poder conjunto |
|---|---|---:|---:|---:|
| 75+75 | rho=0,20 nos dois domínios | 0,717 | 0,765 | 0,576 |
| 75+75 | rho=0,25 nos dois domínios | 0,910 | 0,921 | 0,847 |
| 105+95 | rho=0,20 nos dois domínios | 0,856 | 0,862 | 0,739 |
| 105+95 | rho=0,25 nos dois domínios | 0,961 | 0,965 | 0,931 |
| 145+95 | rho=0,20 nos dois domínios | 0,925 | 0,921 | 0,856 |

São números ilustrativos de uma especificação do simulador; devem ser
recalculados com o script versionado antes de recomendação final.

No cenário nulo com diferença artificial entre domínios, a frequência
de pelo menos uma rejeição ficou próxima de 5%, o esperado para o
procedimento de Holm sob pressupostos modelados.

## Limitações e decisões pendentes

A cópula artificial não representa automaticamente os mapas ou ganhos
F1 reais. Não modela empates, hierarquias de captura, cenas correlacionadas,
falhas de mapa ou condições reais de anotação; não autoriza afirmar que
o poder observado será o poder real. A escolha de efeito mínimo relevante,
agrupamento, avaliador, calibragem e estatística primária deve ser documentada
**antes** de abrir GT/F1.

**Estado do protocolo: `draft_not_frozen`**.
