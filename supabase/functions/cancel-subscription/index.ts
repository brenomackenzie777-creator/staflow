// ============================================================
// StaFlow — Edge Function: cancel-subscription
// ------------------------------------------------------------
// POST { condominioId }
//
// Agenda o cancelamento da assinatura Stripe ao fim do período.
// (cancel_at_period_end=true — acesso mantido até current_period_end)
// Apenas o síndico/membro daquele condomínio pode cancelar.
// O webhook stripe-webhook (customer.subscription.deleted)
// cuida de rebaixar plano → starter no banco quando o período expirar.
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

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST")    return json({ error: "Method not allowed" }, 405);

  try {
    // ── Autenticação ──
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

    const supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE);

    // ── Valida que o usuário é membro do condomínio ──
    const { data: membro } = await supabaseAdmin
      .from("membros_condominio")
      .select("condominio_id")
      .eq("user_id", user.id)
      .eq("condominio_id", condominioId)
      .maybeSingle();

    if (!membro) return json({ error: "Você não tem permissão para cancelar este condomínio." }, 403);

    // ── Busca a assinatura ativa ──
    const { data: sub } = await supabaseAdmin
      .from("subscriptions")
      .select("stripe_subscription_id, plan, status")
      .eq("condominio_id", condominioId)
      .eq("status", "active")
      .maybeSingle();

    if (!sub?.stripe_subscription_id) {
      return json({ error: "Nenhuma assinatura ativa encontrada para este condomínio." }, 404);
    }

    // ── Agenda cancelamento ao fim do período (não cancela imediatamente) ──
    const updated = await stripe.subscriptions.update(sub.stripe_subscription_id, {
      cancel_at_period_end: true,
    });

    // Reflete cancel_at_period_end no banco imediatamente (plano permanece ativo
    // até current_period_end; o rebaixo para starter ocorre via
    // customer.subscription.deleted quando o período expirar).
    const supabaseAdmin2 = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE);
    await supabaseAdmin2.from("subscriptions").update({
      cancel_at_period_end: true,
      updated_at: new Date().toISOString(),
    }).eq("stripe_subscription_id", sub.stripe_subscription_id);

    const periodEnd = updated.current_period_end
      ? new Date(updated.current_period_end * 1000).toLocaleDateString("pt-BR")
      : null;
    const msg = periodEnd
      ? `Cancelamento agendado. Você mantém o acesso até ${periodEnd}.`
      : "Cancelamento agendado. Você mantém o acesso até o fim do período atual.";

    return json({ success: true, cancel_at_period_end: true, message: msg });

  } catch (err) {
    console.error("[cancel-subscription]", err);
    return json({ error: (err as Error).message || "Erro interno." }, 500);
  }
});
