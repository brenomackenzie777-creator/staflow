-- 029_atribuicao_marketing.sql
-- ★ 18/08/2026 — a pedido do Breno: rastrear de onde vêm os cadastros
-- (e-mail, campanha, etc.) pra medir o funil de marketing junto com a
-- receita real, no mesmo lugar que o time de agentes já lê todo dia
-- (panorama_negocio). Aplicado direto via Supabase MCP (apply_migration).

alter table public.condominios
  add column if not exists utm_source text,
  add column if not exists utm_medium text,
  add column if not exists utm_campaign text,
  add column if not exists signup_referrer text;

comment on column public.condominios.utm_source is 'Origem do cadastro (ex: email, instagram, google) — capturado no primeiro toque, via raw_user_meta_data no signup.';
comment on column public.condominios.utm_campaign is 'Campanha específica (ex: leads-agosto-2026) — usado pra ligar receita a uma ação de marketing específica.';

-- ensure_condominio() agora também grava a atribuição de marketing
-- (utm_source/medium/campaign/referrer), lida de raw_user_meta_data —
-- populada pelo front (js/attribution.js captura da URL no primeiro
-- toque, auth/cadastro.html manda junto no signUp()).
create or replace function public.ensure_condominio()
returns uuid
language plpgsql
security definer
set search_path to 'public', 'pg_catalog'
as $function$
declare
  v_cond_id    uuid;
  v_profile    record;
  v_meta       jsonb;
  v_membro     record;
begin
  select * into v_profile from public.profiles where id = auth.uid();
  if v_profile is null then
    raise exception 'Profile nao encontrado para o usuario autenticado.';
  end if;

  select mc.condominio_id, mc.role into v_membro
    from public.membros_condominio mc
    join public.condominios c on c.id = mc.condominio_id
   where mc.user_id = v_profile.id
   order by mc.created_at asc
   limit 1;

  if v_membro.condominio_id is not null then
    if v_profile.condominio_id is distinct from v_membro.condominio_id then
      update public.profiles set condominio_id = v_membro.condominio_id where id = v_profile.id;
    end if;
    return v_membro.condominio_id;
  end if;

  if v_profile.role not in ('sindico','admin') then
    return null;
  end if;

  select raw_user_meta_data into v_meta from auth.users where id = auth.uid();
  if v_meta is null then v_meta := '{}'::jsonb; end if;

  insert into public.condominios (
    nome, endereco, cnpj, email_admin, sindico_id,
    logradouro, numero, bairro, cidade, estado, cep,
    utm_source, utm_medium, utm_campaign, signup_referrer
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
    nullif(regexp_replace(coalesce(v_meta->>'cep', ''), '\D', '', 'g'), ''),
    nullif(v_meta->>'utm_source', ''),
    nullif(v_meta->>'utm_medium', ''),
    nullif(v_meta->>'utm_campaign', ''),
    nullif(v_meta->>'signup_referrer', '')
  )
  returning id into v_cond_id;

  update public.profiles set condominio_id = v_cond_id where id = auth.uid();

  insert into public.membros_condominio (user_id, condominio_id, role)
  values (v_profile.id, v_cond_id, v_profile.role)
  on conflict (user_id, condominio_id) do nothing;

  return v_cond_id;
end
$function$;
