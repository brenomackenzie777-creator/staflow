-- ============================================================
-- StaFlow — Migração 006: Módulo de Tarefas
-- ============================================================

create table if not exists public.tarefas (
  id             uuid primary key default gen_random_uuid(),
  condominio_id  uuid references public.condominios(id) on delete cascade not null,
  titulo         text not null,
  descricao      text,
  funcionario_id uuid references public.funcionarios(id) on delete set null,
  status         text not null default 'pendente'
                   check (status in ('pendente','em_andamento','concluida','cancelada')),
  prioridade     text not null default 'media'
                   check (prioridade in ('baixa','media','alta','urgente')),
  prazo          date,
  created_by     uuid references public.profiles(id),
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

alter table public.tarefas enable row level security;

create policy "tarefas condo read" on public.tarefas
  for select using (condominio_id = my_condominio_id());

create policy "tarefas condo insert" on public.tarefas
  for insert with check (condominio_id = my_condominio_id());

create policy "tarefas condo update" on public.tarefas
  for update using (condominio_id = my_condominio_id());

create policy "tarefas condo delete" on public.tarefas
  for delete using (condominio_id = my_condominio_id());

create trigger set_tarefas_updated_at
  before update on public.tarefas
  for each row execute function touch_updated_at();

create index if not exists idx_tarefas_condo_status
  on public.tarefas (condominio_id, status);
