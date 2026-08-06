# PERFORMANCE.md — Análise de Performance Mobile (colaborador.html)
**Data:** 26/06/2026 | **Metodologia:** wq-performance + Core Web Vitals
**Contexto:** Porteiro em celular básico Android, 4G instável, bateria fraca.

---

## Baseline Estimado (análise estática)

| Métrica | Estimativa Atual | Meta | Status |
|---------|-----------------|------|--------|
| FCP (First Contentful Paint) | ~2.5–3.5s (Slow 4G) | < 1.5s | ❌ |
| LCP (Largest Contentful Paint) | ~3.0–4.0s | < 2.5s | ❌ |
| TTI (Time to Interactive) | ~4.0–5.5s | < 3.5s | ❌ |
| CLS (Cumulative Layout Shift) | ~0.05 (estimado) | < 0.1 | ✅ |
| Botão de ponto acima da dobra | Provavelmente sim | Sempre visível sem scroll | ⚠️ verificar |
| Funciona offline (SW) | ✅ | SW + IndexedDB | ✅ |
| Estabilidade ao voltar de offline | ✅ | Drain automático | ✅ |

*Validar com Lighthouse em produção — throttle Slow 4G, CPU 4x slowdown, mobile emulation.*

---

## Análise do Critical Path de Carregamento

### Sequência atual (render-blocking)

```
1. HTML parse começa
2. ❌ BLOQUEIO: <script src="/js/route-guard.js"> — 9.9KB, sem defer
   → Browser para HTML parse, baixa e executa o script
3. <link rel="preconnect" href="fonts.googleapis.com"> — ok
4. ❌ BLOQUEIO: <link href="fonts.googleapis.com/...Inter..."> — render-blocking CSS externo
   → Browser não renderiza nada até Google Fonts baixar
5. <style> inline (CSS crítico inline) — ✅ não bloqueia
6. HTML parse continua (body)
7. Conteúdo da página renderiza → FCP acontece aqui
8. ~linha 1052: <script src="cdn.jsdelivr.net/supabase-js@2"> — sem defer, bloqueia
9. <script src="/js/supabase-client.js"> — sem defer
10. <script src="/js/auth.js"> — sem defer
11. <script src="/js/validadores.js"> — sem defer
12. <script> inline (~800 linhas de JS da aplicação)
→ TTI acontece aqui (após tudo executar)
```

**Tamanho total de JS baixado:**
- route-guard.js: 9.9KB
- supabase-js CDN: ~200KB (não minificado / ~80KB gzip)
- supabase-client.js: 2.2KB
- auth.js: 12.8KB
- validadores.js: 6.8KB
- JS inline: ~40KB (estimado pelo tamanho do arquivo)
- **Total: ~270KB de JS** (principal gargalo)

---

## Problemas Identificados

### 🔴 P1 — route-guard.js síncrono no `<head>`

**Impacto no FCP: +300–500ms em Slow 4G**

O `route-guard.js` é o primeiro script do arquivo — carregado no `<head>` sem `defer`. Browser bloqueia parsing do HTML enquanto baixa (9.9KB) e executa o script.

**Por que está lá:** Proteção de rota — redireciona para login se não autenticado. A ideia é "redirecionar antes de mostrar qualquer coisa".

**Problema:** Isso sacrifica FCP para todos os usuários (incluindo os autenticados) para proteger de um flash de conteúdo não-autenticado que na prática nunca é visível (a tela carrega escura/vazia antes do JS renderizar).

**Solução sem regressão de segurança:**
```html
<!-- Substituir: -->
<script src="/js/route-guard.js"></script>

<!-- Por: -->
<script src="/js/route-guard.js" defer></script>
```
Com `defer`, o script baixa em paralelo mas executa após o HTML ser parseado — sem mudança de comportamento de segurança (o conteúdo real só renderiza após JS executar de qualquer forma).

**Ganho estimado: FCP -400ms**

---

### 🔴 P2 — Google Fonts render-blocking

**Impacto no FCP: +200–400ms em Slow 4G**

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

Browser não renderiza texto enquanto a font CSS não chega (mesmo com `display=swap` — o CSS precisa ser baixado primeiro para o browser saber que há swap).

**Solução 1 (rápida) — non-blocking load:**
```html
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" onload="this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"></noscript>
```

**Solução 2 (ideal) — self-host Inter:**
```css
/* Baixar Inter de fonts.google.com e hospedar em /assets/fonts/ */
@font-face {
  font-family: 'Inter';
  src: url('/assets/fonts/inter-var.woff2') format('woff2');
  font-weight: 100 900;
  font-display: swap;
}
```
Elimina dependência externa, melhora GDPR (Google Fonts coleta IPs), adiciona ao precache do SW para uso offline.

**Ganho estimado: FCP -300ms**

---

### 🟡 P3 — Supabase SDK via CDN sem defer (~200KB)

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```

- Localizado na linha 1052 (dentro do body), então não bloqueia FCP.
- Porém é carregado antes do script inline da app — sem `defer`, bloqueia parsing do restante do HTML a partir desse ponto.
- ~80KB gzip é o maior download de JS.

**Solução:**
```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js" defer></script>
<script src="/js/supabase-client.js" defer></script>
<script src="/js/auth.js" defer></script>
<script src="/js/validadores.js" defer></script>
```
**Atenção:** O script inline usa `sb` definido pelo supabase-client.js. Com `defer`, todos os scripts com `defer` executam em ordem após HTML parseado — a ordem de execução é preservada. O script inline precisa estar dentro de `DOMContentLoaded` ou ser também `defer`.

---

### 🟡 P4 — Sem preload de assets críticos

O manifesto define `start_url: /colaborador` e o SW precacheia o HTML. Mas falta preload explícito do logo SVG:

```html
<!-- Adicionar ao <head>: -->
<link rel="preload" href="/assets/logo-mark.svg" as="image" type="image/svg+xml">
```

---

## O que Está Funcionando Bem

### ✅ Service Worker e Offline Mode

Implementação sólida:
- Pre-cache de assets críticos no install
- Network-first para HTML (sempre busca atualização)
- Cache-first para assets estáticos
- Bypass total para Supabase/Stripe
- IndexedDB com retry automático
- `sincronizarFilaOffline()` trigada por `window.addEventListener('online')`
- Anti-reentrância com `syncRunning` flag
- Tratamento de `error.code === '23505'` (unique violation = silencioso)

### ✅ CSS in-head (inline `<style>`)

O CSS crítico da aplicação está inline no `<head>`, não em arquivo externo. Isso garante que estilos críticos não bloqueiem adicionalmente o rendering.

### ✅ Otimismo de UI no offline

```js
pontosHoje.push({ tipo: payload.tipo, registrado_em: ..., audit_status: 'OFFLINE_PENDENTE' });
renderPonto();
```
Atualiza a timeline imediatamente sem esperar confirmação do servidor — UX responsiva mesmo offline.

### ✅ Viewport correto para PWA

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, viewport-fit=cover">
```
`viewport-fit=cover` essencial para iPhones com notch. (Porém `maximum-scale=1.0` é problema de acessibilidade — ver BUGS.md BUG-007.)

---

## Plano de Otimização

### Sprint 0 — 1 dia de trabalho (impacto máximo)

```bash
1. Adicionar defer em route-guard.js          → FCP -400ms
2. Google Fonts non-blocking (onload pattern) → FCP -300ms
3. Adicionar /app.css ao PRECACHE do SW       → offline funcional
4. Remover maximum-scale=1.0 do viewport      → acessibilidade
```

**Resultado esperado após Sprint 0:**
- FCP: ~2.5s → ~1.2s (Slow 4G)
- LCP: ~3.5s → ~2.0s
- Meta < 1.5s FCP atingível

### Sprint 1 — Self-host Inter (1–2 dias)

```bash
5. Baixar Inter variable font (woff2)
6. Hospedar em /assets/fonts/
7. @font-face no CSS
8. Adicionar ao PRECACHE do SW
9. Remover link do Google Fonts
```

**Ganho adicional:** FCP -200ms + funciona offline com font correta

### Sprint 2 — Refactor de scripts (Fase 2)

```bash
10. Supabase SDK como módulo ESM local (bundle)
11. defer/async em todos os scripts externos
12. Critical CSS extraction automatizada
```

---

## Como Testar (Chrome DevTools)

```
1. Abrir colaborador.html em produção (https://staflow.app.br/colaborador)
2. DevTools → Performance tab
3. Clicar no ícone de engrenagem → CPU: 4x slowdown
4. Network: Slow 4G
5. Clicar em Record + recarregar página
6. Parar após carregamento completo
7. Verificar: FCP marker, LCP marker, tempo de TTI
```

**Lighthouse CLI (mais preciso):**
```bash
npx lighthouse https://staflow.app.br/colaborador \
  --preset=perf \
  --emulated-form-factor=mobile \
  --throttling-method=simulate \
  --output=html \
  --output-path=./lighthouse-colaborador.html
```

---

*PERFORMANCE.md — StaFlow · 26/06/2026*
