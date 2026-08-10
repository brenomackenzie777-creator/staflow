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
    RESEND_API_KEY, NOTIFY_EMAIL, RESEND_FROM,
)


# ─── Memória ─────────────────────────────────────────────────────

# O free tier do Groq aceita no máximo 6.000 tokens por minuto (~24.000
# caracteres). Ferramentas que leem arquivos precisam de teto, senão a
# memória cresce e derruba o ciclo com erro 413.
LIMITE_MEMORIA = 6000     # caracteres do CLAUDE.md
LIMITE_PROMPTS = 4000     # caracteres do dump de prompts
LIMITE_MERCADO = 4000     # caracteres do doc de mercado/concorrência


class ReadMarketContextTool(BaseTool):
    name: str = "read_market_context"
    description: str = (
        "Lê o resumo de mercado e concorrência do StaFlow "
        "(mercado-concorrencia.md) — tamanho do mercado, concorrentes "
        "diretos e indiretos, posicionamento de preço. Use antes de propor "
        "estratégia de marketing, posicionamento ou análise financeira "
        "que dependa de contexto competitivo."
    )

    def _run(self, input: str = "") -> str:
        path = os.path.join(os.path.dirname(__file__), "..", "..",
                             "mercado-concorrencia.md")
        try:
            with open(path, "r", encoding="utf-8") as f:
                texto = f.read()
            if len(texto) <= LIMITE_MERCADO:
                return texto
            return texto[:LIMITE_MERCADO] + "\n\n[...documento truncado...]"
        except Exception as e:
            return f"Sem doc de mercado disponível: {e}"


class ReadMemoryTool(BaseTool):
    name: str = "read_memory"
    description: str = (
        "Lê o histórico dos ciclos anteriores (CLAUDE.md), já resumido nas "
        "entradas mais recentes. Use no início de cada tarefa."
    )

    def _run(self, input: str = "") -> str:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "CLAUDE.md")
        try:
            with open(path, "r", encoding="utf-8") as f:
                texto = f.read()

            if len(texto) <= LIMITE_MEMORIA:
                return texto

            # Mantém o cabeçalho (contexto fixo do produto) + entradas recentes
            marcador = "\n\n## ["
            if marcador in texto:
                cabecalho, _, historico = texto.partition(marcador)
                cabecalho = cabecalho[:2000]
                recente   = (marcador + historico)[-(LIMITE_MEMORIA - len(cabecalho)):]
                return (cabecalho + "\n\n[...ciclos mais antigos omitidos...]\n"
                        + recente)

            return texto[-LIMITE_MEMORIA:]
        except Exception as e:
            return f"Sem memória prévia: {e}"


class UpdateMemoryTool(BaseTool):
    name: str = "update_memory"
    description: str = (
        "Salva aprendizados no CLAUDE.md para o próximo ciclo. "
        "Parâmetro: content (texto com resumo do ciclo atual, prefixado "
        "com o nome da área, ex: '[Marketing] ...')."
    )

    def _run(self, content: str) -> str:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "CLAUDE.md")
        try:
            with open(path, "r", encoding="utf-8") as f:
                atual = f.read()
            hoje = datetime.date.today().isoformat()
            novo = atual + f"\n\n## [{hoje}] Ciclo automático\n{content}\n"
            partes = novo.split("\n\n## [")
            if len(partes) > 21:
                partes = partes[:1] + partes[-20:]
            novo = "\n\n## [".join(partes)
            with open(path, "w", encoding="utf-8") as f:
                f.write(novo)
            return "CLAUDE.md atualizado."
        except Exception as e:
            return f"Erro ao atualizar CLAUDE.md: {e}"


# ─── Supabase ────────────────────────────────────────────────────

class SupabaseMetricsTool(BaseTool):
    name: str = "supabase_metrics"
    description: str = (
        "Lê métricas reais do StaFlow: usuários, assinaturas, feedbacks e "
        "histórico de execuções. Parâmetro obrigatório loop: informe a área "
        "(marketing, produto, financeiro, suporte ou meta) para filtrar o "
        "histórico, ou 'todos' para ver o histórico geral."
    )

    def _run(self, loop: str = "todos") -> str:
        try:
            sb = create_client(SUPABASE_URL, SUPABASE_KEY)
            usuarios    = sb.table("profiles").select("id,created_at,role", count="exact").execute()
            assinaturas = sb.table("subscriptions").select("id,plan,status", count="exact").eq("status", "active").execute()
            feedbacks   = sb.table("feedback").select("mensagem,tipo,created_at").order("created_at", desc=True).limit(5).execute()
            semana      = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat()
            novos       = sb.table("profiles").select("id", count="exact").gte("created_at", semana).execute()

            query = (
                sb.table("agent_runs")
                .select("agent_name,status,output_summary,loop_name")
                .order("created_at", desc=True)
                .limit(10)
            )
            alvo = (loop or "").strip().lower()
            if alvo and alvo not in ("todos", "geral", "all"):
                query = query.eq("loop_name", alvo)
            runs = query.execute()

            return json.dumps({
                "total_usuarios":     usuarios.count or 0,
                "novos_semana":       novos.count or 0,
                "assinaturas_ativas": assinaturas.count or 0,
                "planos":             [r["plan"] for r in (assinaturas.data or [])],
                "feedbacks":          [{"tipo": f.get("tipo"),
                                       "msg": (f.get("mensagem") or "")[:150]}
                                      for f in (feedbacks.data or [])],
                "ultimas_execucoes":  [{"agente": r.get("agent_name"),
                                       "area": r.get("loop_name"),
                                       "status": r.get("status"),
                                       "resumo": (r.get("output_summary") or "")[:150]}
                                      for r in (runs.data or [])],
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Erro Supabase: {e}"


class SupabaseWriteTool(BaseTool):
    name: str = "supabase_write_agent_run"
    description: str = (
        "Salva o resultado de um agente no Supabase. "
        "Parâmetros: agent_name, output_summary, output_completo, loop_name "
        "(marketing, produto, financeiro, suporte ou meta)."
    )

    def _run(self, agent_name: str, output_summary: str,
             output_completo: str = "", loop_name: str = "geral") -> str:
        try:
            sb = create_client(SUPABASE_URL, SUPABASE_KEY)
            res = sb.table("agent_runs").insert({
                "agent_name":      agent_name,
                "output_summary":  output_summary,
                "output_completo": output_completo,
                "loop_name":       loop_name,
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
            results = client.search(query=query, max_results=4, search_depth="basic")
            saida   = []
            for r in results.get("results", []):
                saida.append(f"**{r['title']}**\n{r['url']}\n{r.get('content','')[:180]}")
            return "\n---\n".join(saida) or "Sem resultados."
        except Exception as e:
            return f"Erro Tavily: {e}"


# ─── GitHub ──────────────────────────────────────────────────────

# Arquivos e pastas que NENHUM agente pode criar ou modificar.
# Mexer neles pode derrubar o site em produção ou o próprio loop de agentes.
ARQUIVOS_PROIBIDOS = {
    "index.html", "style.css", "script.js",
    "vercel.json", "railway.json", "package.json", "package-lock.json",
    "requirements.txt", "CLAUDE.md", ".gitignore", ".env",
}
PASTAS_PROIBIDAS = (
    "scripts/",   # o próprio código dos agentes
    ".github/",   # automações do repositório
    "sql/",       # migrações do banco de dados
    "auth/",      # fluxo de login — crítico
)
# Tamanho mínimo para considerar que há conteúdo real (evita esqueletos vazios)
TAMANHO_MINIMO = 200


def _validar_arquivos(files_dict: dict) -> str:
    """Retorna string de erro se algo for bloqueado, ou '' se estiver tudo ok."""
    if not files_dict:
        return "Nenhum arquivo informado — PR não criado."

    for fname, content in files_dict.items():
        alvo = fname.strip().lstrip("./")

        if alvo in ARQUIVOS_PROIBIDOS:
            return (f"BLOQUEADO: '{alvo}' é um arquivo crítico do StaFlow em "
                    "produção e não pode ser alterado por agentes. "
                    "Proponha a mudança em texto no relatório para o Breno "
                    "decidir manualmente.")

        for pasta in PASTAS_PROIBIDAS:
            if alvo.startswith(pasta):
                return (f"BLOQUEADO: '{alvo}' está em '{pasta}', uma pasta "
                        "protegida. Agentes não alteram esta área. "
                        "Proponha a mudança em texto no relatório.")

        if not isinstance(content, str) or len(content.strip()) < TAMANHO_MINIMO:
            return (f"BLOQUEADO: o conteúdo de '{alvo}' tem apenas "
                    f"{len(str(content).strip())} caracteres — parece um "
                    "rascunho vazio, não código funcional. Escreva o arquivo "
                    "completo e funcional, ou não proponha a mudança.")

    return ""


class GitHubPRTool(BaseTool):
    name: str = "create_github_pr"
    description: str = (
        "Cria um Pull Request no GitHub com código NOVO e COMPLETO. "
        "Parâmetros: title, body, branch, files (JSON string de filename→conteúdo). "
        "PROIBIDO alterar: index.html, style.css, script.js, arquivos de "
        "configuração, e as pastas scripts/, sql/, auth/, .github/. "
        "Cada arquivo precisa ter conteúdo real e funcional — rascunhos "
        "vazios são rejeitados automaticamente."
    )

    def _run(self, title: str, body: str, branch: str = "", files: str = "{}") -> str:
        if not GITHUB_TOKEN:
            return "GITHUB_TOKEN não configurado."
        try:
            files_dict = json.loads(files) if isinstance(files, str) else files

            erro = _validar_arquivos(files_dict)
            if erro:
                return erro

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


# ─── Orçamento diário compartilhado ───────────────────────────────
# ★ 09/08/2026 — o gasto do dia vivia só na memória do processo. Como o
# Railway sobe um container novo a cada cron E a cada deploy, o contador
# voltava a zero toda vez e o time rodava tudo de novo achando que tinha
# a cota inteira. Agora fica no banco, então qualquer execução do dia
# enxerga o que as anteriores já gastaram.
# Não são ferramentas de agente — são funções internas do orquestrador.

def _diagnostico_config() -> str:
    """String segura (sem vazar a chave) pra saber SE a config existe e
    tem o formato esperado, quando um erro de conexão é confuso demais."""
    url_ok = isinstance(SUPABASE_URL, str) and SUPABASE_URL.startswith("http")
    key_len = len(SUPABASE_KEY) if isinstance(SUPABASE_KEY, str) else 0
    return (f"SUPABASE_URL parece válida: {url_ok} "
            f"(começa com '{str(SUPABASE_URL)[:12]}...', "
            f"{len(str(SUPABASE_URL))} chars) | "
            f"SUPABASE_KEY presente: {key_len > 20} ({key_len} chars)")


def ler_gasto_do_dia(dia: str) -> int:
    """Quantos tokens o time já gastou hoje (0 se ainda não rodou)."""
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        r = (sb.table("agent_budget_diario")
             .select("tokens_gastos").eq("dia", dia).limit(1).execute())
        if r.data:
            return int(r.data[0].get("tokens_gastos") or 0)
        return 0
    except Exception as e:
        # Nunca travar o ciclo por causa do contador. Assumir 0 é o
        # comportamento antigo — no pior caso gasta um pouco a mais.
        print(f"[orcamento] não consegui ler o gasto do dia: "
              f"{type(e).__name__}: {e} | {_diagnostico_config()}")
        return 0


def salvar_gasto_do_dia(dia: str, tokens: int) -> None:
    """Grava o total gasto no dia (sobrescreve o valor anterior)."""
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        sb.table("agent_budget_diario").upsert({
            "dia":           dia,
            "tokens_gastos": int(tokens),
            "atualizado_em": datetime.datetime.utcnow().isoformat(),
        }, on_conflict="dia").execute()
    except Exception as e:
        print(f"[orcamento] não consegui salvar o gasto do dia: "
              f"{type(e).__name__}: {e} | {_diagnostico_config()}")


# ─── Recados do Breno (canal único "empresa") ─────────────────────
# Um só lugar onde o Breno deixa pedidos/comentários pro time inteiro
# (tabela public.time_recados, escrita pela página interna equipe.html).
# Todo Coletor lê os pendentes no início do ciclo; quem atender marca
# o recado e escreve a resposta, pra virar uma conversa de verdade
# (mesmo que assíncrona) em vez de um pedido que desaparece no vazio.

class LerRecadosTool(BaseTool):
    name: str = "ler_recados_breno"
    description: str = (
        "Lê os recados/pedidos que o Breno deixou pro time (pendentes ou em "
        "andamento), mais recentes primeiro. Use SEMPRE no início do ciclo, "
        "antes de decidir o que priorizar — um recado do Breno pesa mais que "
        "qualquer prioridade que o agente decidiria sozinho. Parâmetro input: "
        "passe string vazia."
    )

    def _run(self, input: str = "") -> str:
        try:
            sb = create_client(SUPABASE_URL, SUPABASE_KEY)
            recados = (
                sb.table("time_recados")
                .select("id,criado_em,mensagem,area_alvo,status")
                .in_("status", ["pendente", "em_andamento"])
                .order("criado_em", desc=True)
                .limit(10)
                .execute()
            )
            if not recados.data:
                return "Nenhum recado pendente do Breno no momento."
            return json.dumps(recados.data, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Erro ao ler recados: {e}"


class ResponderRecadoTool(BaseTool):
    name: str = "responder_recado_breno"
    description: str = (
        "Marca um recado do Breno como atendido (ou 'nao_prioridade' se não "
        "for o foco deste ciclo) e registra a resposta, que ele vai ver na "
        "página de recados. Parâmetros obrigatórios: recado_id (o id lido em "
        "ler_recados_breno), status ('atendido' ou 'nao_prioridade'), "
        "resposta (texto simples explicando o que foi feito ou por que não "
        "agora), atendido_por (nome da área/agente, ex: 'marketing')."
    )

    def _run(self, recado_id: str, status: str, resposta: str,
             atendido_por: str = "time") -> str:
        if status not in ("atendido", "nao_prioridade", "em_andamento"):
            return "status inválido — use 'atendido', 'em_andamento' ou 'nao_prioridade'."
        try:
            sb = create_client(SUPABASE_URL, SUPABASE_KEY)
            sb.table("time_recados").update({
                "status":       status,
                "resposta":     resposta,
                "atendido_por": atendido_por,
                "atendido_em":  datetime.datetime.utcnow().isoformat(),
            }).eq("id", recado_id).execute()
            return f"Recado {recado_id} marcado como {status}."
        except Exception as e:
            return f"Erro ao responder recado: {e}"


# ─── Meta-Agente Evolutivo ────────────────────────────────────────

class SupabaseFeedbackTool(BaseTool):
    name: str = "supabase_feedback_history"
    description: str = (
        "Lê o histórico de aprovações/rejeições do Breno em TODOS os loops, "
        "incluindo o motivo (feedback_breno) e a área (loop_name). Use para "
        "identificar padrões do que está funcionando ou não em cada agente."
    )

    def _run(self, input: str = "") -> str:
        try:
            sb = create_client(SUPABASE_URL, SUPABASE_KEY)
            runs = (
                sb.table("agent_runs")
                .select("agent_name,loop_name,output_summary,status,feedback_breno,created_at")
                .not_.is_("feedback_breno", "null")
                .order("created_at", desc=True)
                .limit(15)
                .execute()
            )
            if not runs.data:
                return "Nenhum feedback registrado pelo Breno ainda."
            # Corta textos longos: o free tier aceita só 6k tokens/minuto
            enxuto = []
            for r in runs.data:
                enxuto.append({
                    "agente":   r.get("agent_name"),
                    "area":     r.get("loop_name"),
                    "resumo":   (r.get("output_summary") or "")[:180],
                    "status":   r.get("status"),
                    "feedback": (r.get("feedback_breno") or "")[:180],
                    "data":     (r.get("created_at") or "")[:10],
                })
            return json.dumps(enxuto, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Erro ao ler feedback: {e}"


LOOPS_VALIDOS = ("marketing", "produto", "financeiro", "suporte", "meta")


class ListPromptsTool(BaseTool):
    name: str = "listar_agentes"
    description: str = (
        "Devolve o índice resumido de todas as áreas e seus agentes, com o "
        "objetivo de cada um em uma linha. Use PRIMEIRO, para descobrir "
        "qual área investigar. Parâmetro input: passe string vazia."
    )

    def _run(self, input: str = "") -> str:
        base = os.path.join(os.path.dirname(__file__), "prompts")
        try:
            indice = {}
            for fname in sorted(os.listdir(base)):
                if not fname.endswith(".json"):
                    continue
                with open(os.path.join(base, fname), "r", encoding="utf-8") as f:
                    dados = json.load(f)
                indice[fname.replace(".json", "")] = {
                    k: v.get("goal", "")[:110] for k, v in dados.items()
                }
            return (json.dumps(indice, ensure_ascii=False, indent=2)
                    + "\n\nPara ver os detalhes de uma área, use read_prompts "
                      "informando o nome dela.")
        except Exception as e:
            return f"Erro ao listar agentes: {e}"


class ReadPromptsTool(BaseTool):
    name: str = "read_prompts"
    description: str = (
        "Devolve o conteúdo completo dos prompts de UMA área. "
        "Parâmetro obrigatório loop: marketing, produto, financeiro, "
        "suporte ou meta. Use antes de propor qualquer mudança."
    )

    def _run(self, loop: str) -> str:
        base = os.path.join(os.path.dirname(__file__), "prompts")
        try:
            alvo = (loop or "").strip().lower().replace(".json", "")
            if alvo not in LOOPS_VALIDOS:
                return (f"Área '{loop}' não existe. "
                        f"Use uma destas: {', '.join(LOOPS_VALIDOS)}")

            path = os.path.join(base, f"{alvo}.json")
            with open(path, "r", encoding="utf-8") as f:
                conteudo = f.read()

            if len(conteudo) > LIMITE_PROMPTS:
                return conteudo[:LIMITE_PROMPTS] + "\n[...truncado...]"
            return conteudo
        except Exception as e:
            return f"Erro ao ler prompts: {e}"


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
            r = httpx.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}",
                         "Content-Type": "application/json"},
                json={"from": RESEND_FROM,
                      "to": [NOTIFY_EMAIL],
                      "subject": subject,
                      "html": html_body},
                timeout=15,
            )
            if r.status_code >= 400:
                # ★ 09/08/2026 — antes essa falha só voltava como texto pro
                # agente, que seguia em frente sem reclamar. Resultado: o
                # Breno passou dias sem receber relatório nenhum e o log não
                # mostrava nada de errado. Agora aparece no log do Railway.
                print(f"[email] FALHA ao enviar (HTTP {r.status_code}) "
                      f"de {RESEND_FROM} para {NOTIFY_EMAIL}: {r.text[:300]}")
                return (f"FALHA ao enviar email (HTTP {r.status_code}): "
                        f"{r.text[:300]}")
            print(f"[email] enviado de {RESEND_FROM} para {NOTIFY_EMAIL} "
                  f"— assunto: {subject[:80]}")
            return f"Email enviado para {NOTIFY_EMAIL}"
        except Exception as e:
            print(f"[email] ERRO ao enviar: {e}")
            return f"Erro email: {e}"
