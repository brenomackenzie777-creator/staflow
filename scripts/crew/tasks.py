"""
StaFlow — Tarefas do loop autoevolutivo
"""
from crewai import Task
from .agents import (
    coletor, pesquisador, analista,
    estrategista, decisor, executor, observador,
)

# ─── TAREFA 1: COLETAR ──────────────────────────────────────────
tarefa_coletar = Task(
    description=(
        "1. Use read_memory para ler o CLAUDE.md completo e entender o histórico.\n"
        "2. Use supabase_metrics para coletar dados atuais: usuários, assinaturas, feedbacks.\n"
        "3. Compare: estamos crescendo em relação ao ciclo anterior?"
    ),
    expected_output=(
        "Relatório com: (a) contexto histórico resumido, "
        "(b) métricas atuais do Supabase, "
        "(c) comparação com ciclo anterior."
    ),
    agent=coletor,
)

# ─── TAREFA 2: PESQUISAR ────────────────────────────────────────
tarefa_pesquisar = Task(
    description=(
        "Com base no que o Coletor identificou como prioritário, faça 3 pesquisas:\n"
        "1. Baseada na prioridade do ciclo anterior\n"
        "2. 'software controle presença condomínio Brasil 2026'\n"
        "3. 'síndico profissional app tendências'\n"
        "Não repita queries de ciclos anteriores."
    ),
    expected_output=(
        "Relatório com: (a) achados principais por query, "
        "(b) o que é novo vs. já sabíamos, "
        "(c) 2-3 oportunidades concretas."
    ),
    agent=pesquisador,
)

# ─── TAREFA 3: ANALISAR ─────────────────────────────────────────
tarefa_analisar = Task(
    description=(
        "Analise os dados do Coletor e pesquisa do Pesquisador:\n"
        "- Onde estamos perdendo conversão?\n"
        "- O que os feedbacks dizem?\n"
        "- Qual o maior risco e a maior oportunidade agora?\n"
        "- Estamos melhorando vs. ciclo anterior?\n"
        "Baseie-se apenas nos dados reais disponíveis."
    ),
    expected_output=(
        "3-5 insights prioritários, cada um com: "
        "observação, dado de suporte, implicação."
    ),
    agent=analista,
    context=[tarefa_coletar, tarefa_pesquisar],
)

# ─── TAREFA 4: PROPOR ───────────────────────────────────────────
tarefa_propor = Task(
    description=(
        "Com base na análise, proponha até 3 melhorias. Para cada uma:\n"
        "TÍTULO, O QUÊ muda, POR QUÊ (insight), "
        "IMPACTO (alto/médio/baixo), ESFORÇO (pequeno/médio/grande), "
        "RISCO (baixo=só UI/copy | médio | alto=banco/fluxo crítico)\n"
        "Não repita propostas rejeitadas em ciclos anteriores."
    ),
    expected_output="Lista de até 3 propostas com todos os campos preenchidos.",
    agent=estrategista,
    context=[tarefa_analisar],
)

# ─── TAREFA 5: DECIDIR ──────────────────────────────────────────
tarefa_decidir = Task(
    description=(
        "Filtre as propostas:\n"
        "AUTO-EXECUTAR: esforço PEQUENO + risco BAIXO → vai para o Executor.\n"
        "APROVAR-BRENO: todo o resto → use notify_breno com subject "
        "'StaFlow: propostas aguardando aprovação' e resumo HTML.\n"
        "Máximo 2 itens AUTO-EXECUTAR por ciclo."
    ),
    expected_output=(
        "Lista AUTO-EXECUTAR com descrição de implementação + "
        "lista APROVAR-BRENO com confirmação de notificação enviada."
    ),
    agent=decisor,
    context=[tarefa_propor],
)

# ─── TAREFA 6: EXECUTAR ─────────────────────────────────────────
tarefa_executar = Task(
    description=(
        "Para cada item AUTO-EXECUTAR:\n"
        "1. Escreva o código completo (HTML/CSS/JS puro)\n"
        "2. Use create_github_pr com branch 'agent/auto-YYYY-MM-DD-nome'\n"
        "3. Use supabase_write_agent_run para registrar a execução\n"
        "Se não houver itens AUTO-EXECUTAR, registre isso e finalize."
    ),
    expected_output="URLs dos PRs criados ou confirmação de que não havia itens.",
    agent=executor,
    context=[tarefa_decidir],
)

# ─── TAREFA 7: APRENDER ─────────────────────────────────────────
tarefa_aprender = Task(
    description=(
        "Feche o ciclo:\n"
        "1. Use supabase_metrics para capturar métricas finais\n"
        "2. Use update_memory para salvar no CLAUDE.md:\n"
        "   - Data e número do ciclo\n"
        "   - Métricas (antes vs. agora)\n"
        "   - PRs criados automaticamente\n"
        "   - Itens enviados para Breno\n"
        "   - PRIORIDADE DO PRÓXIMO CICLO\n"
        "   - Queries de pesquisa usadas (para não repetir)\n"
        "3. Use notify_breno com subject 'StaFlow: resumo do ciclo semanal' "
        "e HTML com métricas, ações, pendências."
    ),
    expected_output=(
        "Confirmação de que CLAUDE.md foi atualizado e email enviado. "
        "Inclua o conteúdo exato salvo na memória."
    ),
    agent=observador,
    context=[tarefa_coletar, tarefa_analisar, tarefa_propor, tarefa_decidir, tarefa_executar],
)
