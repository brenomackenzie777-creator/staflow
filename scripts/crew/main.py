"""
StaFlow — Orquestrador principal do loop autoevolutivo
======================================================
Uso: python -m scripts.crew.main

Este script monta e executa a Crew completa dos 7 agentes em sequência.
Cada agente recebe o output do anterior como contexto.
"""
import sys
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
        process=Process.sequential,   # Um agente por vez, em ordem
        verbose=True,
        memory=True,                  # CrewAI mantém memória entre agentes
        embedder={
            "provider": "anthropic",
            "config": {"model": "claude-haiku-4-5-20251001"},
        }
    )

    resultado = crew.kickoff()

    print("\n" + "="*60)
    print("  Loop concluído com sucesso!")
    print(f"  Fim: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    return resultado


if __name__ == "__main__":
    try:
        executar_loop()
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Loop falhou: {e}")
        sys.exit(1)
