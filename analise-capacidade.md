# Análise de Capacidade por Camada — StaFlow
**Data:** 2026-06-15 | **Projeto Supabase:** `wsxpskrrzqtdoodpoofx` (sa-east-1)  
**Sem otimismo. Só o que o código e a infraestrutura realmente suportam hoje.**

---

## Estado atual do banco (medido via MCP)

| Tabela | Tamanho | Registros estimados |
|--------|---------|---------------------|
| `funcionarios` | 96 KB | 7 |
| `subscriptions` | 96 KB | 7 |
| `registros_ponto` | 80 KB | 8 |
| `condominios` | 80 KB | 6 |
| `membros_condominio` | 80 KB | — |
| `profiles` | 64 KB | — |
| `faltas` | 64 KB | — |
| `tarefas` | 48 KB | 0 |
| `cupons` | 48 KB | — |
| **TOTAL DB** | **~12 MB** | — |

Auth users: 10 | Condominios: 7 | Funcionários ativos: 7

---

## Camada 1 — Vercel (Frontend Estático)

**Plano atual:** Hobby (gratuito)

| Recurso | Limite Hobby | Uso atual | Preocupação |
|---------|-------------|-----------|-------------|
| Bandwidth | 100 GB/mês | ~0 | Nenhuma no curto prazo |
| Builds | 6.000/mês | baixo | Nenhuma |
| Serverless Functions | ❌ NÃO EXISTE | — | StaFlow não usa — tudo em Edge Functions do Supabase |
| Domínios customizados | Ilimitado | 1 | OK |

**Estimativa de crescimento:**  
Cada página HTML = ~50-150 KB. 100 usuários ativos/dia, ~10 páginas/sessão = ~15 MB/dia = 450 MB/mês.  
Com 500 usuários ativos/dia = ~2,2 GB/mês — ainda dentro dos 100 GB.

**Quando migrar para Vercel Pro ($20/mo):**  
Somente se bandwidth ultrapassar 80 GB/mês OU se precisar de funções serverless (não planejado).  
**Estimativa: nunca** — com a arquitetura atual (static + Supabase Edge Functions).

**Conforto:** ≤ 2.000 usuários ativos/dia  
**Limite real:** 100 GB/mês (~10.000 usuários/dia com sessão média)  
**Quebra:** bandwidth acima de 100 GB (exige Pro)

---

## Camada 2 — Supabase (Banco + Auth + Storage + Realtime)

**Plano atual:** Free (projeto criado 2026-05-15)

### 2a. Banco de Dados (PostgreSQL 17)

| Recurso | Limite Free | Uso atual | Breakeven estimado |
|---------|------------|-----------|-------------------|
| Storage | 500 MB | **12 MB (2,4%)** | ~4.000 condominios |
| Conexões (PgBouncer pool) | 60 conexões diretas (PgBouncer expõe mais) | baixo | — |
| CPU / IOPS | Shared (best-effort) | — | Degradação >50 transações/s |

**Crescimento por condomínio Pro (15 funcionários, uso diário):**
- `registros_ponto`: 15 func × 4 batidas/dia × 30 dias = 1.800 registros/mês ≈ **~180 KB/mês/condo**
- `faltas`: ~5 registros/mês ≈ 1 KB/mês/condo
- `tarefas`: ~20 registros × 2 KB = 40 KB/mês/condo (com renovação)
- **Total estimado: ~250 KB/mês por condomínio ativo**

Com 100 condominios ativos: +25 MB/mês → Storage free (~500 MB) dura ~20 meses.  
Com 500 condominios: Storage free esgota em ~4 meses.

**Ponto crítico de DB storage: ~400-450 condominios ativos** (buffer de segurança).

### 2b. Auth (MAU — Monthly Active Users)

| Recurso | Limite Free | Limite Pro |
|---------|------------|-----------|
| MAU | **50.000** | 100.000 |

**Contagem de MAU por condomínio Pro:**
- 1 síndico + até 15 colaboradores = **16 MAU por condomínio/mês**
- Se todos os colaboradores usam o app de bolso

Com 50.000 MAU free: suporta ~**3.125 condominios Pro** — **não é gargalo no curto prazo**.

**Conforto:** ≤ 1.000 condominios  
**Limite real:** 3.125 condominios (50k MAU / 16)  
**Quebra:** Pro Supabase a $25/mo dobra para 100k MAU

### 2c. Bandwidth (API + Storage)

| Recurso | Limite Free | Uso atual |
|---------|------------|-----------|
| Bandwidth | **2 GB/mês** | ~0 |

**Estimativa por condomínio Pro/mês:**
- API calls (JSON pequenos): ~500 requests/dia × síndico + 60/dia × 15 colaboradores = ~1.400 requests/dia × ~2 KB = 2,8 MB/dia = **~84 MB/mês**
- Storage (fotos de funcionários): upload único ~2 MB/func, download signed URL ~2 MB/acesso × raro
- **~100 MB/mês por condomínio ativo (estimativa conservadora)**

Com 2 GB free: suporta ~**20 condominios ativos** antes de esgoto de bandwidth.

> ⚠️ **ALERTA: bandwidth é o gargalo mais próximo no Supabase Free.**  
> Com 20 condominios Pro ativos em uso real, o limite de 2 GB/mês pode ser atingido.

**Conforto:** ≤ 15 condominios ativos simultâneos  
**Limite real:** ~20 condominios  
**Quebra:** Supabase Pro ($25/mo) → 50 GB bandwidth  
**Com Pro:** suporta ~500 condominios confortavelmente

### 2d. Realtime (WebSocket)

| Recurso | Limite Free | Limite Pro |
|---------|------------|-----------|
| Conexões simultâneas | **200** | 500 |

**Uso atual:** `dashboard.html` abre 1 canal Realtime por aba aberta.  
Cada síndico logado no dashboard = 1 conexão persistente.

**Conforto:** ≤ 150 síndicos com dashboard aberto simultaneamente  
**Limite real:** 200 conexões simultâneas (síndico + colaborador)  
**Quebra:** Supabase Pro → 500 conexões  

> Risco prático: um condomínio com vários síndicos ou um síndico com múltiplas abas pode consumir 3-5 conexões por condomínio. A 200 conexões, o sistema para de aceitar novos subscribers silenciosamente — o dashboard fica desatualizado sem aviso.

**Mitigação sem upgrade:** implementar cleanup via `window.addEventListener('beforeunload', () => channel.unsubscribe())`. Não está no código atual.

### 2e. Storage de Arquivos

| Recurso | Limite Free |
|---------|------------|
| Storage total | 1 GB |
| Bandwidth storage | Incluído nos 2 GB acima |

Buckets existentes:
- `fotos-funcionarios` — fotos de perfil dos funcionários (5 MB/cada)
- `atestados-medicos` — atestados LGPD (10 MB/cada)
- `documentos-condominio` — CCT PDF (20 MB/cada)

**Estimativa:** 15 funcionários × 5 MB fotos + 5 atestados × 10 MB + 1 CCT × 10 MB = **175 MB por condomínio** (caso médio)  
Com 1 GB free storage: ~5 condominios antes de esgoto de storage de arquivos.

> ⚠️ **SEGUNDO ALERTA: storage de arquivos pode esgotar antes do DB.**  
> Foto de todos os 15 funcionários + alguns atestados = ~175 MB/condo. Com 5-6 condominios ativos, o 1 GB de storage livre some.

**Conforto:** ≤ 4 condominios com fotos + atestados completos  
**Limite real:** ~5-6 condominios (1 GB / 175 MB)  
**Quebra:** Storage adicional no Supabase Pro = $0,021/GB extra (praticamente de graça) OU upgrade para Pro que inclui 100 GB

---

## Camada 3 — Edge Functions (Deno / Supabase)

**Funções deployadas:** 3
- `create-checkout-session` (v16) — Stripe Checkout
- `stripe-webhook` (v22) — Recebe eventos do Stripe
- `cancel-subscription` (v3) — Cancela assinatura

| Recurso | Limite Free | Estimativa de uso |
|---------|------------|------------------|
| Invocações/mês | **500.000** | ~100 por cliente pago (checkout + cancel são raros) |
| Tempo de execução | 150ms timeout | Cada função ~200-500ms (tem cold start) |
| Cold start | ~300-500ms | Apenas na 1ª invocação após inatividade |

**Conforto:** Praticamente ilimitado para o volume do StaFlow no curto prazo.  
Com 1.000 clientes fazendo 1 checkout/mês = 1.000 invocações. Longe dos 500.000.

**Risco real:** Cold start de ~300ms pode aparecer como "lentidão" no checkout se a função ficou inativa. Não é breaking, mas pode aumentar abandono.

**Limite real:** 500.000 invocações (inalcançável antes de 10.000+ clientes)  
**Quebra:** N/A

---

## Camada 4 — Stripe (Pagamentos)

| Recurso | Limite | Observação |
|---------|--------|-----------|
| Taxa por transação | 2,99% + R$0,39 | Fixo, não é gargalo de capacidade |
| Checkouts simultâneos | Ilimitado | Stripe não limita |
| Webhooks | 100 eventos/s por endpoint | Inalcançável neste estágio |

**Conclusão:** Stripe não é gargalo em nenhum cenário realista para o StaFlow.

---

## Tabela Resumo — Cenários de Capacidade

| Camada | Recurso | Confortável | Limite (grátis) | Quebra em |
|--------|---------|------------|-----------------|-----------|
| Vercel Hobby | Bandwidth | ≤2.000 usuários/dia | 100 GB/mês | Jamais, arquitetura estática |
| Supabase Free | **Bandwidth API** | **≤15 condos** | **2 GB/mês** | **~20 condos ativos** |
| Supabase Free | Storage arquivos | ≤4 condos | 1 GB | **~5-6 condos** |
| Supabase Free | DB storage | ≤400 condos | 500 MB | ~400+ condos |
| Supabase Free | MAU (auth) | ≤1.000 condos | 50.000 MAU | ~3.125 condos |
| Supabase Free | Realtime | ≤150 síndicos simultâneos | 200 conexões | 200 síndicos online ao mesmo tempo |
| Edge Functions | Invocações | ≤10.000 clientes | 500k/mês | Nunca neste estágio |
| Stripe | — | Ilimitado | N/A | N/A |

---

## Gargalos em ordem de urgência

### 🔴 Gargalo 1 — Bandwidth Supabase (rompe com ~20 condominios)
**Custo para resolver:** Supabase Pro = **US$25/mês** → inclui 50 GB bandwidth  
**Quando fazer:** Ao fechar o **3º cliente ativo** (precaução com margem).  
Com US$25/mês e 2 clientes pagantes a R$950 (anual ≈ R$79/mês) → já é sustentável com MRR ≥ R$158.

### 🟡 Gargalo 2 — Storage de Arquivos (rompe com ~5-6 condominios)
**Custo para resolver:** Supabase Pro (já inclui 100 GB storage).  
O mesmo upgrade do gargalo 1 resolve os dois. **Um único upgrade de US$25/mês resolve os dois principais gargalos imediatamente.**

### 🟡 Gargalo 3 — Realtime (rompe com 200 síndicos simultâneos)
**Mitigação de custo zero:** `channel.unsubscribe()` no `beforeunload` — reduz conexões zumbi.  
**Custo para resolver além da mitigation:** Supabase Pro → 500 conexões simultâneas.

### 🟢 Sem urgência
- DB storage: seguro para centenas de condominios
- MAU: seguro para milhares de condominios
- Vercel: seguro para escala razoável
- Edge Functions: seguro para o próximo ano
- Stripe: nunca é gargalo

---

## Plano de ação — "Quando pagar o quê"

| Quando | Ação | Custo mensal adicional |
|--------|------|----------------------|
| **Ao fechar o 3º cliente** | Upgrade Supabase Pro | US$25/mês (~R$128) |
| Ao atingir ~500 condominios | Avaliar Supabase Team ou Pro+add-ons | US$599+/mês |
| Ao atingir >5.000 usuários/dia em frontend | Avaliar Vercel Pro | US$20/mês |
| Nunca (arquitetura atual) | Edge Functions scaling | — |

### Análise do breakeven real (hoje)
- **Custo fixo atual:** R$128/mês (Supabase Pro já previsto + domínio — per briefing)
- **Breakeven:** 2 clientes Pro anual pagando R$950 = R$1.900 ÷ 12 = R$158/mês recorrente
- **Margem até Supabase Pro ($25/mês ≈ R$128):** incluída no custo fixo do briefing — **já está no orçamento**

**Conclusão:** O modelo atual comporta os primeiros 5 clientes fundadores sem nenhum custo adicional além dos R$128/mês já previstos. O upgrade para Supabase Pro deve ser feito preventivamente ao fechar o 3º cliente ativo, não em emergência.
