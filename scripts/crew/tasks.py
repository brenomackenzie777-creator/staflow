"""
StaFlow — Tarefas parametrizadas por loop de negócio
"""
import json
import os
from crewai import Task

LOOPS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "loops.json")
with open(LOOPS_CONFIG_PATH, "r", encoding="utf-8") as f:
    LOOPS_CONFIG = json.load(f)


def build_loop_tasks(loop_key: str, agents: dict) -> dict:
    """Monta as 7 tarefas do loop, com descrições focadas na área."""
    cfg     = LOOPS_CONFIG[loop_key]
    queries = "\n".join(f"- '{q}'" for q in cfg["queries_pesquisa"])
    nome    = cfg["nome"]

    tarefa_coletar = Task(
        description=(
            f"Ciclo de {nome}.\nFoco: {cfg['foco']}\n\n"
            "1. Use read_memory para ler o histórico geral.\n"
            f"2. Use supabase_metrics com loop='{loop_key}' para coletar "
            "dados relevantes a esta área.\n"
            "3. Compare com o ciclo anterior desta mesma área: estamos "
            "melhorando?"
        ),
        expected_output=(
            "Relatório com contexto histórico desta área + métricas + "
            "comparação com o ciclo anterior."
        ),
        agent=agents["coletor"],
    )

    tarefa_pesquisar = Task(
        description=(
            f"Pesquise sobre: {cfg['foco']}\n\nQueries sugeridas:\n{queries}\n\n"
            "Não repita queries já usadas em ciclos anteriores desta área."
        ),
        expected_output="Achados principais por query + 2-3 oportunidades concretas.",
        agent=agents["pesquisador"],
    )

    tarefa_analisar = Task(
        description=(
            f"Analise os dados e a pesquisa do ciclo de {nome}. Identifique "
            "riscos, oportunidades, e se há evolução em relação ao ciclo "
            "anterior desta área. Baseie-se apenas em dados reais."
        ),
        expected_output="3-5 insights, cada um com observação, dado de suporte e implicação.",
        agent=agents["analista"],
        context=[tarefa_coletar, tarefa_pesquisar],
    )

    tarefa_propor = Task(
        description=(
            f"Proponha até 3 melhorias para {nome}. Para cada uma: TÍTULO, "
            "O QUÊ muda, POR QUÊ (insight), IMPACTO (alto/médio/baixo), "
            "ESFORÇO (pequeno/médio/grande), RISCO (baixo=só UI/copy | "
            "médio | alto=banco/fluxo crítico). Não repita propostas "
            "rejeitadas em ciclos anteriores desta área."
        ),
        expected_output="Lista de até 3 propostas com todos os campos preenchidos.",
        agent=agents["estrategista"],
        context=[tarefa_analisar],
    )

    tarefa_decidir = Task(
        description=(
            "Filtre as propostas:\n"
            "AUTO-EXECUTAR: esforço PEQUENO + risco BAIXO → vai para o Executor.\n"
            "APROVAR-BRENO: todo o resto → use notify_breno com subject "
            f"'StaFlow [{nome}]: propostas aguardando aprovação' e resumo HTML.\n"
            "Máximo 2 itens AUTO-EXECUTAR por ciclo."
        ),
        expected_output=(
            "Lista AUTO-EXECUTAR com descrição de implementação + lista "
            "APROVAR-BRENO com confirmação de notificação enviada."
        ),
        agent=agents["decisor"],
        context=[tarefa_propor],
    )

    tarefa_executar = Task(
        description=(
            "Para cada item AUTO-EXECUTAR:\n"
            "1. Escreva o código completo (HTML/CSS/JS puro)\n"
            f"2. Use create_github_pr com branch 'agent/{loop_key}-YYYY-MM-DD-nome'\n"
            f"3. Use supabase_write_agent_run com loop_name='{loop_key}' para "
            "registrar a execução\n"
            "Se não houver itens AUTO-EXECUTAR, registre isso e finalize."
        ),
        expected_output="URLs dos PRs criados ou confirmação de que não havia itens.",
        agent=agents["executor"],
        context=[tarefa_decidir],
    )

    tarefa_aprender = Task(
        description=(
            f"Feche o ciclo de {nome}:\n"
            f"1. Use supabase_metrics com loop='{loop_key}' para métricas finais\n"
            "2. Use update_memory para salvar no CLAUDE.md, prefixando a "
            f"entrada com '[{nome}]' e incluindo:\n"
            "   - Métricas (antes vs. agora)\n"
            "   - PRs criados automaticamente\n"
            "   - Itens enviados para Breno\n"
            "   - PRIORIDADE DO PRÓXIMO CICLO desta área\n"
            "   - Queries de pesquisa usadas (para não repetir)\n"
            f"3. Use notify_breno com subject 'StaFlow [{nome}]: resumo do ciclo' "
            "e HTML com métricas, ações, pendências."
        ),
        expected_output=(
            "Confirmação de que CLAUDE.md foi atualizado e email enviado, "
            "com o conteúdo exato salvo na memória."
        ),
        agent=agents["observador"],
        context=[tarefa_coletar, tarefa_analisar, tarefa_propor, tarefa_decidir, tarefa_executar],
    )

    return {
        "coletar": tarefa_coletar, "pesquisar": tarefa_pesquisar,
        "analisar": tarefa_analisar, "propor": tarefa_propor,
        "decidir": tarefa_decidir, "executar": tarefa_executar,
        "aprender": tarefa_aprender,
    }


def build_meta_task(meta_agente) -> Task:
    """Tarefa única do Meta-Agente — avalia todos os loops da semana."""
    return Task(
        description=(
            "Você NÃO opera nenhum produto — sua função é melhorar OS "
            "AGENTES de TODOS os loops (marketing, produto, financeiro, "
            "suporte).\n\n"
            "1. Use read_memory para ver o histórico geral da semana.\n"
            "2. Use supabase_feedback_history para ver aprovações/rejeições "
            "do Breno com motivo, em qualquer loop.\n"
            "3. Use read_prompts (sem parâmetro) para ver os prompts de "
            "TODOS os loops.\n"
            "4. Identifique um padrão em UM loop específico: algum agente "
            "comete o mesmo erro mais de uma vez? Algum tipo de proposta é "
            "sempre rejeitado pelo mesmo motivo?\n"
            "5. SE houver um padrão claro (2+ ocorrências), proponha uma "
            "mudança pontual no goal ou backstory de UM único agente de UM "
            "único loop.\n"
            "6. Use create_github_pr para propor: branch "
            "'agent/evolve-<loop>-YYYY-MM-DD', title '[Meta-Agente] "
            "Evolução <loop>: <agente> — <resumo>', body explicando o "
            "padrão observado, files com o JSON COMPLETO e atualizado de "
            "scripts/crew/prompts/<loop>.json (mude apenas o agente "
            "identificado, mantenha os outros 6 exatamente iguais).\n"
            "7. Se NÃO houver padrão claro em nenhum loop, NÃO crie PR. "
            "Apenas declare 'sem mudanças necessárias' e explique por quê.\n\n"
            "IMPORTANTE: nunca proponha mudança em mais de 1 agente por "
            "ciclo. Toda mudança precisa ser pequena, específica e "
            "testável — e só entra em vigor se o Breno aprovar o PR."
        ),
        expected_output=(
            "OU (a) confirmação de PR criado com o padrão observado e a "
            "mudança proposta, OU (b) confirmação explícita de que nenhuma "
            "mudança foi necessária, com justificativa."
        ),
        agent=meta_agente,
    )
