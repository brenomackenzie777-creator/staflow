# ============================================================
# StaFlow — Deploy automatizado das Edge Functions Stripe (Windows)
# ------------------------------------------------------------
# Preencha os placeholders abaixo e rode no PowerShell:
#   .\deploy-stripe.ps1
#
# Pré-requisitos:
#   - Supabase CLI:        npm i -g supabase
#   - Login feito:         supabase login   (ou SUPABASE_ACCESS_TOKEN env)
#   - Bash não:            este é template Windows
# ============================================================
#
# 🛡️  SEGURANÇA — LEIA ANTES DE EDITAR
# ─────────────────────────────────────────────────────────────
# Este arquivo é o TEMPLATE versionado (commitado no git).
# NUNCA preencha secrets reais aqui — copie para a versão
# `.local.ps1` (coberta pelo .gitignore) e preencha lá.
#
#   Copy-Item deploy-stripe.ps1 deploy-stripe.local.ps1
#   notepad deploy-stripe.local.ps1   # preencher secrets reais
#   .\deploy-stripe.local.ps1
#
# ─────────────────────────────────────────────────────────────
# 🚦 TEST MODE vs LIVE MODE — como virar a chave
# ─────────────────────────────────────────────────────────────
# 1) Stripe Dashboard → toggle 'View test data' OFF (canto inf. esq.)
# 2) Products → criar Pro (R$ 99) e Scale (R$ 249) novamente em LIVE
# 3) Developers → API keys → revele 'sk_live_...'
# 4) Developers → Webhooks → Add endpoint LIVE:
#    URL:  https://wsxpskrrzqtdoodpoofx.supabase.co/functions/v1/stripe-webhook
#    Eventos:
#      - checkout.session.completed
#      - customer.subscription.created
#      - customer.subscription.updated
#      - customer.subscription.deleted
#      - invoice.paid
#      - invoice.payment_failed
#    Copie o 'whsec_...' do Signing secret
# 5) Substitua os valores abaixo por sk_live_ / whsec_ / price_LIVE_
# 6) Rode este script
# 7) Atualize js/stripe-config.js com os mesmos price IDs LIVE
# ============================================================

$ErrorActionPreference = "Stop"

# ──────────────────────────────────────────────────────────────
# 1) PREENCHA OS PLACEHOLDERS ABAIXO
# ──────────────────────────────────────────────────────────────
$PROJECT_REF           = "wsxpskrrzqtdoodpoofx"

# 🧪 TEST MODE  → sk_test_... / whsec_... / price_TEST_...
# 🚀 LIVE MODE  → sk_live_... / whsec_LIVE_... / price_LIVE_...
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

# Detecta TEST vs LIVE pelo prefixo da chave
$mode = if ($STRIPE_SECRET_KEY.StartsWith("sk_live_")) { "🚀 LIVE MODE (PRODUCAO)" } else { "🧪 TEST MODE" }
Write-Host "`nModo detectado: $mode" -ForegroundColor Yellow

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
Write-Host "Deploy concluido! Modo: $mode" -ForegroundColor Green
Write-Host ""
Write-Host "Checklist pos-deploy:"
Write-Host "  1. Webhook endpoint configurado em Stripe Dashboard?"
Write-Host "     URL: https://$PROJECT_REF.supabase.co/functions/v1/stripe-webhook"
Write-Host "     Eventos: checkout.session.completed + customer.subscription.*"
Write-Host "              + invoice.paid + invoice.payment_failed"
Write-Host "  2. js/stripe-config.js atualizado com os mesmos price IDs?"
Write-Host "  3. Teste com Stripe CLI: stripe trigger checkout.session.completed"
