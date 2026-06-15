# StaFlow — Fase 2: Mapeamento do Fluxo Completo
**Autor:** Rafael (IA CFO/Diretor Comercial)  
**Data:** 12 de junho de 2026  
**Versão:** 1.0  

---

## Sumário executivo

Auditei o produto de ponta a ponta — cadastro, checkout Stripe, uso diário (ponto/tarefas/faltas), cancelamento e infraestrutura de suporte. Encontrei **4 gaps bloqueantes**, **5 gaps importantes** e **4 melhorias desejáveis**.

O produto está funcionalmente sólido para MVP. Os dois bloqueantes críticos para ir a produção são: **Stripe ainda em test mode** (sem pagamentos reais) e **cancelamento sem período de graça** (risco de chargeback e cancelamento por raiva).

---

## 1. Fluxo real documentado

### 1.1 Cadastro e onboarding

```
SÍNDICO
  → auth/cadastro.html (Step 1: nome/email/senha)
  → Step 2: dados do condomínio (nome, CNPJ opcional, CPF, tel, endereço via ViaCEP)
  → staflowAuth.signUp() com metadata completo
  → Step 3: "Verifique seu e-mail" (contador 60s para reenvio)
  → Clica no link de confirmação → /auth/callback
  → loadFullSession() → ensure_condominio() (RPC cria o condomínio se não existir)
  → route-guard detecta subscription=null → redireciona para /planos.html
  → Síndico escolhe plano → create-checkout-session → Stripe Hosted Checkout
  → Pagamento aprovado → stripe-webhook customer.subscription.created → espelharNoCondominio()
  → Acesso liberado ao /dashboard

COLABORADOR
  → auth/cadastro.html (1-step: email/senha, role=funcionario)
  → staflowAuth.signUp() → confirmação de e-mail
  → Após confirmação → /auth/callback → loadFullSession()
  → claim_funcionario_by_email() RPC tenta vincular pelo e-mail
    ├── Síndico já cadastrou o funcionário → vínculo criado → /colaborador.html (app de bolso)
    └── Síndico ainda NÃO cadastrou → block-screen "Aguardando ativação do Síndico"
```

**Proteções ativas:**
- `email_confirmed_at` validado em `loadFullSession()` — signOut forçado se nulo
- Anti-recon detector: 3+ tentativas de rota admin em 60s → signOut + `suspicious_activity`
- `executarRoteamentoSeguro()` é o único ponto de decisão de rota

---

### 1.2 Fluxo Stripe → Supabase

```
/planos.html
  → Usuário clica num plano (mensal ou anual)
  → create-checkout-session (Edge Function)
       ├── UPGRADE: valida membership, recupera stripe_customer do condomínio existente
       └── NOVO CONDOMÍNIO: INSERT em condominios (status='pending') + membros_condominio
  → Cria Stripe Customer (1 por condomínio, keyed por metadata.condominio_id)
  → Cria Stripe Checkout Session (mode=subscription, allow_promotion_codes=true)
  → Redireciona para Stripe Hosted Checkout

STRIPE → stripe-webhook (Edge Function v20)
  Eventos cobertos:
  ├── checkout.session.completed → espelharNoCondominio() (ativa plano)
  ├── customer.subscription.updated → espelharNoCondominio() (troca de plano)
  ├── customer.subscription.deleted → reset para starter (plano_ativo='starter')
  ├── invoice.payment_succeeded → atualiza current_period_end
  └── invoice.payment_failed → registrado mas sem bloqueio automático de acesso

cancel-subscription (Edge Function v2)
  → Validação manual de Bearer token
  → Valida membership em membros_condominio
  → stripe.subscriptions.cancel() → cancelamento IMEDIATO no Stripe (← gap crítico)
  → Webhook customer.subscription.deleted dispara → rebaixo para starter
```

**Tabelas envolvidas:** `condominios`, `subscriptions`, `membros_condominio`  
**Sincronização:** `espelharNoCondominio()` atualiza `condominios.plano`, `plano_ativo`, `status_assinatura`, `stripe_subscription_id`

---

### 1.3 Uso diário (Síndico/Admin)

```
/dashboard.html
  → bootstrapShell() → loadFullSession() → route-guard
  → KPIs do condomínio ativo (horas, tarefas, equipe recente)
  → Chart.js: gráfico de barras semanal (horas por dia)
  → Multi-CNPJ switcher (renderCondoSwitcher)

/funcionarios.html
  → CRUD de funcionários com limite por plano (trigger enforce_plan_limit_funcionarios)
  → Limites: Starter=3, Pro=15, Advanced=35, Scale=100
  → Invite por e-mail (cadastro link → claim_funcionario_by_email)

/ponto.html
  → Visualização das batidas por data + funcionário
  → Audit pills: FRAUDE_SUSPECT (vermelho), MOCK_SUSPECT (âmbar), LOW_ACCURACY (azul)
  → Edição manual de batidas (btn-edit-hora)
  → Espelho de ponto: exportação XLS com hash SHA-256 + assinaturas
  → Totalizadores: presentes, atrasos, faltas, horas extras

/tarefas.html e /faltas.html
  → Gestão de tarefas por funcionário e registro de faltas/justificativas

/configuracoes.html
  → Dados do condomínio (nome, CNPJ, endereço)
  → Upload de CCT (PDF, máx 20 MB — Supabase Storage)
  → Tolerância de atraso (default 10 min)
  → Seção "Minha assinatura": plano atual + botão cancelar + upgrade
```

---

### 1.4 Uso diário (Colaborador — PWA)

```
/colaborador.html (PWA, max-width 420px)
  → Rota protegida para role=funcionario
  → 3 tabs: Ponto / Tarefas / Justificativas

PONTO (4 batidas: Entrada → Almoço → Volta → Saída)
  → pegarPosicaoGPS() captura lat/lng + classify (OK / LOW_ACCURACY / MOCK_SUSPECT / FRAUDE_SUSPECT)
  → INSERT em registros_ponto com audit_status
  → OFFLINE: IndexedDB (staflow_offline_ponto) → sincroniza ao voltar online
  → Hora noturna calculada client-side (CLT Art.73 §1º, 22h–05h)

TAREFAS
  → Lista tarefas atribuídas pelo síndico
  → Progress ring (% de conclusão)

JUSTIFICATIVAS
  → Tipos: atestado, atraso, falta, saída antecipada
  → Upload de arquivo + descrição
```

---

### 1.5 Cancelamento e downgrade

```
/configuracoes.html → "Cancelar plano" → modal de confirmação
  → fetch POST cancel-subscription
  → Edge Function valida token + membership
  → stripe.subscriptions.cancel() ← IMEDIATO (não cancel_at_period_end)
  → Stripe dispara customer.subscription.deleted
  → stripe-webhook → handleSubscriptionDeleted() → plano='starter', plano_ativo='starter'
  → route-guard na próxima navegação detecta subscription bloqueada → /planos.html
```

---

## 2. Gaps identificados por prioridade

### 🔴 BLOQUEANTE — corrigir antes de ir a produção

---

#### GAP-01 · Stripe em test mode
**Localização:** `supabase/functions/stripe-webhook/index.ts` — variável `STAFLOW_STRIPE_LIVE_MODE = false`  
**Impacto:** Nenhum pagamento real é processado. Toda a grade de planos é simbólica.

**Solução técnica:**
1. No Stripe Dashboard (modo produção): criar os 8 Price IDs reais (Pro mensal/anual, Advanced mensal/anual, Scale mensal/anual).
2. Configurar variáveis de ambiente no Supabase:
   - `STRIPE_SECRET_KEY` → `sk_live_...`
   - `STRIPE_WEBHOOK_SECRET` → endpoint secret do webhook de produção
   - `STAFLOW_STRIPE_LIVE_MODE = true`
3. Atualizar `buildPriceMap()` no `stripe-webhook/index.ts` com Price IDs de produção.
4. Registrar o endpoint no Stripe produção: `https://wsxpskrrzqtdoodpoofx.supabase.co/functions/v1/stripe-webhook`
5. Deploy das Edge Functions.

**Complexidade:** Média (2–3h). Não requer mudança de lógica, só configuração.

---

#### GAP-02 · Cancelamento imediato sem período de graça
**Localização:** `supabase/functions/cancel-subscription/index.ts`  
**Impacto:** Cliente cancela e perde acesso imediato, mesmo tendo pago até o fim do período. Alto risco de chargeback e cancelamento por raiva.

**Solução técnica:**
```typescript
// Substituir:
await stripe.subscriptions.cancel(subscriptionId);

// Por:
await stripe.subscriptions.update(subscriptionId, {
  cancel_at_period_end: true,
});
// Acesso mantido até current_period_end.
// O webhook customer.subscription.deleted disparará na data de expiração real.
```

Atualizar o modal em `configuracoes.html` para exibir: *"Você manterá o acesso até [DATA_FIM_PERIODO]."*

**Complexidade:** Baixa (1h).

---

#### GAP-03 · Condomínios zumbi pós-abandono de checkout
**Localização:** `supabase/functions/create-checkout-session/index.ts`, bloco "NOVO condomínio"  
**Impacto:** Síndico inicia checkout para um 2º condomínio e abandona. Um registro em `condominios` com `status_assinatura='pending'` fica órfão para sempre. Polui dados, confunde contagem de condomínios e pode causar cobrança duplicada em reintento.

**Solução técnica — handler para `checkout.session.expired` no `stripe-webhook`:**
```typescript
case 'checkout.session.expired': {
  const condoId = event.data.object.metadata?.condominio_id;
  if (condoId) {
    const { data: sub } = await supabaseAdmin
      .from('subscriptions').select('id')
      .eq('condominio_id', condoId).maybeSingle();
    if (!sub) {
      // Sem subscription ativa = foi criado no checkout mas nunca pago
      await supabaseAdmin.from('condominios').delete().eq('id', condoId);
    }
  }
  break;
}
```

**Complexidade:** Média (2–3h).

---

#### GAP-04 · Colaborador preso na block-screen sem self-service
**Localização:** `colaborador.html` — `#block-screen`  
**Impacto:** Se o colaborador se cadastra antes de o síndico cadastrá-lo, fica preso com apenas o botão "Sair". Após o síndico cadastrá-lo, o colaborador não sabe que precisa sair e entrar de novo.

**Solução técnica:**
```javascript
// Adicionar botão "Verificar ativação" no block-screen
document.getElementById('btn-retry-claim')?.addEventListener('click', async () => {
  btn.disabled = true; btn.textContent = 'Verificando…';
  await sb.rpc('claim_funcionario_by_email');
  location.reload(); // Sessão reidratada — se vinculado, guard redireciona para /colaborador
});
```

**Complexidade:** Baixa (30min).

---

### 🟡 IMPORTANTE — corrigir em breve

---

#### GAP-05 · "Enterprise" ainda no dropdown de configurações
**Localização:** `configuracoes.html`, linha com `<option value="enterprise">Enterprise</option>`  
**Impacto:** Inconsistência com a grade oficial (Enterprise foi removido). Confunde síndicos que podem tentar "selecionar" um plano inexistente.  
**Solução:** Remover a option. Confirmar ausência em outros arquivos: `grep -r "enterprise" *.html`.  
**Complexidade:** Mínima (5min).

---

#### GAP-06 · Tolerância de atraso sem efeito real
**Localização:** `configuracoes.html` campo `#c-tolerancia` + `ponto.html`  
**Impacto:** Síndico configura tolerância de 10 min mas o campo não é usado em nenhum cálculo. Batidas com 1 min de atraso e 15 min de atraso recebem o mesmo tratamento visual. Perda de credibilidade.  
**Solução:**
1. No save de `configuracoes.html`, incluir `tolerancia_minutos` no UPDATE de `condominios`.
2. Em `ponto.html`, ao renderizar batidas de entrada, comparar `registrado_em` com horário esperado (se parametrizado) e sinalizar atraso dentro/fora da tolerância com cor diferente.  
**Complexidade:** Média (3–4h).

---

#### GAP-07 · Sem proteção contra batida duplicada no banco
**Localização:** `colaborador.html` → `registrarPonto()` + tabela `registros_ponto`  
**Impacto:** A fila offline pode sincronizar a mesma batida duas vezes se a aba for recarregada durante a sincronização. Não há `UNIQUE` constraint no banco para `(funcionario_id, DATE(registrado_em), tipo)`. Resultado: espelho de ponto com duplicatas — risco trabalhista em audiência.

**Solução:**
```sql
-- Migration
ALTER TABLE registros_ponto
  ADD CONSTRAINT uq_ponto_funcionario_dia_tipo
  UNIQUE (funcionario_id, tipo, (registrado_em::date));
```
No `sincronizarFilaOffline()`, tratar erro `23505` (unique violation) como sucesso silencioso.  
**Complexidade:** Baixa (1h).

---

#### GAP-08 · Sem e-mail transacional pós-cancelamento
**Localização:** `stripe-webhook/index.ts` — `handleSubscriptionDeleted()`  
**Impacto:** Quando o síndico cancela ou quando o Stripe cancela por inadimplência, nenhum e-mail é enviado. O síndico pode interpretar o corte de acesso como bug do sistema — alto volume de suporte desnecessário.

**Solução:** No `handleSubscriptionDeleted()`, após o rebaixo, disparar e-mail via Resend/Postmark com confirmação de cancelamento e link para reativar.  
**Complexidade:** Média (2–3h). Requer conta Resend + variável `RESEND_API_KEY`.

---

#### GAP-09 · Portaria MTE 671 sem assinatura ICP-Brasil
**Localização:** `ponto.html` — geração do espelho de ponto  
**Impacto:** O espelho tem hash SHA-256 (boa prática), mas o Art. 74 §3° da CLT + Portaria MTE 671/2021 exige assinatura eletrônica qualificada (ICP-Brasil) para REP-P digital válido em processo trabalhista.

**Solução imediata:** Adicionar disclaimer no rodapé do espelho exportado: *"Documento para controle interno. Para fins trabalhistas, requer assinatura qualificada ICP-Brasil conforme Portaria MTE 671/2021."*  
**Solução definitiva:** Integração com D4Sign ou Gov.br para assinar o PDF.  
**Complexidade:** Disclaimer = mínima (30min). Assinatura ICP = sprint dedicado.

---

### 🟢 DESEJÁVEL — backlog de produto

---

#### GAP-10 · Sem período de trial para síndico
Novo síndico é direcionado imediatamente para pagamento sem possibilidade de explorar o produto. O código do webhook já trata `trialing` mas não é usado no checkout.  
**Solução:** `trial_period_days: 14` em `create-checkout-session` para novos clientes. Ou: nurturing por e-mail para quem fica no Starter.  
**Complexidade:** Baixa para trial Stripe (1h).

---

#### GAP-11 · GPS sem geofencing do condomínio
O antifraude detecta GPS mockado mas não valida proximidade física ao condomínio. Colaborador pode bater ponto de casa com GPS real.  
**Solução:** Armazenar lat/lng do condomínio. No `registrarPonto()`, calcular distância haversine e marcar `audit_status='OUT_OF_RANGE'` se > raio configurado.  
**Complexidade:** Média (4–6h). Cálculo client-side, sem mudança de backend.

---

#### GAP-12 · Sem e-mail de onboarding pós-confirmação
Após confirmar o e-mail, nenhuma comunicação proativa é enviada. Síndico não recebe guia de setup; colaborador não recebe link do app de bolso (PWA).  
**Solução:** Supabase Auth Hook (Email Confirmed) → Edge Function → e-mail segmentado por role.  
**Complexidade:** Média (3–4h).

---

#### GAP-13 · Block-screen sem histórico de tentativas
A tela de bloqueio do colaborador não mostra há quanto tempo está aguardando vinculação nem o e-mail que precisa ser cadastrado de forma destacada. Pequena melhora de UX que reduz suporte.  
**Complexidade:** Mínima (30min).

---

## 3. Tabela resumo

| # | Gap | Prioridade | Complexidade |
|---|-----|-----------|--------------|
| GAP-01 | Stripe em test mode | 🔴 Bloqueante | Média (2–3h) |
| GAP-02 | Cancelamento imediato | 🔴 Bloqueante | Baixa (1h) |
| GAP-03 | Condomínios zumbi | 🔴 Bloqueante | Média (2–3h) |
| GAP-04 | Colaborador sem retry | 🔴 Bloqueante | Baixa (30min) |
| GAP-05 | Enterprise no dropdown | 🟡 Importante | Mínima (5min) |
| GAP-06 | Tolerância sem efeito | 🟡 Importante | Média (3–4h) |
| GAP-07 | Sem dedup no banco | 🟡 Importante | Baixa (1h) |
| GAP-08 | Sem e-mail pós-cancel | 🟡 Importante | Média (2–3h) |
| GAP-09 | MTE 671 sem ICP | 🟡 Importante | Disclaimer mínima |
| GAP-10 | Sem trial | 🟢 Desejável | Baixa (1h) |
| GAP-11 | GPS sem geofence | 🟢 Desejável | Média (4–6h) |
| GAP-12 | Sem e-mail onboarding | 🟢 Desejável | Média (3–4h) |
| GAP-13 | Block-screen UX | 🟢 Desejável | Mínima (30min) |

**Esforço total para 🔴:** ~7h  
**Esforço total para 🟡:** ~11h  

---

## 4. Ordem de ataque recomendada

**Dia 1 — configuração + quick wins:**  
GAP-01 (Stripe produção) · GAP-02 (cancelamento graceful) · GAP-04 (retry colaborador) · GAP-05 (Enterprise dropdown)

**Dia 2 — integridade de dados:**  
GAP-03 (condomínios zumbi) · GAP-07 (unique constraint ponto)

**Dia 3 — funcionalidade e comunicação:**  
GAP-06 (tolerância real) · GAP-08 (e-mail pós-cancel) · GAP-09 (disclaimer MTE 671)

**Backlog:** GAP-10 trial → GAP-12 onboarding → GAP-11 geofence → GAP-13 UX

---

*Documento gerado por auditoria completa dos arquivos: `auth/cadastro.html`, `js/auth.js`, `js/route-guard.js`, `js/app-shell.js`, `create-checkout-session/index.ts`, `stripe-webhook/index.ts`, `cancel-subscription/index.ts`, `colaborador.html`, `ponto.html`, `configuracoes.html`.*
