# Próximo modelo MFI Edge — protótipo iniciado

Foi iniciado um roteador condicional não neural, com dois atributos de mapas
e quatro cabeças já definidas no plano anterior. O código usa regressão ridge
de recompensas por cabeça e escolhe uma cabeça por imagem. A normalização é
aprendida apenas no treino, e a ordenação dos empates é determinística.

O protótipo passou quatro testes sintéticos. Nenhum modelo foi treinado em
dados reais e nenhuma superioridade ou validação externa é alegada.
A arquitetura deriva do plano de desenvolvimento prévio, antes de consultar
os resultados completos H1/H2 atuais. Seus360 originais e grupos de cena
estão listados como proibidos para o novo ajuste; BIPED secundária também
está excluída. Esse conjunto não pode escolher características, operadores,
limiares ou arquitetura do novo modelo nem servir como novo teste final.

Próxima execução: desenvolvimento independente, controles de média/melhor
cabeça fixa/melhor descritor escolhidos só no treino; validação por cenas e
refit interno dos componentes; depois outro teste intocado, auditado e
congelado. A meta prévia de ganho prático é0,01 F1, não resultado obtido.
O oráculo continua sendo teto retrospectivo, não desempenho do roteador.

O módulo é um protótipo de desenvolvimento e não substitui o avaliador fixo
do Paper A. O protocolo permanece draft, sem congelamento do novo modelo.
