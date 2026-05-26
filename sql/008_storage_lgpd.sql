-- ============================================================
-- StaFlow — Migração 008: Storage + LGPD
-- Buckets privados para fotos de funcionários e atestados
-- médicos, com acesso restrito por condomínio via RLS.
-- ============================================================

-- ── BUCKETS ──────────────────────────────────────────────────

-- Bucket privado para fotos de funcionários
-- Path: {condominio_id}/{funcionario_id}.{ext}
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'fotos-funcionarios',
  'fotos-funcionarios',
  false,          -- NUNCA público
  5242880,        -- 5 MB máximo
  array['image/jpeg', 'image/png', 'image/webp']
)
on conflict (id) do nothing;

-- Bucket privado para atestados médicos (dado sensível — LGPD Art. 11)
-- Path: {condominio_id}/{falta_id}.{ext}
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'atestados-medicos',
  'atestados-medicos',
  false,           -- NUNCA público
  10485760,        -- 10 MB máximo
  array['image/jpeg', 'image/png', 'application/pdf']
)
on conflict (id) do nothing;

-- ── RLS: fotos-funcionarios ───────────────────────────────────
-- O primeiro segmento do path deve ser o condominio_id do usuário.
-- Apenas usuários autenticados do mesmo condomínio podem operar.

create policy "fotos select own condo"
  on storage.objects for select
  to authenticated
  using (
    bucket_id = 'fotos-funcionarios'
    AND (storage.foldername(name))[1] = (my_condominio_id())::text
  );

create policy "fotos insert own condo"
  on storage.objects for insert
  to authenticated
  with check (
    bucket_id = 'fotos-funcionarios'
    AND (storage.foldername(name))[1] = (my_condominio_id())::text
  );

create policy "fotos update own condo"
  on storage.objects for update
  to authenticated
  using (
    bucket_id = 'fotos-funcionarios'
    AND (storage.foldername(name))[1] = (my_condominio_id())::text
  )
  with check (
    bucket_id = 'fotos-funcionarios'
    AND (storage.foldername(name))[1] = (my_condominio_id())::text
  );

create policy "fotos delete own condo"
  on storage.objects for delete
  to authenticated
  using (
    bucket_id = 'fotos-funcionarios'
    AND (storage.foldername(name))[1] = (my_condominio_id())::text
  );

-- ── RLS: atestados-medicos ────────────────────────────────────
-- Mesmo padrão: primeiro segmento = condominio_id.
-- LGPD: dado de saúde (Art. 11) — acesso mínimo necessário.

create policy "atestados select own condo"
  on storage.objects for select
  to authenticated
  using (
    bucket_id = 'atestados-medicos'
    AND (storage.foldername(name))[1] = (my_condominio_id())::text
  );

create policy "atestados insert own condo"
  on storage.objects for insert
  to authenticated
  with check (
    bucket_id = 'atestados-medicos'
    AND (storage.foldername(name))[1] = (my_condominio_id())::text
  );

create policy "atestados update own condo"
  on storage.objects for update
  to authenticated
  using (
    bucket_id = 'atestados-medicos'
    AND (storage.foldername(name))[1] = (my_condominio_id())::text
  )
  with check (
    bucket_id = 'atestados-medicos'
    AND (storage.foldername(name))[1] = (my_condominio_id())::text
  );

create policy "atestados delete own condo"
  on storage.objects for delete
  to authenticated
  using (
    bucket_id = 'atestados-medicos'
    AND (storage.foldername(name))[1] = (my_condominio_id())::text
  );

-- ── Colunas nas tabelas existentes ───────────────────────────

alter table public.funcionarios
  add column if not exists foto_path text;

alter table public.faltas
  add column if not exists atestado_path text;

comment on column public.funcionarios.foto_path is
  'Caminho no bucket fotos-funcionarios: {condominio_id}/{funcionario_id}.{ext}. Acesso via signed URL.';

comment on column public.faltas.atestado_path is
  'Caminho no bucket atestados-medicos: {condominio_id}/{falta_id}.{ext}. Dado sensível de saúde — LGPD Art. 11. Acesso via signed URL com TTL.';
