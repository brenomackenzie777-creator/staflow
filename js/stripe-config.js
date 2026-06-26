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
  pro:              'price_1TbmLwCop6xCn5DqUKsiRHO6',  // StaFlow Pro      — R$ 99/mês   [LIVE]
  advanced:         'price_1TgsOxCop6xCn5DqyTsymW19',  // StaFlow Advanced — R$ 159/mês  [LIVE]
  scale:            'price_1TbmMUCop6xCn5Dqu1HUSYyV',  // StaFlow Scale    — R$ 279/mês  [LIVE]

  // ── Anual ───────────────────────────────────────────────────
  pro_annual:       'price_1TgsT2Cop6xCn5DqPpeKRGf8',  // StaFlow Pro      — R$ 950/ano  [LIVE]
  advanced_annual:  'price_1TgsOxCop6xCn5DqmsQJmbPx',  // StaFlow Advanced — R$ 1.500/ano [LIVE]
  scale_annual:     'price_1TgsSUCop6xCn5DqhdqdYLNE',  // StaFlow Scale    — R$ 2.600/ano [LIVE]
};

// Flag de transparência — true = produção LIVE ativa
window.STAFLOW_STRIPE_LIVE_MODE = true;
