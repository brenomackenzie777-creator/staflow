-- ============================================================
-- StaFlow — Adiciona loop_name para distinguir os 4 loops especializados
-- Execute no Supabase SQL Editor
-- ============================================================

ALTER TABLE public.agent_runs
  ADD COLUMN IF NOT EXISTS loop_name text DEFAULT 'geral';

CREATE INDEX IF NOT EXISTS idx_agent_runs_loop_name
  ON public.agent_runs(loop_name);

COMMENT ON COLUMN public.agent_runs.loop_name IS
  'Qual loop especializado gerou esta execução: marketing, produto, financeiro, suporte ou meta.';
