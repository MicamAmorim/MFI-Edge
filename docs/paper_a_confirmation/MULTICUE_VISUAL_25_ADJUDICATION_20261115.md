# Revisão visual dos 25 alertas SIFT — 15/11/2026

A revisão foi realizada pelo assistente sobre as cinco pranchas de imagens originais enviadas pelo pesquisador: `review_01_of_05.png` até `review_05_of_05.png`. Os dados brutos e as pranchas permanecem fora do GitHub. O modelo de decisões `human_review_template.csv` foi confrontado com os 25 pares apresentados.

## Adjudicação dos quadros apresentados

- **1/25 — SAME_SCENE_CONFIRMED**: `09-MDBD-1C` versus `4113_left_0082`, bicicletário, muro e calçada em duas versões/recortes; correspondência também confirmada em originais por SIFT com 2.100/2.116 inliers no audit FLANN.
- **24/25 — DIFFERENT_SCENE**: conteúdos fotográficos claramente distintos nos quadros exibidos, por exemplo fachada de tijolos em `13-BIPED-1C` comparada a vários registros de animais ou ambiente urbano. Cada par e justificativa constam em `multicue_visual_25_decisions.csv`.

A classificação foi realizada por inspeção visual assistida; não representa uma segunda avaliação humana cega e independente. As 24 decisões `DIFFERENT_SCENE` se referem apenas aos **dois quadros visíveis de cada par** e não atestam que as sequências completas sejam independentes em local, fonte ou período de captura.

## Diagnóstico obrigatório do método SIFT/RANSAC

O detector de alertas gerou alguns inliers incompatíveis com a identidade visual — por exemplo, `13-BIPED-1C` versus `4609_left_0080` teve **277/354 (78,2%)** mesmo mostrando uma fachada contra vegetação e um animal. `13-BIPED-1C` versus `4494_left_0070` teve **267/313 (85,3%)**, mas a segunda imagem é subaquática. **Portanto a métrica de inliers usada na triagem apresenta falsos positivos visuais importantes.**

Antes de usar SIFT como filtro para novas coortes, verificar matching recíproco, identidade dos índices dos descritores, distribuição espacial de inliers, plausibilidade da homografia, erro de reprojeção e controles negativos. O detector anterior não constitui um classificador confiável de cena.

## Consequências para o Paper A

1. `4113_left_0082`: permanece **EXCLUDE_PRIOR_EXPOSURE**.
2. `4113_left_2396`: permanece **HOLD_SHARED_CAPTURE_PREFIX**; não houve confirmação de identidade visual, mas compartilha prefixo de captura.
3. Os 24 alertas adicionais são fechados **somente no nível da comparação dos dois quadros**, sem novas exclusões automáticas. Não promover prefixos a uma coorte congelada com base apenas nesses negativos visuais.
4. O teto conservador anterior de **95 prefixos candidatos MultiCue** antes de demais auditorias continua a ser apenas uma contagem estrutural; não equivale a 95 amostras independentes certificadas.
5. Permanecem pendentes revisão de exposição por outras sequências/frames, GT/avaliador, poder estatístico, manifesto da coorte e congelamento formal do protocolo. **Nenhum GT/F1 confirmatório foi acessado nesta revisão.**

A versão completa para preenchimento local foi entregue como CSV ao pesquisador nesta conversa; o CSV versionado aqui mantém decisões e justificativas, sem dados visuais.
