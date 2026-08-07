"""
StaFlow — Orquestrador principal do loop autoevolutivo
Uso: python -m scripts.crew.main
"""
import sys
import time
import datetime
from crewai import Crew, Process

from .agents import (
    coletor, pesquisador, analista,
    estrategista, decisor, executor, observador, meta_agente,
)
from .tasks import (
    tarefa_coletar, tarefa_pesquisar, tarefa_analisar,
    tarefa_propor, tarefa_decidir, tarefa_executar, tarefa_aprender,
    tarefa_evoluir,
)

MAX_RETRIES = 5
BASE_WAIT   = 30   # segundos iniciais; dobra a cada tentativa


def executar_loop():
    print("\n" + "="*60)
    print("  StaFlow — Loop Autoevolutivo")
    print(f"  Início: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    crew = Crew(
        agents=[coletor, pesquisador, analista, estrategista,
                decisor, executor, observador, meta_agente],
        tasks=[tarefa_coletar, tarefa_pesquisar, tarefa_analisar,
               tarefa_propor, tarefa_decidir, tarefa_executar,
               tarefa_aprender, tarefa_evoluir],
        process=Process.sequential,
        verbose=True,
        memory=False,
    )

    wait = BASE_WAIT
    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            resultado = crew.kickoff()
            print("\n" + "="*60)
            print("  Loop concluído com sucesso!")
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
                    wait = min(wait * 2, 300)  # exponential backoff, máx 5 min
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
