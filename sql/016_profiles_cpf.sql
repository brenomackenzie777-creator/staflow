-- ============================================================
-- StaFlow — Migração 016: CPF do síndico em profiles
-- ------------------------------------------------------------
-- Síndicos passam a poder informar o próprio CPF no cadastro.
-- O trigger handle_new_user lê o CPF do metadata (passado no
-- signUp) e grava na coluna. CPF é validado matematicamente
-- no frontend antes do signUp.
-- ============================================================

alter table public.profiles
  add column if not exists cpf text;

comment on column public.profiles.cpf is
  'CPF do usuário (11 dígitos somente números). Validado matematicamente no frontend.';

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public, pg_catalog
as $$
declare
  v_role text;
  v_is_func boolean;
  v_cpf text;
begin
  v_role := lower(coalesce(new.raw_user_meta_data->>'role', 'sindico'));
  if v_role not in ('sindico', 'admin', 'funcionario') then
    v_role := 'sindico';
  end if;
  v_is_func := (v_role = 'funcionario');

  v_cpf := nullif(regexp_replace(coalesce(new.raw_user_meta_data->>'cpf', ''), '\D', '', 'g'), '');

  insert into public.profiles (
    id, full_name, email, role, phone, cpf, condominio_nome, condominio_endereco
  ) values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
    new.email,
    v_role,
    new.raw_user_meta_data->>'phone',
    v_cpf,
    case when v_is_func then null else new.raw_user_meta_data->>'condominio_nome' end,
    case when v_is_func then null else new.raw_user_meta_data->>'condominio_endereco' end
  );
  return new;
end;
$$;
