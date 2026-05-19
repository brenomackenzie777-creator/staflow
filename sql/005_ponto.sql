-- ============================================================
-- StaFlow — Migração 005: Módulo de Ponto
-- ============================================================

create table if not exists public.registros_ponto (
  id             uuid primary key default gen_random_uuid(),
  condominio_id  uuid references public.condominios(id) on delete cascade not null,
  funcionario_id uuid references public.funcionarios(id) on delete cascade not null,
  tipo           text not null check (tipo in ('entrada','saida')),
  registrado_em  timestamptz not null default now(),
  observacao     text,
  registrado_por uuid references public.profiles(id),
  created_at     timestamptz not null default now()
);

alter table public.registros_ponto enable row level security;

create policy "ponto condo read" on public.registros_ponto
  for select using (condominio_id = my_condominio_id());

create policy "ponto condo insert" on public.registros_ponto
  for insert with check (condominio_id = my_condominio_id());

create policy "ponto condo update" on public.registros_ponto
  for update using (condominio_id = my_condominio_id());

create policy "ponto condo delete" on public.registros_ponto
  for delete using (condominio_id = my_condominio_id());

-- Índices para consultas por data
create index if not exists idx_ponto_condominio_data
  on public.registros_ponto (condominio_id, registrado_em desc);

create index if not exists idx_ponto_funcionario_data
  on public.registros_ponto (funcionario_id, registrado_em desc);
