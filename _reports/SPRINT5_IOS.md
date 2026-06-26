# SPRINT5_IOS.md — Validação PWA no iPhone
**Data:** 26/06/2026 | **Responsável:** Rafael (preencher em dispositivo real)  
**Dispositivos a testar:** iPhone SE (menor tela suportada) + iPhone 14 ou superior  
**iOS mínimo suportado:** Safari iOS 16.4+ (SW funciona a partir desta versão)

---

## Pré-requisitos antes de começar

- [ ] Commitar e dar push nas alterações dos Sprints 1–4 (`git push`)
- [ ] Deploy ativo em produção (`vercel --prod` ou via GitHub push)
- [ ] Confirmar acesso a `https://staflow.app.br/colaborador` no Safari do iPhone
- [ ] Ter credenciais de um funcionário de teste cadastrado

---

## 1. Instalação como PWA

| # | Teste | iPhone SE | iPhone 14+ |
|---|-------|-----------|------------|
| 1.1 | Abrir `staflow.app.br/colaborador` no Safari | ⬜ | ⬜ |
| 1.2 | Compartilhar → "Adicionar à Tela de Início" | ⬜ | ⬜ |
| 1.3 | Ícone aparece corretamente (logo I — blocos azuis em PNG) | ⬜ | ⬜ |
| 1.4 | App abre em modo standalone (sem barra de URL do Safari) | ⬜ | ⬜ |
| 1.5 | Status bar com fundo escuro (`#0d0f12`) | ⬜ | ⬜ |

**Observações:**

---

## 2. Autenticação

| # | Teste | Resultado |
|---|-------|-----------|
| 2.1 | Login com email + senha funciona no webview Safari | ⬜ |
| 2.2 | Magic link abre dentro do app (não no Safari externo) | ⬜ |
| 2.3 | Sessão persiste ao fechar e reabrir o app | ⬜ |
| 2.4 | Campos de email e senha sem zoom automático ao focar | ⬜ |

**Observações:**

---

## 3. Fluxo de ponto

| # | Teste | iPhone SE | iPhone 14+ |
|---|-------|-----------|------------|
| 3.1 | Botão de ponto visível sem scroll (acima da dobra) | ⬜ | ⬜ |
| 3.2 | GPS pede permissão na primeira batida | ⬜ | ⬜ |
| 3.3 | Batida registra com `audit_status: OK` | ⬜ | ⬜ |
| 3.4 | Toast de confirmação aparece | ⬜ | ⬜ |
| 3.5 | Timeline atualiza imediatamente após batida | ⬜ | ⬜ |
| 3.6 | Batida de saída completa o par entrada/saída | ⬜ | ⬜ |

**Observações:**

---

## 4. Modo offline

| # | Teste | Resultado |
|---|-------|-----------|
| 4.1 | Desligar WiFi + dados → app ainda abre da cache | ⬜ |
| 4.2 | Bater ponto offline → toast "salvo offline" | ⬜ |
| 4.3 | Pill de batidas pendentes aparece | ⬜ |
| 4.4 | Reconectar → fila sincroniza automaticamente | ⬜ |
| 4.5 | Verificar no dashboard: `audit_status` não é apenas `OFFLINE_PENDENTE` (deve mostrar GPS status concatenado se houve fraude, ou apenas `OFFLINE_PENDENTE` se GPS OK) | ⬜ |

**Observações:**

---

## 5. Upload de atestado

| # | Teste | Resultado |
|---|-------|-----------|
| 5.1 | Toque na área de upload oferece câmera + galeria | ⬜ |
| 5.2 | Upload de JPG da galeria funciona | ⬜ |
| 5.3 | Upload de PDF funciona | ⬜ |
| 5.4 | Arquivo > 10MB exibe mensagem de erro | ⬜ |
| 5.5 | Checkbox LGPD aparece antes de enviar atestado | ⬜ |

**Observações:**

---

## 6. Zoom e acessibilidade

| # | Teste | Resultado |
|---|-------|-----------|
| 6.1 | Pinch-to-zoom funciona (sem bloqueio) | ⬜ |
| 6.2 | Interface legível com zoom a 150% | ⬜ |
| 6.3 | Botão de ponto ainda visível com zoom a 200% | ⬜ |
| 6.4 | Nenhum campo causa zoom automático ao focar | ⬜ |

**Observações:**

---

## 7. Itens específicos iOS

| Item | Esperado | Resultado |
|------|----------|-----------|
| `apple-touch-icon` | Logo I (blocos azuis) 180×180px | ⬜ |
| SW cache funcionando | Página carrega offline após primeira visita | ⬜ |
| Push notifications | **Não funciona** — aceito e esperado | N/A |
| Scroll com momentum | Rolagem suave nativa do iOS | ⬜ |
| Input fields sem zoom | font-size 16px → sem zoom ao focar | ⬜ |
| Notch / Dynamic Island | UI não cortada em iPhones com notch | ⬜ |

---

## Bugs encontrados

*(Rafael preenche aqui — com descrição, screenshot se possível, e commit de correção)*

| # | Descrição | Severidade | Commit |
|---|-----------|-----------|--------|
| | | | |

---

## Checklist de entrega

- [ ] Todos os ⬜ preenchidos com ✅ ou ❌ ou ⚠️
- [ ] Bugs com ❌ foram corrigidos e commitados
- [ ] `git push` final com todas as correções
- [ ] BUGS.md atualizado com eventuais novos bugs iOS

---

## Status final

**[ ] APROVADO — PWA validado em iOS. StaFlow pronto para o primeiro cliente.**

---

*SPRINT5_IOS.md — StaFlow · 26/06/2026 · Preencher em dispositivo real*
