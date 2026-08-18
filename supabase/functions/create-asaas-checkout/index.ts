// ============================================================
// StaFlow — Edge Function: create-asaas-checkout
// ------------------------------------------------------------
// ★ 18/08/2026 — a pedido do Breno: gateway de pagamento novo
// (Asaas), rodando em PARALELO à Stripe (que continua ativa).
// Cria uma ASSINATURA recorrente na Asaas cobrada via Pix e
// devolve o link da fatura (QR code + copia-e-cola) pra
// redirecionar o síndico.
//
// ★ 18/08/2026, mesmo dia — DOIS bugs achados testando ao vivo
// (toast "Failed to send a request to the Edge Function"):
//
// 1. CORS: o front manda um header custom "x-condominio-id" em
//    TODA chamada de function (ver js/supabase-client.js, usado
//    pro contexto multi-CNPJ — create-checkout-session já
//    liberava esse header no Access-Control-Allow-Headers, esta
//    function não). Sem ele na lista, o navegador aceita o
//    preflight OPTIONS (200) mas recusa mandar o POST de
//    verdade — daí o erro genérico do client, sem nem chegar
//    no log da function. Corrigido adicionando x-condominio-id
//    aqui também.
//
// 2. Depois de resolver o CORS, a Asaas ainda recusava (502) a
//    primeira versão, que usava /v3/checkouts com
//    billingTypes:["PIX","CREDIT_CARD"] + chargeTypes:["RECURRENT"]:
//    "O tipo de cobrança DETACHED é obrigatório para PIX" / "só
//    CREDIT_CARD pode ser RECURRENT". O Checkout NÃO permite Pix
//    recorrente misturado com cartão. Corrigido usando o endpoint
//    de ASSINATURA direto (/v3/subscriptions), que aceita
//    billingType:"PIX" recorrente nativamente. O botão "ou pagar
//    com Pix" agora é só Pix (cartão continua no botão principal
//    via Stripe).
//
// Pré-requisito descoberto no mesmo teste: a Asaas EXIGE cpfCnpj
// no cadastro do cliente pagador. Se o condomínio não tiver CNPJ
// cadastrado, a function recusa com mensagem clara em vez do
// erro genérico.
//
// A conta Asaas do Breno é PESSOA FÍSICA (ele desativou o MEI) —
// por isso não emite nota fiscal automaticamente. Isso é uma
// limitação conhecida e aceita por enquanto, não um bug.
//
// Detecta sandbox x produção sozinho pelo prefixo da API Key
// ($aact_hmlg_ = sandbox/homologação, $aact_prod_ = produção).
//
// Requer secrets: ASAAS_API_KEY (Project Settings → Edge
// Functions → Secrets).
// ============================================================

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const ASAAS_API_KEY = Deno.env.get("ASAAS_API_KEY") || "";
const ASAAS_BASE_URL = ASAAS_API_KEY.startsWith("$aact_hmlg")
  ? "https://api-sandbox.asaas.com"
  : "https://api.asaas.com";

const PRECOS: Record<string, number> = {
  pro: 99,
  advanced: 159,
  scale: 279,
};

const NOMES: Record<string, string> = {
  pro: "StaFlow - Plano Pro",
  advanced: "StaFlow - Plano Advanced",
  scale: "StaFlow - Plano Scale",
};

function amanha(diasAFrente = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + diasAFrente);
  return d.toISOString().slice(0, 10);
}

async function asaasFetch(path: string, init: RequestInit) {
  const resp = await fetch(`${ASAAS_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "access_token": ASAAS_API_KEY,
      "User-Agent": "StaFlow/1.0.0",
      ...(init.headers || {}),
    },
  });
  const dados = await resp.json().catch(() => ({}));
  return { ok: resp.ok, status: resp.status, dados };
}

Deno.serve(async (req) => {
  const cors = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-condominio-id",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };

  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405, headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  try {
    if (!ASAAS_API_KEY) {
      console.error("[create-asaas-checkout] ASAAS_API_KEY não configurado");
      return new Response(JSON.stringify({ error: "Gateway não configurado" }), {
        status: 500, headers: { ...cors, "Content-Type": "application/json" },
      });
    }

    const { condominio_id, plano } = await req.json();

    if (!condominio_id || !plano || !PRECOS[plano]) {
      return new Response(JSON.stringify({ error: "condominio_id e plano (pro/advanced/scale) são obrigatórios" }), {
        status: 400, headers: { ...cors, "Content-Type": "application/json" },
      });
    }

    const { data: condo, error: condoErr } = await supabase
      .from("condominios")
      .select("id, nome, cnpj, email_admin, sindico_id")
      .eq("id", condominio_id)
      .maybeSingle();

    if (condoErr || !condo) {
      console.error("[create-asaas-checkout] condomínio não encontrado:", condoErr);
      return new Response(JSON.stringify({ error: "Condomínio não encontrado" }), {
        status: 404, headers: { ...cors, "Content-Type": "application/json" },
      });
    }

    const cpfCnpj = (condo.cnpj || "").replace(/\D/g, "");
    if (!cpfCnpj) {
      return new Response(JSON.stringify({
        error: "Cadastre o CNPJ (ou CPF) do condomínio em Configurações antes de pagar com Pix. A assinatura por cartão continua disponível normalmente.",
      }), {
        status: 400, headers: { ...cors, "Content-Type": "application/json" },
      });
    }

    let email = condo.email_admin;
    if (!email && condo.sindico_id) {
      const { data: auth } = await supabase.auth.admin.getUserById(condo.sindico_id);
      email = auth?.user?.email || null;
    }

    const valor = PRECOS[plano];

    // ── 1. Acha ou cria o cliente na Asaas (pelo externalReference) ──
    const busca = await asaasFetch(
      `/v3/customers?externalReference=${encodeURIComponent(condominio_id)}`,
      { method: "GET" },
    );

    let customerId: string | undefined = busca.ok && busca.dados?.data?.[0]?.id;

    if (!customerId) {
      const criacao = await asaasFetch("/v3/customers", {
        method: "POST",
        body: JSON.stringify({
          name: condo.nome,
          cpfCnpj,
          email: email || undefined,
          externalReference: condominio_id,
        }),
      });
      if (!criacao.ok) {
        console.error("[create-asaas-checkout] falha ao criar cliente:", criacao.status, JSON.stringify(criacao.dados));
        return new Response(JSON.stringify({ error: "Não foi possível cadastrar o pagador na Asaas", detalhe: criacao.dados }), {
          status: 502, headers: { ...cors, "Content-Type": "application/json" },
        });
      }
      customerId = criacao.dados.id;
    }

    // ── 2. Cria a assinatura recorrente cobrada via Pix ──
    const assinatura = await asaasFetch("/v3/subscriptions", {
      method: "POST",
      body: JSON.stringify({
        customer: customerId,
        billingType: "PIX",
        cycle: "MONTHLY",
        value: valor,
        nextDueDate: amanha(1),
        description: `${NOMES[plano]} — ${condo.nome}`,
        externalReference: `${condominio_id}:${plano}`,
      }),
    });

    if (!assinatura.ok) {
      console.error("[create-asaas-checkout] Asaas recusou assinatura:", assinatura.status, JSON.stringify(assinatura.dados));
      return new Response(JSON.stringify({ error: "Falha ao criar assinatura Pix", detalhe: assinatura.dados }), {
        status: 502, headers: { ...cors, "Content-Type": "application/json" },
      });
    }

    const subscriptionId = assinatura.dados.id;

    // ── 3. Pega a primeira cobrança gerada, pra mandar o síndico
    //      direto pra página de pagamento (QR Pix + copia-e-cola) ──
    const cobrancas = await asaasFetch(
      `/v3/payments?subscription=${encodeURIComponent(subscriptionId)}`,
      { method: "GET" },
    );

    const primeiraCobranca = cobrancas.ok ? cobrancas.dados?.data?.[0] : null;

    if (!primeiraCobranca?.invoiceUrl) {
      console.error("[create-asaas-checkout] assinatura criada mas sem cobrança/invoiceUrl:", JSON.stringify(cobrancas.dados));
      return new Response(JSON.stringify({ error: "Assinatura criada, mas não achamos o link de pagamento. Tente novamente em instantes." }), {
        status: 502, headers: { ...cors, "Content-Type": "application/json" },
      });
    }

    console.log(`[create-asaas-checkout] assinatura Pix criada para ${condo.nome} (${plano}): ${subscriptionId}`);

    return new Response(JSON.stringify({ link: primeiraCobranca.invoiceUrl, id: subscriptionId }), {
      status: 200, headers: { ...cors, "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error("[create-asaas-checkout] erro inesperado:", err);
    return new Response(JSON.stringify({ error: "Erro inesperado" }), {
      status: 500, headers: { ...cors, "Content-Type": "application/json" },
    });
  }
});
