-- ============================================================
-- StaFlow — Migração 017: HOTFIX claim_funcionario_by_email
-- ------------------------------------------------------------
-- BUG: as colunas OUT funcionario_id/condominio_id colidem com
-- as colunas das tabelas referenciadas dentro do corpo da função
-- (PL/pgSQL trata como ambíguo → erro 42702).
-- Fix: usar aliases explícitos (f.id, f.condominio_id) em todos
-- os SELECTs internos.
--
-- IMPACTO: até esta migração o claim_funcionario_by_email NUNCA
-- funcionou em prod via RPC do supabase-js (erro 400 sempre).
-- Funcionários cadastrados via /auth/cadastro como colaborador
-- ficavam órfãos — não eram vinculados ao condomínio.
-- Descoberto via teste E2E na Sprint UX.
-- ============================================================

drop function if exists public.claim_funcionario_by_email();

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

  select f.id, f.condominio_id into v_func_id, v_condo_id
    from public.funcionarios f
   where f.auth_user_id = v_user_id
   limit 1;

  if found then
    return query select v_func_id, v_condo_id, true;
    return;
  end if;

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

  return query select v_func_id, v_condo_id, true;
end
$$;

revoke execute on function public.claim_funcionario_by_email() from public;
grant  execute on function public.claim_funcionario_by_email() to authenticated;

comment on function public.claim_funcionario_by_email() is
  'App de bolso: vincula auth.uid() ao funcionario pré-cadastrado com mesmo email. Atualiza profile para role=funcionario + condominio_id correto. (Hotfix 017: usar f.* alias resolve ambiguidade com colunas OUT.)';
