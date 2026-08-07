"""
StaFlow — Orquestrador principal: roteia por loop conforme o dia da semana
Uso: python -m scripts.crew.main
Override manual: LOOP=produto python -m scripts.crew.main
"""
import sys
import os
import time
import datetime
from crewai import Crew, Process

from .agents import build_loop_agents, build_meta_agent
from .tasks import build_loop_tasks, build_meta_task

MAX_RETRIES = 5
BASE_WAIT   = 30   # segundos iniciais; dobra a cada tentativa

# Container roda em UTC; 11h UTC = 8h BRT, sem risco de virar o dia.
DIA_PARA_LOOP = {
    0: "marketing",   # segunda
    1: "produto",     # terça
    2: "financeiro",  # quarta
    3: "suporte",     # quinta
    4: "meta",        # sexta — Meta-Agente avalia a semana inteira
}

ORDEM_AGENTES = ["coletor", "pesquisador", "analista", "estrategista",
                  "decisor", "executor", "observador"]
ORDEM_TAREFAS = ["coletar", "pesquisar", "analisar", "propor",
                  "decidir", "executar", "aprender"]


def montar_crew(loop_key: str) -> Crew:
    if loop_key == "meta":
        meta_agente = build_meta_agent()
        tarefa      = build_meta_task(meta_agente)
        return Crew(agents=[meta_agente], tasks=[tarefa],
                    process=Process.sequential, verbose=True, memory=False)

    agents = build_loop_agents(loop_key)
    tasks  = build_loop_tasks(loop_key, agents)
    return Crew(
        agents=[agents[k] for k in ORDEM_AGENTES],
        tasks=[tasks[k] for k in ORDEM_TAREFAS],
        process=Process.sequential,
        verbose=True,
        memory=False,
    )


def executar_loop():
    loop_key = os.environ.get("LOOP") or DIA_PARA_LOOP.get(
        datetime.datetime.now().weekday()
    )

    if not loop_key:
        print("\nHoje (fim de semana) não há loop agendado. Encerrando.\n")
        return None

    print("\n" + "="*60)
    print(f"  StaFlow — Loop: {loop_key.upper()}")
    print(f"  Início: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    crew = montar_crew(loop_key)

    wait = BASE_WAIT
    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            resultado = crew.kickoff()
            print("\n" + "="*60)
            print(f"  Loop {loop_key} concluído com sucesso!")
            print(f"  Fim: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60 + "\n")
            return resultado

        except Exception as e:
            msg = str(e)
            if "429" in msg or "rate_limit" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
                if tentativa < MAX_RETRIES:
                    print(f"\n[RATE LIMIT] Tentativa {tentativa}/{MAX_RETRIES}. "
                          f"Aguardando {wait}s...\n")
                    time.sleep(wait)
                    wait = min(wait * 2, 300)
                else:
                    print(f"\n[RATE LIMIT] Esgotadas {MAX_RETRIES} tentativas. "
                          "Tente novamente amanhã.")
                    sys.exit(1)
            else:
                print(f"\n[ERRO] {e}")
                raise


if __name__ == "__main__":
    try:
        executar_loop()
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] {e}")
        sys.exit(1)
