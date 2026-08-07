// ============================================================
// StaFlow — Edge Function: excluir-condominio
// ------------------------------------------------------------
// POST { condominioId }
//
// Exclui APENAS um condomínio específico — nunca a conta do
// usuário. Só o síndico (role='sindico' em membros_condominio)
// pode excluir. Se houver assinatura Stripe ativa, cancela na
// hora (não faz sentido continuar cobrando por algo apagado).
// As tabelas filhas (funcionarios, registros_ponto, tarefas,
// faltas, membros_condominio) têm ON DELETE CASCADE em
// condominio_id — apagar a linha em `condominios` já limpa tudo
// no banco. Aqui só cuidamos do que o banco não cuida sozinho:
// validar permissão, cancelar Stripe, e limpar arquivos no Storage.
// ============================================================

import Stripe from "https://esm.sh/stripe@14.21.0?target=deno";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const corsHeaders = {
  "Access-Control-Allow-Origin":  "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY")!, {
  apiVersion: "2024-12-18.acacia",
  httpClient: Stripe.createFetchHttpClient(),
});

const SUPABASE_URL          = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_ANON_KEY     = Deno.env.get("SUPABASE_ANON_KEY")!;
const SUPABASE_SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

async function limparPastaStorage(admin: ReturnType<typeof createClient>, bucket: string, prefixo: string) {
  try {
    const { data: itens } = await admin.storage.from(bucket).list(prefixo, { limit: 1000 });
    if (itens && itens.length > 0) {
      const paths = itens.map((f) => `${prefixo}/${f.name}`);
      await admin.storage.from(bucket).remove(paths);
    }
  } catch (_) { /* limpeza de storage é best-effort */ }
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST")    return json({ error: "Method not allowed" }, 405);

  try {
    const authHeader = req.headers.get("Authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return json({ error: "Sem token de autenticação." }, 401);
    }

    const supabaseUser = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      global: { headers: { Authorization: authHeader } },
    });
    const { data: { user }, error: userErr } = await supabaseUser.auth.getUser();
    if (userErr || !user) return json({ error: "Sessão inválida." }, 401);

    const body = await req.json().catch(() => ({}));
    const { condominioId } = body as { condominioId?: string };
    if (!condominioId) return json({ error: "condominioId obrigatório." }, 400);

    const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE);

    // ── Só o síndico daquele condomínio pode excluir ──
    const { data: membro } = await admin
      .from("membros_condominio")
      .select("role")
      .eq("user_id", user.id)
      .eq("condominio_id", condominioId)
      .maybeSingle();

    if (!membro) return json({ error: "Você não tem acesso a este condomínio." }, 403);
    if (membro.role !== "sindico") {
      return json({ error: "Apenas o síndico responsável pode excluir o condomínio." }, 403);
    }

    const { data: condo, error: condoErr } = await admin
      .from("condominios")
      .select("id, nome")
      .eq("id", condominioId)
      .single();
    if (condoErr || !condo) return json({ error: "Condomínio não encontrado." }, 404);

    // ── Cancela assinatura Stripe ativa, se houver ──
    const { data: sub } = await admin
      .from("subscriptions")
      .select("stripe_subscription_id, status")
      .eq("condominio_id", condominioId)
      .in("status", ["active", "trialing", "past_due"])
      .maybeSingle();

    if (sub?.stripe_subscription_id) {
      try {
        await stripe.subscriptions.cancel(sub.stripe_subscription_id);
      } catch (e) {
        // Já pode estar cancelada no Stripe — não bloqueia a exclusão
        console.error("[excluir-condominio] stripe cancel:", (e as Error).message);
      }
      await admin.from("subscriptions")
        .update({ status: "canceled", updated_at: new Date().toISOString() })
        .eq("stripe_subscription_id", sub.stripe_subscription_id);
    }

    // ── Limpa arquivos no Storage (best-effort) ──
    await Promise.all([
      limparPastaStorage(admin, "documentos-condominio", `${condominioId}/cct`),
      limparPastaStorage(admin, "fotos-funcionarios", condominioId),
      limparPastaStorage(admin, "atestados-medicos", condominioId),
    ]);

    // ── Apaga o condomínio — cascade cuida do resto no banco ──
    const { error: delErr } = await admin.from("condominios").delete().eq("id", condominioId);
    if (delErr) throw delErr;

    // ── Quantos condomínios restam pro usuário? ──
    const { count } = await admin
      .from("membros_condominio")
      .select("condominio_id", { count: "exact", head: true })
      .eq("user_id", user.id);

    return json({ success: true, nomeExcluido: condo.nome, restantes: count ?? 0 });

  } catch (err) {
    console.error("[excluir-condominio]", err);
    return json({ error: (err as Error).message || "Erro interno ao excluir condomínio." }, 500);
  }
});
