#!/usr/bin/env python3
"""
StaFlow — Runner de Agentes Autônomos
======================================
Uso: python agente.py <camila|marcos|rafael>

Fluxo por agente:
  1. Lê CLAUDE.md (memória compartilhada)
  2. Lê histórico do agente no Supabase (últimas N runs + feedbacks)
  3. Chama Anthropic API com contexto completo
  4. Salva output em agents/outputs/<agente>/
  5. Registra run no Supabase (agent_runs)
  6. Atualiza CLAUDE.md com o que foi feito
  7. Envia notificação por email (Resend)

A "autoevolução" acontece no passo 2: o agente lê o que funcionou
(aprovado pelo Breno) e o que não funcionou (rejeitado) nas últimas
semanas, e o LLM naturalmente ajusta o estilo/abordagem.
"""

import os
import sys
import json
import datetime
import pathlib
import httpx
import anthropic
from supabase import create_client

# ─── Config ──────────────────────────────────────────────────────
REPO_ROOT     = pathlib.Path(__file__).parent.parent
CLAUDE_MD     = REPO_ROOT / "CLAUDE.md"
AGENTS_DIR    = REPO_ROOT / "agents"
PROMPTS_DIR   = AGENTS_DIR / "prompts"
OUTPUTS_DIR   = AGENTS_DIR / "outputs"

ANTHROPIC_KEY      = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL       = os.environ["SUPABASE_URL"]
SUPABASE_KEY       = os.environ["SUPABASE_SERVICE_KEY"]
RESEND_KEY         = os.environ.get("RESEND_API_KEY", "")
NOTIFY_EMAIL       = os.environ.get("NOTIFY_EMAIL", "brenomackenzie777@gmail.com")
PRODUCTION_URL     = os.environ.get("PRODUCTION_URL", "https://staflow.app.br")

# Modelo por agente: Haiku para tarefas rápidas, Sonnet para análises complexas
MODELO = {
    "camila": "claude-haiku-4-5-20251001",
    "marcos": "claude-haiku-4-5-20251001",
    "rafael": "claude-sonnet-4-6",   # Rafael faz análise técnica, usa Sonnet
}

# ─── Clientes ────────────────────────────────────────────────────
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
supabase         = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── Helpers ─────────────────────────────────────────────────────

def ler_claude_md() -> str:
    """Lê a memória compartilhada dos agentes."""
    if CLAUDE_MD.exists():
        return CLAUDE_MD.read_text(encoding="utf-8")
    return "# Memória StaFlow\n\n(sem entradas ainda)"


def ler_historico_agente(nome: str, limite: int = 10) -> str:
    """
    Busca as últimas N execuções do agente no Supabase,
    incluindo o status de aprovação (approved/rejected/pending).
    Esta é a fonte da autoevolução — o agente aprende com o passado.
    """
    try:
        res = (
            supabase.table("agent_runs")
            .select("created_at,output_summary,status,feedback_breno")
            .eq("agent_name", nome)
            .order("created_at", desc=True)
            .limit(limite)
            .execute()
        )
        if not res.data:
            return "(sem histórico ainda — esta é a primeira execução)"

        linhas = []
        for run in res.data:
            data    = run.get("created_at", "")[:10]
            status  = run.get("status", "pending")
            summary = run.get("output_summary", "sem resumo")
            fb      = run.get("feedback_breno", "")
            icone   = {"approved": "✅", "rejected": "❌", "pending": "⏳"}.get(status, "❓")
            linha   = f"- {data} {icone} {summary}"
            if fb:
                linha += f" | Feedback Breno: \"{fb}\""
            linhas.append(linha)

        return "\n".join(linhas)
    except Exception as e:
        return f"(erro ao ler histórico: {e})"


def ler_metricas_supabase() -> dict:
    """Lê métricas chave do Supabase para contexto dos agentes."""
    try:
        usuarios = supabase.table("profiles").select("id", count="exact").execute()
        assinaturas = supabase.table("subscriptions").select("id", count="exact").eq("status", "active").execute()
        feedbacks = supabase.table("feedback").select("id,mensagem,created_at").order("created_at", desc=True).limit(5).execute()

        return {
            "total_usuarios": usuarios.count or 0,
            "assinaturas_ativas": assinaturas.count or 0,
            "feedbacks_recentes": feedbacks.data or [],
        }
    except Exception as e:
        return {"erro": str(e)}


def salvar_output(nome: str, conteudo: str) -> pathlib.Path:
    """Salva o output do agente em arquivo datado."""
    pasta = OUTPUTS_DIR / nome
    pasta.mkdir(parents=True, exist_ok=True)
    hoje = datetime.date.today().isoformat()
    arquivo = pasta / f"{hoje}.md"
    arquivo.write_text(conteudo, encoding="utf-8")
    return arquivo


def registrar_run(nome: str, output_summary: str, output_completo: str) -> str:
    """Registra a execução no Supabase. Retorna o ID do registro."""
    try:
        res = supabase.table("agent_runs").insert({
            "agent_name":       nome,
            "output_summary":   output_summary[:500],
            "output_completo":  output_completo[:10000],
            "status":           "pending",   # Breno aprova/rejeita depois
            "created_at":       datetime.datetime.utcnow().isoformat(),
        }).execute()
        return res.data[0]["id"] if res.data else "sem-id"
    except Exception as e:
        print(f"[WARN] Erro ao registrar run: {e}")
        return "erro"


def atualizar_claude_md(nome: str, resumo: str):
    """Adiciona entrada na memória compartilhada CLAUDE.md."""
    conteudo = ler_claude_md()
    hoje = datetime.date.today().isoformat()
    nova_entrada = f"\n## [{hoje}] {nome.capitalize()} executou\n{resumo}\n"

    # Insere após o header, mantém as últimas 30 entradas para não crescer infinito
    linhas = conteudo.split("\n## ")
    if len(linhas) > 31:
        linhas = linhas[:1] + linhas[-30:]   # header + últimas 30 entradas

    novo_conteudo = "\n## ".join(linhas) + nova_entrada
    CLAUDE_MD.write_text(novo_conteudo, encoding="utf-8")


def notificar(nome: str, resumo: str, output_id: str):
    """Envia email de notificação via Resend."""
    if not RESEND_KEY:
        print("[INFO] RESEND_API_KEY não configurado — pulando notificação")
        return

    try:
        resposta_url = f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'staflow')}/actions"

        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_KEY}", "Content-Type": "application/json"},
            json={
                "from":    "agentes@staflow.app.br",
                "to":      [NOTIFY_EMAIL],
                "subject": f"[StaFlow] {nome.capitalize()} concluiu — aguarda sua revisão",
                "html": f"""
                <h2>Agente {nome.capitalize()} executou automaticamente</h2>
                <p><strong>Resumo:</strong> {resumo}</p>
                <p>O output está salvo em <code>agents/outputs/{nome}/</code> no repositório.</p>
                <p><a href="{resposta_url}">Ver no GitHub Actions</a></p>
                <hr>
                <p style="color:#666;font-size:12px">
                  Este email foi gerado automaticamente pelo sistema de agentes StaFlow.<br>
                  Para aprovar ou rejeitar, acesse o Supabase → tabela agent_runs → ID: {output_id}
                </p>
                """,
            },
            timeout=10,
        )
        print(f"[OK] Notificação enviada para {NOTIFY_EMAIL}")
    except Exception as e:
        print(f"[WARN] Erro ao notificar: {e}")


# ─── Montagem do prompt por agente ──────────────────────────────

def montar_prompt(nome: str, memoria: str, historico: str, metricas: dict) -> str:
    prompt_base_path = PROMPTS_DIR / f"{nome}.md"

    if not prompt_base_path.exists():
        raise FileNotFoundError(f"Prompt não encontrado: {prompt_base_path}")

    prompt_base = prompt_base_path.read_text(encoding="utf-8")

    contexto = f"""
# CONTEXTO AUTOMÁTICO — {datetime.date.today().isoformat()}

## Memória compartilhada (CLAUDE.md)
{memoria}

## Histórico das últimas execuções deste agente
(Use isso para autoevolução — adapte sua abordagem com base nos feedbacks anteriores)
{historico}

## Métricas atuais do StaFlow
- Total de usuários cadastrados: {metricas.get('total_usuarios', 'N/A')}
- Assinaturas ativas: {metricas.get('assinaturas_ativas', 'N/A')}
- Feedbacks recentes dos usuários:
{json.dumps(metricas.get('feedbacks_recentes', []), ensure_ascii=False, indent=2)}

---

# INSTRUÇÃO DO AGENTE

{prompt_base}

---

# FORMATO DE SAÍDA OBRIGATÓRIO

Estruture seu output em duas partes:

## RESUMO (1-3 linhas)
Uma descrição curta do que foi feito, para o log de auditoria.

## OUTPUT COMPLETO
O conteúdo real do trabalho (posts, mensagens, relatório, etc.)
"""
    return contexto


# ─── Runner específico Rafael (smoke tests reais) ────────────────

def rafael_smoke_tests() -> str:
    """Rafael faz testes HTTP reais nas páginas críticas da produção."""
    import httpx

    paginas = [
        "/",
        "/staflow-landing.html",
        "/auth/login.html",
        "/auth/cadastro.html",
        "/planos.html",
        "/dashboard.html",
        "/colaborador.html",
        "/service-worker.js",
        "/manifest.json",
    ]

    resultados = []
    with httpx.Client(timeout=15, follow_redirects=True) as client:
        for pagina in paginas:
            url = PRODUCTION_URL + pagina
            try:
                r = client.get(url)
                status = r.status_code
                ok = "✅" if status < 400 else "❌"
                resultados.append(f"{ok} {status} — {url}")
            except Exception as e:
                resultados.append(f"❌ ERRO — {url} ({e})")

    return "\n".join(resultados)


# ─── Execução principal ──────────────────────────────────────────

def executar(nome: str):
    print(f"\n{'='*60}")
    print(f"  StaFlow Agente: {nome.upper()}")
    print(f"  {datetime.datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    # 1. Lê contexto
    print("[1/7] Lendo CLAUDE.md...")
    memoria = ler_claude_md()

    print("[2/7] Lendo histórico do Supabase...")
    historico = ler_historico_agente(nome)

    print("[3/7] Lendo métricas do Supabase...")
    metricas = ler_metricas_supabase()

    # Rafael: inclui resultados reais de smoke tests no prompt
    smoke_resultado = ""
    if nome == "rafael":
        print("[3b/7] Rodando smoke tests em produção...")
        smoke_resultado = rafael_smoke_tests()
        print(smoke_resultado)
        metricas["smoke_tests"] = smoke_resultado

    # 4. Monta prompt e chama LLM
    print(f"[4/7] Montando prompt e chamando {MODELO[nome]}...")
    prompt = montar_prompt(nome, memoria, historico, metricas)

    resposta = anthropic_client.messages.create(
        model=MODELO[nome],
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    output = resposta.content[0].text

    # Extrai resumo (primeira seção)
    resumo = ""
    for linha in output.split("\n"):
        if linha.strip() and not linha.startswith("#"):
            resumo = linha.strip()
            break
    if not resumo:
        resumo = output[:200]

    # 5. Salva output em arquivo
    print(f"[5/7] Salvando output em agents/outputs/{nome}/...")
    arquivo = salvar_output(nome, output)
    print(f"      Salvo em: {arquivo}")

    # 6. Registra no Supabase
    print("[6/7] Registrando run no Supabase...")
    run_id = registrar_run(nome, resumo, output)
    print(f"      ID do run: {run_id}")

    # 7. Atualiza CLAUDE.md
    print("[7/7] Atualizando CLAUDE.md...")
    atualizar_claude_md(nome, resumo)

    # 8. Notifica Breno
    notificar(nome, resumo, run_id)

    print(f"\n[DONE] Agente {nome} concluiu com sucesso.")
    print(f"       Output: {arquivo}")
    print(f"       Resumo: {resumo}\n")

    return output


# ─── Entrypoint ──────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python agente.py <camila|marcos|rafael|todos>")
        sys.exit(1)

    alvo = sys.argv[1].lower()
    agentes = ["camila", "marcos", "rafael"] if alvo == "todos" else [alvo]

    for agente in agentes:
        if agente not in MODELO:
            print(f"[ERRO] Agente desconhecido: {agente}")
            sys.exit(1)
        executar(agente)
