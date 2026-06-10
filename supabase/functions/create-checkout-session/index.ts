// ============================================================
// StaFlow — Edge Function: create-checkout-session (Multi-CNPJ)
// ------------------------------------------------------------
// POST { priceId, condominioId?, condominioNome?, successUrl, cancelUrl }
//
// Casos:
// 1. UPGRADE de condomínio existente → body.condominioId presente
// 2. NOVO condomínio (1º, 2º+) → body.condominioNome presente
//    Cria condominios row (status_assinatura='pending')
//    + membros_condominio (role=sindico) e segue pro checkout.
//    Política comercial: 2º+ condomínio SEMPRE exige plano pago.
//
// metadata.condominio_id é a CHAVE pro webhook.
// ============================================================

import Stripe from "https://esm.sh/stripe@14.21.0?target=deno";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const corsHeaders = {
  "Access-Control-Allow-Origin":  "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-condominio-id",
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
    const authHeader = req.headers.get("Authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return json({ error: "Sem token de autenticação." }, 401);
    }

    const supabaseUser = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      global: { headers: { Authorization: authHeader } },
    });
    const { data: { user }, error: userErr } = await supabaseUser.auth.getUser();
    if (userErr || !user?.email) return json({ error: "Sessão inválida." }, 401);

    const supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE);

    const body = await req.json().catch(() => ({}));
    const { priceId, condominioId: bodyCondoId, condominioNome, successUrl, cancelUrl } = body as {
      priceId?: string;
      condominioId?: string;
      condominioNome?: string;
      successUrl?: string;
      cancelUrl?: string;
    };

    if (!priceId || !successUrl || !cancelUrl) {
      return json({ error: "Faltando priceId, successUrl ou cancelUrl." }, 400);
    }

    // ── Resolve condominio_id ──
    let condominioId: string;
    let stripeCustomerId: string | null = null;

    if (bodyCondoId) {
      // UPGRADE: valida membership
      const { data: membro } = await supabaseAdmin
        .from("membros_condominio")
        .select("condominio_id")
        .eq("user_id", user.id)
        .eq("condominio_id", bodyCondoId)
        .maybeSingle();
      if (!membro) return json({ error: "Você não é membro desse condomínio." }, 403);
      condominioId = bodyCondoId;

      const { data: condo } = await supabaseAdmin
        .from("condominios")
        .select("stripe_subscription_id")
        .eq("id", condominioId)
        .single();
      if (condo?.stripe_subscription_id) {
        try {
          const oldSub = await stripe.subscriptions.retrieve(condo.stripe_subscription_id);
          stripeCustomerId = typeof oldSub.customer === "string" ? oldSub.customer : oldSub.customer.id;
        } catch (_) {}
      }
    } else {
      // NOVO condomínio — exige nome
      if (!condominioNome || condominioNome.trim().length < 2) {
        return json({ error: "Informe o nome do condomínio." }, 400);
      }

      const { data: novoCondo, error: condoErr } = await supabaseAdmin
        .from("condominios")
        .insert({
          nome:              condominioNome.trim(),
          sindico_id:        user.id,
          plano:             "starter",
          plano_ativo:       "starter",
          status_assinatura: "pending",
          ativo:             true,
        })
        .select("id")
        .single();
      if (condoErr) throw new Error("Erro criando condomínio: " + condoErr.message);
      condominioId = novoCondo.id;

      await supabaseAdmin.from("membros_condominio").insert({
        user_id:       user.id,
        condominio_id: condominioId,
        role:          "sindico",
      });
    }

    // ── Customer Stripe (1 customer por condomínio) ──
    if (!stripeCustomerId) {
      const list = await stripe.customers.list({ email: user.email, limit: 10 });
      const match = list.data.find(c => c.metadata?.condominio_id === condominioId);
      if (match) {
        stripeCustomerId = match.id;
      } else {
        const created = await stripe.customers.create({
          email: user.email,
          metadata: { profile_id: user.id, condominio_id: condominioId },
        });
        stripeCustomerId = created.id;
      }
    }

    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      customer: stripeCustomerId,
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: successUrl,
      cancel_url:  cancelUrl,
      allow_promotion_codes: true,
      metadata:           { profile_id: user.id, condominio_id: condominioId },
      subscription_data:  { metadata: { profile_id: user.id, condominio_id: condominioId } },
    });

    return json({ url: session.url, sessionId: session.id, condominioId });

  } catch (err) {
    console.error("[create-checkout-session]", err);
    return json({ error: (err as Error).message || "Erro interno." }, 500);
  }
});
