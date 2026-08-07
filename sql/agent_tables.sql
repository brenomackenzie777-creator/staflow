-- ============================================================
-- StaFlow — Tabelas para o sistema de agentes autônomos
-- Execute no Supabase SQL Editor
-- ============================================================

-- Tabela de feedback dos usuários (alimenta a autoevolução)
CREATE TABLE IF NOT EXISTS public.feedback (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  condominio_id uuid,
  pagina        text,
  mensagem      text NOT NULL,
  tipo          text DEFAULT 'geral' CHECK (tipo IN ('bug', 'sugestao', 'elogio', 'geral')),
  resolvido     boolean DEFAULT false,
  created_at    timestamptz DEFAULT now()
);

ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "usuario_le_proprio_feedback" ON public.feedback
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "usuario_insere_feedback" ON public.feedback
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Tabela de execuções dos agentes (sem CHECK restritivo — aceita qualquer nome)
DROP TABLE IF EXISTS public.agent_runs CASCADE;

CREATE TABLE public.agent_runs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name      text NOT NULL,
  output_summary  text,
  output_completo text,
  status          text DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  feedback_breno  text,
  created_at      timestamptz DEFAULT now(),
  reviewed_at     timestamptz
);

-- Só service_role acessa (agentes usam service_key, Breno acessa via dashboard)
ALTER TABLE public.agent_runs ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS idx_agent_runs_agent_name ON public.agent_runs(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_runs_created_at ON public.agent_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at   ON public.feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_resolvido     ON public.feedback(resolvido);

-- View: resumo por agente nos últimos 30 dias
CREATE OR REPLACE VIEW public.agent_weekly_summary AS
SELECT
  agent_name,
  COUNT(*) FILTER (WHERE status = 'approved') AS aprovados,
  COUNT(*) FILTER (WHERE status = 'rejected') AS rejeitados,
  COUNT(*) FILTER (WHERE status = 'pending')  AS pendentes,
  MAX(created_at) AS ultima_execucao
FROM public.agent_runs
WHERE created_at >= now() - interval '30 days'
GROUP BY agent_name;

COMMENT ON TABLE public.agent_runs IS
  'Log de execuções automáticas dos agentes. Breno aprova ou rejeita cada output.';

COMMENT ON COLUMN public.agent_runs.feedback_breno IS
  'Breno escreve aqui o motivo de rejeição. O agente lê isso na próxima execução.';
