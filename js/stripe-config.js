/* ============================================================
   StaFlow — Configuração de preços do Stripe (FRONTEND)
   ------------------------------------------------------------
   Este arquivo declara o mapa { plano → price_id } usado em
   planos.html ao chamar a Edge Function `create-checkout-session`.

   ⚠️  Substitua os placeholders abaixo pelos price IDs reais
   gerados no Stripe Dashboard:
     Stripe → Products → [Pro/Scale] → seção "Pricing" → ID (price_...)

   IMPORTANTE: este arquivo fica no frontend (público). É seguro
   expor price IDs — eles NÃO são chaves secretas. Apenas a
   STRIPE_SECRET_KEY (sk_...) e STRIPE_WEBHOOK_SECRET (whsec_...)
   precisam ficar nas Edge Functions.
   ============================================================ */

window.STAFLOW_STRIPE_PRICES = {
  pro:   'COLOQUE_AQUI_O_PRICE_ID_PRO',     // ex: price_1Q...
  scale: 'COLOQUE_AQUI_O_PRICE_ID_SCALE'    // ex: price_1Q...
};
