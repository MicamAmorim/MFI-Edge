# Paper A219 — painel de revisão no celular (Tailscale)

## Instalação no repositório MFI-Edge

1. Confirme que está na branch `experiment/paper-a-conditional-confirmation` e que os arquivos de pré-freeze A219 já existem no `F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff`.
2. Extraia o ZIP deste pacote **na raiz da pasta `MFI-Edge`**, preservando `scripts/` e `docs/`.
3. Certifique-se de que Python na `.venv` tem Pillow: `.\.venv\Scripts\python.exe -m pip show Pillow` (ou use `python -m pip show Pillow` na venv ativada). Se faltar, instale somente `Pillow` com `python -m pip install Pillow`.
4. PC e celular devem estar conectados à **mesma rede Tailscale (tailnet)**, com acesso permitido e HTTPS habilitado. O servidor **não** usa Funnel e não é publicado na internet aberta.
5. No PowerShell, na raiz `MFI-Edge`, execute:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\iniciar_revisao_a219_tailscale.ps1
```

6. O script faz a auditoria de metadados primeiro, usa `tailscale serve --bg --https=8443 http://127.0.0.1:18765` e mostra uma URL `https://SEU-PC.SUA-TAILNET.ts.net:8443/` (a URL **real** vem do Tailscale do computador).
7. Abra a URL no navegador do celular com Tailscale conectado. Digite o **PIN temporário de 12 dígitos mostrado no terminal**. Não poste PIN em chats, logs ou redes sociais.
8. Mantenha o terminal do servidor aberto. As decisões são guardadas em `F:\MFI-Edge-Data\MultiCue\paper_a_completion\scientific_signoff\MOBILE_A219_RASCUNHO\decisions_DRAFT.json`, com histórico das revisões. Use *Exportar dossiê* para gerar um ZIP auditável.

Se quiser testar **sem Tailscale**:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\iniciar_revisao_a219_tailscale.ps1 -SomenteLocal
```

O endereço local é `http://127.0.0.1:18765/`.

Para interromper o backend, `Ctrl+C`. Como Tailscale Serve fica em segundo plano, desligue o proxy depois:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\parar_revisao_a219_tailscale.ps1
```

## Como interpretar as imagens

**Coorte A219:** 125 BIPED train RGB e 94 MultiCue originais. O painel confere hash dos arquivos A219 e nunca abre GT confirmatório. **BIPED train:** pasta de 200 imagens RGB disponibilizada localmente, não um manifesto de imagens efetivamente usadas em treinamento. **BIPED test:** imagens RGB do split test se presentes, não resultados ou GT. **MultiCue:** quadros RGB originais disponíveis. **UDED:** imagens RGB de desenvolvimento se existirem nos diretórios esperados.

Em *Comparar cenas*, o **dHash** encontra imagens visualmente parecidas e permite comparação lado a lado. O dHash é apenas triagem, não prova de independência ou de contaminação. O painel cruza metadados históricos explicitamente autorizados, e distingue *referência textual* de *execução confirmada*.

## As decisões

- *Aprovar preliminarmente* registra **somente seu julgamento**, com justificativa e hash da seleção. Não emite `FINAL_INDEPENDENT_REVIEW.json`, não altera `protocol.json`, não executa `freeze_paper_a_from_independent_review.py` em modo freeze e não abre GT, H5, F1, mapas ou H1/H2.
- Se não houver prova de ausência de sobreposição, marque **pendente**, **possível uso anterior** ou **exigir evidências**, não a classifique como limpa apenas por não ter encontrado uma menção.
- O pacote exportado deve ser examinado por um **revisor científico independente**, que deliberará sobre cenas, histórico, P1, GT v2 e teste estatístico antes de qualquer freeze.

## Proteção de segurança

- O backend escuta **somente em 127.0.0.1**, separado do Tailscale Serve, com PIN efêmero de 12 dígitos, cookie `HttpOnly`, token CSRF e verificação de origem.
- As imagens permitidas são **originais RGB de diretórios especificados**, com caminho limitado a uma allowlist criada no servidor; arquivos de GT, anotações, F1 e H5 não entram na lista de origem.
- O painel não aceita caminho local informado pelo navegador, não abre diretórios arbitrários, não executa comandos fornecidos pelo usuário e não sobrescreve a revisão científica oficial.
- Se o conjunto original, qualquer hash crítico ou o protocolo ativo mudar, o salvamento de decisões falhará até análise manual.
- A porta **8443** foi escolhida para não alterar o serviço comum na 443; se já estiver ocupada, o launcher recusa sobrescrever outro serviço.

## Limitações e dados ausentes

A ferramenta encontra arquivos **disponíveis** no clone e nos diretórios citados, mas não pode provar que todos os treinamentos antigos estão registrados. Se não houver arquivos originais UDED, se um log antigo tiver sido removido ou se a origem de determinado ajuste não estiver documentada, aparecerá como **indisponível/pendente**. Para decidir contaminação, será necessário usar logs reais de execução e a proveniência dos dados usados em fitting; mosaicos de imagens por si só não comprovam ausência de vazamento científico.

## Testes automatizados (opcionais)

No PowerShell, a partir da raiz do repositório:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -p test_paper_a_mobile_review.py -v
```

Os testes geram somente imagens RGB sintéticas e um arquivo-canário em pasta GT fictícia para verificar que o servidor não a disponibiliza. Não acessam dados reais de resultados.
