#!/usr/bin/env bash
# ============================================================
# StaFlow — Deploy automatizado das Edge Functions Stripe
# ------------------------------------------------------------
# Preenche os placeholders abaixo e rode:
#   bash deploy-stripe.sh
#
# Pré-requisitos:
#   - Supabase CLI instalado: npm i -g supabase
#   - Login feito:            supabase login
# ============================================================

set -euo pipefail

# ──────────────────────────────────────────────────────────────
# 1) PREENCHA OS PLACEHOLDERS ABAIXO
# ──────────────────────────────────────────────────────────────
PROJECT_REF="wsxpskrrzqtdoodpoofx"

STRIPE_SECRET_KEY="sk_test_REPLACE_ME"            # Stripe → Developers → API keys
STRIPE_WEBHOOK_SECRET="whsec_REPLACE_ME"          # Stripe → Developers → Webhooks → seu endpoint → Signing secret
STRIPE_PRICE_PRO="price_REPLACE_ME_PRO"           # Stripe → Products → Pro   → Pricing → API ID
STRIPE_PRICE_SCALE="price_REPLACE_ME_SCALE"       # Stripe → Products → Scale → Pricing → API ID

# ──────────────────────────────────────────────────────────────
# 2) Sanidade
# ──────────────────────────────────────────────────────────────
echo "▶ Verificando Supabase CLI…"
command -v supabase >/dev/null 2>&1 || {
  echo "✗ Supabase CLI não encontrado. Instale com: npm i -g supabase"
  exit 1
}

for var in STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET STRIPE_PRICE_PRO STRIPE_PRICE_SCALE; do
  val="${!var}"
  if [[ "$val" == *"REPLACE_ME"* ]]; then
    echo "✗ $var ainda contém placeholder. Edite este arquivo antes de rodar."
    exit 1
  fi
done

# ──────────────────────────────────────────────────────────────
# 3) Link do projeto
# ──────────────────────────────────────────────────────────────
echo "▶ Linkando projeto $PROJECT_REF…"
supabase link --project-ref "$PROJECT_REF"

# ──────────────────────────────────────────────────────────────
# 4) Secrets nas Edge Functions
# ──────────────────────────────────────────────────────────────
echo "▶ Definindo secrets…"
supabase secrets set \
  STRIPE_SECRET_KEY="$STRIPE_SECRET_KEY" \
  STRIPE_WEBHOOK_SECRET="$STRIPE_WEBHOOK_SECRET" \
  STRIPE_PRICE_PRO="$STRIPE_PRICE_PRO" \
  STRIPE_PRICE_SCALE="$STRIPE_PRICE_SCALE"

# ──────────────────────────────────────────────────────────────
# 5) Deploy das duas funções
# ──────────────────────────────────────────────────────────────
echo "▶ Deploy create-checkout-session…"
supabase functions deploy create-checkout-session

echo "▶ Deploy stripe-webhook…"
supabase functions deploy stripe-webhook

# ──────────────────────────────────────────────────────────────
echo ""
echo "✓ Deploy concluído!"
echo ""
echo "Próximos passos:"
echo "  1. No Stripe Dashboard → Developers → Webhooks → Add endpoint"
echo "     URL: https://${PROJECT_REF}.supabase.co/functions/v1/stripe-webhook"
echo "     Eventos: customer.subscription.created"
echo "              customer.subscription.updated"
echo "              customer.subscription.deleted"
echo "              invoice.payment_failed"
echo "  2. Copie o NOVO Signing secret e re-rode este script com o valor atualizado."
echo "  3. Preencha js/stripe-config.js com os mesmos price IDs."
