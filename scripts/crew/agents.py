"""
StaFlow — Agentes especializados por loop de negócio

Cada loop (marketing, produto, financeiro, suporte) tem seu próprio conjunto
de 7 agentes, com prompts carregados de scripts/crew/prompts/<loop>.json.
O Meta-Agente Evolutivo é compartilhado entre todos os loops e lê
scripts/crew/prompts/meta.json.
"""
import json
import os
from crewai import Agent
from .config import haiku, PRODUCT_CONTEXT
from .tools import (
    SupabaseMetricsTool, SupabaseWriteTool, SupabaseSmokeTestTool,
    TavilySearchTool, GitHubPRTool, UpdateMemoryTool, NotifyTool,
    ReadMemoryTool, SupabaseFeedbackTool, ReadPromptsTool,
)

supabase_metrics  = SupabaseMetricsTool()
supabase_write    = SupabaseWriteTool()
smoke_tests       = SupabaseSmokeTestTool()
tavily_search     = TavilySearchTool()
github_pr         = GitHubPRTool()
update_memory     = UpdateMemoryTool()
notify            = NotifyTool()
read_memory       = ReadMemoryTool()
supabase_feedback = SupabaseFeedbackTool()
read_prompts      = ReadPromptsTool()

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
BASE = f"\n\nProduto:\n{PRODUCT_CONTEXT}\n\nRegra: use apenas dados reais. Nunca invente métricas."

LOOPS = ["marketing", "produto", "financeiro", "suporte"]


def _load_prompts(loop_key: str) -> dict:
    path = os.path.join(PROMPTS_DIR, f"{loop_key}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_agent(prompts: dict, key: str, tools: list) -> Agent:
    p = prompts[key]
    return Agent(
        role=p["role"],
        goal=p["goal"],
        backstory=p["backstory"] + BASE,
        tools=tools,
        llm=haiku,
        verbose=True,
        allow_delegation=False,
    )


def build_loop_agents(loop_key: str) -> dict:
    """Constrói os 7 agentes operacionais de um loop específico."""
    prompts = _load_prompts(loop_key)
    return {
        "coletor":      _build_agent(prompts, "coletor", [read_memory, supabase_metrics]),
        "pesquisador":  _build_agent(prompts, "pesquisador", [tavily_search]),
        "analista":     _build_agent(prompts, "analista", []),
        "estrategista": _build_agent(prompts, "estrategista", []),
        "decisor":      _build_agent(prompts, "decisor", [notify]),
        "executor":     _build_agent(prompts, "executor", [github_pr, supabase_write]),
        "observador":   _build_agent(prompts, "observador", [supabase_metrics, update_memory, notify]),
    }


def build_meta_agent() -> Agent:
    """Meta-Agente Evolutivo — compartilhado entre os 4 loops."""
    path = os.path.join(PROMPTS_DIR, "meta.json")
    with open(path, "r", encoding="utf-8") as f:
        p = json.load(f)["meta_agente"]
    return Agent(
        role=p["role"],
        goal=p["goal"],
        backstory=p["backstory"] + BASE,
        tools=[read_memory, supabase_feedback, read_prompts, github_pr],
        llm=haiku,
        verbose=True,
        allow_delegation=False,
    )
