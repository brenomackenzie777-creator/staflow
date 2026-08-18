"""
StaFlow — Configuração central da Crew
"""
import os
import logging
from crewai import LLM

log = logging.getLogger("staflow")


# ★ 12/08/2026 — dois dias de falha silenciosa causados por variável de
# ambiente mal colada no Railway:
#
#   SUPABASE_URL = "https://wsxpskrrzqtdoodpoofx.supabase.co
#                  ↑ uma aspa sobrando, colada no valor
#   NOTIFY_EMAIL = brenomackenzie777@gmail.com PRODUCTION_URL=https://...
#                                              ↑ outra variável grudada
#
# A primeira derrubou TODA gravação no Supabase ("Invalid URL"): o ciclo
# rodava sem dado nenhum, não salvava histórico e não respondia recado.
# A segunda fez o Resend recusar todo e-mail com HTTP 422 — por isso o
# Breno nunca recebeu relatório.
#
# Nenhuma das duas aparecia como erro de configuração: apareciam como
# erro de rede e erro de e-mail, bem longe da causa. Daqui pra frente a
# gente limpa na entrada e avisa alto no log.
def _env(nome: str, padrao: str = "") -> str:
    """Lê variável de ambiente removendo aspas e espaços acidentais."""
    bruto = os.environ.get(nome, padrao) or ""
    limpo = bruto.strip().strip('"').strip("'").strip()
    if limpo != bruto:
        log.warning("Variável %s vinha com aspas/espaços sobrando e foi "
                    "limpa automaticamente. Corrija no Railway.", nome)
    return limpo


def _env_email(nome: str, padrao: str = "") -> str:
    """Igual ao _env, mas garante UM endereço só.
    Se vier mais coisa grudada (outra variável, por exemplo), fica só a
    primeira palavra — que é o endereço."""
    valor = _env(nome, padrao)
    if valor and (" " in valor or "\t" in valor):
        primeiro = valor.split()[0]
        log.warning("Variável %s tinha conteúdo extra grudado (%r). Usando "
                    "só %r. Corrija no Railway.", nome, valor[:80], primeiro)
        valor = primeiro
    return valor

# ─── LLM ─────────────────────────────────────────────────────────
# Limites do free tier do Groq (docs oficiais):
#   llama-3.1-8b-instant     ->  6.000 tokens/min | 500.000/dia
#   llama-3.3-70b-versatile  -> 12.000 tokens/min | 100.000/dia
# O gargalo real é o limite POR MINUTO: o CrewAI reenvia toda a conversa a
# cada chamada de ferramenta, então uma única requisição passa de 6k fácil.
# O 70b dobra essa folga e ainda raciocina melhor.
haiku = LLM(
    model="openai/llama-3.3-70b-versatile",
    api_key=_env("GROQ_API_KEY"),
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
SUPABASE_URL        = _env("SUPABASE_URL")
SUPABASE_KEY        = _env("SUPABASE_SERVICE_KEY")
TAVILY_API_KEY      = _env("TAVILY_API_KEY")
GITHUB_TOKEN        = _env("GITHUB_TOKEN")
GITHUB_REPO         = _env("GITHUB_REPOSITORY", "brenomackenzie777-creator/staflow")
NOTIFY_EMAIL        = _env_email("NOTIFY_EMAIL", "brenomackenzie777@gmail.com")
RESEND_API_KEY      = _env("RESEND_API_KEY")
# ★ 09/08/2026 — o padrão era onboarding@resend.dev (endereço de teste do
# Resend). Ele só entrega pro dono da conta e cai em spam com frequência —
# foi por isso que o Breno nunca recebeu relatório nenhum. O domínio
# staflow.app.br já está verificado no Resend (é de onde saem os emails do
# produto), então os agentes agora mandam de lá.
RESEND_FROM         = _env("RESEND_FROM", "StaFlow Agentes <agentes@staflow.app.br>")
PRODUCTION_URL      = _env("PRODUCTION_URL", "https://staflow.app.br")

# ★ 18/08/2026 — canal Telegram: o Breno pediu pra conversar com o time em
# vez de só deixar recado assíncrono em /agentes.html. TELEGRAM_CHAT_ID
# identifica SÓ a conversa dele — sem isso o bot fica mudo (não manda nada
# pra ninguém, por segurança).
TELEGRAM_BOT_TOKEN  = _env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID    = _env("TELEGRAM_CHAT_ID")

# ── Aviso alto e claro se algo essencial estiver malformado ──
if not SUPABASE_URL.startswith("https://"):
    log.error("SUPABASE_URL não começa com https:// (valor tem %d chars, "
              "começa com %r). Nada será gravado no banco até corrigir "
              "essa variável no Railway.", len(SUPABASE_URL), SUPABASE_URL[:14])
if "@" not in NOTIFY_EMAIL:
    log.error("NOTIFY_EMAIL não parece um e-mail (%r). Nenhum relatório "
              "será entregue até corrigir no Railway.", NOTIFY_EMAIL[:60])

# ─── Contexto do produto ─────────────────────────────────────────
PRODUCT_CONTEXT = """
StaFlow — controle de presença para condomínios (https://staflow.app.br)
Stack: HTML/CSS/JS + Supabase + Stripe + Vercel
Planos: Starter R$0 (3 func.) | Pro R$99 (15) | Advanced R$159 (35) | Scale R$279 (100)
Design: #3B82F6 azul, #111827 fundo, fonte Inter
Público: síndicos e administradoras de condomínio no Brasil
"""
