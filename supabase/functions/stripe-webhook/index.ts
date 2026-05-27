// ============================================================
// StaFlow — Edge Function: stripe-webhook (PRONTA PARA LIVE MODE)
// ------------------------------------------------------------
// Endpoint POST /functions/v1/stripe-webhook
// Headers obrigatórios: Stripe-Signature
//
// Eventos tratados:
//   - checkout.session.completed     → snapshot inicial pós-pagamento
//   - customer.subscription.created  → upsert subscription
//   - customer.subscription.updated  → upsert subscription
//   - customer.subscription.deleted  → status = 'canceled'
//   - invoice.paid                   → confirma renovação
//   - invoice.payment_failed         → status = 'past_due'
//
// Após cada evento que afeta status, ESPELHA em condominios:
//   - condominios.status_assinatura
//   - condominios.stripe_subscription_id
//   - condominios.plano
// Isso permite ao route-guard fazer 1 query rápida sem JOIN.
//
// Service role bypassa RLS; segurança HMAC via Stripe-Signature
// é verificada ANTES de qualquer escrita.
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

  const rawBody = await req.text();

  let event: Stripe.Event;
  try {
    event = await stripe.webhooks.constructEventAsync(
      rawBody, signature, WEBHOOK_SECRET,
    );
  } catch (err) {
    console.error("[webhook] Assinatura HMAC inválida:", (err as Error).message);
    return new Response(
      `Webhook signature verification failed: ${(err as Error).message}`,
      { status: 400 },
    );
  }

  console.log(`[webhook] Evento: ${event.type} (${event.id}) · live=${event.livemode}`);

  try {
    switch (event.type) {
      case "checkout.session.completed":
        await handleCheckoutCompleted(event.data.object as Stripe.Checkout.Session);
        break;
      case "customer.subscription.created":
      case "customer.subscription.updated":
        await handleSubscriptionUpsert(event.data.object as Stripe.Subscription);
        break;
      case "customer.subscription.deleted":
        await handleSubscriptionDeleted(event.data.object as Stripe.Subscription);
        break;
      case "invoice.paid":
        await handleInvoicePaid(event.data.object as Stripe.Invoice);
        break;
      case "invoice.payment_failed":
        await handlePaymentFailed(event.data.object as Stripe.Invoice);
        break;
      default:
        console.log(`[webhook] Evento ignorado: ${event.type}`);
    }

    return new Response(JSON.stringify({ received: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error(`[webhook] Erro processando ${event.type}:`, err);
    // 500 → Stripe retenta com backoff exponencial (3 dias)
    return new Response(
      JSON.stringify({ error: (err as Error).message }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
});

// ============================================================
// HELPERS — espelho atômico em condominios
// ============================================================
async function espelharNoCondominio(
  condominioId: string | null,
  data: {
    status_assinatura?: string;
    stripe_subscription_id?: string | null;
    plano?: string;
  },
) {
  if (!condominioId) return;
  const { error } = await supabase
    .from("condominios")
    .update(data)
    .eq("id", condominioId);
  if (error) console.error("[espelho condominio]", error);
}

// ============================================================
// HANDLERS
// ============================================================

async function handleCheckoutCompleted(session: Stripe.Checkout.Session) {
  // Snapshot inicial — confirma pagamento e linka condominio
  const profileId    = session.metadata?.profile_id    ?? null;
  const condominioId = session.metadata?.condominio_id || null;
  const subId        = typeof session.subscription === "string"
    ? session.subscription
    : session.subscription?.id;

  if (!profileId) {
    console.warn(`[webhook] checkout.completed ${session.id} sem profile_id — ignorado`);
    return;
  }

  // Pega detalhes da subscription para saber o plano via price
  let plano: "pro" | "scale" = "pro";
  if (subId) {
    try {
      const sub = await stripe.subscriptions.retrieve(subId);
      const priceId = sub.items.data[0]?.price.id ?? null;
      if (priceId && PRICE_TO_PLAN[priceId]) plano = PRICE_TO_PLAN[priceId];
    } catch (e) { /* fallback p/ 'pro' */ }
  }

  await espelharNoCondominio(condominioId, {
    status_assinatura:      "active",
    stripe_subscription_id: subId ?? null,
    plano,
  });

  console.log(`[webhook] checkout.completed: profile=${profileId} sub=${subId} plano=${plano}`);
}

async function handleSubscriptionUpsert(sub: Stripe.Subscription) {
  const profileId    = sub.metadata?.profile_id    ?? null;
  const condominioId = sub.metadata?.condominio_id || null;
  const priceId      = sub.items.data[0]?.price.id ?? null;
  const plano        = priceId ? PRICE_TO_PLAN[priceId] : undefined;

  if (!profileId) {
    console.warn(`[webhook] Subscription ${sub.id} sem profile_id — ignorada`);
    return;
  }

  // Tabela subscriptions (fonte da verdade detalhada)
  const payload = {
    profile_id:             profileId,
    condominio_id:          condominioId,
    plan:                   plano ?? "pro",
    status:                 sub.status,
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

  // Espelha em condominios
  await espelharNoCondominio(condominioId, {
    status_assinatura:      sub.status,
    stripe_subscription_id: sub.id,
    plano:                  plano ?? "pro",
  });

  console.log(`[webhook] Subscription upserted: profile=${profileId} status=${sub.status}`);
}

async function handleSubscriptionDeleted(sub: Stripe.Subscription) {
  const condominioId = sub.metadata?.condominio_id || null;

  const { error } = await supabase
    .from("subscriptions")
    .update({
      status:               "canceled",
      cancel_at_period_end: false,
      canceled_at:          new Date().toISOString(),
      updated_at:           new Date().toISOString(),
    })
    .eq("stripe_subscription_id", sub.id);
  if (error) throw error;

  await espelharNoCondominio(condominioId, {
    status_assinatura: "canceled",
  });

  console.log(`[webhook] Subscription canceled: ${sub.id}`);
}

async function handleInvoicePaid(invoice: Stripe.Invoice) {
  // Renovação bem-sucedida — reativa se estava past_due
  const subId = typeof invoice.subscription === "string"
    ? invoice.subscription
    : invoice.subscription?.id;
  if (!subId) return;

  // Busca a subscription pra pegar condominio_id e re-sincronizar
  try {
    const sub = await stripe.subscriptions.retrieve(subId);
    const condominioId = sub.metadata?.condominio_id || null;

    await supabase.from("subscriptions")
      .update({ status: sub.status, updated_at: new Date().toISOString() })
      .eq("stripe_subscription_id", subId);

    await espelharNoCondominio(condominioId, {
      status_assinatura:      sub.status,
      stripe_subscription_id: subId,
    });
    console.log(`[webhook] invoice.paid: sub=${subId} status=${sub.status}`);
  } catch (e) {
    console.error("[webhook] invoice.paid lookup falhou:", e);
  }
}

async function handlePaymentFailed(invoice: Stripe.Invoice) {
  const subId = typeof invoice.subscription === "string"
    ? invoice.subscription
    : invoice.subscription?.id;
  if (!subId) {
    console.warn(`[webhook] invoice.payment_failed sem subscription — ignorado`);
    return;
  }

  const { error } = await supabase
    .from("subscriptions")
    .update({ status: "past_due", updated_at: new Date().toISOString() })
    .eq("stripe_subscription_id", subId);
  if (error) throw error;

  // Espelha em condominios para o route-guard bloquear acesso admin
  let condominioId: string | null = null;
  try {
    const sub = await stripe.subscriptions.retrieve(subId);
    condominioId = sub.metadata?.condominio_id || null;
  } catch (_) { /* segue sem espelho */ }

  await espelharNoCondominio(condominioId, {
    status_assinatura: "past_due",
  });

  console.log(`[webhook] Subscription past_due: ${subId} (route-guard vai redirecionar p/ /planos)`);
}
