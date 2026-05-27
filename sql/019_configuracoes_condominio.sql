-- ============================================================
-- StaFlow — Migração 019: Configurações do condomínio
-- ------------------------------------------------------------
-- 1) Endereço estruturado (campo `endereco` legado vira fallback)
-- 2) E-mail administrativo do condomínio
-- 3) Upload da CCT (PDF) + tolerância de atraso configurável
-- 4) Bucket privado documentos-condominio com policies por condo
-- ============================================================

alter table public.condominios
  add column if not exists logradouro             text,
  add column if not exists numero                 text,
  add column if not exists bairro                 text,
  add column if not exists cidade                 text,
  add column if not exists estado                 text,
  add column if not exists cep                    text,
  add column if not exists email_admin            text,
  add column if not exists cct_path               text,
  add column if not exists tolerancia_atraso_min  int  not null default 10;

comment on column public.condominios.logradouro            is 'Logradouro (rua/avenida) — usado no espelho de ponto MTE 671.';
comment on column public.condominios.cep                   is 'CEP somente dígitos (8 caracteres).';
comment on column public.condominios.email_admin           is 'E-mail administrativo público (notificações, relatórios).';
comment on column public.condominios.cct_path              is 'Caminho da CCT vigente no bucket documentos-condominio.';
comment on column public.condominios.tolerancia_atraso_min is 'Tolerância em minutos para atraso de batida de ponto (default 10).';

-- ── Bucket privado para documentos do condomínio ──
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'documentos-condominio',
  'documentos-condominio',
  false,
  20971520,   -- 20 MB
  array['application/pdf']
)
on conflict (id) do update set
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

-- Policies (mesmo padrão dos buckets atestados/fotos: path[1] = condominio_id)
drop policy if exists "documentos: select own condo" on storage.objects;
create policy "documentos: select own condo"
  on storage.objects for select
  using (bucket_id = 'documentos-condominio'
         and (storage.foldername(name))[1] = (my_condominio_id())::text);

drop policy if exists "documentos: insert own condo" on storage.objects;
create policy "documentos: insert own condo"
  on storage.objects for insert
  with check (bucket_id = 'documentos-condominio'
              and (storage.foldername(name))[1] = (my_condominio_id())::text);

drop policy if exists "documentos: update own condo" on storage.objects;
create policy "documentos: update own condo"
  on storage.objects for update
  using (bucket_id = 'documentos-condominio'
         and (storage.foldername(name))[1] = (my_condominio_id())::text);

drop policy if exists "documentos: delete own condo" on storage.objects;
create policy "documentos: delete own condo"
  on storage.objects for delete
  using (bucket_id = 'documentos-condominio'
         and (storage.foldername(name))[1] = (my_condominio_id())::text);
