"""
StaFlow — Orquestrador principal: roteia por loop conforme o dia da semana
Uso: python -m scripts.crew.main
Override manual: LOOP=produto python -m scripts.crew.main
Log detalhado (debug):  VERBOSE=1 python -m scripts.crew.main
"""
import sys
import os
import time
import logging
import datetime
from crewai import Crew, Process

from .config import MAX_RPM
from .agents import build_loop_agents, build_meta_agent, build_meta_relator
from .tasks import build_loop_tasks, build_meta_task, build_meta_relatorio_task

MAX_RETRIES = 5
BASE_WAIT   = 30   # segundos iniciais; dobra a cada tentativa

# O log verboso do CrewAI estoura o limite do Railway (500 linhas/seg) e
# derruba justamente as linhas de erro que importam. Ligue só para depurar.
VERBOSE = os.environ.get("VERBOSE", "").strip() in ("1", "true", "True")

# Silencia o ruído das bibliotecas; mantém avisos e erros.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
for _lib in ("httpx", "httpcore", "LiteLLM", "litellm", "openai", "urllib3"):
    logging.getLogger(_lib).setLevel(logging.WARNING)

log = logging.getLogger("staflow")

# ★ 08/08/2026 — a pedido do Breno: em vez de UM loop por dia útil, roda
# quantos loops de negócio couberem por dia, TODOS OS DIAS (inclusive fim
# de semana), até usar 50% da cota diária do Groq (100.000 tokens/dia no
# free tier — ver scripts/crew/config.py). Os outros 50% ficam de reserva
# pra retries, o Meta-Agente de sexta e qualquer chamada manual (LOOP=x).
#
# Ordem de execução gira por dia (dia do ano % 4) pra nenhuma área ficar
# sempre em último — se o orçamento acabar no meio, quem tomava o corte
# antes era sempre "suporte"; agora o corte roda entre as 4 áreas.
LOOPS_DE_NEGOCIO = ["marketing", "produto", "financeiro", "suporte"]

COTA_DIARIA_TOKENS   = int(os.environ.get("COTA_DIARIA_TOKENS", "100000"))
FRACAO_ORCAMENTO     = float(os.environ.get("FRACAO_ORCAMENTO_DIARIO", "0.5"))
ORCAMENTO_DIARIO     = int(COTA_DIARIA_TOKENS * FRACAO_ORCAMENTO)

ORDEM_AGENTES = ["coletor", "pesquisador", "analista", "estrategista",
                  "decisor", "executor", "observador", "relator"]
ORDEM_TAREFAS = ["coletar", "pesquisar", "analisar", "propor",
                  "decidir", "executar", "aprender", "relatar"]


def _tokens_do_crew(crew: Crew) -> int:
    """Lê o total de tokens gastos num crew.kickoff() já concluído.
    Defensivo: versões diferentes do CrewAI expõem usage_metrics de
    formas ligeiramente diferentes — nunca deixa a falta desse número
    derrubar o loop inteiro."""
    try:
        m = crew.usage_metrics
        if m is None:
            return 0
        if hasattr(m, "total_tokens"):
            return int(m.total_tokens or 0)
        if isinstance(m, dict):
            return int(m.get("total_tokens", 0) or 0)
    except Exception:
        pass
    return 0


def _ordem_do_dia() -> list:
    """Gira a ordem das 4 áreas conforme o dia do ano, pra distribuir
    igualmente quem corre risco de ficar de fora quando o orçamento
    aperta."""
    giro = datetime.date.today().timetuple().tm_yday % len(LOOPS_DE_NEGOCIO)
    return LOOPS_DE_NEGOCIO[giro:] + LOOPS_DE_NEGOCIO[:giro]


def montar_crew(loop_key: str) -> Crew:
    if loop_key == "meta":
        meta_agente   = build_meta_agent()
        meta_relator  = build_meta_relator()
        tarefa_meta   = build_meta_task(meta_agente)
        tarefa_relato = build_meta_relatorio_task(meta_relator, tarefa_meta)
        return Crew(agents=[meta_agente, meta_relator],
                    tasks=[tarefa_meta, tarefa_relato],
                    process=Process.sequential, verbose=VERBOSE, memory=False,
                    max_rpm=MAX_RPM)

    agents = build_loop_agents(loop_key)
    tasks  = build_loop_tasks(loop_key, agents)
    return Crew(
        agents=[agents[k] for k in ORDEM_AGENTES],
        tasks=[tasks[k] for k in ORDEM_TAREFAS],
        process=Process.sequential,
        verbose=VERBOSE,
        memory=False,
        max_rpm=MAX_RPM,
    )


def _rodar_um_loop(loop_key: str):
    """Roda um loop (com retries). Retorna (sucesso, tokens_gastos, parar_o_dia).
    parar_o_dia=True só quando a COTA DIÁRIA acabou — aí não adianta tentar
    os outros loops de hoje, todos vão bater na mesma parede."""
    inicio = time.time()
    log.info("=" * 50)
    log.info("StaFlow — Loop: %s", loop_key.upper())
    log.info("=" * 50)

    crew = montar_crew(loop_key)
    wait = BASE_WAIT

    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            crew.kickoff()
            tokens = _tokens_do_crew(crew)
            dur = int(time.time() - inicio)
            log.info("=" * 50)
            log.info("Loop %s concluído em %dmin%02ds (~%d tokens)",
                      loop_key, dur // 60, dur % 60, tokens)
            log.info("=" * 50)
            return True, tokens, False

        except Exception as e:
            msg = str(e)

            # 413 = pedido grande demais. Esperar não resolve, mas encolher a
            # memória resolve: cada tentativa aperta o teto de leitura e
            # remonta o crew do zero, com conversa limpa.
            if "413" in msg or "Request too large" in msg:
                from . import tools
                if tentativa < 3:
                    tools.LIMITE_MEMORIA = max(1200, tools.LIMITE_MEMORIA // 2)
                    tools.LIMITE_PROMPTS = max(1000, tools.LIMITE_PROMPTS // 2)
                    log.warning(
                        "Pedido grande demais. Reduzindo a memória lida "
                        "(agora %d caracteres) e tentando de novo (%d/3).",
                        tools.LIMITE_MEMORIA, tentativa
                    )
                    time.sleep(65)          # zera a janela de tokens/minuto
                    crew = montar_crew(loop_key)   # conversa limpa
                    continue

                log.error(
                    "Pedido segue grande demais mesmo com a memória mínima "
                    "para o loop %s. Pulando pra o próximo. Detalhe: %s",
                    loop_key, msg[:250]
                )
                return False, _tokens_do_crew(crew), False

            # Cota DIÁRIA esgotada: esperar minutos não resolve, só vira o dia.
            # Isso encerra a rotação inteira de hoje, não só este loop.
            if "tokens per day" in msg or "TPD" in msg:
                log.error(
                    "Cota diária de IA esgotada (100.000 tokens/dia do plano "
                    "gratuito) durante o loop %s. Os loops restantes de hoje "
                    "ficam pra amanhã.", loop_key
                )
                return False, _tokens_do_crew(crew), True

            # Chamada de ferramenta malformada pelo modelo. É falha de geração,
            # não de código — outra tentativa normalmente sai correta.
            # O Groq manda essa falha com pelo menos 3 textos diferentes;
            # os três precisam cair aqui, senão o loop inteiro trava.
            if ("tool_use_failed" in msg
                    or "Failed to call a function" in msg
                    or "tool call validation failed" in msg
                    or "which was not in request.tools" in msg):
                if tentativa < MAX_RETRIES:
                    log.warning("O modelo gerou uma chamada de ferramenta "
                                "inválida (tentativa %d/%d). Refazendo em 10s.",
                                tentativa, MAX_RETRIES)
                    time.sleep(10)
                    crew = montar_crew(loop_key)   # conversa limpa
                    continue
                log.error("O modelo falhou em chamar as ferramentas "
                          "corretamente no loop %s após %d tentativas. "
                          "Pulando pra o próximo.", loop_key, MAX_RETRIES)
                return False, _tokens_do_crew(crew), False

            if "429" in msg or "rate_limit" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
                if tentativa < MAX_RETRIES:
                    log.warning("Limite da IA atingido (tentativa %d/%d). "
                                "Aguardando %ds...", tentativa, MAX_RETRIES, wait)
                    time.sleep(wait)
                    wait = min(wait * 2, 300)
                else:
                    log.error("Limite da IA esgotado no loop %s após %d "
                              "tentativas. Pulando pra o próximo.",
                              loop_key, MAX_RETRIES)
                    return False, _tokens_do_crew(crew), False
            else:
                log.error("Falha no loop %s: %s. Pulando pra o próximo.",
                           loop_key, msg[:500])
                return False, _tokens_do_crew(crew), False

    return False, 0, False


def executar_loop():
    # Override manual (LOOP=marketing python -m scripts.crew.main) — roda
    # só esse loop, ignora rotação e orçamento diário.
    loop_manual = os.environ.get("LOOP")
    if loop_manual:
        _rodar_um_loop(loop_manual)
        return

    hoje     = datetime.date.today()
    eh_sexta = hoje.weekday() == 4   # 0=segunda ... 4=sexta

    ordem = _ordem_do_dia()
    log.info("Orçamento de hoje: %d tokens (%.0f%% de %d/dia). Ordem: %s",
              ORCAMENTO_DIARIO, FRACAO_ORCAMENTO * 100, COTA_DIARIA_TOKENS,
              " → ".join(ordem))

    gasto = 0
    concluidos, pulados = [], []

    for i, loop_key in enumerate(ordem):
        if gasto >= ORCAMENTO_DIARIO:
            restante = ordem[i:]
            pulados.extend(restante)
            log.info("Orçamento diário atingido (%d/%d tokens). Loops "
                      "restantes de hoje (%s) ficam pra amanhã.",
                      gasto, ORCAMENTO_DIARIO, ", ".join(restante))
            break

        sucesso, tokens, parar_o_dia = _rodar_um_loop(loop_key)
        gasto += tokens
        (concluidos if sucesso else pulados).append(loop_key)

        if parar_o_dia:
            restante = ordem[i + 1:]
            pulados.extend(restante)
            if restante:
                log.warning("Loops restantes de hoje (%s) ficam pra amanhã "
                            "— cota diária esgotada.", ", ".join(restante))
            break

    # Sexta-feira: se ainda sobrar orçamento, fecha a semana com o
    # Meta-Agente (avalia os 4 loops e propõe ajuste de prompt).
    if eh_sexta:
        if gasto < ORCAMENTO_DIARIO:
            log.info("Sexta-feira — rodando o Meta-Agente (avaliação da semana).")
            sucesso, tokens, _ = _rodar_um_loop("meta")
            gasto += tokens
            (concluidos if sucesso else pulados).append("meta")
        else:
            log.warning("Sexta-feira, mas o orçamento diário já esgotou — "
                        "o Meta-Agente fica pra próxima sexta.")

    log.info("=" * 50)
    log.info("Dia concluído: %d loop(s) rodados (%s) · %d/%d tokens (%.0f%%)",
              len(concluidos), ", ".join(concluidos) or "nenhum",
              gasto, ORCAMENTO_DIARIO,
              (gasto / ORCAMENTO_DIARIO * 100) if ORCAMENTO_DIARIO else 0)
    if pulados:
        log.info("Ficaram de fora hoje: %s", ", ".join(pulados))
    log.info("=" * 50)


if __name__ == "__main__":
    try:
        executar_loop()
    except Exception as e:
        log.error("ERRO CRÍTICO: %s", str(e)[:500])
        sys.exit(1)
