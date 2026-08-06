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

-- RLS: usuário vê só o próprio feedback; service_role vê tudo
ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "usuario_le_proprio_feedback" ON public.feedback
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "usuario_insere_feedback" ON public.feedback
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Tabela de execuções dos agentes (log de auditoria + fonte de aprendizado)
CREATE TABLE IF NOT EXISTS public.agent_runs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name      text NOT NULL CHECK (agent_name IN ('camila', 'marcos', 'rafael')),
  output_summary  text,
  output_completo text,
  status          text DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  feedback_breno  text,      -- Breno escreve aqui o motivo de aprovação/rejeição
  created_at      timestamptz DEFAULT now(),
  reviewed_at     timestamptz
);

-- Só service_role acessa (agentes usam service_key, Breno acessa via dashboard)
ALTER TABLE public.agent_runs ENABLE ROW LEVEL SECURITY;

-- Índices para queries frequentes
CREATE INDEX IF NOT EXISTS idx_agent_runs_agent_name ON public.agent_runs(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_runs_created_at ON public.agent_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at   ON public.feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_resolvido     ON public.feedback(resolvido);

-- ============================================================
-- View útil: resumo semanal por agente (para CLAUDE.md)
-- ============================================================
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

-- ============================================================
-- Comentários para o Breno entender
-- ============================================================
COMMENT ON TABLE public.feedback IS
  'Feedback dos síndicos/admins no app. Alimenta a evolução dos agentes.';

COMMENT ON TABLE public.agent_runs IS
  'Log de execuções automáticas dos agentes (Camila, Marcos, Rafael).
   Breno aprova ou rejeita cada output — o histórico treina o agente.';

COMMENT ON COLUMN public.agent_runs.status IS
  'pending = aguarda revisão do Breno | approved = bom | rejected = ruim';

COMMENT ON COLUMN public.agent_runs.feedback_breno IS
  'Breno escreve aqui o motivo de rejeição. Ex: "tom muito formal" ou "dados errados"
   O agente lê isso na próxima execução e adapta o estilo.';
