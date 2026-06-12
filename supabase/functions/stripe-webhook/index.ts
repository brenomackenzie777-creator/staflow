// ============================================================
// StaFlow — Edge Function: stripe-webhook (Multi-CNPJ)
// ------------------------------------------------------------
// Eventos:
//   - checkout.session.completed  → ativa condomínio pós-pagamento
//   - checkout.session.expired    → limpa condomínio zumbi (checkout abandonado)
//   - customer.subscription.*     → upsert por condominio_id
//   - invoice.paid                → reativa past_due
//   - invoice.payment_failed      → status='past_due'
//
// CHAVE DE LINK: metadata.condominio_id em TODA escrita. profile_id
// é só pra trilha de auditoria — fonte da verdade é condominio_id.
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

// Map price_id → plano (mensal + anual)
function buildPriceMap(): Record<string, "pro" | "advanced" | "scale"> {
  const map: Record<string, "pro" | "advanced" | "scale"> = {};
  const add = (envKey: string, plan: "pro" | "advanced" | "scale") => {
    const id = Deno.env.get(envKey);
    if (id) map[id] = plan;
  };
  add("STRIPE_PRICE_PRO",              "pro");
  add("STRIPE_PRICE_PRO_ANNUAL",       "pro");
  add("STRIPE_PRICE_ADVANCED",         "advanced");
  add("STRIPE_PRICE_ADVANCED_ANNUAL",  "advanced");
  add("STRIPE_PRICE_SCALE",            "scale");
  add("STRIPE_PRICE_SCALE_ANNUAL",     "scale");
  return map;
}
const PRICE_TO_PLAN = buildPriceMap();

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });
  const signature = req.headers.get("stripe-signature");
  if (!signature) return new Response("Missing stripe-signature", { status: 400 });

  const rawBody = await req.text();
  let event: Stripe.Event;
  try {
    event = await stripe.webhooks.constructEventAsync(rawBody, signature, WEBHOOK_SECRET);
  } catch (err) {
    return new Response(`Webhook signature failed: ${(err as Error).message}`, { status: 400 });
  }

  try {
    switch (event.type) {
      case "checkout.session.completed":
        await handleCheckoutCompleted(event.data.object as Stripe.Checkout.Session);
        break;
      case "checkout.session.expired":
        await handleCheckoutExpired(event.data.object as Stripe.Checkout.Session);
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
    }
    return new Response(JSON.stringify({ received: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error(`[webhook] ${event.type} falhou:`, err);
    return new Response(JSON.stringify({ error: (err as Error).message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});

// ─── Espelho atômico em condominios (chave: condominio_id) ───
async function espelharNoCondominio(
  condominioId: string | null,
  data: {
    status_assinatura?: string;
    stripe_subscription_id?: string | null;
    plano?: string;
    plano_ativo?: string;
  },
) {
  if (!condominioId) return;
  const { error } = await supabase.from("condominios").update(data).eq("id", condominioId);
  if (error) console.error("[espelho condominio]", error);
}

async function handleCheckoutCompleted(session: Stripe.Checkout.Session) {
  const profileId    = session.metadata?.profile_id    ?? null;
  const condominioId = session.metadata?.condominio_id ?? null;
  const subId        = typeof session.subscription === "string"
    ? session.subscription
    : session.subscription?.id;

  if (!condominioId) {
    console.warn(`[webhook] checkout.completed ${session.id} sem condominio_id`);
    return;
  }

  let plano: "pro" | "advanced" | "scale" = "pro";
  let stripeCustomerId: string | null = null;
  let periodStart: string | null = null;
  let periodEnd: string | null = null;
  let priceId: string | null = null;

  if (subId) {
    try {
      const sub = await stripe.subscriptions.retrieve(subId);
      priceId = sub.items.data[0]?.price.id ?? null;
      if (priceId && PRICE_TO_PLAN[priceId]) plano = PRICE_TO_PLAN[priceId];
      stripeCustomerId = typeof sub.customer === "string" ? sub.customer : sub.customer.id;
      periodStart = new Date(sub.current_period_start * 1000).toISOString();
      periodEnd   = new Date(sub.current_period_end   * 1000).toISOString();
    } catch (_) { /* fallback pro */ }
  }

  // Upsert na tabela subscriptions (failsafe — customer.subscription.created pode chegar depois)
  if (profileId) {
    const subPayload = {
      profile_id:             profileId,
      condominio_id:          condominioId,
      plan:                   plano,
      status:                 "active",
      stripe_customer_id:     stripeCustomerId,
      stripe_subscription_id: subId ?? null,
      stripe_price_id:        priceId,
      current_period_start:   periodStart,
      current_period_end:     periodEnd,
      cancel_at_period_end:   false,
      updated_at:             new Date().toISOString(),
    };
    const { error: subErr } = await supabase
      .from("subscriptions")
      .upsert(subPayload, { onConflict: "profile_id,condominio_id" });
    if (subErr) console.error("[webhook] upsert subscriptions falhou:", subErr);
  }

  await espelharNoCondominio(condominioId, {
    status_assinatura:      "active",
    stripe_subscription_id: subId ?? null,
    plano,
    plano_ativo:            plano,
  });
}

// ─── Cleanup: checkout expirado sem pagamento → remove condomínio zumbi ───
// Dispara quando o usuário abre o Stripe Checkout mas não paga.
// create-checkout-session cria o registro em condominios(status='pending')
// antes do pagamento — aqui desfazemos se nenhuma subscription foi criada.
async function handleCheckoutExpired(session: Stripe.Checkout.Session) {
  const condominioId = session.metadata?.condominio_id ?? null;
  if (!condominioId) return;

  // Verifica se já existe subscription ativa para esse condomínio.
  // Se sim, foi pago em outra tentativa — não mexe.
  const { data: sub } = await supabase
    .from("subscriptions")
    .select("id")
    .eq("condominio_id", condominioId)
    .maybeSingle();

  if (sub) {
    console.log(`[checkout.expired] condominio ${condominioId} já tem subscription — ignorando`);
    return;
  }

  // Sem subscription → condomínio foi criado provisoriamente e nunca ativado
  const { error } = await supabase
    .from("condominios")
    .delete()
    .eq("id", condominioId)
    .eq("status_assinatura", "pending"); // segurança extra: só deleta se ainda pending

  if (error) {
    console.error(`[checkout.expired] erro ao deletar condomínio zumbi ${condominioId}:`, error);
  } else {
    console.log(`[checkout.expired] condomínio zumbi ${condominioId} removido`);
  }
}

async function handleSubscriptionUpsert(sub: Stripe.Subscription) {
  const profileId    = sub.metadata?.profile_id    ?? null;
  const condominioId = sub.metadata?.condominio_id ?? null;
  const priceId      = sub.items.data[0]?.price.id ?? null;
  const plano        = priceId ? PRICE_TO_PLAN[priceId] : undefined;

  if (!condominioId) {
    console.warn(`[webhook] Subscription ${sub.id} sem condominio_id — ignorada`);
    return;
  }

  // Upsert por (profile_id, condominio_id) — N subs por user agora possível
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
    .upsert(payload, { onConflict: "profile_id,condominio_id" });
  if (error) throw error;

  await espelharNoCondominio(condominioId, {
    status_assinatura:      sub.status,
    stripe_subscription_id: sub.id,
    plano:                  plano ?? "pro",
    plano_ativo:            plano ?? "pro",
  });
}

async function handleSubscriptionDeleted(sub: Stripe.Subscription) {
  const condominioId = sub.metadata?.condominio_id ?? null;

  await supabase.from("subscriptions")
    .update({
      status:               "canceled",
      plan:                 "starter",
      cancel_at_period_end: false,
      canceled_at:          new Date().toISOString(),
      updated_at:           new Date().toISOString(),
    })
    .eq("stripe_subscription_id", sub.id);

  // Rebaixa condomínio para starter — limites e acesso resetados
  await espelharNoCondominio(condominioId, {
    status_assinatura: "canceled",
    plano:             "starter",
    plano_ativo:       "starter",
  });
}

async function handleInvoicePaid(invoice: Stripe.Invoice) {
  const subId = typeof invoice.subscription === "string" ? invoice.subscription : invoice.subscription?.id;
  if (!subId) return;
  try {
    const sub = await stripe.subscriptions.retrieve(subId);
    const condominioId = sub.metadata?.condominio_id ?? null;
    await supabase.from("subscriptions")
      .update({ status: sub.status, updated_at: new Date().toISOString() })
      .eq("stripe_subscription_id", subId);
    await espelharNoCondominio(condominioId, {
      status_assinatura:      sub.status,
      stripe_subscription_id: subId,
    });
  } catch (e) {
    console.error("[webhook] invoice.paid lookup falhou:", e);
  }
}

async function handlePaymentFailed(invoice: Stripe.Invoice) {
  const subId = typeof invoice.subscription === "string" ? invoice.subscription : invoice.subscription?.id;
  if (!subId) return;

  await supabase.from("subscriptions")
    .update({ status: "past_due", updated_at: new Date().toISOString() })
    .eq("stripe_subscription_id", subId);

  let condominioId: string | null = null;
  try {
    const sub = await stripe.subscriptions.retrieve(subId);
    condominioId = sub.metadata?.condominio_id ?? null;
  } catch (_) {}
  await espelharNoCondominio(condominioId, { status_assinatura: "past_due" });
}
