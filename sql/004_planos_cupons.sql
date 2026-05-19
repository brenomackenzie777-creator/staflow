-- ============================================================
-- StaFlow — Migração 004: Planos, Cupons e Assinaturas
-- ============================================================

-- Tabela de cupons de desconto
create table if not exists public.cupons (
  id               uuid primary key default gen_random_uuid(),
  code             text unique not null,
  descricao        text,
  discount_percent int  not null default 100 check (discount_percent between 0 and 100),
  max_uses         int,           -- null = ilimitado
  uses_count       int  not null default 0,
  valid_for_plans  text[],        -- null = todos os planos
  expires_at       timestamptz,
  active           boolean not null default true,
  created_at       timestamptz not null default now()
);

alter table public.cupons enable row level security;

-- Qualquer usuário autenticado pode ler cupons ativos (para validar)
create policy "read active cupons" on public.cupons
  for select using (active = true);

-- -------------------------------------------------------
-- Cupão de teste (100% off, ilimitado, sem expiração)
-- -------------------------------------------------------
insert into public.cupons (code, descricao, discount_percent, max_uses, active)
values ('TESTE', 'Acesso de teste — 100% de desconto em qualquer plano', 100, null, true)
on conflict (code) do nothing;

-- Tabela de assinaturas
create table if not exists public.subscriptions (
  id                   uuid primary key default gen_random_uuid(),
  profile_id           uuid references public.profiles(id) on delete cascade not null unique,
  condominio_id        uuid references public.condominios(id) on delete set null,
  plan                 text not null default 'starter'
                         check (plan in ('starter','pro','scale','enterprise')),
  status               text not null default 'pending'
                         check (status in ('active','trialing','canceled','pending','past_due')),
  coupon_used          text,
  discount_percent     int  default 0,
  current_period_start timestamptz default now(),
  current_period_end   timestamptz,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now()
);

alter table public.subscriptions enable row level security;

create policy "own subscription read" on public.subscriptions
  for select using (profile_id = auth.uid());

create policy "own subscription insert" on public.subscriptions
  for insert with check (profile_id = auth.uid());

create policy "own subscription update" on public.subscriptions
  for update using (profile_id = auth.uid());

-- Trigger de updated_at
create trigger set_subscriptions_updated_at
  before update on public.subscriptions
  for each row execute function touch_updated_at();

-- -------------------------------------------------------
-- Ativa plano Pro para perfis existentes (usuários legados)
-- Novos usuários passarão pela tela de planos normalmente.
-- -------------------------------------------------------
insert into public.subscriptions (profile_id, condominio_id, plan, status, coupon_used, discount_percent)
select
  p.id,
  p.condominio_id,
  'pro',
  'active',
  'LEGADO',
  100
from public.profiles p
where not exists (
  select 1 from public.subscriptions s where s.profile_id = p.id
)
on conflict (profile_id) do nothing;
