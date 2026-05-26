# StaFlow

> **Uma jornada mais prática.** SaaS de gestão de funcionários para condomínios brasileiros — ponto digital, tarefas, faltas, relatórios e cobrança recorrente.

🌐 **Produção:** https://staflow.vercel.app
📦 **Repo:** https://github.com/brenomackenzie777-creator/staflow

---

## ✨ Filosofia & Arquitetura

StaFlow é construído com uma stack **deliberadamente enxuta**: zero framework no frontend, zero build step, zero `node_modules` em produção. Tudo o que o navegador roda é HTML, CSS e JavaScript que você pode ler.

| Camada | Tecnologia | Por quê |
|---|---|---|
| **Estrutura** | HTML5 semântico, sem template engine | Cada página é autocontida e debugável no DevTools |
| **Estilo** | CSS puro com **Custom Properties** (`--navy`, `--teal`, `--radius`…) em `auth/auth.css` | Design system tematizável, dark-first, mobile-first (breakpoint 768px) |
| **Lógica** | Vanilla JS em **módulos IIFE** (`(function(){ ... })()`) com namespaces `window.staflowAuth`, `window.staflowApp`, `window.staflowSupabase` | Sem build, sem bundler, sem CSP exigindo nonces — apenas funções globalmente acessíveis |
| **Backend** | **Supabase** (Postgres + Row Level Security + Auth + Storage) | Multi-tenancy enforced no banco; o frontend nunca confia em si mesmo |
| **Pagamentos** | **Stripe Checkout** + Webhooks via **Supabase Edge Functions** (Deno/TypeScript) | Hosted checkout (PCI fora do escopo), assinatura HMAC validada no servidor |
| **Hosting** | **Vercel** com auto-deploy do GitHub | Push em `main` publica em segundos; security headers e `cleanUrls` configurados em `vercel.json` |

A elegância está na separação: o frontend é "burro" (pede dados, mostra dados); toda a regra de negócio que importa vive em policies de RLS e funções `SECURITY DEFINER` no Postgres — auditáveis, versionadas em `sql/`, e impossíveis de burlar via DevTools.

---

## 🧱 Estrutura do repositório

```
.
├── staflow-landing.html             # Landing page pública
├── auth/                            # Login, cadastro, reset, callback PKCE
│   ├── login.html · cadastro.html · recuperar-senha.html
│   ├── nova-senha.html · callback.html
│   └── auth.css                     # Tokens do design system
│
├── dashboard.html                   # Painel com stats inteligentes
├── funcionarios.html                # CRUD + upload de foto (Storage)
├── ponto.html                       # Registro de entrada/saída + espelho mensal
├── tarefas.html                     # Gestão de tarefas da equipe
├── faltas.html                      # Faltas/atestados/férias (atestado em bucket privado)
├── planos.html                      # Pricing + cupom + checkout Stripe
├── configuracoes.html               # Perfil + condomínio
│
├── js/
│   ├── supabase-client.js           # Singleton sb (apenas anon key — pública por design)
│   ├── auth.js                      # signIn/signUp/checkAuth/checkSubscription
│   ├── app-shell.js                 # Sidebar, toast, skeleton, exportCSV, route-guard
│   └── stripe-config.js             # window.STAFLOW_STRIPE_PRICES (preencher após criar prices)
│
├── app.css                          # Layout, tabela, modal, skeleton, responsivo
├── assets/                          # Logos SVG
│
├── sql/                             # Migrações Postgres (rodar em ordem)
│   ├── 001_init_auth_schema.sql     # condominios, profiles, trigger handle_new_user
│   ├── 002_fix_rls_recursion.sql    # my_condominio_id() e my_role() SECURITY DEFINER
│   ├── 003_funcionarios.sql
│   ├── 004_planos_cupons.sql        # cupons + subscriptions + cupom TESTE (100% off)
│   ├── 005_ponto.sql                # registros_ponto
│   ├── 006_tarefas.sql
│   ├── 007_faltas.sql
│   ├── 008_storage_lgpd.sql         # Buckets fotos-funcionarios + atestados-medicos
│   ├── 009_stripe_schema.sql        # Campos stripe_* + view v_active_subscriptions
│   └── 010_security_hardening.sql   # FORCE RLS, search_path fix, view SECURITY INVOKER
│
├── supabase/
│   ├── config.toml                  # verify_jwt overrides (webhook = false)
│   └── functions/
│       ├── create-checkout-session/ # Cria Customer + Checkout Session no Stripe
│       └── stripe-webhook/          # Valida HMAC e sincroniza subscriptions
│
├── deploy-stripe.sh · deploy-stripe.ps1  # Automação do deploy das Edge Functions
└── vercel.json                      # cleanUrls, headers de segurança
```

---

## 🚀 Rodar localmente

```bash
npx serve .
# → http://localhost:3000
```

Não há build, não há `npm install`. O `supabase-client.js` aponta para o projeto de produção, então login e dados são reais — use uma conta de teste ou o cupom `TESTE` para acessar o dashboard sem pagar.

---

## 🧩 Módulos 100% operacionais

| Módulo | Status | Highlights |
|---|---|---|
| **Auth** | ✅ | Email/senha + confirmação por e-mail via PKCE (`exchangeCodeForSession`), reset de senha, route guard em todas as páginas internas |
| **Multi-tenancy** | ✅ | RLS por `condominio_id` em **8 tabelas** + `FORCE ROW LEVEL SECURITY` (até o owner respeita) |
| **Funcionários** | ✅ | CRUD com upload de foto em bucket privado, signed URLs em batch (1 req para a tabela inteira) |
| **Ponto** | ✅ | Entrada/saída do dia + motor `calcularMetricasPeriodo()` + espelho mensal consolidado em CSV |
| **Tarefas** | ✅ | CRUD com status ciclável, prioridade, prazo, responsável |
| **Faltas / LGPD** | ✅ | Faltas, atestados, férias, licença. Atestado vai para bucket privado `atestados-medicos` (Art. 11 LGPD — dado de saúde), acesso só via signed URL com TTL de 1h |
| **BI / Relatórios** | ✅ | Dashboard cruza faltas+ponto+tarefas em tempo real, distingue "em atestado/licença" de "falta injustificada", export CSV unificado com BOM UTF-8 |
| **Stripe** | ✅ | Edge Functions (`create-checkout-session` + `stripe-webhook`) com HMAC, gating reativo no frontend (`past_due` → bloqueio automático, `_blocked` → redirect com motivo) |
| **UI/UX** | ✅ | Skeleton loaders animados, sistema de toast 4 variantes, drawer mobile com backdrop+ESC, tabelas com scroll horizontal touch, breakpoints 768px e 480px |

---

## 🔒 Postura de segurança (Go-Live)

Auditoria final usando **Supabase Database Linter** + revisão manual:

| Categoria | Status |
|---|---|
| RLS em todas as tabelas | ✅ 8/8 com `ENABLE` + `FORCE` |
| Políticas RLS por operação | ✅ Select/Insert/Update/Delete cobertas em todas as tabelas e nos 2 buckets Storage |
| `search_path` fixo em funções | ✅ Todas as 5 funções `public.*` com `SET search_path = public, pg_catalog` |
| Views | ✅ `v_active_subscriptions` com `security_invoker = true` |
| Anon role | ✅ Sem `EXECUTE` em nenhuma função `SECURITY DEFINER` |
| `handle_new_user` | ✅ Revogado de TODOS os roles (só roda como trigger interno) |
| Webhook HMAC | ✅ `stripe.webhooks.constructEventAsync` antes de qualquer escrita |
| Secrets em código | ✅ Apenas anon key do Supabase (pública por design); todas as `sk_*`, `whsec_*` e `SERVICE_ROLE` vivem em `Deno.env.get(...)` |
| `.gitignore` | ✅ `.env*`, `supabase/.temp/`, `deploy-stripe.local.*` cobertos |

**Avisos aceitos (intencionais, documentados):**
- `my_condominio_id()`, `my_role()`, `ensure_condominio()` permanecem `SECURITY DEFINER` acessíveis ao role `authenticated` — necessário para que as policies de RLS funcionem e para que o usuário possa instanciar seu próprio condomínio. Cada uma retorna **apenas dados do próprio chamador** (`auth.uid()`).
- *Leaked Password Protection* — habilitar em produção via **Supabase Dashboard → Auth → Settings → "Enable password breach detection"** (uma flag, não SQL).

---

## 🛠️ Setup do zero

```bash
# 1. Banco — aplicar migrações em ordem
#    Via Supabase MCP, CLI ou cole no SQL Editor:
sql/001_init_auth_schema.sql
sql/002_fix_rls_recursion.sql
sql/003_funcionarios.sql
sql/004_planos_cupons.sql
sql/005_ponto.sql
sql/006_tarefas.sql
sql/007_faltas.sql
sql/008_storage_lgpd.sql
sql/009_stripe_schema.sql
sql/010_security_hardening.sql

# 2. Edge Functions Stripe (preencher placeholders no script primeiro)
./deploy-stripe.sh             # Linux/Mac
./deploy-stripe.ps1            # Windows

# 3. Frontend
#    a) Preencha js/stripe-config.js com os price IDs reais
#    b) git push → Vercel deploya em main automaticamente
```

---

## 📐 Convenções de código

- **Naming**: `snake_case` em SQL, `camelCase` em JS, `kebab-case` em arquivos
- **IIFE pattern**: cada `js/*.js` envelopa em `(function(){ 'use strict'; ... })()` e expõe via `window.staflow*`
- **CSS tokens**: nunca hardcode cor — use `var(--teal)`, `var(--navy)`, `var(--white-dim)`
- **Commits**: padrão semântico (`feat:`, `fix:`, `chore:`) com `Co-Authored-By: Claude…`

---

© 2026 StaFlow Tecnologia — **v1.0 Go-Live ready** 🚀
