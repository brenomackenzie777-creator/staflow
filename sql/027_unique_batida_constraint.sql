-- ============================================================
-- StaFlow — Migração 027: Unique constraint em registros_ponto
-- ------------------------------------------------------------
-- Problema: a fila offline (IndexedDB) pode sincronizar a mesma
-- batida duas vezes se a aba for recarregada durante a sync
-- (ex: INSERT → falha de rede → registrado em IndexedDB →
-- aba recarrega → sync roda novamente → INSERT duplicado).
--
-- Solução: constraint única em (funcionario_id, registrado_em).
-- Isso garante idempotência no servidor sem bloquear o modelo
-- de 4 batidas por dia (2 entradas + 2 saídas), pois cada
-- batida tem um timestamp distinto.
--
-- NOTA: NÃO usar (funcionario_id, tipo, DATE(registrado_em))
-- pois quebraria o modelo de 4 batidas — por dia há 2 entradas
-- e 2 saídas, todas com tipo 'entrada' ou 'saida' respectivamente.
-- ============================================================

-- 1. Remove duplicatas existentes antes de criar a constraint
--    (mantém a batida mais recente de cada par duplicado)
DELETE FROM public.registros_ponto a
USING public.registros_ponto b
WHERE a.id < b.id
  AND a.funcionario_id = b.funcionario_id
  AND a.registrado_em  = b.registrado_em;

-- 2. Cria índice único que previne inserções idênticas
CREATE UNIQUE INDEX IF NOT EXISTS uq_registros_ponto_funcionario_ts
  ON public.registros_ponto (funcionario_id, registrado_em);

-- 3. Comentário no índice para documentação
COMMENT ON INDEX uq_registros_ponto_funcionario_ts IS
  'Previne batidas duplicadas da fila offline (mesmo funcionário, mesmo timestamp). '
  'O código de sync deve tratar violação 23505 como sucesso silencioso.';
