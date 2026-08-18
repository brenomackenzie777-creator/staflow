// ============================================================
// StaFlow — Edge Function: create-asaas-checkout
// ------------------------------------------------------------
// ★ 18/08/2026 — a pedido do Breno: gateway de pagamento novo
// (Asaas), rodando em PARALELO à Stripe (que continua ativa).
// Espelha create-checkout-session (Stripe): recebe o plano e o
// condomínio, cria um Checkout hospedado pela Asaas (Pix ou
// cartão, cobrança recorrente mensal) e devolve o link pra
// redirecionar o síndico.
//
// A conta Asaas do Breno é PESSOA FÍSICA (ele desativou o MEI) —
// por isso não emite nota fiscal automaticamente. Isso é uma
// limitação conhecida e aceita por enquanto, não um bug.
//
// Detecta sandbox x produção sozinho pelo prefixo da API Key
// ($aact_hmlg_ = sandbox/homologação, $aact_prod_ = produção) —
// mesma lição do bug do SUPABASE_URL: variável errada não pode
// depender de humano lembrar de trocar em dois lugares.
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

const PRODUCTION_URL = Deno.env.get("PRODUCTION_URL") || "https://staflow.app.br";

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

// PNG transparente 1x1 — a Asaas exige imageBase64 no item, mas não
// faz sentido gastar tempo com arte disso agora.
const PIXEL_TRANSPARENTE =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";

function amanha(diasAFrente = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + diasAFrente);
  return d.toISOString().slice(0, 10);
}

Deno.serve(async (req) => {
  const cors = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
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

    // Busca dados do condomínio + e-mail do síndico (fallback se não
    // tiver email_admin cadastrado).
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

    let email = condo.email_admin;
    if (!email && condo.sindico_id) {
      const { data: auth } = await supabase.auth.admin.getUserById(condo.sindico_id);
      email = auth?.user?.email || null;
    }

    const valor = PRECOS[plano];

    const corpoCheckout = {
      billingTypes: ["PIX", "CREDIT_CARD"],
      chargeTypes: ["RECURRENT"],
      minutesToExpire: 120,
      externalReference: `${condominio_id}:${plano}`,
      callback: {
        successUrl: `${PRODUCTION_URL}/configuracoes.html?asaas=sucesso`,
        cancelUrl: `${PRODUCTION_URL}/configuracoes.html?asaas=cancelado`,
      },
      items: [
        {
          name: NOMES[plano],
          description: `Assinatura mensal StaFlow — ${condo.nome}`,
          quantity: 1,
          value: valor,
          imageBase64: PIXEL_TRANSPARENTE,
        },
      ],
      customerData: {
        name: condo.nome,
        cpfCnpj: (condo.cnpj || "").replace(/\D/g, "") || undefined,
        email: email || undefined,
      },
      subscription: {
        cycle: "MONTHLY",
        nextDueDate: amanha(1),
      },
    };

    const resp = await fetch(`${ASAAS_BASE_URL}/v3/checkouts`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "access_token": ASAAS_API_KEY,
        "User-Agent": "StaFlow/1.0.0",
      },
      body: JSON.stringify(corpoCheckout),
    });

    const dados = await resp.json();

    if (!resp.ok) {
      console.error("[create-asaas-checkout] Asaas recusou:", resp.status, JSON.stringify(dados));
      return new Response(JSON.stringify({ error: "Falha ao criar checkout", detalhe: dados }), {
        status: 502, headers: { ...cors, "Content-Type": "application/json" },
      });
    }

    console.log(`[create-asaas-checkout] checkout criado para ${condo.nome} (${plano}): ${dados.id}`);

    return new Response(JSON.stringify({ link: dados.link, id: dados.id }), {
      status: 200, headers: { ...cors, "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error("[create-asaas-checkout] erro inesperado:", err);
    return new Response(JSON.stringify({ error: "Erro inesperado" }), {
      status: 500, headers: { ...cors, "Content-Type": "application/json" },
    });
  }
});
