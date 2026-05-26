// ============================================================
// StaFlow — Edge Function: create-checkout-session
// ------------------------------------------------------------
// POST { priceId, condominioId, successUrl, cancelUrl }
// Headers: Authorization: Bearer <supabase_access_token>
//
// 1. Identifica o usuário pelo JWT do Supabase
// 2. Procura customer no Stripe pelo e-mail (reuso) ou cria um
// 3. Cria Checkout Session em modo `subscription`
// 4. Injeta metadata { condominio_id, profile_id } para o webhook
// 5. Retorna { url } para o frontend redirecionar
// ============================================================

import Stripe from "https://esm.sh/stripe@14.21.0?target=deno";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

// ---- CORS ----------------------------------------------------
const corsHeaders = {
  "Access-Control-Allow-Origin":  "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

// ---- Clients (singletons por cold start) --------------------
const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY")!, {
  apiVersion: "2024-12-18.acacia",
  httpClient: Stripe.createFetchHttpClient(), // recomendado no Deno
});

const SUPABASE_URL          = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_ANON_KEY     = Deno.env.get("SUPABASE_ANON_KEY")!;
const SUPABASE_SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

// ---- Helpers -------------------------------------------------
function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

// ============================================================
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return json({ error: "Method not allowed" }, 405);
  }

  try {
    // ---- 1. Autenticar usuário pelo JWT --------------------
    const authHeader = req.headers.get("Authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return json({ error: "Sem token de autenticação." }, 401);
    }

    // Cliente "como o usuário" — respeita RLS
    const supabaseUser = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      global: { headers: { Authorization: authHeader } },
    });

    const { data: { user }, error: userErr } = await supabaseUser.auth.getUser();
    if (userErr || !user?.email) {
      return json({ error: "Sessão inválida." }, 401);
    }

    // ---- 2. Validar body -----------------------------------
    const body = await req.json().catch(() => ({}));
    const { priceId, condominioId, successUrl, cancelUrl } = body as {
      priceId?: string;
      condominioId?: string;
      successUrl?: string;
      cancelUrl?: string;
    };

    if (!priceId || !successUrl || !cancelUrl) {
      return json({ error: "Faltando priceId, successUrl ou cancelUrl." }, 400);
    }

    // ---- 3. Buscar/criar customer no Stripe ---------------
    // Cliente admin (service role) para ler a subscription atual sem RLS
    const supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE);
    const { data: existingSub } = await supabaseAdmin
      .from("subscriptions")
      .select("stripe_customer_id")
      .eq("profile_id", user.id)
      .maybeSingle();

    let customerId = existingSub?.stripe_customer_id ?? null;

    if (!customerId) {
      // Tenta achar por e-mail no Stripe (idempotente em re-tentativas)
      const list = await stripe.customers.list({ email: user.email, limit: 1 });
      if (list.data.length > 0) {
        customerId = list.data[0].id;
      } else {
        const created = await stripe.customers.create({
          email: user.email,
          metadata: {
            profile_id:    user.id,
            condominio_id: condominioId ?? "",
          },
        });
        customerId = created.id;
      }
    }

    // ---- 4. Criar Checkout Session ------------------------
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      customer: customerId,
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: successUrl,
      cancel_url:  cancelUrl,
      allow_promotion_codes: true,
      // metadata vai tanto na Session quanto na Subscription criada,
      // para o webhook conseguir relacionar com o condomínio.
      metadata: {
        profile_id:    user.id,
        condominio_id: condominioId ?? "",
      },
      subscription_data: {
        metadata: {
          profile_id:    user.id,
          condominio_id: condominioId ?? "",
        },
      },
    });

    return json({ url: session.url, sessionId: session.id });

  } catch (err) {
    console.error("[create-checkout-session]", err);
    return json(
      { error: (err as Error).message || "Erro interno." },
      500
    );
  }
});
