"""
StaFlow — 7 Agentes do Loop Autoevolutivo
"""
from crewai import Agent
from .config import haiku, PRODUCT_CONTEXT
from .tools import (
    SupabaseMetricsTool, SupabaseWriteTool, SupabaseSmokeTestTool,
    TavilySearchTool, GitHubPRTool, UpdateMemoryTool, NotifyTool,
    ReadMemoryTool, SubAgentTool,
)

supabase_metrics = SupabaseMetricsTool()
supabase_write   = SupabaseWriteTool()
smoke_tests      = SupabaseSmokeTestTool()
tavily_search    = TavilySearchTool()
github_pr        = GitHubPRTool()
update_memory    = UpdateMemoryTool()
notify           = NotifyTool()
read_memory      = ReadMemoryTool()
create_sub_agent = SubAgentTool()

BASE = f"\n\nProduto:\n{PRODUCT_CONTEXT}\n\nRegra: use apenas dados reais. Nunca invente métricas."

# ─── AGENTE 1: COLETOR ──────────────────────────────────────────
coletor = Agent(
    role="Coletor de Dados",
    goal="Ler a memória histórica e coletar métricas reais do Supabase para iniciar o ciclo.",
    backstory=(
        "Você inicia cada ciclo. Primeiro lê o histórico (CLAUDE.md), "
        "depois coleta dados reais do Supabase. "
        "Nunca avança sem ter o contexto histórico + dados atuais." + BASE
    ),
    tools=[read_memory, supabase_metrics, create_sub_agent],
    llm=haiku, verbose=True, allow_delegation=False,
)

# ─── AGENTE 2: PESQUISADOR ──────────────────────────────────────
pesquisador = Agent(
    role="Pesquisador de Mercado",
    goal="Pesquisar o mercado externo com foco nas prioridades identificadas pelo Coletor.",
    backstory=(
        "Você monitora concorrentes e tendências do mercado de condomínios. "
        "Evolui a pesquisa a cada ciclo — não repete queries já usadas." + BASE
    ),
    tools=[tavily_search, create_sub_agent],
    llm=haiku, verbose=True, allow_delegation=False,
)

# ─── AGENTE 3: ANALISTA ─────────────────────────────────────────
analista = Agent(
    role="Analista de Dados",
    goal="Cruzar dados internos e pesquisa de mercado para gerar insights acionáveis.",
    backstory=(
        "Você transforma dados brutos em insights. "
        "Compara ciclos para identificar tendências. "
        "Baseia-se apenas em dados reais." + BASE
    ),
    tools=[create_sub_agent],
    llm=haiku, verbose=True, allow_delegation=False,
)

# ─── AGENTE 4: ESTRATEGISTA ─────────────────────────────────────
estrategista = Agent(
    role="Estrategista de Crescimento",
    goal="Criar propostas concretas de melhoria baseadas na análise.",
    backstory=(
        "Você propõe melhorias práticas. Aprende com o histórico: "
        "não repete propostas rejeitadas. Máximo 3 propostas por ciclo." + BASE
    ),
    tools=[create_sub_agent],
    llm=haiku, verbose=True, allow_delegation=False,
)

# ─── AGENTE 5: DECISOR ──────────────────────────────────────────
decisor = Agent(
    role="Decisor de Prioridades",
    goal="Decidir o que executar automaticamente e o que enviar ao Breno.",
    backstory=(
        "Regra: AUTO-EXECUTAR = esforço pequeno + risco baixo (só UI/copy). "
        "APROVAR-BRENO = mudanças de banco, features novas, risco médio/alto. "
        "Máximo 2 itens AUTO-EXECUTAR por ciclo." + BASE
    ),
    tools=[notify, create_sub_agent],
    llm=haiku, verbose=True, allow_delegation=False,
)

# ─── AGENTE 6: EXECUTOR ─────────────────────────────────────────
executor = Agent(
    role="Executor de Código",
    goal="Transformar decisões AUTO-EXECUTAR em código e criar Pull Requests no GitHub.",
    backstory=(
        "Você é o engenheiro da crew. Stack: HTML/CSS/JS puro, Supabase, "
        "design com #3B82F6 azul, #111827 fundo, Inter. "
        "Branch sempre no formato 'agent/auto-YYYY-MM-DD-nome'." + BASE
    ),
    tools=[github_pr, supabase_write, create_sub_agent],
    llm=haiku, verbose=True, allow_delegation=False,
)

# ─── AGENTE 7: OBSERVADOR ───────────────────────────────────────
observador = Agent(
    role="Observador de Aprendizado",
    goal="Registrar aprendizados no CLAUDE.md e enviar resumo ao Breno.",
    backstory=(
        "Você fecha o loop. Escreve para o PRÓXIMO Coletor: "
        "métricas, ações executadas, pendências, prioridade do próximo ciclo." + BASE
    ),
    tools=[supabase_metrics, update_memory, notify, create_sub_agent],
    llm=haiku, verbose=True, allow_delegation=False,
)
