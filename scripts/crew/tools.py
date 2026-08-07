"""
StaFlow — Ferramentas customizadas para a Crew
"""
import os
import json
import datetime
import httpx
from crewai.tools import BaseTool
from supabase import create_client
from tavily import TavilyClient
from github import Github

from .config import SUPABASE_URL, SUPABASE_KEY, TAVILY_API_KEY, GITHUB_TOKEN, GITHUB_REPO, PRODUCTION_URL


# ─── Memória ─────────────────────────────────────────────────────

class ReadMemoryTool(BaseTool):
    name: str = "read_memory"
    description: str = (
        "Lê o CLAUDE.md — memória compartilhada de todos os ciclos anteriores. "
        "Use no início da sua tarefa para entender o histórico do produto, "
        "o que foi tentado antes, o que funcionou e as prioridades do próximo ciclo."
    )

    def _run(self, input: str = "") -> str:
        claude_md = os.path.join(os.path.dirname(__file__), "..", "..", "CLAUDE.md")
        try:
            with open(claude_md, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Sem memória prévia disponível: {e}"


class UpdateMemoryTool(BaseTool):
    name: str = "update_memory"
    description: str = (
        "Atualiza o CLAUDE.md com os aprendizados do ciclo atual. "
        "Escreva de forma útil para o próximo ciclo — este texto será lido "
        "pelo Coletor na próxima execução. Input: string com o conteúdo."
    )

    def _run(self, content: str) -> str:
        claude_md = os.path.join(os.path.dirname(__file__), "..", "..", "CLAUDE.md")
        try:
            with open(claude_md, "r", encoding="utf-8") as f:
                atual = f.read()

            hoje      = datetime.date.today().isoformat()
            nova_linha = f"\n## [{hoje}] Loop automático\n{content}\n"
            novo      = atual + nova_linha

            # Mantém últimas 30 entradas
            partes = novo.split("\n## [")
            if len(partes) > 31:
                partes = partes[:1] + partes[-30:]
            novo = "\n## [".join(partes)

            with open(claude_md, "w", encoding="utf-8") as f:
                f.write(novo)
            return "CLAUDE.md atualizado com sucesso."
        except Exception as e:
            return f"Erro ao atualizar CLAUDE.md: {e}"


# ─── Sub-agente ──────────────────────────────────────────────────

class SubAgentTool(BaseTool):
    name: str = "create_sub_agent"
    description: str = (
        "Cria e executa um sub-agente especializado para uma tarefa específica. "
        "Use quando sua tarefa principal exigir especialização extra que você não tem. "
        "Input: JSON com 'role' (papel), 'goal' (objetivo) e 'task' (tarefa detalhada)."
    )

    def _run(self, role: str, goal: str, task: str) -> str:
        from crewai import Agent, Task, Crew, Process
        from .config import haiku

        try:
            sub_agent = Agent(
                role=role,
                goal=goal,
                backstory=(
                    f"Você é um sub-agente especializado criado para: {goal}. "
                    "Execute com precisão e retorne um resultado detalhado e acionável."
                ),
                llm=haiku,
                verbose=False,
                allow_delegation=False,
            )

            sub_task = Task(
                description=task,
                expected_output="Resultado detalhado e acionável da tarefa especializada.",
                agent=sub_agent,
            )

            sub_crew = Crew(
                agents=[sub_agent],
                tasks=[sub_task],
                process=Process.sequential,
                verbose=False,
                memory=False,
            )

            result = sub_crew.kickoff()
            return f"Sub-agente '{role}' concluiu:\n{str(result)}"
        except Exception as e:
            return f"Erro ao criar sub-agente: {e}"


# ─── Supabase ────────────────────────────────────────────────────

class SupabaseMetricsTool(BaseTool):
    name: str = "supabase_metrics"
    description: str = (
        "Lê métricas reais do StaFlow no Supabase: cadastros, assinaturas, "
        "feedbacks, conversão. Use para coletar dados antes de analisar."
    )

    def _run(self, input: str = "") -> str:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        try:
            usuarios     = sb.table("profiles").select("id,created_at,role", count="exact").execute()
            assinaturas  = sb.table("subscriptions").select("id,plan,status", count="exact").eq("status", "active").execute()
            feedbacks    = sb.table("feedback").select("mensagem,tipo,created_at").order("created_at", desc=True).limit(10).execute()
            agent_runs   = sb.table("agent_runs").select("agent_name,status,output_summary,feedback_breno").order("created_at", desc=True).limit(20).execute()

            semana_atras = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat()
            novos        = sb.table("profiles").select("id", count="exact").gte("created_at", semana_atras).execute()

            return json.dumps({
                "total_usuarios":       usuarios.count or 0,
                "novos_esta_semana":    novos.count or 0,
                "assinaturas_ativas":   assinaturas.count or 0,
                "planos_ativos":        [r["plan"] for r in (assinaturas.data or [])],
                "feedbacks_recentes":   feedbacks.data or [],
                "historico_agentes":    agent_runs.data or [],
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Erro ao ler Supabase: {e}"


class SupabaseWriteTool(BaseTool):
    name: str = "supabase_write_agent_run"
    description: str = (
        "Salva o resultado de uma execução do agente no Supabase (tabela agent_runs). "
        "Parâmetros: agent_name (nome do agente), output_summary (resumo curto), "
        "output_completo (output completo em texto)."
    )

    def _run(self, agent_name: str, output_summary: str, output_completo: str = "") -> str:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        try:
            payload = {
                "agent_name":      agent_name,
                "output_summary":  output_summary,
                "output_completo": output_completo,
                "created_at":      datetime.datetime.utcnow().isoformat(),
                "status":          "pending",
            }
            res = sb.table("agent_runs").insert(payload).execute()
            return f"Salvo com ID: {res.data[0]['id']}"
        except Exception as e:
            return f"Erro ao salvar: {e}"


class SupabaseSmokeTestTool(BaseTool):
    name: str = "smoke_tests"
    description: str = "Roda smoke tests HTTP em produção e retorna status de cada página."

    def _run(self, input: str = "") -> str:
        paginas = [
            "/", "/staflow-landing.html", "/auth/login.html",
            "/auth/cadastro.html", "/planos.html", "/dashboard.html",
            "/colaborador.html", "/service-worker.js", "/manifest.json",
        ]
        resultados = []
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            for p in paginas:
                url = PRODUCTION_URL + p
                try:
                    r   = client.get(url)
                    ok  = "✅" if r.status_code < 400 else "❌"
                    resultados.append(f"{ok} {r.status_code} — {url}")
                except Exception as e:
                    resultados.append(f"❌ ERRO — {url} ({e})")
        return "\n".join(resultados)


# ─── Tavily Search ───────────────────────────────────────────────

class TavilySearchTool(BaseTool):
    name: str = "tavily_search"
    description: str = (
        "Pesquisa na web usando Tavily. Use para buscar notícias sobre concorrentes, "
        "tendências de mercado de condomínios, regulações, e novidades do setor. "
        "Input: string com a query de busca."
    )

    def _run(self, query: str) -> str:
        try:
            client  = TavilyClient(api_key=TAVILY_API_KEY)
            results = client.search(query=query, max_results=5, search_depth="basic")
            output  = []
            for r in results.get("results", []):
                output.append(f"**{r['title']}**\n{r['url']}\n{r.get('content', '')[:300]}\n")
            return "\n---\n".join(output) or "Sem resultados."
        except Exception as e:
            return f"Erro na busca: {e}"


# ─── GitHub PR ───────────────────────────────────────────────────

class GitHubPRTool(BaseTool):
    name: str = "create_github_pr"
    description: str = (
        "Cria um Pull Request no GitHub com mudanças de código propostas. "
        "Parâmetros: title (título do PR), body (descrição do que muda e como testar), "
        "branch (nome do branch, ex: agent/auto-2026-08-07-nome), "
        "files (JSON string com dict filename→content dos arquivos a criar/atualizar)."
    )

    def _run(self, title: str, body: str, branch: str = "", files: str = "{}") -> str:
        if not GITHUB_TOKEN:
            return "GITHUB_TOKEN não configurado — PR não criado."
        try:
            files_dict = json.loads(files) if isinstance(files, str) else files
            g          = Github(GITHUB_TOKEN)
            repo       = g.get_repo(GITHUB_REPO)
            main_sha   = repo.get_branch("main").commit.sha

            if not branch:
                branch = f"agent/auto-{datetime.date.today().isoformat()}"
            repo.create_git_ref(ref=f"refs/heads/{branch}", sha=main_sha)

            for filename, content in files_dict.items():
                try:
                    existing = repo.get_contents(filename, ref=branch)
                    repo.update_file(filename, f"agent: update {filename}", content, existing.sha, branch=branch)
                except Exception:
                    repo.create_file(filename, f"agent: create {filename}", content, branch=branch)

            pr = repo.create_pull(
                title=title,
                body=body,
                head=branch,
                base="main",
            )
            return f"PR criado: {pr.html_url}"
        except Exception as e:
            return f"Erro ao criar PR: {e}"


# ─── Notificação Email ───────────────────────────────────────────

class NotifyTool(BaseTool):
    name: str = "notify_breno"
    description: str = (
        "Envia email de notificação para o Breno via Resend. "
        "Parâmetros: subject (assunto do email), html_body (corpo em HTML)."
    )

    def _run(self, subject: str, html_body: str) -> str:
        resend_key   = os.environ.get("RESEND_API_KEY", "")
        notify_email = os.environ.get("NOTIFY_EMAIL", "brenomackenzie777@gmail.com")
        if not resend_key:
            return "RESEND_API_KEY não configurado — email não enviado."
        try:
            httpx.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
                json={
                    "from":    "agentes@staflow.app.br",
                    "to":      [notify_email],
                    "subject": subject,
                    "html":    html_body,
                },
                timeout=10,
            )
            return f"Email enviado para {notify_email}"
        except Exception as e:
            return f"Erro ao notificar: {e}"
