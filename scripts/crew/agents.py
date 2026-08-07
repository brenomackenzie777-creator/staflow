"""
StaFlow — 8 Agentes do Loop Autoevolutivo

Os prompts (goal/backstory) de cada agente NÃO ficam fixos aqui — eles são
lidos de prompts.json. Isso permite que o Meta-Agente (8º agente) proponha
mudanças reais de comportamento via Pull Request, sem precisar editar código.
"""
import json
import os
from crewai import Agent
from .config import haiku, PRODUCT_CONTEXT
from .tools import (
    SupabaseMetricsTool, SupabaseWriteTool, SupabaseSmokeTestTool,
    TavilySearchTool, GitHubPRTool, UpdateMemoryTool, NotifyTool,
    ReadMemoryTool, SubAgentTool, SupabaseFeedbackTool, ReadPromptsTool,
)

supabase_metrics   = SupabaseMetricsTool()
supabase_write     = SupabaseWriteTool()
smoke_tests        = SupabaseSmokeTestTool()
tavily_search      = TavilySearchTool()
github_pr          = GitHubPRTool()
update_memory      = UpdateMemoryTool()
notify             = NotifyTool()
read_memory        = ReadMemoryTool()
create_sub_agent   = SubAgentTool()
supabase_feedback  = SupabaseFeedbackTool()
read_prompts       = ReadPromptsTool()

PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "prompts.json")

with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
    PROMPTS = json.load(f)

BASE = f"\n\nProduto:\n{PRODUCT_CONTEXT}\n\nRegra: use apenas dados reais. Nunca invente métricas."


def build_agent(key: str, tools: list) -> Agent:
    p = PROMPTS[key]
    return Agent(
        role=p["role"],
        goal=p["goal"],
        backstory=p["backstory"] + BASE,
        tools=tools,
        llm=haiku,
        verbose=True,
        allow_delegation=False,
    )


# ─── AGENTE 1: COLETOR ──────────────────────────────────────────
coletor = build_agent("coletor", [read_memory, supabase_metrics])

# ─── AGENTE 2: PESQUISADOR ──────────────────────────────────────
pesquisador = build_agent("pesquisador", [tavily_search])

# ─── AGENTE 3: ANALISTA ─────────────────────────────────────────
analista = build_agent("analista", [])

# ─── AGENTE 4: ESTRATEGISTA ─────────────────────────────────────
estrategista = build_agent("estrategista", [])

# ─── AGENTE 5: DECISOR ──────────────────────────────────────────
decisor = build_agent("decisor", [notify])

# ─── AGENTE 6: EXECUTOR ─────────────────────────────────────────
executor = build_agent("executor", [github_pr, supabase_write])

# ─── AGENTE 7: OBSERVADOR ───────────────────────────────────────
observador = build_agent("observador", [supabase_metrics, update_memory, notify])

# ─── AGENTE 8: META-AGENTE EVOLUTIVO ────────────────────────────
# Não opera o produto. Lê o histórico de decisões do Breno e propõe
# mudanças de prompt via PR — nunca se auto-modifica em produção.
meta_agente = build_agent(
    "meta_agente",
    [read_memory, supabase_feedback, read_prompts, github_pr],
)
