// ============================================================
// StaFlow — Edge Function: notificar-atraso
// ------------------------------------------------------------
// Chamada pelo app do colaborador (colaborador.html) quando uma
// batida de ENTRADA é registrada além da tolerância configurada
// em Configurações. Envia email ao síndico via Resend.
//
// Requer o secret RESEND_API_KEY configurado no projeto
// (Project Settings → Edge Functions → Secrets, ou
// `supabase secrets set RESEND_API_KEY=...`).
//
// Best-effort: qualquer falha aqui NÃO deve impedir a batida de
// ponto já registrada — por isso sempre responde 200, mesmo em
// erro, e loga o motivo para debug via get_logs.
// ============================================================

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY");
const FROM_EMAIL = "StaFlow <notificacoes@staflow.app.br>";

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });

  try {
    const { funcionario_id, minutos_atraso, registrado_em } = await req.json();

    if (!funcionario_id || !minutos_atraso) {
      return new Response(JSON.stringify({ ok: false, reason: "payload incompleto" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    // 1. Busca funcionário + condomínio
    const { data: func, error: funcErr } = await supabase
      .from("funcionarios")
      .select("id, nome, condominio_id, horario_inicio")
      .eq("id", funcionario_id)
      .single();

    if (funcErr || !func) {
      console.error("[notificar-atraso] funcionário não encontrado:", funcErr);
      return new Response(JSON.stringify({ ok: false, reason: "funcionário não encontrado" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    const { data: condo } = await supabase
      .from("condominios")
      .select("nome, email_admin")
      .eq("id", func.condominio_id)
      .maybeSingle();

    // 2. Resolve email de destino: email_admin do condomínio,
    //    com fallback pro email de auth do síndico vinculado.
    let destinatario = condo?.email_admin || null;

    if (!destinatario) {
      const { data: membro } = await supabase
        .from("membros_condominio")
        .select("user_id")
        .eq("condominio_id", func.condominio_id)
        .eq("role", "sindico")
        .limit(1)
        .maybeSingle();

      if (membro?.user_id) {
        const { data: authUser } = await supabase.auth.admin.getUserById(membro.user_id);
        destinatario = authUser?.user?.email || null;
      }
    }

    if (!destinatario) {
      console.warn("[notificar-atraso] sem email de destino para condomínio", func.condominio_id);
      return new Response(JSON.stringify({ ok: false, reason: "sem email de destino" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    if (!RESEND_API_KEY) {
      console.error("[notificar-atraso] RESEND_API_KEY não configurado");
      return new Response(JSON.stringify({ ok: false, reason: "RESEND_API_KEY ausente" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    const horaBatida = registrado_em
      ? new Date(registrado_em).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", timeZone: "America/Sao_Paulo" })
      : "—";

    const html = `
      <div style="font-family:sans-serif;max-width:480px;margin:0 auto;">
        <h2 style="color:#111827;">⏰ Atraso registrado</h2>
        <p><strong>${func.nome}</strong> bateu o ponto de entrada às <strong>${horaBatida}</strong>,
        ${minutos_atraso} minuto(s) além do horário previsto e da tolerância configurada.</p>
        <p style="color:#6B7280;font-size:13px;">Condomínio: ${condo?.nome || "—"}</p>
        <p style="color:#6B7280;font-size:12px;margin-top:24px;">
          Esta é uma notificação automática do StaFlow. Ajuste a tolerância de atraso em Configurações.
        </p>
      </div>
    `;

    const resp = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: FROM_EMAIL,
        to: destinatario,
        subject: `⏰ ${func.nome} bateu ponto atrasado (${minutos_atraso}min)`,
        html,
      }),
    });

    if (!resp.ok) {
      const errText = await resp.text();
      console.error("[notificar-atraso] Resend falhou:", resp.status, errText);
      return new Response(JSON.stringify({ ok: false, reason: "resend_failed" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error("[notificar-atraso] erro inesperado:", err);
    return new Response(JSON.stringify({ ok: false, reason: "erro inesperado" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }
});
