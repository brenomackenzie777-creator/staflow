# BUGS.md — QA Brutal do Fluxo Completo StaFlow
**Data:** 26/06/2026 | **Metodologia:** systematic-debugging  
**Atualizado:** 26/06/2026 — Sprints 1–4 executados · Aprovação: Breno (Cérebro) · Opção D (PWA melhorado)

---

## Legenda de Prioridade
- **P1** — Quebra fluxo em produção, perda de dados ou fraude possível
- **P2** — Degradação de UX ou edge case que afeta percentual dos usuários
- **P3** — Melhoria, inconsistência menor, código defensivo

---

## BUG-001 — GPS audit_status perdido em modo offline
**Prioridade:** P1 — Segurança / Antifraude | **Status:** ✅ CORRIGIDO (Sprint 1 · 26/06/2026)  
**Arquivo:** `colaborador.html` linhas 1472–1492

**Descrição:**  
Quando o funcionário bate ponto offline, a função `registrarPonto()` captura o GPS e executa `classificarGPS()` gerando um `audit_status` (FRAUDE_SUSPECT, MOCK_SUSPECT, OK, LOW_ACCURACY). Porém, antes de inserir no IndexedDB, o código sobrescreve o status:
```js
payload.audit_status = 'OFFLINE_PENDENTE';  // linha 1477
```
O `audit_status` real do GPS é descartado. Quando a fila sincroniza, o registro chega ao servidor com `OFFLINE_PENDENTE`, sem rastreio de fraude.

**Impacto:** Funcionário com GPS mockado pode bater ponto offline e, ao sincronizar, o registro aparece sem flag de fraude. Derrota a proteção antifraude do `classificarGPS()`.

**Reprodução:**
1. Ativar "GPS mockado" no Android (Developer Options → Mock Location).
2. Desligar WiFi + dados móveis no dispositivo.
3. Bater ponto no colaborador.html — registra como `OFFLINE_PENDENTE`.
4. Reconectar internet — sync drena a fila.
5. Verificar no dashboard: batida aparece sem flag de fraude.

**Correção:**
```js
// Em vez de sobrescrever, concatenar:
const gpsStatus = pos?.audit_status ?? 'OK';
payload.audit_status = gpsStatus === 'OK' || gpsStatus === 'LOW_ACCURACY'
  ? 'OFFLINE_PENDENTE'
  : `OFFLINE_PENDENTE+${gpsStatus}`;  // ex: 'OFFLINE_PENDENTE+FRAUDE_SUSPECT'
```
Ou adicionar campo separado `gps_audit_status` na tabela `registros_ponto` para preservar ambas as informações.

---

## BUG-002 — Fallback offline não preserva GPS status no fluxo online-failed
**Prioridade:** P1 — Segurança / Antifraude | **Status:** ✅ CORRIGIDO (Sprint 1 · 26/06/2026)  
**Arquivo:** `colaborador.html` linhas 1500–1515

**Descrição:**  
No fluxo online (INSERT no Supabase), se o INSERT falhar (ex: WiFi sem internet real), o código tem um fallback que salva offline. Nesse fallback, o `payload.audit_status` é sobrescrito novamente:
```js
payload.audit_status = 'OFFLINE_PENDENTE';  // linha 1505
```
O mesmo problema do BUG-001, mas no caminho do fallback online→offline.

**Correção:** Mesma do BUG-001.

---

## BUG-003 — Sincronização offline não trata erro de RLS (não é 23505)
**Prioridade:** P2 — Confiabilidade | **Status:** ✅ CORRIGIDO (Sprint 3 · 26/06/2026)  
**Arquivo:** `colaborador.html` linhas 1400–1443 (`sincronizarFilaOffline`)

**Descrição:**  
A sync trata `error.code === '23505'` (unique violation) como sucesso silencioso. Outros erros (ex: `42501` permission denied por RLS, ou `23503` foreign key violation se o funcionário foi deletado) incrementam `fail++` mas o item permanece na fila indefinidamente — nenhum log, nenhuma notificação ao usuário além do toast genérico.

**Impacto:** Se o condomínio foi deletado ou o funcionário desvinculado, as batidas offline nunca sincronizam e o usuário não sabe. A pill continua mostrando "N batidas aguardando sincronização" para sempre.

**Correção:**
```js
// Em sincronizarFilaOffline, tratar erros não-recuperáveis:
const UNRECOVERABLE_CODES = ['42501', '23503', 'PGRST301'];
if (UNRECOVERABLE_CODES.includes(error.code)) {
  // Mover para fila morta ou notificar explicitamente
  console.error('[offline] batida irrecuperável, removendo da fila:', error);
  await OfflineQueue.remove(item.id);
  // Toast específico
  toast('⚠️ Batida offline não pôde ser sincronizada (acesso negado). Contate o síndico.', 'error');
  ok++;  // remove da contagem de pendentes
  continue;
}
```

---

## BUG-004 — `route-guard.js` bloqueia rendering antes de qualquer pixel
**Prioridade:** P2 — Performance / UX | **Status:** ✅ CORRIGIDO (Sprint 2 · 26/06/2026)  
**Arquivo:** `colaborador.html` linha 20

**Descrição:**  
```html
<script src="/js/route-guard.js"></script>  <!-- sem defer/async -->
```
O script de 9.9KB é carregado sincronicamente no `<head>`. Em 4G lento (500ms RTT), isso adiciona ~300–500ms ao FCP. O usuário vê tela branca enquanto o script baixa e executa.

**Reprodução:**
1. Chrome DevTools → Network tab → throttle para "Slow 4G".
2. Recarregar `colaborador.html`.
3. Observar waterfall: `route-guard.js` bloqueia antes do `<body>` começar a renderizar.

**Correção:** `<script src="/js/route-guard.js" defer></script>`  
Testar que o guard ainda intercepta corretamente (verificar se o script usa `DOMContentLoaded` ou espera por eventos — se sim, `defer` é seguro).

---

## BUG-005 — `apple-touch-icon` como SVG não funciona no iOS
**Prioridade:** P2 — PWA | **Status:** ✅ CORRIGIDO (Sprint 3 · 26/06/2026)  
**Arquivo:** `colaborador.html` linha 13, `manifest.json`

**Descrição:**  
```html
<link rel="apple-touch-icon" href="/assets/logo-mark.svg">
```
iOS Safari não suporta SVG para apple-touch-icon. O ícone na home screen do iPhone aparece vazio ou com fallback genérico.

**Correção:** Gerar PNG 180×180 e PNG 512×512 do logo e referenciar:
```html
<link rel="apple-touch-icon" sizes="180x180" href="/assets/icon-180.png">
```

---

## BUG-006 — Fluxo de invite funcionário — sem feedback de email já cadastrado
**Prioridade:** P2 — UX Onboarding | **Status:** ✅ CORRIGIDO (Sprint 3 · 26/06/2026)  
**Arquivo:** `auth/cadastro.html` — fallback signInWithOtp quando `already registered`

**Descrição:**  
Quando um funcionário já cadastrado no Supabase Auth tenta criar outra conta com o mesmo email, o `signUp` retorna erro genérico. O síndico adiciona o funcionário com um email que já existe no sistema, e o funcionário recebe o magic link mas a tentativa de `signUp` com senha falha silenciosamente.

**Impacto:** Funcionários com emails preexistentes ficam em estado "convidado" mas nunca ativam — o síndico não recebe feedback claro.

**Correção:** Tratar `User already registered` explicitamente no fluxo de onboarding:
```js
if (error?.message?.includes('already registered')) {
  // Email existe — tentar claim direto via signInWithOtp
  await sb.auth.signInWithOtp({ email, options: { shouldCreateUser: false } });
  toast('Email já cadastrado. Enviamos um link de acesso.', 'info');
}
```

---

## BUG-007 — `max-scale=1.0` no viewport impede zoom de acessibilidade
**Prioridade:** P2 — Acessibilidade | **Status:** ✅ CORRIGIDO (Sprint 2 · 26/06/2026)  
**Arquivo:** `colaborador.html` linha 4

**Descrição:**  
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, viewport-fit=cover">
```
`maximum-scale=1.0` impede que usuários com deficiência visual apliquem zoom via gestos no iOS/Android. Isso viola WCAG 2.1 Success Criterion 1.4.4 (Resize Text).

**Correção:** Remover `maximum-scale=1.0`:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
```
A UI deve ser testada com zoom a 200% para garantir que o botão de ponto não some.

---

## BUG-008 — Sem validação de tipo MIME no upload de atestados (frontend)
**Prioridade:** P2 — Segurança / LGPD | **Status:** ✅ JÁ IMPLEMENTADO (sessão anterior)  
**Arquivo:** `faltas.html`

**Descrição:**  
O `<input type="file">` aceita `image/jpeg,image/png,application/pdf` via atributo `accept`, mas não há validação JavaScript antes do upload. O atributo `accept` é uma sugestão ao OS, não uma restrição — usuários podem ignorá-lo.

**Nota:** O storage bucket no Supabase tem `allowed_mime_types` configurado, então arquivos inválidos serão rejeitados pelo servidor. Mas a validação client-side melhora a UX.

**Correção:**
```js
function validarMimeAtestado(file) {
  const ALLOWED = ['image/jpeg', 'image/png', 'application/pdf'];
  if (!ALLOWED.includes(file.type)) {
    toast('Formato inválido. Use JPG, PNG ou PDF.', 'error');
    return false;
  }
  if (file.size > 10 * 1024 * 1024) {
    toast('Arquivo muito grande. Máximo 10MB.', 'error');
    return false;
  }
  return true;
}
```

---

## BUG-009 — Service Worker não cacheia `app.css` (funcionalidade offline parcial)
**Prioridade:** P3 — PWA | **Status:** ✅ CORRIGIDO (Sprint 2 · 26/06/2026) — SW bumped para v2  
**Arquivo:** `service-worker.js`

**Descrição:**  
O `PRECACHE` array não inclui `/app.css`. Em modo offline, `colaborador.html` carrega (está cacheado) mas sem estilos — aparece como HTML sem CSS.

**Reprodução:**
1. Abrir `colaborador.html` com internet.
2. DevTools → Application → Service Workers → verificar cache.
3. Simular offline com DevTools → Network → Offline.
4. Recarregar — HTML renderiza sem estilos.

**Correção:**
```js
const PRECACHE = [
  '/colaborador',
  '/app.css',          // ← adicionar
  '/assets/logo-mark.svg',
  '/auth/auth.css',
  '/js/supabase-client.js',
  '/js/auth.js',
  '/js/route-guard.js',
  '/js/validadores.js',
  '/manifest.json'
];
```

---

## BUG-010 — Sem `robots.txt` — Google indexa páginas autenticadas
**Prioridade:** P3 — SEO / Segurança | **Status:** ✅ CORRIGIDO (Sprint 4 · 26/06/2026)  

**Descrição:**  
Sem `robots.txt`, o Googlebot tenta crawlear `/dashboard`, `/ponto`, `/colaborador`, etc. Essas páginas redirecionam ao login, mas geram erros de crawl e podem vazar estrutura de URL.

**Correção:** Criar `/robots.txt` (ver WQ_AUDIT.md P1 item 2).

---

## Resumo

| Bug | Prioridade | Área | Status |
|-----|-----------|------|--------|
| BUG-001 | P1 | Segurança/GPS | ✅ CORRIGIDO |
| BUG-002 | P1 | Segurança/GPS | ✅ CORRIGIDO |
| BUG-003 | P2 | Confiabilidade | ✅ CORRIGIDO |
| BUG-004 | P2 | Performance | ✅ CORRIGIDO |
| BUG-005 | P2 | PWA/iOS | ✅ CORRIGIDO |
| BUG-006 | P2 | Onboarding | ✅ CORRIGIDO |
| BUG-007 | P2 | Acessibilidade | ✅ CORRIGIDO |
| BUG-008 | P2 | Segurança/UX | ✅ JÁ IMPLEMENTADO |
| BUG-009 | P3 | PWA/offline | ✅ CORRIGIDO |
| BUG-010 | P3 | SEO | ✅ CORRIGIDO |

**10/10 bugs resolvidos — pronto para git push e deploy.**

---

*BUGS.md — StaFlow · 26/06/2026*
