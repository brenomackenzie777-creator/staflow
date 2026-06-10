-- ============================================================
-- StaFlow — Migração 025: plano_ativo enum + subscriptions N:1 condo
-- ------------------------------------------------------------
-- 1. Cria enum plano_enum (mantém condominios.plano text por compat)
-- 2. Adiciona condominios.plano_ativo (enum), popula dos valores atuais
-- 3. Adiciona subscriptions.condominio_id + popula retroativo
-- 4. Remove UNIQUE de subscriptions.profile_id (suporta N subs/user)
-- 5. Cria UNIQUE composto (profile_id, condominio_id) + único stripe_sub_id
-- ============================================================

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'plano_enum') THEN
    CREATE TYPE plano_enum AS ENUM ('starter','pro','advanced','scale','enterprise');
  END IF;
END $$;

ALTER TABLE public.condominios
  ADD COLUMN IF NOT EXISTS plano_ativo plano_enum NOT NULL DEFAULT 'starter';

UPDATE public.condominios
   SET plano_ativo = CASE lower(COALESCE(plano,'starter'))
     WHEN 'starter'    THEN 'starter'::plano_enum
     WHEN 'pro'        THEN 'pro'::plano_enum
     WHEN 'advanced'   THEN 'advanced'::plano_enum
     WHEN 'scale'      THEN 'scale'::plano_enum
     WHEN 'enterprise' THEN 'enterprise'::plano_enum
     ELSE 'starter'::plano_enum
   END
 WHERE plano_ativo IS DISTINCT FROM 'starter'::plano_enum
    OR lower(COALESCE(plano,'starter')) <> 'starter';

ALTER TABLE public.subscriptions
  ADD COLUMN IF NOT EXISTS condominio_id uuid REFERENCES public.condominios(id) ON DELETE CASCADE;

UPDATE public.subscriptions s
   SET condominio_id = p.condominio_id
  FROM public.profiles p
 WHERE p.id = s.profile_id
   AND s.condominio_id IS NULL
   AND p.condominio_id IS NOT NULL;

ALTER TABLE public.subscriptions
  DROP CONSTRAINT IF EXISTS subscriptions_profile_id_key;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'subscriptions_profile_condo_key') THEN
    ALTER TABLE public.subscriptions
      ADD CONSTRAINT subscriptions_profile_condo_key UNIQUE (profile_id, condominio_id);
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS subscriptions_stripe_sub_id_uidx
  ON public.subscriptions(stripe_subscription_id)
  WHERE stripe_subscription_id IS NOT NULL;
