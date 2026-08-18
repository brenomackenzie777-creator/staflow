// ============================================================
// StaFlow — Edge Function: telegram-webhook
// ------------------------------------------------------------
// ★ 18/08/2026 — a pedido do Breno: um canal onde ele conversa
// com o time em vez de só deixar recado assíncrono em
// /agentes.html. O Telegram chama esta função toda vez que o
// Breno manda mensagem pro bot. A função:
//   1. Confirma que quem mandou é o Breno (chat_id == TELEGRAM_CHAT_ID).
//      Qualquer outro chat_id é ignorado — o bot não vira uma
//      caixa de entrada pública.
//   2. Grava a mensagem em time_recados (mesma tabela que
//      /agentes.html usa), pra o ciclo CEO do dia seguinte tratar
//      como prioridade.
//   3. Responde na hora no Telegram avisando que foi recebido —
//      a resposta de verdade (o que o time decidiu fazer) chega
//      depois, quando o Executor chamar responder_recado_breno
//      (que já manda mensagem de volta pro Telegram).
//
// Requer os secrets no projeto (Project Settings → Edge Functions
// → Secrets, ou `supabase secrets set`):
//   TELEGRAM_BOT_TOKEN  — token dado pelo @BotFather
//   TELEGRAM_CHAT_ID    — id da conversa do Breno com o bot
//   BRENO_USER_ID       — id dele em auth.users/profiles (autor_id)
//
// Depois de fazer o deploy, registre esta URL como webhook do bot
// (uma vez só, visitando no navegador — não precisa programar nada):
//   https://api.telegram.org/bot<TOKEN>/setWebhook?url=<URL_DESTA_FUNCAO>
//
// Sempre responde 200 pro Telegram, mesmo em erro interno — um
// erro aqui não pode fazer o Telegram ficar reenviando a mensagem
// em loop.
// ============================================================

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const TELEGRAM_BOT_TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN");
const TELEGRAM_CHAT_ID   = Deno.env.get("TELEGRAM_CHAT_ID");
const BRENO_USER_ID      = Deno.env.get("BRENO_USER_ID");

async function responder(chatId: string | number, texto: string) {
  if (!TELEGRAM_BOT_TOKEN) return;
  try {
    await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, text: texto }),
    });
  } catch (err) {
    console.error("[telegram-webhook] falha ao responder no Telegram:", err);
  }
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });

  try {
    const update = await req.json();
    const msg = update?.message;
    const texto = msg?.text as string | undefined;
    const chatId = msg?.chat?.id;

    if (!msg || !texto || chatId === undefined) {
      // update sem mensagem de texto (ex: edição, sticker, etc.) — ignora.
      return new Response("ok", { status: 200 });
    }

    // ── Segurança: só o Breno fala com o time por aqui ──
    if (!TELEGRAM_CHAT_ID || String(chatId) !== String(TELEGRAM_CHAT_ID)) {
      console.warn("[telegram-webhook] mensagem de chat_id não autorizado:", chatId);
      // Não revela nada — só ignora silenciosamente.
      return new Response("ok", { status: 200 });
    }

    // /start e afins não viram recado
    if (texto.trim().startsWith("/")) {
      await responder(chatId,
        "Oi! Pode mandar sua mensagem direto, sem comando — eu levo pro " +
        "time e o ciclo de amanhã (~8h) trata como prioridade.");
      return new Response("ok", { status: 200 });
    }

    if (!BRENO_USER_ID) {
      console.error("[telegram-webhook] BRENO_USER_ID não configurado");
      await responder(chatId,
        "Recebi sua mensagem, mas o canal ainda não está 100% configurado " +
        "(faltou um ajuste técnico). O Breno/Claude precisa configurar o " +
        "secret BRENO_USER_ID.");
      return new Response("ok", { status: 200 });
    }

    const { error } = await supabase.from("time_recados").insert({
      autor_id: BRENO_USER_ID,
      mensagem: texto,
      area_alvo: null,
      status: "pendente",
    });

    if (error) {
      console.error("[telegram-webhook] falha ao gravar recado:", error);
      await responder(chatId,
        "Recebi, mas deu erro ao salvar pro time ver. Tenta de novo em " +
        "instantes ou avisa o Claude.");
      return new Response("ok", { status: 200 });
    }

    await responder(chatId,
      "Recebido ✅ Vou tratar isso no próximo ciclo do time (todo dia por " +
      "volta das 8h). Te aviso aqui mesmo assim que tiver resposta.");

    return new Response("ok", { status: 200 });
  } catch (err) {
    console.error("[telegram-webhook] erro inesperado:", err);
    return new Response("ok", { status: 200 });
  }
});
