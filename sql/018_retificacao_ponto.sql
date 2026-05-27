-- ============================================================
-- StaFlow — Migração 018: Retificação de ponto pelo síndico
-- ------------------------------------------------------------
-- Permite editar horário de batida mantendo trilha de auditoria:
--   motivo_edicao: texto obrigatório informando porquê
--   editado_por:   uuid do admin que fez a alteração
--   editado_em:    timestamp da retificação
--   audit_status:  novo valor 'EDITADO_ADMIN' grava a alteração
-- ============================================================

alter table public.registros_ponto
  add column if not exists motivo_edicao text,
  add column if not exists editado_por   uuid references auth.users(id) on delete set null,
  add column if not exists editado_em    timestamptz;

comment on column public.registros_ponto.motivo_edicao is
  'Motivo informado pelo síndico ao retificar uma batida (obrigatório quando audit_status=EDITADO_ADMIN).';
comment on column public.registros_ponto.editado_por is
  'UUID do auth.user que executou a retificação.';
comment on column public.registros_ponto.editado_em is
  'Timestamp da retificação para auditoria.';
