/* ============================================================
   StaFlow — Configuração de preços do Stripe (FRONTEND)
   ------------------------------------------------------------
   Este arquivo declara o mapa { plano → price_id } usado em
   planos.html ao chamar a Edge Function `create-checkout-session`.

   🛡️  ARQUITETURA DE SEGURANÇA — IMPORTANTE
   ────────────────────────────────────────────────────────────
   O StaFlow usa **Stripe Checkout Hosted** (Stripe redireciona
   o usuário para checkout.stripe.com). Isso significa:

   ✅ ZERO chaves secretas no frontend (sk_* nunca aparece)
   ✅ ZERO chaves publishable no frontend (pk_* desnecessária)
   ✅ Apenas price_id (públicos por design) ficam aqui
   ✅ Todas as chamadas reais ao Stripe acontecem nas Edge
      Functions (server-side, com STRIPE_SECRET_KEY do env)

   Para virar LIVE MODE:
   1. Crie produtos no Stripe Dashboard em "View test data: OFF"
   2. Copie os price_id de produção (`price_LIVE_...`)
   3. Substitua os valores abaixo
   4. No Supabase secrets:
      - STRIPE_SECRET_KEY = sk_live_...
      - STRIPE_WEBHOOK_SECRET = whsec_... (do endpoint LIVE)
      - STRIPE_PRICE_PRO   = price_LIVE_...
      - STRIPE_PRICE_SCALE = price_LIVE_...
   5. Configure webhook endpoint LIVE no Stripe Dashboard
   ============================================================ */

window.STAFLOW_STRIPE_PRICES = {
  // ⚠️  Trocar para price_LIVE_... ao virar produção
  pro:   'price_1TbMBAE7YYxcPUBAsoNhJvCq',  // StaFlow Pro   — R$ 99/mês
  scale: 'price_1TbMBhE7YYxcPUBAX6eUrgYJ'   // StaFlow Scale — R$ 249/mês
};

// Flag de transparência — apenas mudou para true após o switch LIVE
// (não afeta funcionamento, só permite UI mostrar selos diferentes
// em ambientes test vs prod se quiser)
window.STAFLOW_STRIPE_LIVE_MODE = false;
