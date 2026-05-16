-- ============================================================
-- StaFlow — Tabela funcionarios + RLS
-- Cada funcionário pertence a um condomínio.
-- Síndicos / admins do condomínio gerenciam tudo.
-- ============================================================

create table if not exists public.funcionarios (
  id              uuid primary key default gen_random_uuid(),
  condominio_id   uuid not null references public.condominios(id) on delete cascade,
  nome            text not null,
  cpf             text,
  cargo           text not null default 'porteiro'
                  check (cargo in ('porteiro','zelador','faxineira','jardineiro','seguranca','outro')),
  telefone        text,
  email           text,
  data_admissao   date,
  turno           text default 'integral'
                  check (turno in ('manha','tarde','noite','integral','escala')),
  ativo           boolean not null default true,
  observacoes     text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  created_by      uuid references public.profiles(id) on delete set null
);

create index if not exists funcionarios_condominio_idx on public.funcionarios(condominio_id);
create index if not exists funcionarios_ativo_idx      on public.funcionarios(ativo);
create index if not exists funcionarios_nome_idx       on public.funcionarios(nome);

-- updated_at automático
drop trigger if exists funcionarios_touch_updated on public.funcionarios;
create trigger funcionarios_touch_updated
  before update on public.funcionarios
  for each row execute function public.touch_updated_at();

-- RLS
alter table public.funcionarios enable row level security;

drop policy if exists "funcionarios: condo members read"  on public.funcionarios;
drop policy if exists "funcionarios: sindico admin write" on public.funcionarios;

-- Qualquer usuário do condomínio pode ler funcionários do seu condomínio
create policy "funcionarios: condo members read"
  on public.funcionarios for select
  using (condominio_id = public.my_condominio_id());

-- Síndicos e admins podem criar/editar/excluir funcionários do seu condomínio
create policy "funcionarios: sindico admin write"
  on public.funcionarios for all
  using (
    condominio_id = public.my_condominio_id()
    and public.my_role() in ('sindico','admin')
  )
  with check (
    condominio_id = public.my_condominio_id()
    and public.my_role() in ('sindico','admin')
  );

-- ============================================================
-- AUTO-PROVISIONAMENTO DO CONDOMÍNIO
-- O trigger handle_new_user já popula profiles.condominio_nome
-- mas NÃO cria uma linha em condominios. Vamos criar uma função
-- helper que o usuário chama após o login para garantir que existe.
-- ============================================================
create or replace function public.ensure_condominio()
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_cond_id   uuid;
  v_profile   record;
begin
  select * into v_profile from public.profiles where id = auth.uid();
  if v_profile is null then
    raise exception 'Profile não encontrado para o usuário autenticado.';
  end if;

  -- Já tem condomínio vinculado?
  if v_profile.condominio_id is not null then
    return v_profile.condominio_id;
  end if;

  -- Só sindicos/admins criam condomínios automaticamente
  if v_profile.role not in ('sindico','admin') then
    return null;
  end if;

  -- Cria um novo condomínio com base no que veio do cadastro
  insert into public.condominios (nome, endereco, sindico_id)
  values (
    coalesce(v_profile.condominio_nome, 'Meu Condomínio'),
    v_profile.condominio_endereco,
    v_profile.id
  )
  returning id into v_cond_id;

  -- Vincula no profile
  update public.profiles set condominio_id = v_cond_id where id = auth.uid();

  return v_cond_id;
end;
$$;

-- ============================================================
-- FIM
-- ============================================================
