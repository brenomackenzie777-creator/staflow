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
      - STRIPE_PRICE_PRO              = price_LIVE_...
      - STRIPE_PRICE_PRO_ANNUAL      = price_LIVE_...
      - STRIPE_PRICE_ADVANCED        = price_LIVE_...
      - STRIPE_PRICE_ADVANCED_ANNUAL = price_LIVE_...
      - STRIPE_PRICE_SCALE           = price_LIVE_...
      - STRIPE_PRICE_SCALE_ANNUAL    = price_LIVE_...
   5. Configure webhook endpoint LIVE no Stripe Dashboard
   ============================================================ */

window.STAFLOW_STRIPE_PRICES = {
  // ── Mensal ──────────────────────────────────────────────────
  // ⚠️  Trocar para price_LIVE_... ao virar produção
  pro:              'price_1TgyK9Cop6xCn5DqhwtPtndQ',  // StaFlow Pro      — R$ 99/mês   [TEST]
  advanced:         'price_1TgyKiCop6xCn5DqrEeTron1',  // StaFlow Advanced — R$ 159/mês  [TEST]
  scale:            'price_1TgyKRCop6xCn5DqIhYrFzJJ',  // StaFlow Scale    — R$ 279/mês  [TEST]

  // ── Anual ───────────────────────────────────────────────────
  pro_annual:       'price_1ThBNjCop6xCn5DqOHGoIutH',  // StaFlow Pro      — R$ 950/ano  [TEST]
  advanced_annual:  'price_1ThBMlCop6xCn5DqqehkpjSV',  // StaFlow Advanced — R$ 1.500/ano [TEST]
  scale_annual:     'price_1ThBNQCop6xCn5DqngA7tzCc',  // StaFlow Scale    — R$ 2.390/ano [TEST]
};

// Flag de transparência — apenas mudou para true após o switch LIVE
// (não afeta funcionamento, só permite UI mostrar selos diferentes
// em ambientes test vs prod se quiser)
window.STAFLOW_STRIPE_LIVE_MODE = false;
