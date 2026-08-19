-- ============================================================
-- StaFlow — agent_runs passa a aceitar status = 'failed'
-- ★ 19/08/2026 — já APLICADA em produção via Supabase MCP.
--    Arquivo aqui só pra deixar registro no repositório.
-- ------------------------------------------------------------
-- O QUE ESTAVA ERRADO
--
-- O orquestrador do time de agentes (scripts/crew/main.py, função
-- _registrar_execucao) grava status='failed' quando um ciclo é
-- interrompido. Mas o CHECK desta tabela só aceitava
-- 'pending' / 'approved' / 'rejected'.
--
-- Resultado: TODA tentativa de registrar uma falha era recusada pelo
-- banco, o erro caía no try/except do Python (que só loga um aviso), e
-- o ciclo sumia sem deixar rastro. Na prática, a tabela agent_runs só
-- sabia registrar SUCESSO.
--
-- Como isso apareceu no mundo real: entre 17 e 19/08/2026 o ciclo
-- quebrou todos os dias (a Groq desativou o modelo llama-3.3-70b em
-- 16/08 — ver scripts/crew/config.py). O gasto de token aparecia
-- direitinho em agent_budget_diario, mas agent_runs ficava vazia — o
-- time parecia simplesmente não ter rodado.
--
-- Falha silenciosa é pior que falha barulhenta: a primeira você só
-- descobre por acaso, dias depois.
-- ============================================================

alter table public.agent_runs drop constraint if exists agent_runs_status_check;

alter table public.agent_runs add constraint agent_runs_status_check
  check (status = any (array['pending','approved','rejected','failed']));
