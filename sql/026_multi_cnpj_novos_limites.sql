-- ============================================================
-- StaFlow — Migração 026: Novos limites Multi-CNPJ
-- ------------------------------------------------------------
-- Atualiza trigger 022 com a grade comercial Multi-CNPJ:
--   starter:  3 funcionários
--   pro:      15 funcionários
--   advanced: 35 funcionários
--   scale:    100 funcionários
-- Lê de condominios.plano_ativo (enum) com fallback no plano text.
-- ============================================================

CREATE OR REPLACE FUNCTION public.enforce_plan_limit_funcionarios()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
DECLARE
  v_plano text;
  v_count int;
  v_limit int;
BEGIN
  IF TG_OP = 'INSERT' AND COALESCE(NEW.ativo, true) = false THEN
    RETURN NEW;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF OLD.ativo IS NOT DISTINCT FROM NEW.ativo THEN RETURN NEW; END IF;
    IF NEW.ativo = false THEN RETURN NEW; END IF;
  END IF;

  SELECT COALESCE(plano_ativo::text, plano, 'starter') INTO v_plano
    FROM public.condominios
   WHERE id = NEW.condominio_id;

  v_limit := CASE lower(COALESCE(v_plano, 'starter'))
    WHEN 'starter'    THEN 3
    WHEN 'pro'        THEN 15
    WHEN 'advanced'   THEN 35
    WHEN 'scale'      THEN 100
    WHEN 'enterprise' THEN 2147483647
    ELSE 3
  END;

  SELECT count(*) INTO v_count
    FROM public.funcionarios
   WHERE condominio_id = NEW.condominio_id
     AND ativo = true
     AND id <> COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000'::uuid);

  IF v_count >= v_limit THEN
    RAISE EXCEPTION 'PLAN_LIMIT_REACHED: % funcionários ativos atinge o limite do plano % (max %)', v_count, v_plano, v_limit
      USING ERRCODE = 'P0001', HINT = 'Faça upgrade do plano em /planos';
  END IF;

  RETURN NEW;
END $$;
