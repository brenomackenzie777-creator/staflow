/* ============================================================
   StaFlow — Configuração de preços do Stripe (FRONTEND)
   ------------------------------------------------------------
   Este arquivo declara o mapa { plano → price_id } usado em
   planos.html ao chamar a Edge Function `create-checkout-session`.

   IMPORTANTE: price IDs são públicos por design do Stripe —
   eles identificam o produto, não autorizam cobranças. Apenas
   a STRIPE_SECRET_KEY (sk_...) e STRIPE_WEBHOOK_SECRET (whsec_...)
   precisam ficar nas Edge Functions (nunca no frontend).
   ============================================================ */

window.STAFLOW_STRIPE_PRICES = {
  pro:   'price_1TbMBAE7YYxcPUBAsoNhJvCq',  // StaFlow Pro — R$ 99/mês
  scale: 'price_1TbMBhE7YYxcPUBAX6eUrgYJ'   // StaFlow Scale — R$ 249/mês
};
