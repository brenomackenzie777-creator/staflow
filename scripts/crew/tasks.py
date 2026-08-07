"""
StaFlow — Tarefas de cada agente no loop autoevolutivo
O output do Observador alimenta o Coletor do próximo ciclo via CLAUDE.md.
"""
from crewai import Task
from .agents import (
    coletor, pesquisador, analista,
    estrategista, decisor, executor, observador,
)


# ─── TAREFA 1: COLETAR ──────────────────────────────────────────
tarefa_coletar = Task(
    description=(
        "INÍCIO DO CICLO AUTOEVOLUTIVO.\n\n"
        "Passo 1 — Use read_memory para ler o CLAUDE.md completo. "
        "Identifique: o que foi feito no último ciclo, quais eram as prioridades, "
        "o que funcionou e o que foi rejeitado. Este contexto histórico guia tudo.\n\n"
        "Passo 2 — Use supabase_metrics para coletar os dados atuais do StaFlow: "
        "total de usuários, novos esta semana, assinaturas ativas por plano, "
        "feedbacks recentes, histórico de execuções dos agentes.\n\n"
        "Passo 3 — Compare o estado atual com o histórico: estamos crescendo? "
        "As melhorias anteriores surtiram efeito?\n\n"
        "Se precisar de análise de dados mais profunda, use create_sub_agent."
    ),
    expected_output=(
        "Relatório combinado com:\n"
        "1. Resumo do contexto histórico (últimos ciclos, prioridades identificadas)\n"
        "2. Métricas atuais do Supabase\n"
        "3. Comparação: crescimento ou retração vs. ciclo anterior\n"
        "4. Reflexão do agente (seção obrigatória)"
    ),
    agent=coletor,
)

# ─── TAREFA 2: PESQUISAR ────────────────────────────────────────
tarefa_pesquisar = Task(
    description=(
        "Com base no que o Coletor identificou como prioritário, pesquise o mercado.\n\n"
        "NÃO repita as mesmas queries de ciclos anteriores — evolua a pesquisa. "
        "Se o Coletor indicou uma prioridade específica, aprofunde nela.\n\n"
        "Queries obrigatórias (adapte conforme o contexto do ciclo):\n"
        "1. Baseada na prioridade do ciclo anterior (lida da memória)\n"
        "2. 'software controle presença condomínio Brasil 2026'\n"
        "3. 'síndico profissional app gestão tendências'\n\n"
        "Use create_sub_agent se precisar de análise competitiva aprofundada de um concorrente específico."
    ),
    expected_output=(
        "Relatório de pesquisa com:\n"
        "1. Principais achados por query\n"
        "2. O que é novo vs. o que já sabíamos de ciclos anteriores\n"
        "3. 2-3 oportunidades concretas identificadas\n"
        "4. Reflexão do agente (seção obrigatória)"
    ),
    agent=pesquisador,
)

# ─── TAREFA 3: ANALISAR ─────────────────────────────────────────
tarefa_analisar = Task(
    description=(
        "Analise os dados do Coletor e a pesquisa do Pesquisador em conjunto.\n\n"
        "Responda especificamente:\n"
        "- Onde estamos perdendo usuários ou não convertendo?\n"
        "- O que os feedbacks dizem que precisamos melhorar?\n"
        "- O que os concorrentes têm que nós não temos?\n"
        "- Qual o maior risco para o StaFlow agora?\n"
        "- Qual a maior oportunidade imediata?\n"
        "- Estamos evoluindo em relação ao ciclo anterior?\n\n"
        "Baseie-se apenas nos dados disponíveis. Use create_sub_agent para análises específicas complexas."
    ),
    expected_output=(
        "Análise com:\n"
        "1. 3-5 insights prioritários (cada um com: observação, dados de suporte, implicação)\n"
        "2. Comparação com ciclo anterior (melhorou? piorou? estável?)\n"
        "3. Reflexão do agente (seção obrigatória)"
    ),
    agent=analista,
    context=[tarefa_coletar, tarefa_pesquisar],
)

# ─── TAREFA 4: PROPOR ───────────────────────────────────────────
tarefa_propor = Task(
    description=(
        "Com base na análise, crie propostas concretas de melhoria.\n\n"
        "IMPORTANTE: Consulte o histórico de propostas anteriores (via contexto do Coletor). "
        "Não repita o que foi rejeitado. Priorize o que foi bem recebido.\n\n"
        "Para cada proposta inclua:\n"
        "- TÍTULO: nome curto\n"
        "- O QUÊ: descrição do que muda\n"
        "- POR QUÊ: insight que justifica\n"
        "- IMPACTO: baixo/médio/alto\n"
        "- ESFORÇO: pequeno (<2h) / médio (1-2 dias) / grande (>1 semana)\n"
        "- RISCO: baixo (só UI/copy) / médio / alto (mudança de DB ou fluxo crítico)\n\n"
        "Máximo 5 propostas. Use create_sub_agent para detalhar implementações complexas."
    ),
    expected_output=(
        "Lista de até 5 propostas formatadas com todos os campos acima, "
        "mais a reflexão do agente (seção obrigatória)."
    ),
    agent=estrategista,
    context=[tarefa_analisar],
)

# ─── TAREFA 5: DECIDIR ──────────────────────────────────────────
tarefa_decidir = Task(
    description=(
        "Analise as propostas e decida o que executar.\n\n"
        "REGRA DE DECISÃO AUTÔNOMA:\n"
        "- AUTO-EXECUTAR: esforço PEQUENO + risco BAIXO → vai direto pro Executor\n"
        "- APROVAR-BRENO: esforço MÉDIO/GRANDE ou risco MÉDIO/ALTO → notifica Breno\n\n"
        "Você prefere agir. Só consulta o Breno quando realmente necessário. "
        "Para tarefas APROVAR-BRENO, use notify_breno com subject "
        "'StaFlow: propostas aguardando aprovação' e um resumo HTML claro.\n\n"
        "Máximo 2 tarefas AUTO-EXECUTAR por ciclo."
    ),
    expected_output=(
        "Decisão final:\n"
        "- Lista AUTO-EXECUTAR (com descrição detalhada de implementação)\n"
        "- Lista APROVAR-BRENO (confirmação de email enviado)\n"
        "- Reflexão do agente (seção obrigatória)"
    ),
    agent=decisor,
    context=[tarefa_propor],
)

# ─── TAREFA 6: EXECUTAR ─────────────────────────────────────────
tarefa_executar = Task(
    description=(
        "Para cada tarefa AUTO-EXECUTAR:\n\n"
        "1. Se for complexa, use create_sub_agent para partes específicas "
        "(ex: sub-agente de UI para o HTML, sub-agente de lógica para o JS)\n"
        "2. Escreva o código completo e funcional\n"
        "3. Use create_github_pr com:\n"
        "   - branch: 'agent/auto-YYYY-MM-DD-nome'\n"
        "   - title: '[Agent] nome da melhoria'\n"
        "   - body: o quê muda, por quê, como testar\n"
        "   - files: dict com arquivos modificados\n"
        "4. Use supabase_write_agent_run para registrar a execução\n\n"
        "Se não houver tarefas AUTO-EXECUTAR, registre isso e finalize."
    ),
    expected_output=(
        "URLs dos Pull Requests criados (ou confirmação de que não havia tarefas), "
        "mais a reflexão do agente (seção obrigatória)."
    ),
    agent=executor,
    context=[tarefa_decidir],
)

# ─── TAREFA 7: APRENDER — fecha o loop ──────────────────────────
tarefa_aprender = Task(
    description=(
        "FECHAMENTO DO CICLO AUTOEVOLUTIVO.\n\n"
        "Você está escrevendo para o PRÓXIMO Coletor — seja útil para ele.\n\n"
        "Passo 1 — Use supabase_metrics para capturar o estado atual (ponto de comparação)\n\n"
        "Passo 2 — Use update_memory para salvar no CLAUDE.md:\n"
        "  • Data e número do ciclo\n"
        "  • Métricas: usuários, assinaturas (antes vs. ciclo anterior)\n"
        "  • O que foi executado automaticamente (PRs criados)\n"
        "  • O que foi enviado para o Breno aprovar\n"
        "  • Reflexões sintetizadas de cada agente\n"
        "  • PRIORIDADE DO PRÓXIMO CICLO: o que o Coletor deve focar\n"
        "  • Queries de pesquisa já usadas (para o Pesquisador não repetir)\n\n"
        "Passo 3 — Use notify_breno com subject 'StaFlow: resumo do ciclo semanal' "
        "e um HTML com: métricas, ações tomadas, pendências de aprovação.\n\n"
        "Passo 4 — Escreva sua reflexão sobre a evolução do sistema de agentes."
    ),
    expected_output=(
        "Confirmação de que CLAUDE.md foi atualizado e email enviado. "
        "Inclua o conteúdo exato que foi salvo na memória — "
        "ele será a base do próximo ciclo."
    ),
    agent=observador,
    context=[tarefa_coletar, tarefa_analisar, tarefa_propor, tarefa_decidir, tarefa_executar],
)
