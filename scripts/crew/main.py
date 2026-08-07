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

# Container roda em UTC; 11h UTC = 8h BRT, sem risco de virar o dia.
DIA_PARA_LOOP = {
    0: "marketing",   # segunda
    1: "produto",     # terça
    2: "financeiro",  # quarta
    3: "suporte",     # quinta
    4: "meta",        # sexta — Meta-Agente avalia a semana inteira
}

ORDEM_AGENTES = ["coletor", "pesquisador", "analista", "estrategista",
                  "decisor", "executor", "observador", "relator"]
ORDEM_TAREFAS = ["coletar", "pesquisar", "analisar", "propor",
                  "decidir", "executar", "aprender", "relatar"]


def montar_crew(loop_key: str) -> Crew:
    if loop_key == "meta":
        meta_agente   = build_meta_agent()
        meta_relator  = build_meta_relator()
        tarefa_meta   = build_meta_task(meta_agente)
        tarefa_relato = build_meta_relatorio_task(meta_relator, tarefa_meta)
        return Crew(agents=[meta_agente, meta_relator],
                    tasks=[tarefa_meta, tarefa_relato],
                    process=Process.sequential, verbose=VERBOSE, memory=False)

    agents = build_loop_agents(loop_key)
    tasks  = build_loop_tasks(loop_key, agents)
    return Crew(
        agents=[agents[k] for k in ORDEM_AGENTES],
        tasks=[tasks[k] for k in ORDEM_TAREFAS],
        process=Process.sequential,
        verbose=VERBOSE,
        memory=False,
    )


def executar_loop():
    loop_key = os.environ.get("LOOP") or DIA_PARA_LOOP.get(
        datetime.datetime.now().weekday()
    )

    if not loop_key:
        log.info("Fim de semana — nenhum loop agendado hoje. Encerrando.")
        return None

    inicio = time.time()
    log.info("=" * 50)
    log.info("StaFlow — Loop: %s", loop_key.upper())
    log.info("=" * 50)

    crew = montar_crew(loop_key)

    wait = BASE_WAIT
    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            resultado = crew.kickoff()
            dur = int(time.time() - inicio)
            log.info("=" * 50)
            log.info("Loop %s concluído em %dmin%02ds", loop_key, dur // 60, dur % 60)
            log.info("=" * 50)
            return resultado

        except Exception as e:
            msg = str(e)

            # 413 = pedido grande demais. Esperar não resolve — o tamanho não
            # muda com o tempo. Falha rápido com diagnóstico em vez de gastar
            # 5 tentativas inúteis.
            if "413" in msg or "Request too large" in msg:
                log.error(
                    "Pedido grande demais para o modelo (limite de 6.000 "
                    "tokens/minuto do plano gratuito). Isso indica que a "
                    "memória ou o histórico cresceram além do teto. "
                    "Detalhe: %s", msg[:300]
                )
                sys.exit(1)

            if "429" in msg or "rate_limit" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
                if tentativa < MAX_RETRIES:
                    log.warning("Limite da IA atingido (tentativa %d/%d). "
                                "Aguardando %ds...", tentativa, MAX_RETRIES, wait)
                    time.sleep(wait)
                    wait = min(wait * 2, 300)
                else:
                    log.error("Limite da IA esgotado após %d tentativas. "
                              "Tente novamente amanhã.", MAX_RETRIES)
                    sys.exit(1)
            else:
                log.error("Falha no loop %s: %s", loop_key, msg[:500])
                raise


if __name__ == "__main__":
    try:
        executar_loop()
    except Exception as e:
        log.error("ERRO CRÍTICO: %s", str(e)[:500])
        sys.exit(1)
