"""
StaFlow — Ferramentas dos agentes
Todas as tools usam parâmetros explícitos (sem JSON embutido em string).
"""
import os
import json
import datetime
import httpx
from crewai.tools import BaseTool
from supabase import create_client
from tavily import TavilyClient
from github import Github

from .config import (
    SUPABASE_URL, SUPABASE_KEY, TAVILY_API_KEY,
    GITHUB_TOKEN, GITHUB_REPO, PRODUCTION_URL,
)


# ─── Memória ─────────────────────────────────────────────────────

class ReadMemoryTool(BaseTool):
    name: str = "read_memory"
    description: str = (
        "Lê o CLAUDE.md com o histórico de ciclos anteriores. "
        "Use no início de cada tarefa para entender o contexto."
    )

    def _run(self, input: str = "") -> str:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "CLAUDE.md")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Sem memória prévia: {e}"


class UpdateMemoryTool(BaseTool):
    name: str = "update_memory"
    description: str = (
        "Salva aprendizados no CLAUDE.md para o próximo ciclo. "
        "Parâmetro: content (texto com resumo do ciclo atual)."
    )

    def _run(self, content: str) -> str:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "CLAUDE.md")
        try:
            with open(path, "r", encoding="utf-8") as f:
                atual = f.read()
            hoje = datetime.date.today().isoformat()
            novo = atual + f"\n\n## [{hoje}] Ciclo automático\n{content}\n"
            partes = novo.split("\n\n## [")
            if len(partes) > 31:
                partes = partes[:1] + partes[-30:]
            novo = "\n\n## [".join(partes)
            with open(path, "w", encoding="utf-8") as f:
                f.write(novo)
            return "CLAUDE.md atualizado."
        except Exception as e:
            return f"Erro ao atualizar CLAUDE.md: {e}"


# ─── Sub-agente ──────────────────────────────────────────────────

class SubAgentTool(BaseTool):
    name: str = "create_sub_agent"
    description: str = (
        "Cria e executa um sub-agente especializado. "
        "Parâmetros: role (papel), goal (objetivo), task (tarefa detalhada)."
    )

    def _run(self, role: str, goal: str, task: str) -> str:
        from crewai import Agent, Task, Crew, Process
        from .config import haiku
        try:
            agent = Agent(
                role=role, goal=goal,
                backstory=f"Sub-agente especializado: {goal}",
                llm=haiku, verbose=False, allow_delegation=False,
            )
            t = Task(
                description=task,
                expected_output="Resultado detalhado e acionável.",
                agent=agent,
            )
            crew = Crew(agents=[agent], tasks=[t], process=Process.sequential,
                        verbose=False, memory=False)
            result = crew.kickoff()
            return f"Sub-agente '{role}':\n{str(result)}"
        except Exception as e:
            return f"Erro no sub-agente: {e}"


# ─── Supabase ────────────────────────────────────────────────────

class SupabaseMetricsTool(BaseTool):
    name: str = "supabase_metrics"
    description: str = "Lê métricas reais do StaFlow: usuários, assinaturas, feedbacks."

    def _run(self, input: str = "") -> str:
        try:
            sb = create_client(SUPABASE_URL, SUPABASE_KEY)
            usuarios    = sb.table("profiles").select("id,created_at,role", count="exact").execute()
            assinaturas = sb.table("subscriptions").select("id,plan,status", count="exact").eq("status", "active").execute()
            feedbacks   = sb.table("feedback").select("mensagem,tipo,created_at").order("created_at", desc=True).limit(5).execute()
            semana      = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat()
            novos       = sb.table("profiles").select("id", count="exact").gte("created_at", semana).execute()
            runs        = sb.table("agent_runs").select("agent_name,status,output_summary").order("created_at", desc=True).limit(10).execute()
            return json.dumps({
                "total_usuarios":     usuarios.count or 0,
                "novos_semana":       novos.count or 0,
                "assinaturas_ativas": assinaturas.count or 0,
                "planos":             [r["plan"] for r in (assinaturas.data or [])],
                "feedbacks":          feedbacks.data or [],
                "ultimas_execucoes":  runs.data or [],
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Erro Supabase: {e}"


class SupabaseWriteTool(BaseTool):
    name: str = "supabase_write_agent_run"
    description: str = (
        "Salva o resultado de um agente no Supabase. "
        "Parâmetros: agent_name, output_summary, output_completo."
    )

    def _run(self, agent_name: str, output_summary: str, output_completo: str = "") -> str:
        try:
            sb = create_client(SUPABASE_URL, SUPABASE_KEY)
            res = sb.table("agent_runs").insert({
                "agent_name":      agent_name,
                "output_summary":  output_summary,
                "output_completo": output_completo,
                "status":          "pending",
                "created_at":      datetime.datetime.utcnow().isoformat(),
            }).execute()
            return f"Salvo: {res.data[0]['id']}"
        except Exception as e:
            return f"Erro ao salvar: {e}"


class SupabaseSmokeTestTool(BaseTool):
    name: str = "smoke_tests"
    description: str = "Roda testes HTTP nas páginas principais do StaFlow em produção."

    def _run(self, input: str = "") -> str:
        paginas = ["/", "/staflow-landing.html", "/auth/login.html",
                   "/auth/cadastro.html", "/planos.html", "/dashboard.html"]
        resultados = []
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            for p in paginas:
                url = PRODUCTION_URL + p
                try:
                    r  = client.get(url)
                    ok = "✅" if r.status_code < 400 else "❌"
                    resultados.append(f"{ok} {r.status_code} {url}")
                except Exception as e:
                    resultados.append(f"❌ ERRO {url}: {e}")
        return "\n".join(resultados)


# ─── Tavily ──────────────────────────────────────────────────────

class TavilySearchTool(BaseTool):
    name: str = "tavily_search"
    description: str = "Pesquisa na web. Parâmetro: query (string de busca)."

    def _run(self, query: str) -> str:
        if not TAVILY_API_KEY:
            return "TAVILY_API_KEY não configurado."
        try:
            client  = TavilyClient(api_key=TAVILY_API_KEY)
            results = client.search(query=query, max_results=5, search_depth="basic")
            saida   = []
            for r in results.get("results", []):
                saida.append(f"**{r['title']}**\n{r['url']}\n{r.get('content','')[:200]}")
            return "\n---\n".join(saida) or "Sem resultados."
        except Exception as e:
            return f"Erro Tavily: {e}"


# ─── GitHub ──────────────────────────────────────────────────────

class GitHubPRTool(BaseTool):
    name: str = "create_github_pr"
    description: str = (
        "Cria um Pull Request no GitHub. "
        "Parâmetros: title, body, branch, files (JSON string de filename→conteúdo)."
    )

    def _run(self, title: str, body: str, branch: str = "", files: str = "{}") -> str:
        if not GITHUB_TOKEN:
            return "GITHUB_TOKEN não configurado."
        try:
            files_dict = json.loads(files) if isinstance(files, str) else files
            g        = Github(GITHUB_TOKEN)
            repo     = g.get_repo(GITHUB_REPO)
            sha      = repo.get_branch("main").commit.sha
            if not branch:
                branch = f"agent/auto-{datetime.date.today().isoformat()}"
            repo.create_git_ref(ref=f"refs/heads/{branch}", sha=sha)
            for fname, content in files_dict.items():
                try:
                    ex = repo.get_contents(fname, ref=branch)
                    repo.update_file(fname, f"agent: update {fname}", content, ex.sha, branch=branch)
                except Exception:
                    repo.create_file(fname, f"agent: create {fname}", content, branch=branch)
            pr = repo.create_pull(title=title, body=body, head=branch, base="main")
            return f"PR criado: {pr.html_url}"
        except Exception as e:
            return f"Erro PR: {e}"


# ─── Email ───────────────────────────────────────────────────────

class NotifyTool(BaseTool):
    name: str = "notify_breno"
    description: str = (
        "Envia email para o Breno via Resend. "
        "Parâmetros: subject (assunto), html_body (corpo em HTML)."
    )

    def _run(self, subject: str, html_body: str) -> str:
        if not RESEND_API_KEY:
            return "RESEND_API_KEY não configurado — email não enviado."
        try:
            httpx.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}",
                         "Content-Type": "application/json"},
                json={"from": "agentes@staflow.app.br",
                      "to": [NOTIFY_EMAIL],
                      "subject": subject,
                      "html": html_body},
                timeout=10,
            )
            return f"Email enviado para {NOTIFY_EMAIL}"
        except Exception as e:
            return f"Erro email: {e}"
