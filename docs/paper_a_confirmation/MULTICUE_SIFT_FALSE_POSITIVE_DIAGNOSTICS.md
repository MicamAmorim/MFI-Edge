# Diagnóstico dos falsos positivos geométricos — revisão antes do freeze

As cinco pranchas originais permitiram adjudicar 1/25 pares como mesma cena
e 24/25 como fotos visualmente distintas. Alguns dos 24 pares distintos
tiveram 267 ou 277 inliers RANSAC na triagem FLANN, indicando que o critério
automático anterior não identifica confiavelmente cópias de cenas.

## Nova verificação, sem reprocessar imagens

O script de diagnóstico lê apenas os descritores SIFT em cache no F:.
Aplica razão Lowe mais estrita (0.70) em ambos os sentidos, retém somente
correspondências recíprocas, calcula homografia dos pares e relata dispersão
espacial das correspondências e condicionamento da matriz.

~~~powershell
git pull --ff-only origin experiment/paper-a-conditional-confirmation
python .\tests\test_paper_a_multicue_sift_false_positives.py
python .\scripts\diagnose_paper_a_multicue_sift_false_positives.py
~~~

Gera:
- F:\MFI-Edge-Data\MultiCue\multicue_sift_mutual_validation_diagnostics.json
- F:\MFI-Edge-Data\MultiCue\multicue_sift_mutual_validation_diagnostics.csv

Este procedimento **não relê imagens, GT/H5 ou F1**, não altera decisões
visuais, não treina classificador e não autoriza congelamento de coorte.
É um teste de falha do método de triagem, não uma confirmação de H1/H2.

A referência positiva permanece UDED 09-MDBD-1C versus MultiCue
4113_left_0082; o prefixo 4113 segue fora de qualquer seleção provisória.
