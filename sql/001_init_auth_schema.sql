-- ============================================================
-- StaFlow — Migração inicial
-- Tabelas: profiles, condominios
-- Trigger: handle_new_user (cria profile automaticamente no signup)
-- RLS: políticas por usuário e por condomínio
-- ============================================================

-- 1. EXTENSÕES -----------------------------------------------
create extension if not exists "pgcrypto";

-- 2. TABELA CONDOMINIOS (precisa existir antes de profiles por causa do FK) --
create table if not exists public.condominios (
  id           uuid primary key default gen_random_uuid(),
  nome         text not null,
  endereco     text,
  sindico_id   uuid,                                          -- FK adicionado abaixo (após profiles)
  plano        text not null default 'starter'
               check (plano in ('starter','pro','scale','enterprise')),
  ativo        boolean not null default true,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- 3. TABELA PROFILES ---------------------------------------
create table if not exists public.profiles (
  id                    uuid primary key references auth.users(id) on delete cascade,
  full_name             text not null,
  email                 text not null,
  phone                 text,
  role                  text not null default 'sindico'
                        check (role in ('sindico','admin','funcionario')),
  condominio_nome       text,
  condominio_endereco   text,
  condominio_id         uuid references public.condominios(id) on delete set null,
  avatar_url            text,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

-- FK reverso: sindico_id em condominios → profiles
alter table public.condominios
  drop constraint if exists condominios_sindico_id_fkey;
alter table public.condominios
  add  constraint condominios_sindico_id_fkey
  foreign key (sindico_id) references public.profiles(id) on delete set null;

-- Índices úteis
create index if not exists profiles_condominio_id_idx on public.profiles(condominio_id);
create index if not exists profiles_email_idx          on public.profiles(email);
create index if not exists condominios_sindico_id_idx  on public.condominios(sindico_id);

-- 4. TRIGGER: cria profile automaticamente ao criar usuário ---
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, email, role, phone, condominio_nome, condominio_endereco)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
    new.email,
    coalesce(new.raw_user_meta_data->>'role', 'sindico'),
    new.raw_user_meta_data->>'phone',
    new.raw_user_meta_data->>'condominio_nome',
    new.raw_user_meta_data->>'condominio_endereco'
  );
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- 5. TRIGGER: mantém updated_at ---------------------------
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end;
$$;

drop trigger if exists profiles_touch_updated   on public.profiles;
create trigger profiles_touch_updated
  before update on public.profiles
  for each row execute function public.touch_updated_at();

drop trigger if exists condominios_touch_updated on public.condominios;
create trigger condominios_touch_updated
  before update on public.condominios
  for each row execute function public.touch_updated_at();

-- 6. ROW LEVEL SECURITY -----------------------------------
alter table public.profiles    enable row level security;
alter table public.condominios enable row level security;

-- ---- profiles ----
drop policy if exists "profiles: self select"      on public.profiles;
drop policy if exists "profiles: self update"      on public.profiles;
drop policy if exists "profiles: self insert"      on public.profiles;
drop policy if exists "profiles: sindico read condo" on public.profiles;

-- Cada usuário lê o próprio perfil
create policy "profiles: self select"
  on public.profiles for select
  using (auth.uid() = id);

-- Cada usuário edita o próprio perfil
create policy "profiles: self update"
  on public.profiles for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- Permite o próprio insert (fallback caso o trigger falhe)
create policy "profiles: self insert"
  on public.profiles for insert
  with check (auth.uid() = id);

-- Síndico vê todos os perfis do mesmo condomínio
create policy "profiles: sindico read condo"
  on public.profiles for select
  using (
    exists (
      select 1 from public.profiles me
      where me.id = auth.uid()
        and me.role = 'sindico'
        and me.condominio_id is not null
        and me.condominio_id = profiles.condominio_id
    )
  );

-- ---- condominios ----
drop policy if exists "condominios: sindico full"   on public.condominios;
drop policy if exists "condominios: members read"   on public.condominios;

-- Síndico tem acesso total ao próprio condomínio
create policy "condominios: sindico full"
  on public.condominios for all
  using  (sindico_id = auth.uid())
  with check (sindico_id = auth.uid());

-- Qualquer usuário do condomínio pode ler dados básicos
create policy "condominios: members read"
  on public.condominios for select
  using (
    exists (
      select 1 from public.profiles p
      where p.id = auth.uid()
        and p.condominio_id = condominios.id
    )
  );

-- ============================================================
-- FIM
-- ============================================================
