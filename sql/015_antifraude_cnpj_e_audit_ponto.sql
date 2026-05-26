-- ============================================================
-- StaFlow — Migração 015: Antifraude (CNPJ + auditoria GPS)
-- ------------------------------------------------------------
-- 1) condominios.cnpj: identificador fiscal validado matematicamente
--    no frontend antes do insert. Único quando preenchido.
-- 2) registros_ponto.audit_status: marcador para o síndico auditar
--    batidas suspeitas vindas do app de bolso. Valores possíveis:
--      NULL              → não auditado / não aplicável (desktop)
--      'OK'              → GPS dentro do esperado
--      'LOW_ACCURACY'    → accuracy > 150m
--      'MOCK_SUSPECT'    → padrão suspeito de mock location
--      'FRAUDE_SUSPECT'  → múltiplos sinais combinados
-- ============================================================

alter table public.condominios
  add column if not exists cnpj text;

create unique index if not exists condominios_cnpj_uidx
  on public.condominios(cnpj)
  where cnpj is not null;

comment on column public.condominios.cnpj is
  'CNPJ (14 dígitos, somente números). Validado matematicamente no frontend antes do insert (algoritmo oficial Receita Federal).';

alter table public.registros_ponto
  add column if not exists audit_status text;

comment on column public.registros_ponto.audit_status is
  'Marcador antifraude vindo do app de bolso. NULL=não auditado, OK, LOW_ACCURACY, MOCK_SUSPECT, FRAUDE_SUSPECT.';
