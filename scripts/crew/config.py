"""
StaFlow — Configuração central da Crew
"""
import os
from crewai import LLM

# ─── LLM ─────────────────────────────────────────────────────────
# Limites do free tier do Groq (docs oficiais):
#   llama-3.1-8b-instant     ->  6.000 tokens/min | 500.000/dia
#   llama-3.3-70b-versatile  -> 12.000 tokens/min | 100.000/dia
# O gargalo real é o limite POR MINUTO: o CrewAI reenvia toda a conversa a
# cada chamada de ferramenta, então uma única requisição passa de 6k fácil.
# O 70b dobra essa folga e ainda raciocina melhor.
haiku = LLM(
    model="openai/llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
    max_tokens=1200,
    temperature=0.3,
)

# Teto de rodadas de ferramenta por agente. Cada rodada acumula na conversa,
# e é isso que estoura o limite por minuto. 4 é suficiente: nenhum agente
# tem mais de 4 ferramentas.
MAX_ITER = int(os.environ.get("MAX_ITER", "4"))

# RPM do free tier é 30. 20 deixa margem e evita rajadas.
MAX_RPM = int(os.environ.get("MAX_RPM", "20"))

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
