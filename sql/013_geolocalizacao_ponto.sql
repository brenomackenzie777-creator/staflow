-- ============================================================
-- StaFlow — Migração 013: Geolocalização no registro de ponto
-- ------------------------------------------------------------
-- Persiste lat/lng/accuracy do GPS do dispositivo no momento
-- da batida — metadado de auditoria do app de bolso.
-- Campos são NULLABLE: pontos registrados pelo síndico no
-- desktop continuam funcionando sem geo.
-- ============================================================

alter table public.registros_ponto
  add column if not exists latitude   numeric(10,7),
  add column if not exists longitude  numeric(10,7),
  add column if not exists accuracy_m integer;

comment on column public.registros_ponto.latitude   is 'Latitude GPS no momento da batida (graus decimais, WGS84).';
comment on column public.registros_ponto.longitude  is 'Longitude GPS no momento da batida (graus decimais, WGS84).';
comment on column public.registros_ponto.accuracy_m is 'Precisão do GPS em metros (raio do erro reportado pelo dispositivo).';
