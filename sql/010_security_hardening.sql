-- ============================================================
-- StaFlow — Migração 010: Security Hardening (Go-Live)
-- Corrige achados do Supabase Database Linter:
--   ERROR  0010 — view SECURITY DEFINER
--   WARN   0011 — search_path mutável em funções
--   WARN   0028/0029 — SECURITY DEFINER functions expostas no /rpc
-- ============================================================

-- ── 1. View v_active_subscriptions: força SECURITY INVOKER ───
-- Por padrão, views em Postgres 15+ podem ser security_invoker
-- (respeitam RLS de quem consulta). Recriamos explicitamente.

drop view if exists public.v_active_subscriptions;

create view public.v_active_subscriptions
with (security_invoker = true)
as
select s.*
from public.subscriptions s
where s.status in ('active', 'trialing')
  and (s.current_period_end is null or s.current_period_end > now());

comment on view public.v_active_subscriptions is
  'Subscriptions vigentes (active/trialing E não expiradas). SECURITY INVOKER — respeita RLS do consultante.';

-- ── 2. Fixar search_path em funções (anti-injection) ──────────
-- Funções sem search_path fixo podem ser sequestradas por um
-- esquema malicioso anteposto ao search_path do role.

alter function public.touch_updated_at()
  set search_path = public, pg_catalog;

alter function public.my_condominio_id()
  set search_path = public, pg_catalog;

alter function public.my_role()
  set search_path = public, pg_catalog;

alter function public.ensure_condominio()
  set search_path = public, pg_catalog;

alter function public.handle_new_user()
  set search_path = public, pg_catalog;

-- ── 3. Restringir EXECUTE em SECURITY DEFINER ─────────────────
-- handle_new_user é trigger interno do Supabase Auth — NUNCA
-- deve ser chamável via /rest/v1/rpc.
revoke execute on function public.handle_new_user() from anon, authenticated, public;

-- PostgreSQL concede EXECUTE TO PUBLIC por padrão em CREATE FUNCTION.
-- Revogamos de PUBLIC (que inclui anon) e regrantamos apenas para
-- authenticated — necessário para que as RLS policies que usam essas
-- funções continuem funcionando, mas bloqueia chamadas anônimas.
revoke execute on function public.my_condominio_id()  from public;
revoke execute on function public.my_role()           from public;
revoke execute on function public.ensure_condominio() from public;

grant execute on function public.my_condominio_id()  to authenticated;
grant execute on function public.my_role()           to authenticated;
grant execute on function public.ensure_condominio() to authenticated;

-- ── 4. Reforço opcional: FORCE RLS nas tabelas core ───────────
-- Por padrão, o role `postgres` (proprietário) bypassa RLS.
-- FORCE garante que NEM o owner escape — útil em produção,
-- já que toda escrita do app passa por anon/authenticated/service_role.

alter table public.profiles        force row level security;
alter table public.condominios     force row level security;
alter table public.funcionarios    force row level security;
alter table public.registros_ponto force row level security;
alter table public.tarefas         force row level security;
alter table public.faltas          force row level security;
alter table public.cupons          force row level security;
alter table public.subscriptions   force row level security;
