// ============================================================
// StaFlow — Edge Function: stripe-webhook
// ------------------------------------------------------------
// Endpoint POST /functions/v1/stripe-webhook
// Headers obrigatórios: Stripe-Signature
//
// Eventos tratados:
//   - customer.subscription.created   → upsert subscription
//   - customer.subscription.updated   → upsert subscription
//   - customer.subscription.deleted   → status = 'canceled'
//   - invoice.payment_failed          → status = 'past_due'
//
// Service role bypassa RLS (público=internet, mas valida assinatura
// HMAC do Stripe antes de qualquer escrita).
// ============================================================

import Stripe from "https://esm.sh/stripe@14.21.0?target=deno";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY")!, {
  apiVersion: "2024-12-18.acacia",
  httpClient: Stripe.createFetchHttpClient(),
});

const WEBHOOK_SECRET = Deno.env.get("STRIPE_WEBHOOK_SECRET")!;
const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

// Mapeia price_id do Stripe → nome do plano interno.
// Configure via env (não hardcode os IDs).
const PRICE_TO_PLAN: Record<string, "pro" | "scale"> = {
  [Deno.env.get("STRIPE_PRICE_PRO")   ?? "_unset_pro"]:   "pro",
  [Deno.env.get("STRIPE_PRICE_SCALE") ?? "_unset_scale"]: "scale",
};

// ============================================================
Deno.serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  const signature = req.headers.get("stripe-signature");
  if (!signature) {
    return new Response("Missing stripe-signature header", { status: 400 });
  }

  // IMPORTANTE: body BRUTO (Uint8Array → string) é obrigatório
  // para verificar HMAC. Não use req.json() aqui.
  const rawBody = await req.text();

  let event: Stripe.Event;
  try {
    // No Deno é obrigatório usar a versão *Async* (crypto async)
    event = await stripe.webhooks.constructEventAsync(
      rawBody,
      signature,
      WEBHOOK_SECRET,
    );
  } catch (err) {
    console.error("[webhook] Assinatura inválida:", (err as Error).message);
    return new Response(`Webhook signature verification failed: ${(err as Error).message}`, { status: 400 });
  }

  console.log(`[webhook] Evento recebido: ${event.type} (${event.id})`);

  try {
    switch (event.type) {
      case "customer.subscription.created":
      case "customer.subscription.updated": {
        await handleSubscriptionUpsert(event.data.object as Stripe.Subscription);
        break;
      }
      case "customer.subscription.deleted": {
        await handleSubscriptionDeleted(event.data.object as Stripe.Subscription);
        break;
      }
      case "invoice.payment_failed": {
        await handlePaymentFailed(event.data.object as Stripe.Invoice);
        break;
      }
      default:
        console.log(`[webhook] Evento ignorado: ${event.type}`);
    }

    return new Response(JSON.stringify({ received: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error(`[webhook] Erro processando ${event.type}:`, err);
    // Retorna 500 para o Stripe re-tentar (com backoff exponencial)
    return new Response(
      JSON.stringify({ error: (err as Error).message }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
});

// ============================================================
// Handlers
// ============================================================

async function handleSubscriptionUpsert(sub: Stripe.Subscription) {
  const profileId    = sub.metadata?.profile_id    ?? null;
  const condominioId = sub.metadata?.condominio_id || null;
  const priceId      = sub.items.data[0]?.price.id ?? null;
  const plan         = priceId ? PRICE_TO_PLAN[priceId] : undefined;

  if (!profileId) {
    // Sem metadata.profile_id não conseguimos linkar — log e ignora.
    // Acontece em testes manuais no dashboard sem passar metadata.
    console.warn(`[webhook] Subscription ${sub.id} sem metadata.profile_id — ignorada`);
    return;
  }

  const payload = {
    profile_id:             profileId,
    condominio_id:          condominioId,
    plan:                   plan ?? "pro",
    status:                 sub.status, // active | trialing | past_due | canceled | incomplete | etc.
    stripe_customer_id:     typeof sub.customer === "string" ? sub.customer : sub.customer.id,
    stripe_subscription_id: sub.id,
    stripe_price_id:        priceId,
    current_period_start:   new Date(sub.current_period_start * 1000).toISOString(),
    current_period_end:     new Date(sub.current_period_end   * 1000).toISOString(),
    cancel_at_period_end:   sub.cancel_at_period_end,
    canceled_at:            sub.canceled_at ? new Date(sub.canceled_at * 1000).toISOString() : null,
    trial_end:              sub.trial_end   ? new Date(sub.trial_end   * 1000).toISOString() : null,
    updated_at:             new Date().toISOString(),
  };

  const { error } = await supabase
    .from("subscriptions")
    .upsert(payload, { onConflict: "profile_id" });

  if (error) throw error;
  console.log(`[webhook] Subscription upserted: profile=${profileId} status=${sub.status}`);
}

async function handleSubscriptionDeleted(sub: Stripe.Subscription) {
  // Pode chegar pelo stripe_subscription_id OU pelo profile_id no metadata
  const stripeSubId = sub.id;

  const { error } = await supabase
    .from("subscriptions")
    .update({
      status:               "canceled",
      cancel_at_period_end: false,
      canceled_at:          new Date().toISOString(),
      updated_at:           new Date().toISOString(),
    })
    .eq("stripe_subscription_id", stripeSubId);

  if (error) throw error;
  console.log(`[webhook] Subscription canceled: ${stripeSubId}`);
}

async function handlePaymentFailed(invoice: Stripe.Invoice) {
  // O invoice tem subscription (id) e customer
  const stripeSubId = typeof invoice.subscription === "string"
    ? invoice.subscription
    : invoice.subscription?.id;

  if (!stripeSubId) {
    console.warn(`[webhook] invoice.payment_failed sem subscription — ignorado (invoice ${invoice.id})`);
    return;
  }

  const { error } = await supabase
    .from("subscriptions")
    .update({
      status:     "past_due",
      updated_at: new Date().toISOString(),
    })
    .eq("stripe_subscription_id", stripeSubId);

  if (error) throw error;
  console.log(`[webhook] Subscription marcada past_due: ${stripeSubId}`);
}
