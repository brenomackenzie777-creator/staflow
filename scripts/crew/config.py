"""
StaFlow — Configuração central da Crew
"""
import os
from crewai import LLM

# ─── LLM ─────────────────────────────────────────────────────────
# Groq llama-3.1-8b-instant — free tier 500k tokens/dia (vs 100k do 70b)
haiku = LLM(
    model="openai/llama-3.1-8b-instant",
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
    max_tokens=1200,
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
# onboarding@resend.dev funciona sem verificar domínio — troque para
# agentes@staflow.app.br só depois de verificar o domínio no Resend.
RESEND_FROM         = os.environ.get("RESEND_FROM", "onboarding@resend.dev")
PRODUCTION_URL      = os.environ.get("PRODUCTION_URL", "https://staflow.app.br")

# ─── Contexto do produto ─────────────────────────────────────────
PRODUCT_CONTEXT = """
StaFlow — controle de presença para condomínios (https://staflow.app.br)
Stack: HTML/CSS/JS + Supabase + Stripe + Vercel
Planos: Starter R$0 (3 func.) | Pro R$99 (15) | Advanced R$159 (35) | Scale R$279 (100)
Design: #3B82F6 azul, #111827 fundo, fonte Inter
Público: síndicos e administradoras de condomínio no Brasil
"""
