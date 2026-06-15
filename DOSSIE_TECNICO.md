# 📘 Dossiê de Alinhamento Técnico — StaFlow

**Destinatário:** Claude Co-Work (CFO / Estrategista)
**Versão:** Snapshot pós-commit `c072bd7` · 26 de maio de 2026
**Produção:** https://staflow.app.br · Supabase project `wsxpskrrzqtdoodpoofx`
**Repo:** github.com/brenomackenzie777-creator/staflow

---

## 1. Estrutura & Arquivos Core

### 1.1 Árvore de diretórios (essencial)

```
staflow/
├── 📄 staflow-landing.html       # Landing pública (CTAs → /auth/cadastro)
├── 🔐 dashboard.html              # Painel síndico (admin) — Realtime ativo
├── 📱 colaborador.html            # PWA do funcionário — offline-first
├── 📄 funcionarios.html           # CRUD equipe (síndico)
├── 📄 ponto.html                  # Tabela ponto + retificação + espelho legal
├── 📄 tarefas.html                # CRUD tarefas (síndico)
├── 📄 faltas.html                 # Faltas + atestados (síndico)
├── 📄 configuracoes.html          # Configurações do condomínio (síndico)
├── 📄 planos.html                 # Stripe Checkout + selos de segurança
├── 📄 404.html                    # Fallback de 404 com meta refresh
│
├── auth/
│   ├── login.html · cadastro.html · callback.html
│   ├── recuperar-senha.html · nova-senha.html
│   └── auth.css                   # Design tokens (paleta, fontes, radius)
│
├── js/                            # ★ Camada de lógica compartilhada
│   ├── supabase-client.js         # Singleton sb (anon key, PKCE auth)
│   ├── auth.js                    # signIn/signUp/loadFullSession/checkSubscription
│   ├── route-guard.js             # ★ Tronco Superior de Roteamento (decideRota pura)
│   ├── app-shell.js               # bootstrapShell (sidebar, sub gate, ensure_condominio)
│   ├── validadores.js             # validarCPF/CNPJ algoritmos oficiais RF
│   └── stripe-config.js           # window.STAFLOW_STRIPE_PRICES (apenas price_id)
│
├── 🛰️ manifest.json                # PWA manifest (display:standalone)
├── 🛰️ service-worker.js            # SW: precache + network-first HTML + bypass APIs
│
├── app.css · assets/logo-mark.svg
│
├── sql/                           # 21 migrações sequenciais (idempotentes)
│   ├── 001_init_auth_schema → 010_security_hardening      (Sprint 1: MVP)
│   ├── 011_compliance_trabalhista                          (CCT-RJ + NR-15)
│   ├── 012_link_auth_to_funcionarios → 017_hotfix         (Vínculo + GPS + Stripe)
│   ├── 018_retificacao_ponto                               (Compliance fiscal)
│   ├── 019_configuracoes_condominio                        (endereço + CCT + bucket)
│   ├── 020_stripe_live_espelho_condominios                 (Stripe LIVE-ready)
│   └── 021_enable_realtime_dashboard                       (publication realtime)
│
├── supabase/
│   ├── config.toml                # verify_jwt overrides
│   └── functions/
│       ├── create-checkout-session/   # POST → Stripe Checkout Session (server-only)
│       └── stripe-webhook/            # HMAC + 6 eventos + espelho atômico
│
├── deploy-stripe.ps1 / .sh        # Templates de deploy LIVE/TEST (com instruções)
├── vercel.json                    # cleanUrls + security headers
└── .gitignore                     # .env* + deploy-stripe.local.* + _tmp_*
```

### 1.2 Papel dos arquivos core

| Arquivo | Responsabilidade única |
|---|---|
| **`dashboard.html`** | Painel exclusivo do síndico/admin. Carrega stats operacionais (presentes, faltas, tarefas), compliance financeiro (provisões CCT 13º/Férias/FGTS/Passivo), alertas trabalhistas (NR-15, hora extra), card de auditoria GPS e equipe recente. **Realtime via `sb.channel()` escutando `postgres_changes` em `registros_ponto`, `faltas` e `tarefas` filtradas por `condominio_id` — atualiza sem F5 quando funcionário bate ponto.** Protegido pelo route-guard que ejeta funcionário → `/colaborador`. |
| **`colaborador.html`** | PWA mobile-first exclusivo do funcionário. Botão de ponto monumental (240px) com 4 estados (entrada/almoço/volta/saída), GPS antifraude (`classificarGPS` retorna OK/MOCK_SUSPECT/FRAUDE_SUSPECT/LOW_ACCURACY), tarefas reais com toggle, upload LGPD de atestados pra bucket privado. **Modo offline via IndexedDB (`staflow_offline_ponto`/`pontos_pendentes`)** — bate ponto sem internet, drena automaticamente no `online`. Sub-tela "Aguardando ativação do Síndico" se claim falhar. |
| **`js/route-guard.js`** | **Tronco Superior de Roteamento Autoritativo** — única decisão de rota do sistema. Função pura `decideRota(user, profile, pathname, opts)` + side-effect controlado em `ejetar()` com anti-loop (suprime redirect pra mesma rota). Whitelist de paths classificados em `PUBLIC`/`FUNCIONARIO`/`ADMIN`/`PLANOS`. **Validado por 20 unit tests** cobrindo todos os cenários de cruzamento. |
| **`manifest.json`** | PWA manifest. `display:standalone` (tela cheia sem barra do browser), `start_url:/colaborador`, `theme_color:#0d0f12` (dark consistente), ícones em SVG (any + maskable 192/512) apontando `/assets/logo-mark.svg`, shortcut "Bater ponto" pra home screen do device. Servido em produção HTTP 200. |
| **`service-worker.js`** | SW de cache estratégico. **PRECACHE** de assets críticos (logo, CSS, JS shell) no install. **Network-first** para HTML (sempre busca atualizações do Vercel — cai no cache só se offline). **Cache-first** para assets estáticos. **BYPASS TOTAL** para `wsxpskrrzqtdoodpoofx.supabase.co`, `api.stripe.com`, `checkout.stripe.com`, `viacep.com.br` (sempre online — sem stale-while-revalidate em dados sensíveis). Auto-update via `skipWaiting` + `clients.claim`. |

---

## 2. Engenharia de Dados — Camada Realtime

### 2.1 Tabelas centrais do fluxo

#### `registros_ponto` — fonte da verdade do ponto digital

| Coluna | Tipo | Origem | Notas |
|---|---|---|---|
| `id` | uuid PK | default | — |
| `condominio_id` | uuid FK | Multi-tenant | RLS filtra por `my_condominio_id()` |
| `funcionario_id` | uuid FK | App de bolso | Pareia com `funcionarios.auth_user_id` |
| `tipo` | text | `'entrada'` ou `'saida'` (alternados) | Motor `calcularMetricasPeriodo` pareia sequencialmente |
| `registrado_em` | timestamptz | Client clock | Server timestamp gera `created_at` separado |
| **`latitude`** | numeric(10,7) | GPS WGS84 | Migração 013 |
| **`longitude`** | numeric(10,7) | GPS WGS84 | Migração 013 |
| **`accuracy_m`** | integer | Precisão GPS em metros | Migração 013 |
| **`audit_status`** | text | **Sinal antifraude** | Valores possíveis: `OK` · `LOW_ACCURACY` (acc>150m) · `MOCK_SUSPECT` (1 sinal de mock) · `FRAUDE_SUSPECT` (2+ sinais) · `EDITADO_ADMIN` (retificado pelo síndico) · `OFFLINE_PENDENTE` (na fila IDB) |
| `motivo_edicao` | text | Síndico retifica | Migração 018 — compliance fiscal |
| `editado_por` / `editado_em` | uuid+ts | Trilha auditoria | Migração 018 |
| **REALTIME** | — | `supabase_realtime` publication | Migração 021 |

#### `faltas` — registro de ausências (+ bucket LGPD)

| Coluna | Tipo | Notas |
|---|---|---|
| `id`, `condominio_id`, `funcionario_id`, `data`, `created_at`, `updated_at` | padrão | — |
| `tipo` | text | `falta` · `atestado` · `ferias` · `licenca` |
| `justificada` | bool | Diferencia falta injustificada (ponto pro dashboard) |
| `observacao` | text | Texto livre |
| **`atestado_path`** | text | Caminho no **bucket privado** |
| **REALTIME** | — | publication ativa |

**Bucket `atestados-medicos`** (Storage):
- Privado · 10 MB · MIME `image/jpeg|png|application/pdf`
- Path determinístico: `<condominio_id>/<funcionario_id>/<yyyymmdd>-<rand>.<ext>`
- **4 policies RLS** (SELECT/INSERT/UPDATE/DELETE) usando `(storage.foldername(name))[1] = my_condominio_id()` → isolamento multi-tenant
- **LGPD Art. 11** — dado de saúde (atestado) tratado como sensível, signed URL com TTL 1h pro síndico visualizar

#### `tarefas` — checklist da equipe

| Coluna | Tipo | Notas |
|---|---|---|
| `id`, `condominio_id`, `funcionario_id`, `titulo`, `descricao` | padrão | — |
| `status` | text | `pendente` · `em_andamento` · `concluida` |
| `prioridade` | text | `alta` · `media` · `baixa` (badges coloridos) |
| `prazo` | date | Renderiza ordenado por prazo no /colaborador |
| **REALTIME** | — | publication ativa |

### 2.2 Stack Realtime

```js
// dashboard.html — boot
sb.channel('dash-<condo_id>')
  .on('postgres_changes',
      { event:'*', schema:'public', table:'registros_ponto',
        filter:'condominio_id=eq.X' },
      () => scheduleRefresh())              // debounce 800ms
  .on('postgres_changes', { ...table:'faltas'  }, scheduleRefresh)
  .on('postgres_changes', { ...table:'tarefas' }, scheduleRefresh)
  .subscribe();
```

**Garantia de segurança:** RLS por linha continua aplicado — o canal só entrega eventos das linhas que o cliente pode `SELECT`. Síndico de outro condomínio nunca recebe payloads do alheio.

---

## 3. Roteamento — Regra de Bifurcação Autoritativa

**Único ponto de decisão em todo o sistema:** `executarRoteamentoSeguro(user, profile, opts)` em `js/route-guard.js` (chamado por TODA página privada no boot).

### 3.1 Tabela de decisão (10 cenários cobertos)

| User | Role | Path acessado | Subscription | → Destino |
|:---:|:---:|---|:---:|---|
| ✗ | — | qualquer público | — | **allow** |
| ✗ | — | qualquer privado | — | `/auth/login.html` |
| ✓ | `funcionario` | `/colaborador` | — | **allow** |
| ✓ | `funcionario` | qualquer outra | — | **ejeta** `/colaborador.html` |
| ✓ | `sindico`/`admin` | `/colaborador` | — | **ejeta** `/dashboard.html` |
| ✓ | `sindico`/`admin` | rotas admin | ativa | **allow** |
| ✓ | `sindico`/`admin` | rotas admin | bloqueada | **ejeta** `/planos?reason=...` |
| ✓ | `sindico`/`admin` | `/planos` | qualquer | **allow** |
| ✓ | logado | `/auth/login` | — | **ejeta** para destino correto |
| ✓ | role desconhecida | qualquer | — | `/auth/login.html` |

**Whitelist de roles enforced no banco** (trigger `handle_new_user` v016): aceita apenas `sindico`/`admin`/`funcionario`. Tentativa de escalada via `raw_user_meta_data.role='admin'` no signup cai em `sindico` por default seguro.

**Anti-loop:** `ejetar()` compara `target.normalizado === current.normalizado` e suprime redirect. Caso degenerado vira `console.warn` + render normal (preferível travar que reload-loop).

---

## 4. Status Operacional Consolidado

### 4.1 Modelo de negócio

| Vetor | Status | Detalhes |
|---|:---:|---|
| **Self-service via Stripe** | ✅ pronto | Edge Function `create-checkout-session` autentica via JWT do Supabase, cria customer + session com `metadata: {profile_id, condominio_id, subscription_data}`. Stripe Checkout Hosted (zero PCI scope no StaFlow) |
| **Modo Stripe** | 🟡 LIVE-ready, atualmente TEST | Infra completa pra virada LIVE (deploy-stripe.ps1 detecta auto pelo prefixo `sk_live_`). Falta: criar produtos em LIVE no Stripe Dashboard + atualizar 2 vars + push |
| **Webhook (6 eventos)** | ✅ v3 ACTIVE | `checkout.session.completed` · `subscription.created/updated/deleted` · `invoice.paid` · `invoice.payment_failed` → espelha atomicamente em `condominios.{status_assinatura, stripe_subscription_id, plano}` |
| **Retentativas Stripe** | ✅ honradas | Função retorna 500 em falha → Stripe retenta com backoff exponencial por 3 dias |
| **Past_due → bloqueio** | ✅ automático | Route-guard ejeta síndico inadimplente pra `/planos?reason=past_due` no próximo boot |

### 4.2 PWA Instalável

| Componente | Status |
|---|:---:|
| `manifest.json` servido (1.171 bytes, HTTP 200) | ✅ |
| `service-worker.js` registrado (3.109 bytes) | ✅ |
| Display standalone (tela cheia) | ✅ |
| Apple touch icon + meta iOS | ✅ |
| Ícone + theme color escuro consistente | ✅ |
| Install prompt (Chrome Android) | ✅ |

### 4.3 Offline-First (IndexedDB)

| Componente | Status |
|---|:---:|
| Módulo `OfflineQueue` (5 ops, 5 try/catch) | ✅ |
| IDB `staflow_offline_ponto` / store `pontos_pendentes` | ✅ |
| `registrarPonto()` roteia online/offline via `navigator.onLine` | ✅ |
| Fallback automático online→offline se INSERT falhar | ✅ |
| Sync drena em 3 gatilhos (evento `online`, boot, manual) | ✅ |
| Lock `syncRunning` previne reentrância | ✅ |
| UI: pill `⚡ N batidas aguardando` + timeline com pill `OFFLINE` | ✅ |
| Toasts pedidos (amarelo offline + verde sync) | ✅ |

### 4.4 Realtime no Dashboard

| Componente | Status |
|---|:---:|
| Publication `supabase_realtime` habilitada nas 3 tabelas | ✅ (migração 021) |
| Channel `dash-<condo_id>` no boot | ✅ |
| Debounce 800ms previne rajadas | ✅ |
| Promise.allSettled defensivo (uma carga não trava outra) | ✅ |
| RLS por linha garante isolamento de tenant | ✅ |

### 4.5 Antifraude trabalhista

| Mecanismo | Como funciona |
|---|---|
| **GPS antifraude** (`classificarGPS`) | 4 sinais examinados: accuracy redonda (0/1/5/10), `pos.coords.mocked`, drift de timestamp >5min, perfil mock típico (altitude null + acc<5). 2+ sinais → `FRAUDE_SUSPECT` |
| **Validação fiscal real** | `validarCPF` + `validarCNPJ` com algoritmos oficiais RF (29 unit tests passando, incluindo Petrobras + Banco do Brasil) |
| **Retificação com trilha** | Síndico edita batida → `audit_status='EDITADO_ADMIN'` + `motivo_edicao` + `editado_por` + `editado_em` |
| **Espelho de ponto MTE 671** | PDF print-ready com tabela dia-a-dia, totalizadores CLT, linhas de assinatura e **hash SHA-256** dos metadados (qualquer alteração posterior modifica o hash → prova de integridade) |
| **CCT-RJ + NR-15 enforcement** | Dashboard alerta faxineiras sem `adicional_insalubridade=true`; alerta porteiros com >2h extras/dia (CLT Art.59) |

### 4.6 Multi-tenancy & Segurança

| Camada | Aplicação |
|---|---|
| **RLS** | 24 policies em 8 tabelas + `FORCE ROW LEVEL SECURITY` (até owner respeita) |
| **search_path fixo** | Todas as 5 funções `public.*` com `SET search_path = public, pg_catalog` (anti-injection) |
| **Whitelist de roles** | Trigger `handle_new_user` aceita apenas sindico/admin/funcionario |
| **`SECURITY DEFINER` restritas** | `handle_new_user` REVOKED de TODOS; outras só p/ authenticated |
| **HMAC webhook** | `stripe.webhooks.constructEventAsync` antes de qualquer escrita |
| **Zero secrets no frontend** | Validado por auditoria grep — única ocorrência de `sk_*` é JSDoc placeholder |

---

## 5. Pontos para Alinhamento Financeiro com o CFO

### 5.1 Pricing já cabeado no Stripe (test mode)

| Plano | Price ID | Valor mensal | Limites comerciais sugeridos |
|---|---|---|---|
| **Starter** | (gratuito interno) | R$ 0 | Sugestão: até 5 funcionários |
| **Pro** | `price_1TbMBAE7YYxcPUBAsoNhJvCq` | R$ 99,00 | Sugestão: até 20 funcionários |
| **Scale** | `price_1TbMBhE7YYxcPUBAX6eUrgYJ` | R$ 249,00 | Sugestão: ilimitado |
| **Enterprise** | manual (mailto) | sob consulta | white-label / SLA dedicado |

### 5.2 Custos de infra atuais

| Item | Fornecedor | Custo atual |
|---|---|---|
| Hosting frontend | Vercel | Plano free (suficiente até ~100GB tráfego) |
| Banco + Storage + Edge Functions + Realtime | Supabase | Plano Pro recomendado p/ produção ($25/mês — desbloqueia PITR backup + 100GB storage) |
| Stripe processing | Stripe | 3.99% + R$ 0,39 por transação aprovada |
| Domínio | (ainda não comprado) | ~R$ 40/ano se for `.com.br` |

### 5.3 Travas financeiras já implementáveis

| Trava | Onde aplicar |
|---|---|
| **Limite por plano** (max funcionários) | Adicionar validação em `funcionarios.html` antes do INSERT, checando `subscription.plan` |
| **Bloqueio de inadimplente** | ✅ Já implementado — route-guard ejeta `past_due` pra `/planos` |
| **Trial 14 dias** | Configurável via `subscription_data.trial_period_days` na Edge Function `create-checkout-session` |
| **Webhook de invoice.paid** | ✅ Já trata renovação e reativa contas que estavam `past_due` |
| **Espelho de ponto p/ contabilidade** | ✅ Hash SHA-256 garante integridade pra prestação de contas |

---

## 6. Próximos passos sugeridos (para discussão com CFO)

1. **Virar chave Stripe para LIVE** (10 passos manuais documentados em `deploy-stripe.ps1`)
2. **Adicionar enforcement de limite de funcionários por plano** (~30 linhas de código)
3. **Comprar domínio próprio** + apontar pra Vercel (1h)
4. **Subir para Supabase Pro** antes de aceitar primeiro cliente pagante (Point-in-Time Recovery é mandatório)
5. **Página de Trial 14 dias** (configuração no Stripe, sem código novo)

---

**Sistema operando em modelo Self-Service via Stripe (test mode → LIVE-ready) · PWA instalável com IndexedDB offline · Sync Realtime · 21 migrações · 8 tabelas RLS-protegidas · Zero secrets no frontend · Anti-loop guard validado.**
