-- ============================================================
-- StaFlow — Migração 024: my_condominio_id() context-aware
-- + is_membro_do_condominio() + RPC meus_condominios()
-- ------------------------------------------------------------
-- Estratégia: cliente passa o condominio_id "ativo" via header
-- HTTP customizado x-condominio-id. Se não houver, fallback no
-- primeiro condomínio do user (back-compat 1:1).
-- ============================================================

CREATE OR REPLACE FUNCTION public.my_condominio_id()
RETURNS uuid
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
DECLARE
  v_uid uuid;
  v_ctx text;
  v_id  uuid;
BEGIN
  v_uid := auth.uid();
  IF v_uid IS NULL THEN RETURN NULL; END IF;

  BEGIN
    v_ctx := current_setting('request.headers', true)::jsonb ->> 'x-condominio-id';
  EXCEPTION WHEN OTHERS THEN
    v_ctx := NULL;
  END;

  IF v_ctx IS NOT NULL AND v_ctx <> '' THEN
    SELECT mc.condominio_id INTO v_id
      FROM public.membros_condominio mc
     WHERE mc.user_id = v_uid
       AND mc.condominio_id = v_ctx::uuid
     LIMIT 1;
    IF v_id IS NOT NULL THEN RETURN v_id; END IF;
  END IF;

  SELECT mc.condominio_id INTO v_id
    FROM public.membros_condominio mc
   WHERE mc.user_id = v_uid
   ORDER BY mc.created_at ASC
   LIMIT 1;
  RETURN v_id;
END $$;

CREATE OR REPLACE FUNCTION public.is_membro_do_condominio(p_condo_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.membros_condominio
     WHERE user_id = auth.uid()
       AND condominio_id = p_condo_id
  );
$$;

REVOKE EXECUTE ON FUNCTION public.is_membro_do_condominio(uuid) FROM public;
GRANT  EXECUTE ON FUNCTION public.is_membro_do_condominio(uuid) TO authenticated;

CREATE OR REPLACE FUNCTION public.meus_condominios()
RETURNS TABLE(
  condominio_id     uuid,
  nome              text,
  plano             text,
  status_assinatura text,
  role              text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
  SELECT
    c.id,
    c.nome,
    c.plano,
    c.status_assinatura,
    mc.role
    FROM public.condominios c
    JOIN public.membros_condominio mc ON mc.condominio_id = c.id
   WHERE mc.user_id = auth.uid()
   ORDER BY c.created_at ASC;
$$;

REVOKE EXECUTE ON FUNCTION public.meus_condominios() FROM public;
GRANT  EXECUTE ON FUNCTION public.meus_condominios() TO authenticated;
