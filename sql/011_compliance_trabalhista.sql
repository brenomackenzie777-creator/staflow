-- ============================================================
-- StaFlow — Migração 011: Compliance trabalhista por funcionário
-- ------------------------------------------------------------
-- Adiciona campos para evitar passivos sob CCT-RJ 2025:
--   - salario_base: substitui o piso CCT no dashboard
--     (o cálculo cai no PISO_CCT_RJ[cargo] apenas se este
--      campo for null)
--   - adicional_insalubridade: flag obrigatória para cargos
--     de limpeza/faxina (CCT-RJ pós-2025 + NR-15, 20% sobre piso)
-- ============================================================

alter table public.funcionarios
  add column if not exists salario_base            numeric(10,2),
  add column if not exists adicional_insalubridade boolean not null default false;

comment on column public.funcionarios.salario_base is
  'Salário base mensal em BRL. Se null, dashboard usa PISO_CCT_RJ[cargo] como fallback.';

comment on column public.funcionarios.adicional_insalubridade is
  'Adicional de insalubridade 20% (NR-15) — obrigatório para cargos de limpeza/faxina conforme CCT-RJ.';
