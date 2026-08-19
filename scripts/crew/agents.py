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
from .config import haiku, PRODUCT_CONTEXT, MAX_ITER
from .tools import (
    SupabaseMetricsTool, SupabaseWriteTool, SupabaseSmokeTestTool,
    TavilySearchTool, GitHubPRTool, UpdateMemoryTool, NotifyTool,
    ReadMemoryTool, SupabaseFeedbackTool, ReadPromptsTool,
    ListPromptsTool, ReadMarketContextTool,
    LerRecadosTool, ResponderRecadoTool, PanoramaNegocioTool,
    EvoluirPromptTool, HistoricoEvolucaoTool, ler_prompts_ativos,
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
listar_agentes    = ListPromptsTool()
market_context    = ReadMarketContextTool()
ler_recados       = LerRecadosTool()
responder_recado  = ResponderRecadoTool()
panorama          = PanoramaNegocioTool()
evoluir_prompt    = EvoluirPromptTool()
historico_evol    = HistoricoEvolucaoTool()

# Log verboso do CrewAI estoura o limite de 500 linhas/seg do Railway.
# Ligue com VERBOSE=1 só quando precisar depurar.
VERBOSE = os.environ.get("VERBOSE", "").strip() in ("1", "true", "True")

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
        verbose=VERBOSE,
        allow_delegation=False,
        max_iter=MAX_ITER,
    )


def build_loop_agents(loop_key: str) -> dict:
    """Constrói os 7 agentes operacionais de um loop específico."""
    prompts = _load_prompts(loop_key)

    # Contexto de mercado/concorrência só é relevante pra quem pensa em
    # posicionamento e preço — marketing e financeiro.
    coletor_tools = [read_memory, supabase_metrics, ler_recados]
    if loop_key in ("marketing", "financeiro"):
        coletor_tools.append(market_context)

    return {
        "coletor":      _build_agent(prompts, "coletor", coletor_tools),
        "pesquisador":  _build_agent(prompts, "pesquisador", [tavily_search]),
        "analista":     _build_agent(prompts, "analista", []),
        "estrategista": _build_agent(prompts, "estrategista", []),
        "decisor":      _build_agent(prompts, "decisor", [notify, responder_recado]),
        "executor":     _build_agent(prompts, "executor", [github_pr, supabase_write]),
        "observador":   _build_agent(prompts, "observador", [supabase_metrics, update_memory]),
        "relator":      _build_agent(prompts, "relator", [notify]),
    }


ORDEM_CEO = ["analista", "estrategista", "executor", "relator"]


def _prompts_ceo() -> dict:
    """Prompts do ciclo CEO, com o banco mandando e o arquivo como rede.

    ★ 12/08/2026 — os prompts passaram a viver no Supabase pra o time
    conseguir se autoevoluir: reescrever um arquivo não funcionaria, já
    que o container do Railway é descartado a cada execução. Se o banco
    estiver fora do ar, caímos no `ceo.json` — o ciclo nunca fica sem
    prompt e nunca deixa de rodar por causa disso."""
    do_arquivo = _load_prompts("ceo")
    do_banco   = ler_prompts_ativos("ceo")
    if not do_banco:
        return do_arquivo

    final = {}
    for chave, base in do_arquivo.items():
        vivo = do_banco.get(chave)
        final[chave] = {
            "role":      (vivo or {}).get("role")      or base["role"],
            "goal":      (vivo or {}).get("goal")      or base["goal"],
            "backstory": (vivo or {}).get("backstory") or base["backstory"],
        }
    return final


def build_ceo_agents() -> dict:
    """★ 10/08/2026 — a pedido do Breno: UM loop só, que enxerga a operação
    inteira e decide como CEO, em vez de 4 loops por área.

    Além de ser o que ele pediu, é o que cabe na cota: 8 agentes custavam
    ~26 mil tokens por ciclo e 4 ciclos (105 mil) nunca couberam nos 100 mil
    diários do Groq. Com 4 agentes, um ciclo custa ~13 mil — sobra folga de
    verdade pra erro, retry e execução manual."""
    prompts = _prompts_ceo()
    return {
        "analista":     _build_agent(prompts, "analista",
                                     [panorama, read_memory, market_context]),
        # ★ 19/08/2026 — o CEO ganhou market_context. Antes ele decidia
        # estratégia de aquisição com pesquisa solta na web, sem enxergar
        # quem são os concorrentes nem onde a StaFlow ganha deles. Sem
        # esse contexto, a tendência é propor marketing genérico de SaaS
        # em vez de usar a vantagem real (ponto feito pra condomínio).
        "estrategista": _build_agent(prompts, "estrategista",
                                     [tavily_search, market_context]),
        # O Executor é quem fecha o ciclo — e também quem ajusta o time.
        # Ferramentas de autoevolução ficam com ele porque é ele que viu o
        # ciclo inteiro acontecer e sabe onde emperrou.
        "executor":     _build_agent(prompts, "executor",
                                     [github_pr, supabase_write, responder_recado,
                                      update_memory, historico_evol, evoluir_prompt]),
        "relator":      _build_agent(prompts, "relator", [notify]),
    }


def _load_meta_prompts() -> dict:
    path = os.path.join(PROMPTS_DIR, "meta.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_meta_agent() -> Agent:
    """Meta-Agente Evolutivo — compartilhado entre os 4 loops."""
    p = _load_meta_prompts()["meta_agente"]
    return Agent(
        role=p["role"],
        goal=p["goal"],
        backstory=p["backstory"] + BASE,
        tools=[read_memory, supabase_feedback, listar_agentes,
               read_prompts, github_pr],
        llm=haiku,
        verbose=VERBOSE,
        allow_delegation=False,
        max_iter=MAX_ITER,
    )


def build_meta_relator() -> Agent:
    """Relator semanal — fecha a sexta-feira com o resumo da semana."""
    p = _load_meta_prompts()["relator"]
    return Agent(
        role=p["role"],
        goal=p["goal"],
        backstory=p["backstory"] + BASE,
        tools=[read_memory, supabase_metrics, notify],
        llm=haiku,
        verbose=VERBOSE,
        allow_delegation=False,
        max_iter=MAX_ITER,
    )
