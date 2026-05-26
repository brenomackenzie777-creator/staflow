-- ============================================================
-- StaFlow — Migração 014: Hardening do trigger handle_new_user
-- ------------------------------------------------------------
-- Antes: aceitava QUALQUER string em raw_user_meta_data.role
-- (risco: alguém poderia enviar role='admin' no signUp e
-- escalar privilégios).
--
-- Agora: whitelist estrita ('sindico'|'admin'|'funcionario').
-- Qualquer valor fora cai em 'sindico' (default seguro).
-- Bonus: se role='funcionario', NÃO grava condominio_nome/
-- endereco do metadata (esses campos são lixo para colaborador).
-- ============================================================

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public, pg_catalog
as $$
declare
  v_role text;
  v_is_func boolean;
begin
  -- Whitelist de roles. Default seguro = 'sindico'.
  v_role := lower(coalesce(new.raw_user_meta_data->>'role', 'sindico'));
  if v_role not in ('sindico', 'admin', 'funcionario') then
    v_role := 'sindico';
  end if;
  v_is_func := (v_role = 'funcionario');

  insert into public.profiles (
    id, full_name, email, role, phone, condominio_nome, condominio_endereco
  ) values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
    new.email,
    v_role,
    new.raw_user_meta_data->>'phone',
    case when v_is_func then null else new.raw_user_meta_data->>'condominio_nome' end,
    case when v_is_func then null else new.raw_user_meta_data->>'condominio_endereco' end
  );
  return new;
end;
$$;

comment on function public.handle_new_user() is
  'Trigger on auth.users insert: cria profile correspondente. Whitelist de roles (sindico/admin/funcionario, default sindico). Para role=funcionario não grava campos de condominio.';
