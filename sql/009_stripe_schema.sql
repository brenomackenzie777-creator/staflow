-- ============================================================
-- StaFlow — Migração 009: Stripe Schema
-- Adiciona campos do Stripe na tabela subscriptions para
-- integração com Checkout / Customer Portal / Webhooks.
-- ============================================================

-- ── Campos Stripe ──────────────────────────────────────────────

alter table public.subscriptions
  add column if not exists stripe_customer_id     text,
  add column if not exists stripe_subscription_id text,
  add column if not exists stripe_price_id        text,
  add column if not exists cancel_at_period_end   boolean not null default false,
  add column if not exists canceled_at            timestamptz,
  add column if not exists trial_end              timestamptz;

-- ── Índices únicos (Stripe IDs são únicos por escopo) ─────────

create unique index if not exists subscriptions_stripe_customer_id_key
  on public.subscriptions (stripe_customer_id)
  where stripe_customer_id is not null;

create unique index if not exists subscriptions_stripe_subscription_id_key
  on public.subscriptions (stripe_subscription_id)
  where stripe_subscription_id is not null;

-- ── Comentários (documentação inline) ─────────────────────────

comment on column public.subscriptions.stripe_customer_id is
  'ID do customer no Stripe (cus_xxx). Único por perfil. Preenchido na 1ª compra.';

comment on column public.subscriptions.stripe_subscription_id is
  'ID da subscription no Stripe (sub_xxx). Atualizado por webhook customer.subscription.*.';

comment on column public.subscriptions.stripe_price_id is
  'ID do price ativo no Stripe (price_xxx). Permite saber qual plano/intervalo está vigente.';

comment on column public.subscriptions.cancel_at_period_end is
  'true quando o usuário cancelou mas ainda tem acesso até current_period_end.';

comment on column public.subscriptions.canceled_at is
  'Timestamp em que o cancelamento foi processado pelo Stripe.';

comment on column public.subscriptions.trial_end is
  'Fim do período de trial (se aplicável). status=trialing enquanto now() < trial_end.';

-- ── View útil: assinatura "vigente" (active OU trialing E não expirada) ──

create or replace view public.v_active_subscriptions as
select s.*
from public.subscriptions s
where s.status in ('active', 'trialing')
  and (
    s.current_period_end is null              -- assinatura sem vencimento (ex: cupom TESTE)
    or s.current_period_end > now()           -- ainda dentro do período
  );

comment on view public.v_active_subscriptions is
  'Subscriptions com status active/trialing E ainda dentro do período vigente. Usada pelo frontend para gating de acesso.';
