-- ============================================================
-- StaFlow — Migração 023: Tabela membros_condominio (N:N user↔condo)
-- ------------------------------------------------------------
-- Habilita o modelo Multi-CNPJ: 1 usuário pode ser membro de N
-- condomínios com roles diferentes. Popula com vínculos existentes
-- (profiles.condominio_id 1:1) para zero regressão de dados.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.membros_condominio (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  condominio_id uuid NOT NULL REFERENCES public.condominios(id) ON DELETE CASCADE,
  role          text NOT NULL DEFAULT 'sindico'
                CHECK (role IN ('sindico','admin','zelador','funcionario')),
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, condominio_id)
);

CREATE INDEX IF NOT EXISTS membros_user_idx  ON public.membros_condominio(user_id);
CREATE INDEX IF NOT EXISTS membros_condo_idx ON public.membros_condominio(condominio_id);

-- Popula com dados existentes (back-compat)
INSERT INTO public.membros_condominio (user_id, condominio_id, role)
SELECT p.id, p.condominio_id, COALESCE(p.role, 'sindico')
  FROM public.profiles p
 WHERE p.condominio_id IS NOT NULL
ON CONFLICT (user_id, condominio_id) DO NOTHING;

ALTER TABLE public.membros_condominio ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.membros_condominio FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "membros: self read" ON public.membros_condominio;
CREATE POLICY "membros: self read"
  ON public.membros_condominio FOR SELECT
  USING (user_id = auth.uid());

DROP POLICY IF EXISTS "membros: admin write" ON public.membros_condominio;
CREATE POLICY "membros: admin write"
  ON public.membros_condominio FOR ALL
  USING (EXISTS (
    SELECT 1 FROM public.membros_condominio mc2
     WHERE mc2.condominio_id = membros_condominio.condominio_id
       AND mc2.user_id       = auth.uid()
       AND mc2.role IN ('sindico','admin')
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM public.membros_condominio mc2
     WHERE mc2.condominio_id = membros_condominio.condominio_id
       AND mc2.user_id       = auth.uid()
       AND mc2.role IN ('sindico','admin')
  ));
