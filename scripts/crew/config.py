"""
StaFlow — Configuração central da Crew
"""
import os
from crewai import LLM

# ─── LLM ─────────────────────────────────────────────────────────
# Gemini 2.0 Flash Lite — 1 M tokens/dia grátis (vs 100k do Groq)
haiku = LLM(
    model="openai/gemini-2.0-flash-lite",
    api_key=os.environ["GOOGLE_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    max_tokens=2048,
    temperature=0.3,
)

# ─── Variáveis de ambiente ────────────────────────────────────────
SUPABASE_URL        = os.environ["SUPABASE_URL"]
SUPABASE_KEY        = os.environ["SUPABASE_SERVICE_KEY"]
TAVILY_API_KEY      = os.environ.get("TAVILY_API_KEY", "")
GITHUB_TOKEN        = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO         = os.environ.get("GITHUB_REPOSITORY", "brenomackenzie777-creator/staflow")
NOTIFY_EMAIL        = os.environ.get("NOTIFY_EMAIL", "brenomackenzie777@gmail.com")
RESEND_API_KEY      = os.environ.get("RESEND_API_KEY", "")
PRODUCTION_URL      = os.environ.get("PRODUCTION_URL", "https://staflow.app.br")

# ─── Contexto do produto (lido por todos os agentes) ─────────────
PRODUCT_CONTEXT = """
Produto: StaFlow — controle de presença para condomínios
URL: https://staflow.app.br
Stack: HTML/CSS/JS estático + Supabase + Stripe LIVE + Vercel

Planos:
- Starter: R$0 (até 3 funcionários)
- Pro: R$99/mês (até 15)
- Advanced: R$159/mês (até 35)
- Scale: R$279/mês (até 100)

Identidade: azul #3B82F6, fundo #111827, fonte Inter
Mercado: síndicos profissionais e administradoras de condomínio no Brasil
"""
