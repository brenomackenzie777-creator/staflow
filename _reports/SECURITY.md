# SECURITY.md — Auditoria de Segurança StaFlow
**Data:** 26/06/2026 | **Metodologia:** snyk-secure-at-inception

---

## Resumo Executivo

O StaFlow tem uma postura de segurança **acima da média para um SaaS em early stage**. RLS, FORCE ROW LEVEL SECURITY, SECURITY DEFINER com search_path fixo, HMAC no webhook Stripe e buckets privados com RLS de storage estão todos corretamente implementados. Os gaps identificados são críticos mas corrigíveis em menos de um dia de trabalho.

| Área | Status | Risco Residual |
|------|--------|----------------|
| Isolamento entre condos (RLS) | ✅ Sólido | Baixo |
| GPS antifraude | ⚠️ Gap offline | Alto |
| Storage atestados | ✅ Correto | Baixo |
| Webhook Stripe HMAC | ✅ Correto | Baixo |
| Security headers HTTP | ❌ Ausente | Médio |
| CORS edge functions | ⚠️ Wildcard | Médio |
| Injection (SQL/search_path) | ✅ Corrigido | Baixo |
| Exposição de anon key | ✅ By design | Baixo |

---

## 1. Isolamento entre Condominios (RLS)

### ✅ Aprovado com ressalvas

**O que está correto:**

`my_condominio_id()` e `my_role()` são funções SECURITY DEFINER com `search_path` fixo:
```sql
create or replace function public.my_condominio_id()
returns uuid language sql security definer stable
set search_path = public, pg_catalog
as $$ select condominio_id from public.profiles where id = auth.uid() limit 1; $$;
```

FORCE RLS nas tabelas core garante que nem o owner do schema escapa:
```sql
alter table public.profiles        force row level security;
alter table public.condominios     force row level security;
alter table public.funcionarios    force row level security;
alter table public.registros_ponto force row level security;
alter table public.tarefas         force row level security;
alter table public.faltas          force row level security;
alter table public.subscriptions   force row level security;
```

Policies de storage vinculam o primeiro segmento do path ao `my_condominio_id()`:
```sql
(storage.foldername(name))[1] = (my_condominio_id())::text
```
Isso garante que um síndico do Condo A não acessa fotos ou atestados do Condo B.

**Atenção — verificar:**

A migração `023_multi_cnpj_membros_condominio.sql` introduz `membros_condominio` para síndicos profissionais que gerenciam múltiplos condos. O header `x-condominio-id` define o condo ativo via `my_condominio_id()`. Verificar se existe policy que impede um síndico de injetar um `condominio_id` de outro síndico no header:

```js
// js/supabase-client.js linha 31
// Multi-CNPJ: header customizado lido por my_condominio_id() no Postgres.
```

**Risco:** Se `my_condominio_id()` lê o header diretamente sem validar membership, um síndico autenticado poderia enviar `x-condominio-id: <uuid-de-outro-condo>` e acessar dados alheios.

**Ação:** Verificar se `my_condominio_id()` valida que o usuário autenticado é membro do condo informado no header, ou se retorna apenas o condo do perfil (seguro).

---

## 2. GPS Antifraude

### ❌ Gap Crítico — Modo Offline

**Problema (BUG-001/002):** Em modo offline, `audit_status` é sobrescrito para `OFFLINE_PENDENTE`, descartando o resultado de `classificarGPS()`. Um funcionário com GPS mockado pode contornar a detecção de fraude simplesmente estando offline.

**Código problemático:**
```js
// colaborador.html linha 1477
payload.audit_status = 'OFFLINE_PENDENTE';  // SOBRESCREVE o GPS classificado
```

**O que está correto:**
```js
function classificarGPS(pos) {
  const sinais = [];
  // Detecta mocks baseado em múltiplos sinais GPS simultâneos
  if (sinais.length >= 2) return { status: 'FRAUDE_SUSPECT', sinais };
  if (sinais.length === 1) return { status: 'MOCK_SUSPECT',  sinais };
  return { status: 'OK', sinais: [] };
}
```
A lógica de detecção é sólida para o modo online.

**Correção:**
```js
// Preservar GPS status no campo separado antes de sobrescrever
const gpsClassificacao = pos?.audit_status ?? 'OK';
payload.gps_audit_status = gpsClassificacao;  // novo campo na tabela
payload.audit_status = 'OFFLINE_PENDENTE';

// Migração SQL necessária:
// ALTER TABLE registros_ponto ADD COLUMN gps_audit_status text;
```

Ou concatenar no status:
```js
payload.audit_status = ['FRAUDE_SUSPECT', 'MOCK_SUSPECT'].includes(gpsClassificacao)
  ? `OFFLINE+${gpsClassificacao}`
  : 'OFFLINE_PENDENTE';
```

---

## 3. Storage — Buckets de Atestados Médicos

### ✅ Correto

**Configuração verificada:**
- `atestados-medicos` bucket: `public = false` — nunca acessível diretamente por URL
- RLS policies: todas as operações (SELECT, INSERT, UPDATE, DELETE) validam `(storage.foldername(name))[1] = (my_condominio_id())::text`
- Signed URLs com TTL de 3600s (1h) — linha 606 de `faltas.html`:
  ```js
  .createSignedUrl(path, 3600);
  ```
- `allowed_mime_types: ['image/jpeg', 'image/png', 'application/pdf']` no bucket
- `file_size_limit: 10485760` (10MB)

**Não há leak de path entre condos** — mesmo que um síndico adivinhe o UUID de outro condo, a RLS bloqueia o acesso.

**Melhoria sugerida (P3):** Reduzir TTL para 1800s (30min) para dados sensíveis de saúde.

---

## 4. Webhook Stripe — HMAC

### ✅ Correto

**Validação verificada em `supabase/functions/stripe-webhook/index.ts`:**
```ts
const signature = req.headers.get("stripe-signature");
if (!signature) return new Response("Missing stripe-signature", { status: 400 });

const rawBody = await req.text();
let event: Stripe.Event;
try {
  event = await stripe.webhooks.constructEventAsync(rawBody, signature, WEBHOOK_SECRET);
} catch (err) {
  return new Response(`Webhook signature failed: ${(err as Error).message}`, { status: 400 });
}
```

- Usa `constructEventAsync` (versão async do Deno) com o `WEBHOOK_SECRET` do ambiente
- Rejeita requests sem header `stripe-signature`
- Rejeita payload com assinatura inválida com 400 antes de processar qualquer evento

**Nenhuma ação necessária.**

---

## 5. Security Headers HTTP

### ❌ Ausente

Nenhuma das páginas nem o Vercel deployment tem security headers configurados.

**Vetores de risco:**
- Sem `X-Frame-Options: DENY` → clickjacking possível (embutir em iframe malicioso)
- Sem `X-Content-Type-Options: nosniff` → MIME sniffing attacks
- Sem `Content-Security-Policy` → XSS via injeção de scripts

**Correção — criar `vercel.json` na raiz:**
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
        {
          "key": "Permissions-Policy",
          "value": "camera=(), microphone=(), geolocation=(self 'https://staflow.app.br')"
        }
      ]
    }
  ]
}
```

**CSP completa (Fase 2 — requer teste):**
```json
{
  "key": "Content-Security-Policy",
  "value": "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net https://js.stripe.com; connect-src 'self' https://*.supabase.co https://api.stripe.com; font-src 'self' https://fonts.gstatic.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: blob:; frame-src https://js.stripe.com"
}
```
*`unsafe-inline` temporário para os `<style>` inline — a eliminar na Fase 2.*

---

## 6. CORS na Edge Function create-checkout-session

### ⚠️ Wildcard — Risco Médio

```ts
const corsHeaders = {
  "Access-Control-Allow-Origin":  "*",   // ← qualquer origin
  ...
};
```

**Risco:** Qualquer site na internet pode fazer POST para a edge function com um token válido de um usuário StaFlow. Se um usuário autenticado visitar um site malicioso, o site poderia disparar um checkout em nome do usuário.

**Mitigação atual:** A function valida o `Authorization: Bearer <token>` do Supabase — sem token válido, rejeita. O atacante precisaria do token JWT do usuário, o que já seria um comprometimento de sessão completo.

**Correção recomendada (melhoria de defesa):**
```ts
const ALLOWED_ORIGINS = [
  'https://staflow.app.br',
  'https://www.staflow.app.br',
  'https://staflow.vercel.app',  // remover após migração completa
];

const origin = req.headers.get('origin') ?? '';
const allowedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];

const corsHeaders = {
  "Access-Control-Allow-Origin": allowedOrigin,
  "Vary": "Origin",
  ...
};
```

---

## 7. Injeção SQL / search_path

### ✅ Correto

Migração 010 (`010_security_hardening.sql`) corrige todos os achados:
- `search_path = public, pg_catalog` fixo em todas as SECURITY DEFINER functions
- EXECUTE revogado de `public` para `handle_new_user`, `my_condominio_id`, `my_role`, `ensure_condominio`
- EXECUTE regrantado apenas para `authenticated`
- View `v_active_subscriptions` com `security_invoker = true`

**Nenhuma ação necessária.**

---

## 8. Anon Key Exposta no Frontend

### ✅ By Design — Não é vulnerabilidade

A `SUPABASE_ANON_KEY` em `js/supabase-client.js` é pública por design do Supabase. O modelo de segurança é RLS + JWT, não segredo da anon key. Qualquer scanner de segurança vai flagear isso — é falso positivo.

**Documentar** para evitar alarme em auditorias externas:
```js
// NOTA PARA REVISORES DE SEGURANÇA:
// SUPABASE_ANON_KEY é projetada para ser pública — é a chave de "usuário não autenticado"
// do Supabase. A segurança real vem de RLS (Row Level Security) no banco.
// Ver: https://supabase.com/docs/guides/api/api-keys
```

---

## Plano de Ação

### Antes do Lançamento (< 4h)

| # | Ação | Arquivo | Risco mitigado |
|---|------|---------|----------------|
| 1 | Corrigir GPS offline (BUG-001/002) | colaborador.html | GPS fraude |
| 2 | Criar vercel.json com security headers | vercel.json (novo) | Clickjacking, MIME sniff |
| 3 | Verificar my_condominio_id() com header multi-CNPJ | sql/024 | Isolamento entre condos |

### Sprint 1 Pós-Lançamento

| # | Ação | Risco mitigado |
|---|------|----------------|
| 4 | Restringir CORS origin em edge functions | CSRF |
| 5 | Reduzir TTL signed URLs para 30min | Exposição de dados sensíveis |
| 6 | Documentar anon key nos comentários do código | Falsos positivos em scan |

### Fase 2

| # | Ação | Risco mitigado |
|---|------|----------------|
| 7 | CSP completa no vercel.json | XSS |
| 8 | Rate limiting na edge function de checkout | Abuso de API |
| 9 | Alertas automáticos em FRAUDE_SUSPECT/MOCK_SUSPECT | Detecção ativa |

---

*SECURITY.md — StaFlow · 26/06/2026*
