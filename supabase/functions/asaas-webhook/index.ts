// ============================================================
// StaFlow — Edge Function: asaas-webhook
// ------------------------------------------------------------
// ★ 18/08/2026 — recebe os eventos da Asaas (assinatura criada,
// pagamento confirmado, atraso, cancelamento) e mantém
// status_assinatura / plano_ativo / asaas_subscription_id /
// asaas_customer_id do condomínio em dia. Espelha o papel do
// stripe-webhook, em paralelo — Stripe continua funcionando.
//
// Segurança: a Asaas manda um header "asaas-access-token" com o
// valor configurado na hora de criar o Webhook no painel. NUNCA
// é a API Key (a documentação da própria Asaas pede pra não usar
// a API Key aqui). Requer secret ASAAS_WEBHOOK_TOKEN.
//
// O condomínio é identificado por `externalReference`
// ("condominioId:plano"), gravado na criação do Checkout em
// create-asaas-checkout. Se o evento não trouxer externalReference
// (alguns eventos de pagamento não trazem, só o de assinatura),
// cai pro fallback de achar o condomínio por asaas_subscription_id
// já salvo antes.
// ============================================================

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const ASAAS_WEBHOOK_TOKEN = Deno.env.get("ASAAS_WEBHOOK_TOKEN");

function parseExternalReference(ref?: string | null): { condominioId: string; plano: string } | null {
  if (!ref || !ref.includes(":")) return null;
  const [condominioId, plano] = ref.split(":");
  if (!condominioId || !plano) return null;
  return { condominioId, plano };
}

async function condominioIdPorAssinatura(subscriptionId?: string | null): Promise<string | null> {
  if (!subscriptionId) return null;
  const { data } = await supabase
    .from("condominios")
    .select("id")
    .eq("asaas_subscription_id", subscriptionId)
    .maybeSingle();
  return data?.id || null;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });

  // ── Segurança: valida o token do webhook ──
  const tokenRecebido = req.headers.get("asaas-access-token");
  if (!ASAAS_WEBHOOK_TOKEN) {
    console.error("[asaas-webhook] ASAAS_WEBHOOK_TOKEN não configurado — recusando tudo por segurança");
    return new Response("not configured", { status: 500 });
  }
  if (tokenRecebido !== ASAAS_WEBHOOK_TOKEN) {
    console.warn("[asaas-webhook] token inválido recebido");
    return new Response("unauthorized", { status: 401 });
  }

  try {
    const body = await req.json();
    const evento: string = body?.event || "";
    console.log(`[asaas-webhook] evento recebido: ${evento}`);

    // ── Eventos de assinatura: criação grava os IDs no condomínio ──
    if (evento === "SUBSCRIPTION_CREATED" || evento === "SUBSCRIPTION_UPDATED") {
      const sub = body.subscription;
      const ref = parseExternalReference(sub?.externalReference);
      if (ref) {
        await supabase.from("condominios").update({
          asaas_subscription_id: sub.id,
          asaas_customer_id: sub.customer,
          plano: ref.plano,
          plano_ativo: ref.plano,
        }).eq("id", ref.condominioId);
        console.log(`[asaas-webhook] assinatura ${sub.id} vinculada ao condomínio ${ref.condominioId}`);
      } else {
        console.warn("[asaas-webhook] SUBSCRIPTION_CREATED sem externalReference utilizável:", sub?.id);
      }
      return new Response("ok", { status: 200 });
    }

    if (evento === "SUBSCRIPTION_INACTIVATED" || evento === "SUBSCRIPTION_DELETED") {
      const sub = body.subscription;
      const ref = parseExternalReference(sub?.externalReference);
      const condominioId = ref?.condominioId || await condominioIdPorAssinatura(sub?.id);
      if (condominioId) {
        await supabase.from("condominios").update({ status_assinatura: "inactive" }).eq("id", condominioId);
        console.log(`[asaas-webhook] assinatura ${sub?.id} inativada — condomínio ${condominioId}`);
      }
      return new Response("ok", { status: 200 });
    }

    // ── Eventos de pagamento: confirmação liga a assinatura ──
    if (evento === "PAYMENT_CONFIRMED" || evento === "PAYMENT_RECEIVED") {
      const pay = body.payment;
      const ref = parseExternalReference(pay?.externalReference);
      const condominioId = ref?.condominioId || await condominioIdPorAssinatura(pay?.subscription);
      if (condominioId) {
        const update: Record<string, unknown> = { status_assinatura: "active" };
        if (ref) { update.plano = ref.plano; update.plano_ativo = ref.plano; }
        if (pay?.customer) update.asaas_customer_id = pay.customer;
        if (pay?.subscription) update.asaas_subscription_id = pay.subscription;
        await supabase.from("condominios").update(update).eq("id", condominioId);
        console.log(`[asaas-webhook] pagamento confirmado — condomínio ${condominioId} ativo`);
      } else {
        console.warn("[asaas-webhook] PAYMENT_CONFIRMED sem condomínio identificável:", pay?.id);
      }
      return new Response("ok", { status: 200 });
    }

    if (evento === "PAYMENT_OVERDUE") {
      const pay = body.payment;
      const ref = parseExternalReference(pay?.externalReference);
      const condominioId = ref?.condominioId || await condominioIdPorAssinatura(pay?.subscription);
      if (condominioId) {
        await supabase.from("condominios").update({ status_assinatura: "overdue" }).eq("id", condominioId);
        console.log(`[asaas-webhook] pagamento atrasado — condomínio ${condominioId}`);
      }
      return new Response("ok", { status: 200 });
    }

    // Evento que não tratamos ainda — só confirma recebimento.
    return new Response("ok", { status: 200 });
  } catch (err) {
    console.error("[asaas-webhook] erro inesperado:", err);
    // 200 mesmo em erro interno pra não empilhar retry infinito da Asaas
    // por um bug nosso — o log já registra pra investigar depois.
    return new Response("ok", { status: 200 });
  }
});
