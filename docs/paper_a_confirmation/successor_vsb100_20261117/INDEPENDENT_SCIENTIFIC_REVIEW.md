# Revisão científica independente pré-freeze — MFI-Edge

**Decisão:** aprovo o congelamento prospectivo do pacote exato revisado e sua execução fixa, condicionado à criação e validação do novo commit de freeze antes de qualquer GT candidato. Esta decisão não é um commit de freeze nem confirmação de H1/H2.

**Revisor:** Codex independent agent /root/independent_vsb100_review. Agente Codex separado do preparador, autorizado pelo usuário, com inspeção e verificações próprias. Não se apresenta como revisor humano, instituição externa ou revisão por pares do periódico. **UTC:** 2026-11-18T00:23:52.557596+00:00.

| População | Fonte | Unidades |
|---|---|---:|
| Primária | MultiCue | 62 |
| Primária | NYUDv2 — salas oficiais test | 153 |
| Primária | VSB100 — um quadro por vídeo | 97 |
| Secundária exploratória | BIPED train | 48 |

O teste primário usa **312 unidades em três domínios**, preservando o mínimo original de 60 por domínio. As 48 BIPED não entram nos rhos, p-valores ou decisões primárias. As 360 linhas foram reconferidas por identidade, SHA256 original e geometria; as 48 máscaras BIPED tiveram somente seus bytes opacos re-hashados, sem decodificação. Conferi 294 disposições BIPED/MultiCue e 287 fontes Python fixadas por hash.

## Achados que exigiram correção

Não aprovei a proposta inicial N221. Minha inspeção própria encontrou, entre outros, BIPED076/077 com o mesmo Nissan e travessia; train250/test248 com a mesma oliveira/fachada; train097/test098 com o mesmo Dacia e prédio; train143/144/153 versus test145 com a mesma Escola Saltells; train194/195 versus test192 com o mesmo Renault e muro. Recomendei componente conservador196–200 e quarentena de231 por exposição não resolvida. Em MultiCue, identifiquei o caminho4451/4452, a ligação do panorama4407/4409 e as vistas do prédio4114/4163/4190. As relações e exclusões foram propagadas aos componentes completos; não se escolheu N por F1.

A perda de BIPED abaixo do mínimo amostral levou à emenda explícita pré-GT: BIPED secundária, MultiCue/NYUD/VSB primárias. Nenhum resultado confirmatório guiou essa decisão. A nova amostra resulta de mais cenas efetivamente revisadas, com as hipóteses, funções, limiares e receita preservados.

## Evidência revisada independentemente

Inspecionei todos os RGBs candidatos nos atlas próprios, os casos necessários em maior resolução, test50 BIPED e UDED30 históricos. Revisei os **43 alertas suplementares** por par identificado: VSB9 em91.377 comparações e NYUD34 em160.650. Todos eram falsos positivos de cena; marcas de televisão ou seis correspondências esparsas não bastam para identificar o mesmo lugar. A ausência de alertas não foi tratada como prova de independência.

Reconstruí a seleção por hash dos nomes de97 quadros VSB e verifiquei a exclusão do vídeo inteiro reservado e dos dois vídeos claramente animados. Conferi os153 IDs NYUD no split oficial test e sua sala, além da exclusão de cinco salas historicamente expostas e duas cozinhas em quarentena. Os153 RGBs foram comparados ao HDF oficial de imagens:151 coincidem pixel a pixel com o crop[45:470,40:600]; img6258 eimg5636 diferem apenas em regiões de rostos (0,361% e1,276% dos pixels). Isso é compatível com desfoque fornecido pela distribuição, como inferência; não restaurei rostos, não realinhei RGB/GT e não criei máscaras de exclusão. O PNG ECCV14 fornecido permanece canônico.

Verifiquei sete provas P1, dez blobs históricos Git (ou transformação exata CRLF), os14 IDs/digests de desenvolvimento, o arquivo original de parâmetros e igualdade exata de memberships, limiares, capacidade e Möbius. A capacidade é monótona e coerente com Möbius. A receita original permanece byte-exata. A declaração externa de não sobreposição decorre deste exame da coorte e não de alterar o artefato P1.

Confirmei os novos decoders somente nas reservas já excluídas: NYUD train img5003 fornece uma referência Boundaries425×560; VSB Train/alec_baldwin fornece quatro referências720×1280. Não abri GT dos candidatos. As políticas são nativas, específicas por fonte e sem união de anotadores ou redimensionamento de GT: BIPED1, MultiCue6, NYUD1, VSB4. É um avaliador pareado próprio, não ODS/OIS/AP oficial Berkeley nem avaliação oficial VSB/NYUD.

## Código, inferência e condições de execução

Revisei guard, transição de freeze, executor, decoders e análise. Foram corrigidos cache sem hashes, status sintético em registros reais, vínculo dos GT BIPED/MultiCue, política explícita de abortar a execução inteira e SHA256 por streaming. A verificação exige revisão independente, arquivos/fontes exatos e commit Git antes do GT. Cache NPZ preserva quatro mapas float32 nativos e quatro predições booleanas, com hashes do arquivo e dos arrays. Os96 testes de regressão sintéticos e o smoke com descritores reais sobre RGB sintético passaram, conforme receipts vinculados. Eles não são avaliações reais.

O estimando fixo é a média de Spearman dentro de domínio, pesos n_d−1; H1 negativa/H2 positiva;100.000 permutações bloqueadas por domínio; Holm familiar0,05;2.000 bootstraps estratificados. O poder conjunto sintético no desenho312 é93,59% sob magnitude0,20 homogênea; cai a58,79% se VSB tiver efeito zero e31,32% se o efeito VSB inverter. Estes são pressupostos/sensibilidades, não evidência de confirmação.

Nenhuma linha pode ser removida ou substituída depois de ver GT; qualquer GT/mapa inválido interrompe o estudo fixado e exige relato separado de desvio. Não alterar membros, limiares, parâmetros, código ou política sob a mesma assinatura. Se os bytes revisados mudarem, esta aprovação deixa de autorizar aquele pacote.

## Limites e alcance

A independência é operacional, apoiada em RGB, componentes, metadados e histórico inspecionado; não uma prova matemática de IID. IDs de residência NYUD não estão disponíveis. NYUD é uma família já presente no desenvolvimento, com novas salas operacionais; VSB não tinha uso encontrado no histórico rastreado, sem garantia sobre uso não documentado. VSB e NYUD fornecem contornos perceptuais/de objetos, com granularidade diferente das bordas densas MultiCue/BIPED. A inferência vale para a associação ponderada das três fontes primárias, não confirmações separadas em todas elas ou na BIPED.

Uma associação com o sinal previsto pode coexistir com deltaF1 médio negativo. Portanto, uma hipótese passar não prova ganho médio positivo, superioridade universal nem um seletor adaptativo validado. Os resultados reais posteriores e a redação científica ainda devem ser checados.

**Hash da decisão independente:** `718464bdfd67f3d79e9f918ceb83f78b8e774ee77578cb468fdc7d78c796e4c9`. **Hash da planilha revisada360:** `6dc9623998c000dcec551a7f2312683cb1a2d28abab8093fdb0f20710709caa1`. **Hash do protocolo aprovado:** `335ddd2b790a3e861f869d950e90b5dab79702b2642ffb0a7eb1fbf6058ced41`. A decisão JSON contém os oito hashes finais e evidências adicionais. Nenhum GT candidato, mapa, XY ou F1 real foi aberto/computado nesta revisão.
