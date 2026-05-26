# ============================================================
# StaFlow — Deploy automatizado das Edge Functions Stripe (Windows)
# ------------------------------------------------------------
# Preencha os placeholders abaixo e rode no PowerShell:
#   .\deploy-stripe.ps1
#
# Pré-requisitos:
#   - Supabase CLI:  npm i -g supabase
#   - Login feito:   supabase login
# ============================================================

$ErrorActionPreference = "Stop"

# ──────────────────────────────────────────────────────────────
# 1) PREENCHA OS PLACEHOLDERS ABAIXO
# ──────────────────────────────────────────────────────────────
$PROJECT_REF           = "wsxpskrrzqtdoodpoofx"

$STRIPE_SECRET_KEY     = "sk_test_REPLACE_ME"        # Stripe → Developers → API keys
$STRIPE_WEBHOOK_SECRET = "whsec_REPLACE_ME"          # Stripe → Developers → Webhooks → Signing secret
$STRIPE_PRICE_PRO      = "price_REPLACE_ME_PRO"      # Stripe → Products → Pro   → Pricing → API ID
$STRIPE_PRICE_SCALE    = "price_REPLACE_ME_SCALE"    # Stripe → Products → Scale → Pricing → API ID

# ──────────────────────────────────────────────────────────────
# 2) Sanidade
# ──────────────────────────────────────────────────────────────
Write-Host "Verificando Supabase CLI..." -ForegroundColor Cyan
if (-not (Get-Command supabase -ErrorAction SilentlyContinue)) {
  Write-Host "Supabase CLI nao encontrado. Instale com: npm i -g supabase" -ForegroundColor Red
  exit 1
}

$vars = @{
  "STRIPE_SECRET_KEY"     = $STRIPE_SECRET_KEY
  "STRIPE_WEBHOOK_SECRET" = $STRIPE_WEBHOOK_SECRET
  "STRIPE_PRICE_PRO"      = $STRIPE_PRICE_PRO
  "STRIPE_PRICE_SCALE"    = $STRIPE_PRICE_SCALE
}
foreach ($k in $vars.Keys) {
  if ($vars[$k] -like "*REPLACE_ME*") {
    Write-Host "$k ainda contem placeholder. Edite este arquivo antes de rodar." -ForegroundColor Red
    exit 1
  }
}

# ──────────────────────────────────────────────────────────────
# 3) Link do projeto
# ──────────────────────────────────────────────────────────────
Write-Host "Linkando projeto $PROJECT_REF..." -ForegroundColor Cyan
supabase link --project-ref $PROJECT_REF
if (-not $?) { exit 1 }

# ──────────────────────────────────────────────────────────────
# 4) Secrets nas Edge Functions
# ──────────────────────────────────────────────────────────────
Write-Host "Definindo secrets..." -ForegroundColor Cyan
supabase secrets set `
  "STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY" `
  "STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK_SECRET" `
  "STRIPE_PRICE_PRO=$STRIPE_PRICE_PRO" `
  "STRIPE_PRICE_SCALE=$STRIPE_PRICE_SCALE"
if (-not $?) { exit 1 }

# ──────────────────────────────────────────────────────────────
# 5) Deploy das duas funcoes
# ──────────────────────────────────────────────────────────────
Write-Host "Deploy create-checkout-session..." -ForegroundColor Cyan
supabase functions deploy create-checkout-session
if (-not $?) { exit 1 }

Write-Host "Deploy stripe-webhook..." -ForegroundColor Cyan
supabase functions deploy stripe-webhook
if (-not $?) { exit 1 }

# ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Deploy concluido!" -ForegroundColor Green
Write-Host ""
Write-Host "Proximos passos:"
Write-Host "  1. No Stripe Dashboard -> Developers -> Webhooks -> Add endpoint"
Write-Host "     URL: https://$PROJECT_REF.supabase.co/functions/v1/stripe-webhook"
Write-Host "     Eventos: customer.subscription.created"
Write-Host "              customer.subscription.updated"
Write-Host "              customer.subscription.deleted"
Write-Host "              invoice.payment_failed"
Write-Host "  2. Copie o NOVO Signing secret e re-rode este script com o valor atualizado."
Write-Host "  3. Preencha js/stripe-config.js com os mesmos price IDs."
