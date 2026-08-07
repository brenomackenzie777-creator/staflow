"""
StaFlow — Orquestrador principal do loop autoevolutivo
======================================================
Uso: python -m scripts.crew.main
"""
import sys
import time
import datetime
from crewai import Crew, Process

from .agents import (
    coletor, pesquisador, analista,
    estrategista, decisor, executor, observador,
)
from .tasks import (
    tarefa_coletar, tarefa_pesquisar, tarefa_analisar,
    tarefa_propor, tarefa_decidir, tarefa_executar, tarefa_aprender,
)

MAX_RETRIES = 3
RETRY_WAIT  = 90   # segundos de espera após rate limit


def executar_loop():
    print("\n" + "="*60)
    print("  StaFlow — Loop Autoevolutivo")
    print(f"  Início: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    crew = Crew(
        agents=[
            coletor,
            pesquisador,
            analista,
            estrategista,
            decisor,
            executor,
            observador,
        ],
        tasks=[
            tarefa_coletar,
            tarefa_pesquisar,
            tarefa_analisar,
            tarefa_propor,
            tarefa_decidir,
            tarefa_executar,
            tarefa_aprender,
        ],
        process=Process.sequential,
        verbose=True,
        memory=False,
    )

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
            if "429" in msg or "rate_limit" in msg.lower():
                if tentativa < MAX_RETRIES:
                    print(f"\n[RATE LIMIT] Tentativa {tentativa}/{MAX_RETRIES}. "
                          f"Aguardando {RETRY_WAIT}s...\n")
                    time.sleep(RETRY_WAIT)
                else:
                    print(f"\n[RATE LIMIT] Esgotadas as {MAX_RETRIES} tentativas. "
                          "Tente novamente amanhã ou atualize o plano do LLM.")
                    sys.exit(1)
            else:
                raise


if __name__ == "__main__":
    try:
        executar_loop()
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Loop falhou: {e}")
        sys.exit(1)
