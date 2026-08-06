# Aprovação do Plano — Rafael

**Data:** 26/06/2026  
**De:** Breno (Cérebro)

---

## PLAN_mobile.md — APROVADO com direção

**Decisão:** Opção C — PWA melhorado. Sem Capacitor, sem app store por agora.

**Motivo:** O PWA já funciona na home screen do Android e iOS. A prioridade é corrigir os bugs encontrados e garantir que o app funcione perfeitamente em ambas as plataformas sem complexidade de store.

**Limitação aceita:** Push notifications não funcionam no iPhone (Safari). Tudo mais funciona — ponto, GPS, offline, home screen. Push pode entrar quando houver receita para investir em app nativo.

---

## Execução imediata — ordem de prioridade

### SPRINT 1 — P1s de segurança (hoje)

**BUG-001 + BUG-002 — GPS audit_status offline**

Correção confirmada — usa concatenação em vez de sobrescrever:

```js
const gpsStatus = pos?.audit_status ?? 'OK';
payload.audit_status = gpsStatus === 'OK' || gpsStatus === 'LOW_ACCURACY'
  ? 'OFFLINE_PENDENTE'
  : `OFFLINE_PENDENTE+${gpsStatus}`;
```

Aplica nos dois pontos do código (`colaborador.html` linhas ~1477 e ~1505). Depois: testa o fluxo completo de GPS mockado offline → sync → verifica que o dashboard exibe o flag correto.

---

### SPRINT 2 — Quick wins (< 30min no total)

Executar em sequência, cada um é uma linha de código:

1. **BUG-004** — `<script src="/js/route-guard.js" defer></script>` (FCP cai de ~3s para ~1.2s)
2. **BUG-007** — Remover `maximum-scale=1.0` do viewport em todos os arquivos HTML
3. **BUG-009** — Adicionar `/app.css` ao array `PRECACHE` do service-worker.js

Depois dos 3: rodar `/wq-performance` e confirmar que o FCP estimado caiu abaixo de 1.5s.

---

### SPRINT 3 — P2s restantes (~3h)

4. **BUG-005** — Gerar `icon-180.png` e `icon-512.png` do logo I (monograma SF — blocos azuis) e referenciar no HTML como apple-touch-icon
5. **BUG-003** — Tratar erros irrecuperáveis na fila offline (ver código no BUGS.md)
6. **BUG-006** — Tratar `User already registered` no fluxo de invite (ver código no BUGS.md)
7. **BUG-008** — Validação MIME client-side nos atestados (ver código no BUGS.md)

---

### SPRINT 4 — SEO/infra (P3, ~20min)

8. **BUG-010** — Criar `robots.txt` bloqueando páginas autenticadas
9. **WQ gaps** — Meta descriptions nas 2 páginas sem, security headers no vercel.json

---

### SPRINT 5 — iOS PWA (1 semana)

Objetivo: `colaborador.html` funciona perfeitamente na home screen do iPhone.

Checklist:
- [ ] `apple-touch-icon` em PNG (BUG-005 resolve isso)
- [ ] Viewport sem `maximum-scale=1.0` (BUG-007 resolve isso)
- [ ] `manifest.json` com `display: standalone` e `start_url: /colaborador` — já correto
- [ ] Testar adição à home screen no Safari iOS 16+ e 17+
- [ ] Testar fluxo de ponto completo no iPhone (entrada → GPS → saída)
- [ ] Testar offline mode no Safari (SW funciona no iOS 16.4+)
- [ ] Botão de ponto visível sem scroll em iPhone SE (menor tela suportada)

---

## Logo oficial atualizada

A logo escolhida é a **variante I — dois blocos azuis geométricos em S** (arquivo `logo-I-geometrico-blocos.png`).

Quando gerar os ícones para apple-touch-icon (BUG-005), usa essa logo, não o bolt.

O `assets/logo-mark.svg` ainda é o hexágono azul usado no SVG do site — mantém por enquanto. Os ícones PNG para apple-touch-icon e manifest devem usar a variante I.

---

## Entregáveis desta sprint

Quando terminar cada sprint, atualiza o BUGS.md com:
- Status: `CORRIGIDO` ou `PENDENTE`
- Commit onde foi corrigido

Quando todos os P1s e P2s estiverem corrigidos, roda `/verification-before-completion` antes de subir para produção.

---

*Aprovação do Cérebro · StaFlow · 26/06/2026*
