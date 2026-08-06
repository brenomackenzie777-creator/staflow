# WQ_AUDIT.md — Web Quality Audit StaFlow
**Data:** 26/06/2026 | **Metodologia:** wq-web-quality-audit (Addy Osmani)

---

## Score Geral por Página

| Página | SEO | Acessibilidade | Performance | Best Practices | PWA | Total |
|--------|-----|---------------|-------------|----------------|-----|-------|
| staflow-landing.html | 85 | 90 | 70 | 80 | 0 | **65** |
| colaborador.html | 60 | 85 | 65 | 75 | 95 | **76** |
| dashboard.html | 55 | 80 | 70 | 75 | 0 | **56** |
| auth/cadastro.html | 40 | 75 | 72 | 75 | 0 | **52** |
| auth/login.html | 50 | 80 | 75 | 75 | 0 | **56** |
| planos.html | 40 | 80 | 68 | 75 | 0 | **53** |

*Scores estimados por análise estática de código — validar com Lighthouse real em produção.*

---

## Achados por Categoria

### 🔴 SEO — Crítico

**planos.html e auth/cadastro.html — sem `<meta name="description">`**
- Impacto: Google não consegue gerar snippet nas SERPs. Direto na taxa de cliques.
- Correção:
```html
<!-- planos.html -->
<meta name="description" content="Escolha o plano StaFlow ideal para seu condomínio — Starter grátis, Pro R$99/mês, Scale R$279/mês.">

<!-- auth/cadastro.html -->
<meta name="description" content="Crie sua conta no StaFlow e comece a gerir ponto e tarefas do seu condomínio hoje.">
```

**5 de 6 páginas sem Open Graph tags**
- Apenas `staflow-landing.html` tem OG tags. Dashboard, auth, planos, colaborador não têm.
- Impacto: compartilhamento no WhatsApp (canal principal do cliente síndico) exibe preview vazio.
- Prioridade para `planos.html` e `staflow-landing.html`.
- Correção:
```html
<!-- planos.html -->
<meta property="og:title" content="Planos StaFlow — do Starter ao Scale">
<meta property="og:description" content="SaaS de gestão de ponto para condomínios. Começa grátis.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://staflow.app.br/planos">
<meta property="og:image" content="https://staflow.app.br/assets/og-image.png">
```

**Sem sitemap.xml e robots.txt**
- Crawlers não sabem o que indexar. `auth/` não deve ser indexada.
- Criar `/robots.txt`:
```
User-agent: *
Allow: /
Allow: /planos
Allow: /politica-privacidade
Allow: /termos-de-uso
Disallow: /auth/
Disallow: /dashboard
Disallow: /funcionarios
Disallow: /ponto
Disallow: /faltas
Disallow: /tarefas
Disallow: /configuracoes
Disallow: /colaborador
Sitemap: https://staflow.app.br/sitemap.xml
```

---

### 🔴 Performance — Crítico

**`route-guard.js` carregado de forma síncrona no `<head>` do colaborador.html**
- Linha 20 de `colaborador.html`: `<script src="/js/route-guard.js"></script>` bloqueante.
- Este script (9.9KB) bloqueia rendering até terminar de baixar e executar.
- Impacto direto no FCP (First Contentful Paint) — especialmente em 4G lento.
- Correção: adicionar `defer` (o route-guard não precisa rodar antes do DOM):
```html
<script src="/js/route-guard.js" defer></script>
```
**Atenção:** testar se o guard ainda intercepta corretamente com defer — se a lógica lê o DOM, ok. Se roda antes do DOMContentLoaded, pode precisar de ajuste.

**Google Fonts render-blocking em colaborador.html e staflow-landing.html**
- `<link href="https://fonts.googleapis.com/css2?family=Inter...">` bloqueia rendering.
- Correção (preload + display=swap já está em uso, mas link é bloqueante):
```html
<!-- Substituir por: -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"></noscript>
```
**Alternativa melhor:** self-host Inter via `@font-face` (elimina request externo e GDPR concern com Google Fonts).

**Supabase SDK carregado via CDN sem defer/async (colaborador.html linha 1052)**
```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```
- Script externo, sem `defer`. Bloqueia renderização se CDN for lento.
- Correção: `defer` + versão pinada:
```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js" defer></script>
```

**app.css sem minificação (19.4KB não-minificado)**
- Em produção no Vercel, o CSS não passa por build step. 19.4KB é razoável mas poderia ser ~12KB minificado.
- Solução imediata: Vercel Edge Network comprime com gzip automaticamente. Impacto menor.

**Sem critical CSS inlining**
- O CSS crítico (acima da dobra) não está inline. Para `colaborador.html`, o botão de ponto deve aparecer sem aguardar app.css.
- Para Fase 2 considerar critical CSS extraction.

---

### 🟡 Acessibilidade

**Imagens sem `alt` em dashboard.html, auth/cadastro.html, auth/login.html, planos.html**
- Cada uma tem 1 `<img>` sem atributo `alt` (ou com `alt` vazio não-decorativo).
- Em dashboard.html linha 768: foto do funcionário tem `alt` dinâmico com iniciais — ✅ correto.
- Verificar as outras 3 imagens (provavelmente logos).
- Correção: `alt=""` para decorativas, `alt="Logo StaFlow"` para logo funcional.

**Contraste — verificar cores de texto muted**
- `--text-muted: #9CA3AF` sobre `--surface: #1F2937` → ratio ~4.5:1 (passa AA).
- `--text-faint: #6B7280` sobre `--surface: #1F2937` → ratio ~3.1:1 (falha AA para texto normal, passa AA para texto grande).
- Achado: textos hint/label pequenos em `--text-faint` podem falhar WCAG 2.1 AA.

**Ausência de `role="main"` e landmarks ARIA**
- Páginas do app (`dashboard.html`, `colaborador.html`) não têm `<main>` como elemento principal.
- Screen readers não conseguem navegar diretamente ao conteúdo.
- Correção: envolver conteúdo principal em `<main id="main-content">` e adicionar `<a href="#main-content" class="sr-only">Pular para o conteúdo</a>` no início de cada página.

**Botão de ponto em colaborador.html — verificar `aria-label` dinâmico**
- O texto do botão muda (ENTRADA / ALMOÇO / VOLTA / SAÍDA). Verificar se o `aria-label` acompanha a mudança programaticamente.

---

### 🟡 Best Practices

**Sem Content-Security-Policy (CSP)**
- Nenhuma página tem header CSP. Risco de XSS aumentado.
- Para Vercel, adicionar `vercel.json`:
```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=(self)" }
      ]
    }
  ]
}
```
**Nota:** CSP completa (com `script-src`, `connect-src`) requer cuidado com Supabase/Stripe inline — adicionar na Fase 2.

**Supabase URL e anon key expostos no frontend (js/supabase-client.js)**
- Isso é esperado e seguro no modelo Supabase — o `anon key` é projetado para ser público. RLS é a defesa real.
- Não é bug, mas documentar para não gerar alarme em security scans.

---

### 🟢 PWA — Apenas colaborador.html

**O que está correto:**
- `manifest.json` completo com icons, theme_color, display=standalone, orientation=portrait.
- Service Worker com estratégia network-first para HTML, cache-first para assets.
- Fallback offline: cai para `/colaborador` cacheado.
- Pill de indicação de batidas pendentes offline.
- IndexedDB com retry automático.

**O que falta:**
- `manifest.json` referenciado em `staflow-landing.html`? Não. Ok — landing não precisa de PWA.
- `apple-touch-icon` aponta para SVG (`/assets/logo-mark.svg`) — iOS prefere PNG 180×180.
- Sem `screenshots` no manifest (exigido para "Add to Home Screen" prompt no Chrome 117+).

---

## Plano de Correções Priorizadas

### P1 — Fazer antes do lançamento (< 1 dia de trabalho)

| # | Ação | Arquivo | Impacto |
|---|------|---------|---------|
| 1 | Adicionar `defer` em `route-guard.js` | colaborador.html | FCP -300ms |
| 2 | Criar `robots.txt` | / | SEO crawl |
| 3 | Meta description em planos.html e cadastro.html | 2 arquivos | SEO CTR |
| 4 | OG tags em planos.html | planos.html | WhatsApp share |
| 5 | Adicionar security headers em `vercel.json` | vercel.json (criar) | Best Practices |
| 6 | `alt=""` nas imagens sem alt | 3 arquivos | Acessibilidade |

### P2 — Sprint 1 pós-lançamento

| # | Ação | Impacto |
|---|------|---------|
| 7 | Google Fonts non-blocking (preload pattern) | FCP -200ms |
| 8 | Supabase CDN com `defer` | FCP -100ms |
| 9 | `<main>` landmark + skip link em todas as páginas | WCAG 2.1 |
| 10 | apple-touch-icon PNG 180×180 | PWA iOS |
| 11 | Sitemap.xml | SEO |

### P3 — Fase 2

| # | Ação | Impacto |
|---|------|---------|
| 12 | Self-host Inter (eliminar Google Fonts) | Perf + GDPR |
| 13 | Critical CSS inline para colaborador.html | FCP |
| 14 | CSP header completa | Segurança XSS |
| 15 | Screenshots no manifest.json | PWA install rate |

---

*WQ_AUDIT.md — StaFlow · 26/06/2026*
