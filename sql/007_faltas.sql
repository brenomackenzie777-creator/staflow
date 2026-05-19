-- ============================================================
-- StaFlow — Migração 007: Módulo de Faltas
-- ============================================================

create table if not exists public.faltas (
  id             uuid primary key default gen_random_uuid(),
  condominio_id  uuid references public.condominios(id) on delete cascade not null,
  funcionario_id uuid references public.funcionarios(id) on delete cascade not null,
  data           date not null,
  tipo           text not null default 'falta'
                   check (tipo in ('falta','atestado','ferias','licenca')),
  justificada    boolean not null default false,
  observacao     text,
  created_by     uuid references public.profiles(id),
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

alter table public.faltas enable row level security;

create policy "faltas condo read" on public.faltas
  for select using (condominio_id = my_condominio_id());

create policy "faltas condo insert" on public.faltas
  for insert with check (condominio_id = my_condominio_id());

create policy "faltas condo update" on public.faltas
  for update using (condominio_id = my_condominio_id());

create policy "faltas condo delete" on public.faltas
  for delete using (condominio_id = my_condominio_id());

create trigger set_faltas_updated_at
  before update on public.faltas
  for each row execute function touch_updated_at();

create index if not exists idx_faltas_condo_data
  on public.faltas (condominio_id, data desc);

create index if not exists idx_faltas_funcionario
  on public.faltas (funcionario_id, data desc);
