-- ============================================================
-- StaFlow — Correção: recursão infinita na policy de profiles
-- O problema: a policy "sindico read condo" faz SELECT em
-- public.profiles dentro de uma policy de public.profiles → loop.
-- Solução: função SECURITY DEFINER que bypassa RLS para
-- buscar o condominio_id e role do usuário atual.
-- ============================================================

-- 1. Remove a policy problemática
drop policy if exists "profiles: sindico read condo" on public.profiles;

-- 2. Função auxiliar que roda SEM RLS (security definer)
--    Retorna o condominio_id do usuário autenticado.
create or replace function public.my_condominio_id()
returns uuid
language sql
security definer
stable
set search_path = public
as $$
  select condominio_id from public.profiles where id = auth.uid() limit 1;
$$;

-- 3. Função auxiliar que retorna o role do usuário autenticado.
create or replace function public.my_role()
returns text
language sql
security definer
stable
set search_path = public
as $$
  select role from public.profiles where id = auth.uid() limit 1;
$$;

-- 4. Recria a policy usando as funções (sem auto-referência)
create policy "profiles: sindico read condo"
  on public.profiles for select
  using (
    public.my_role() = 'sindico'
    and public.my_condominio_id() is not null
    and condominio_id = public.my_condominio_id()
  );

-- ============================================================
-- FIM
-- ============================================================
