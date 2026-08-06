"""
StaFlow — Tarefas de cada agente no loop autoevolutivo
"""
from crewai import Task
from .agents import (
    coletor, pesquisador, analista,
    estrategista, decisor, executor, observador,
)


# ─── TAREFA 1: COLETAR ──────────────────────────────────────────
tarefa_coletar = Task(
    description=(
        "Use a ferramenta supabase_metrics para coletar todos os dados atuais do StaFlow. "
        "Retorne um relatório estruturado com: total de usuários, novos esta semana, "
        "assinaturas ativas por plano, feedbacks recentes dos usuários, e histórico "
        "de execuções anteriores dos agentes (o que foi aprovado/rejeitado pelo Breno)."
    ),
    expected_output=(
        "Relatório JSON ou markdown com todos os dados coletados do Supabase, "
        "incluindo métricas numéricas e textos de feedback dos usuários."
    ),
    agent=coletor,
)

# ─── TAREFA 2: PESQUISAR ────────────────────────────────────────
tarefa_pesquisar = Task(
    description=(
        "Use a ferramenta tavily_search para pesquisar as seguintes queries:\n"
        "1. 'software controle presença condomínio Brasil 2026'\n"
        "2. 'gestão condomínio app sindico tendencias'\n"
        "3. 'concorrentes StaFlow ponto eletrônico condomínio'\n\n"
        "Compile os resultados mais relevantes: o que os concorrentes estão lançando, "
        "que problemas os síndicos estão reclamando online, e oportunidades de mercado."
    ),
    expected_output=(
        "Relatório de pesquisa com: principais concorrentes identificados, "
        "tendências do mercado, e 2-3 oportunidades concretas para o StaFlow."
    ),
    agent=pesquisador,
)

# ─── TAREFA 3: ANALISAR ─────────────────────────────────────────
tarefa_analisar = Task(
    description=(
        "Com base nos dados coletados (Tarefa 1) e na pesquisa de mercado (Tarefa 2), "
        "faça uma análise completa. Identifique:\n"
        "- Onde estamos perdendo usuários ou não convertendo?\n"
        "- O que os feedbacks dizem que precisamos melhorar?\n"
        "- O que os concorrentes têm que nós não temos?\n"
        "- Qual o maior risco para o StaFlow agora?\n"
        "- Qual a maior oportunidade imediata?\n\n"
        "Seja específico e baseado nos dados. Sem especulações."
    ),
    expected_output=(
        "Análise estruturada com 3-5 insights prioritários, cada um com: "
        "observação, dados de suporte, e implicação para o produto."
    ),
    agent=analista,
    context=[tarefa_coletar, tarefa_pesquisar],
)

# ─── TAREFA 4: PROPOR ───────────────────────────────────────────
tarefa_propor = Task(
    description=(
        "Com base na análise (Tarefa 3), crie uma lista de melhorias concretas. "
        "Para cada proposta inclua:\n"
        "- TÍTULO: nome curto da melhoria\n"
        "- O QUÊ: descrição clara do que muda\n"
        "- POR QUÊ: qual insight da análise justifica isso\n"
        "- IMPACTO ESPERADO: baixo/médio/alto + métrica de sucesso\n"
        "- ESFORÇO: pequeno (< 2h) / médio (1-2 dias) / grande (+ 1 semana)\n"
        "- RISCO: baixo (só UI/copy) / médio / alto (mudança de DB ou fluxo crítico)\n\n"
        "Máximo 5 propostas por ciclo."
    ),
    expected_output=(
        "Lista de até 5 propostas de melhoria formatadas com todos os campos acima."
    ),
    agent=estrategista,
    context=[tarefa_analisar],
)

# ─── TAREFA 5: DECIDIR ──────────────────────────────────────────
tarefa_decidir = Task(
    description=(
        "Analise as propostas (Tarefa 4) e tome as decisões:\n\n"
        "AUTO-EXECUTAR (máx. 2): propostas com esforço PEQUENO e risco BAIXO. "
        "Essas vão direto para o Executor.\n\n"
        "APROVAR-BRENO: todo o resto. Para essas, use notify_breno para enviar um email "
        "ao Breno com subject 'StaFlow: propostas aguardando sua aprovação' e um "
        "resumo HTML das propostas.\n\n"
        "Retorne uma lista clara: quais vão para AUTO-EXECUTAR e quais para APROVAR-BRENO."
    ),
    expected_output=(
        "Decisão final: lista de tarefas AUTO-EXECUTAR (com descrição detalhada do que fazer) "
        "e lista de tarefas APROVAR-BRENO (já notificadas por email)."
    ),
    agent=decisor,
    context=[tarefa_propor],
)

# ─── TAREFA 6: EXECUTAR ─────────────────────────────────────────
tarefa_executar = Task(
    description=(
        "Para cada tarefa marcada como AUTO-EXECUTAR (Tarefa 5):\n\n"
        "1. Escreva o código HTML/CSS/JS necessário para implementar a melhoria\n"
        "2. Use create_github_pr para criar um PR com:\n"
        "   - branch: 'agent/auto-YYYY-MM-DD-nome-da-melhoria'\n"
        "   - title: '[Agent] nome da melhoria'\n"
        "   - body: descrição clara do que muda, por quê, e como testar\n"
        "   - files: dict com os arquivos modificados\n"
        "3. Use supabase_write_agent_run para registrar a execução\n\n"
        "Se não houver tarefas AUTO-EXECUTAR, registre isso e finalize."
    ),
    expected_output=(
        "URLs dos Pull Requests criados (ou confirmação de que não havia tarefas "
        "para auto-executar neste ciclo)."
    ),
    agent=executor,
    context=[tarefa_decidir],
)

# ─── TAREFA 7: APRENDER ─────────────────────────────────────────
tarefa_aprender = Task(
    description=(
        "Finalize o ciclo com aprendizados:\n\n"
        "1. Use supabase_metrics para ler o estado atual (para comparar com próximo ciclo)\n"
        "2. Resuma o que aconteceu neste ciclo: dados coletados, insights identificados, "
        "   propostas feitas, tarefas executadas automaticamente, tarefas enviadas pro Breno\n"
        "3. Identifique: o que funcionou bem neste ciclo? O que pode melhorar?\n"
        "4. Use update_memory para salvar esses aprendizados no CLAUDE.md\n"
        "5. Use notify_breno para enviar um email de resumo do ciclo com subject "
        "   'StaFlow: resumo do ciclo semanal' e o relatório completo em HTML\n\n"
        "Este resumo alimenta o próximo loop."
    ),
    expected_output=(
        "Confirmação de que CLAUDE.md foi atualizado e email de resumo foi enviado. "
        "Inclua o texto do aprendizado registrado."
    ),
    agent=observador,
    context=[tarefa_coletar, tarefa_analisar, tarefa_propor, tarefa_decidir, tarefa_executar],
)
