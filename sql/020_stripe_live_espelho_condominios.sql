-- ============================================================
-- StaFlow — Migração 020: Stripe LIVE + espelho de assinatura
-- ------------------------------------------------------------
-- 1) Espelha status_assinatura e stripe_subscription_id em
--    condominios (route-guard checa apenas 1 query rápida)
-- 2) Atualiza ensure_condominio() para ler endereço estruturado
--    do auth.users.raw_user_meta_data (preenchido no /auth/cadastro)
-- ============================================================

alter table public.condominios
  add column if not exists status_assinatura      text default 'inactive',
  add column if not exists stripe_subscription_id text;

comment on column public.condominios.status_assinatura is
  'Espelho de subscriptions.status: active|trialing|past_due|canceled|inactive. Atualizado pelo stripe-webhook.';
comment on column public.condominios.stripe_subscription_id is
  'ID da subscription do Stripe vinculada ao condomínio.';

create unique index if not exists condominios_stripe_subscription_id_uidx
  on public.condominios(stripe_subscription_id)
  where stripe_subscription_id is not null;

create or replace function public.ensure_condominio()
returns uuid
language plpgsql
security definer
set search_path = public, pg_catalog
as $$
declare
  v_cond_id    uuid;
  v_profile    record;
  v_meta       jsonb;
begin
  select * into v_profile from public.profiles where id = auth.uid();
  if v_profile is null then
    raise exception 'Profile nao encontrado para o usuario autenticado.';
  end if;

  if v_profile.condominio_id is not null then
    return v_profile.condominio_id;
  end if;

  if v_profile.role not in ('sindico','admin') then
    return null;
  end if;

  select raw_user_meta_data into v_meta from auth.users where id = auth.uid();
  if v_meta is null then v_meta := '{}'::jsonb; end if;

  insert into public.condominios (
    nome, endereco, cnpj, email_admin, sindico_id,
    logradouro, numero, bairro, cidade, estado, cep
  )
  values (
    coalesce(v_profile.condominio_nome, v_meta->>'condominio_nome', 'Meu Condominio'),
    coalesce(v_profile.condominio_endereco, v_meta->>'condominio_endereco'),
    nullif(regexp_replace(coalesce(v_meta->>'condominio_cnpj', ''), '\D', '', 'g'), ''),
    nullif(v_meta->>'email_admin', ''),
    v_profile.id,
    nullif(v_meta->>'logradouro', ''),
    nullif(v_meta->>'numero', ''),
    nullif(v_meta->>'bairro', ''),
    nullif(v_meta->>'cidade', ''),
    nullif(v_meta->>'estado', ''),
    nullif(regexp_replace(coalesce(v_meta->>'cep', ''), '\D', '', 'g'), '')
  )
  returning id into v_cond_id;

  update public.profiles set condominio_id = v_cond_id where id = auth.uid();
  return v_cond_id;
end
$$;
