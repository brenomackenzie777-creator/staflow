-- ============================================================
-- StaFlow — 028: horário do funcionário, correções de vínculo
-- multi-CNPJ e suporte a exclusão de condomínio
-- ------------------------------------------------------------
-- Consolida no repositório mudanças já aplicadas em produção via
-- MCP do Supabase nesta sessão. Idempotente — pode rodar de novo
-- sem quebrar nada.
-- ============================================================

-- 1) Horário de trabalho por funcionário (início/fim/almoço)
alter table public.funcionarios
  add column if not exists horario_inicio time,
  add column if not exists horario_fim    time,
  add column if not exists horas_almoco_min int;

-- 2) claim_funcionario_by_email() — agora também garante o vínculo
--    em membros_condominio (bug antigo deixava funcionário sem RLS
--    funcionando nas próprias abas do app dele).
create or replace function public.claim_funcionario_by_email()
 returns TABLE(funcionario_id uuid, condominio_id uuid, vinculado boolean)
 language plpgsql
 security definer
 set search_path to 'public', 'pg_catalog'
as $function$
declare
  v_user_id   uuid;
  v_email     text;
  v_func_id   uuid;
  v_condo_id  uuid;
begin
  v_user_id := auth.uid();
  if v_user_id is null then
    return query select null::uuid, null::uuid, false;
    return;
  end if;

  select email into v_email from auth.users where id = v_user_id;
  if v_email is null then
    return query select null::uuid, null::uuid, false;
    return;
  end if;

  -- Já vinculado?
  select f.id, f.condominio_id into v_func_id, v_condo_id
    from public.funcionarios f
   where f.auth_user_id = v_user_id
   limit 1;

  if found then
    -- Garante o vínculo em membros_condominio mesmo pra quem já foi
    -- vinculado antes desta correção (idempotente).
    insert into public.membros_condominio (user_id, condominio_id, role)
    values (v_user_id, v_condo_id, 'funcionario')
    on conflict (user_id, condominio_id) do nothing;

    return query select v_func_id, v_condo_id, true;
    return;
  end if;

  -- Procura funcionário ainda não vinculado com o mesmo email
  select f.id, f.condominio_id into v_func_id, v_condo_id
    from public.funcionarios f
   where lower(f.email) = lower(v_email)
     and f.auth_user_id is null
     and f.ativo = true
   limit 1;

  if not found then
    return query select null::uuid, null::uuid, false;
    return;
  end if;

  update public.funcionarios
     set auth_user_id = v_user_id
   where id = v_func_id;

  update public.profiles
     set role = 'funcionario',
         condominio_id = v_condo_id
   where id = v_user_id;

  insert into public.membros_condominio (user_id, condominio_id, role)
  values (v_user_id, v_condo_id, 'funcionario')
  on conflict (user_id, condominio_id) do nothing;

  return query select v_func_id, v_condo_id, true;
end
$function$;

-- 3) meus_condominios() — nunca mostra condomínio 'pending' (checkout
--    abandonado) no switcher do síndico.
create or replace function public.meus_condominios()
returns table(condominio_id uuid, nome text, plano text, status_assinatura text, role text)
language sql
stable security definer
set search_path to 'public', 'pg_catalog'
as $function$
  SELECT
    c.id, c.nome, c.plano, c.status_assinatura, mc.role
    FROM public.condominios c
    JOIN public.membros_condominio mc ON mc.condominio_id = c.id
   WHERE mc.user_id = auth.uid()
     AND c.status_assinatura <> 'pending'
   ORDER BY c.created_at ASC;
$function$;

-- 4) ensure_condominio() — fonte de verdade passa a ser
--    membros_condominio (N:N), não profiles.condominio_id (ponteiro
--    legado que fica desatualizado quando 1 de vários condomínios do
--    síndico é excluído). Sem essa correção, excluir 1 condomínio de
--    um síndico com vários faria o sistema criar um condomínio extra
--    do nada na próxima vez que ele entrasse.
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

  insert into public.membros_condominio (user_id, condominio_id, role)
  values (v_profile.id, v_cond_id, v_profile.role)
  on conflict (user_id, condominio_id) do nothing;

  return v_cond_id;
end
$function$;
