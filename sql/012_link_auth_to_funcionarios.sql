-- ============================================================
-- StaFlow — Migração 012: Vínculo auth.users ↔ funcionarios
-- ------------------------------------------------------------
-- Permite que o app de bolso (colaborador.html) saiba qual
-- funcionario está logado. O síndico pré-cadastra o funcionário
-- com e-mail; ao se cadastrar no /auth, o funcionário "reivindica"
-- seu registro via claim_funcionario_by_email().
-- ============================================================

-- 1. Coluna de vínculo (única — um auth user = um funcionario)
alter table public.funcionarios
  add column if not exists auth_user_id uuid references auth.users(id) on delete set null;

create unique index if not exists funcionarios_auth_user_id_uidx
  on public.funcionarios(auth_user_id)
  where auth_user_id is not null;

comment on column public.funcionarios.auth_user_id is
  'Vínculo opcional com auth.users — usado quando o funcionário tem login próprio no app de bolso.';

-- 2. Policy adicional: funcionário lê o próprio registro de funcionarios
drop policy if exists "funcionarios: self read"  on public.funcionarios;
create policy "funcionarios: self read"
  on public.funcionarios for select
  using (auth_user_id = auth.uid());

-- 3. RPC: reivindica o funcionário pelo email do usuário logado
create or replace function public.claim_funcionario_by_email()
returns table(funcionario_id uuid, condominio_id uuid, vinculado boolean)
language plpgsql
security definer
set search_path = public, pg_catalog
as $$
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
  select id, condominio_id into v_func_id, v_condo_id
  from public.funcionarios
  where auth_user_id = v_user_id
  limit 1;

  if found then
    return query select v_func_id, v_condo_id, true;
    return;
  end if;

  -- Procura funcionário ainda não vinculado com o mesmo email
  select id, condominio_id into v_func_id, v_condo_id
  from public.funcionarios
  where lower(email) = lower(v_email) and auth_user_id is null and ativo = true
  limit 1;

  if not found then
    return query select null::uuid, null::uuid, false;
    return;
  end if;

  update public.funcionarios set auth_user_id = v_user_id where id = v_func_id;
  update public.profiles
     set role = 'funcionario',
         condominio_id = v_condo_id
   where id = v_user_id;

  return query select v_func_id, v_condo_id, true;
end
$$;

revoke execute on function public.claim_funcionario_by_email() from public;
grant  execute on function public.claim_funcionario_by_email() to authenticated;

comment on function public.claim_funcionario_by_email() is
  'App de bolso: vincula auth.users ao funcionario pré-cadastrado com mesmo email. Atualiza profile para role=funcionario e seta condominio_id.';
