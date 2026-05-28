-- ============================================================
-- StaFlow — Migração 021: Habilita Realtime para o dashboard
-- ------------------------------------------------------------
-- Adiciona registros_ponto, faltas e tarefas à publication
-- supabase_realtime para que sb.channel().on('postgres_changes')
-- funcione no dashboard do síndico.
-- RLS continua aplicado: cada cliente só recebe eventos das
-- linhas que ele pode ler (filtrado por condominio_id).
-- ============================================================

do $$
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    if not exists (
      select 1 from pg_publication_tables
       where pubname='supabase_realtime' and schemaname='public' and tablename='registros_ponto'
    ) then
      alter publication supabase_realtime add table public.registros_ponto;
    end if;
    if not exists (
      select 1 from pg_publication_tables
       where pubname='supabase_realtime' and schemaname='public' and tablename='faltas'
    ) then
      alter publication supabase_realtime add table public.faltas;
    end if;
    if not exists (
      select 1 from pg_publication_tables
       where pubname='supabase_realtime' and schemaname='public' and tablename='tarefas'
    ) then
      alter publication supabase_realtime add table public.tarefas;
    end if;
  end if;
end $$;
