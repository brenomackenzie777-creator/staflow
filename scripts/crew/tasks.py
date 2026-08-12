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
            "1. Use ler_recados_breno PRIMEIRO — são pedidos/comentários que "
            "o próprio Breno deixou pro time. Se houver algum relevante para "
            f"'{loop_key}' (no campo area_alvo, ou sem área definida), ele é "
            "PRIORIDADE MÁXIMA deste ciclo — mais importante que qualquer "
            "prioridade que o time escolheria sozinho. Inclua o id de cada "
            "recado relevante no relatório, para o Decisor conseguir "
            "respondê-lo depois.\n"
            "2. Use read_memory para ler o histórico geral.\n"
            f"3. Use supabase_metrics com loop='{loop_key}' para coletar "
            "dados relevantes a esta área.\n"
            "4. Compare com o ciclo anterior desta mesma área: estamos "
            "melhorando?"
        ),
        expected_output=(
            "Relatório com: recados do Breno relevantes (com id) + contexto "
            "histórico desta área + métricas + comparação com o ciclo anterior."
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
            "Máximo 2 itens AUTO-EXECUTAR por ciclo.\n\n"
            "Se o Coletor listou algum recado do Breno com id: para cada um, "
            "use responder_recado_breno. Se o ciclo já resolveu ou tratou o "
            "pedido, status='atendido' explicando o que foi feito. Se o "
            "ciclo não deu conta agora, status='em_andamento' ou "
            "'nao_prioridade', explicando por quê e quando será tratado. "
            f"Sempre informe atendido_por='{loop_key}'. NUNCA deixe um "
            "recado do Breno sem resposta quando ele foi listado pelo Coletor."
        ),
        expected_output=(
            "Lista AUTO-EXECUTAR com descrição de implementação + lista "
            "APROVAR-BRENO com confirmação de notificação enviada + "
            "confirmação de que todo recado do Breno listado pelo Coletor "
            "foi respondido."
        ),
        agent=agents["decisor"],
        context=[tarefa_propor, tarefa_coletar],
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
            "   - Queries de pesquisa usadas (para não repetir)"
        ),
        expected_output=(
            "Confirmação de que CLAUDE.md foi atualizado, com o conteúdo "
            "exato salvo na memória."
        ),
        agent=agents["observador"],
        context=[tarefa_coletar, tarefa_analisar, tarefa_propor, tarefa_decidir, tarefa_executar],
    )

    tarefa_relatar = Task(
        description=(
            f"Escreva o relatório do ciclo de {nome} para o Breno (CEO, não "
            "programador). Ele precisa entender tudo sem saber nada de código.\n\n"
            "Estruture o email em HTML simples, com estas seções:\n\n"
            "1. RESUMO EM UMA FRASE — o que aconteceu hoje, direto\n"
            "2. OS NÚMEROS — as métricas desta área, sempre comparando com o "
            "ciclo anterior. Se não houver dado, diga que ainda não temos\n"
            "3. O QUE DESCOBRIMOS — os principais achados da análise e da "
            "pesquisa de mercado, em linguagem comum\n"
            "4. O QUE JÁ FIZEMOS — mudanças que o time preparou sozinho. "
            "Explique o que muda na prática para o usuário do StaFlow, não "
            "como foi feito tecnicamente\n"
            "5. PRECISA DA SUA DECISÃO — o que está esperando ele. Para cada "
            "item: o que é, por que importa, e o que acontece se ele aprovar "
            "ou não. Se não há nada esperando, diga isso claramente\n"
            "6. O QUE VEM NO PRÓXIMO CICLO desta área\n\n"
            "Use HTML básico (h2, p, ul, li, strong). Nada de jargão técnico.\n"
            f"Envie com notify_breno, subject: 'StaFlow [{nome}] — relatório de hoje'."
        ),
        expected_output=(
            "Confirmação do envio do email + o texto completo do relatório "
            "que foi enviado."
        ),
        agent=agents["relator"],
        context=[tarefa_coletar, tarefa_pesquisar, tarefa_analisar,
                 tarefa_propor, tarefa_decidir, tarefa_executar, tarefa_aprender],
    )

    return {
        "coletar": tarefa_coletar, "pesquisar": tarefa_pesquisar,
        "analisar": tarefa_analisar, "propor": tarefa_propor,
        "decidir": tarefa_decidir, "executar": tarefa_executar,
        "aprender": tarefa_aprender, "relatar": tarefa_relatar,
    }


def build_ceo_tasks(agents: dict) -> dict:
    """★ 10/08/2026 — o ciclo único da operação inteira.

    Quatro etapas: entender → decidir UMA coisa → fazer → contar pro Breno.
    Cada tarefa recebe só o contexto que precisa, pra conversa não inchar e
    estourar o limite de tokens por minuto do Groq."""

    tarefa_entender = Task(
        description=(
            "Você está abrindo o ciclo diário da StaFlow. Sua função é dizer "
            "onde a empresa está HOJE.\n\n"
            "1. Use panorama_negocio (parâmetro vazio) — é sua fonte principal.\n"
            "2. Use read_memory pra ver o que os ciclos anteriores decidiram.\n\n"
            "Depois escreva um retrato curto e honesto cobrindo:\n"
            "- CADASTRO: entrou gente nova? quantos nos últimos 7 dias?\n"
            "- ATIVAÇÃO: quem cadastrou e nunca bateu ponto? (é o furo mais caro)\n"
            "- RECEITA: quantos pagam DE VERDADE (com assinatura no Stripe)?\n"
            "- VOZ DO CLIENTE: o que reclamaram?\n"
            "- RECADOS DO BRENO: liste cada recado pendente COM O ID — o "
            "Executor vai precisar do id pra responder.\n"
            "- MUDOU O QUÊ desde o ciclo anterior?\n\n"
            "Regra dura: número que não está no panorama, você não cita. "
            "Se algo não dá pra saber, escreva 'não temos esse dado'. "
            "Empresa nova tem número pequeno — isso não é problema, "
            "interpretar errado é."
        ),
        expected_output=(
            "Retrato da empresa em tópicos, com os números reais, os recados "
            "pendentes do Breno com seus ids, e o que mudou desde o último ciclo."
        ),
        agent=agents["analista"],
    )

    tarefa_decidir = Task(
        description=(
            "Você é o CEO. Escolha A ÚNICA prioridade da empresa para hoje.\n\n"
            "Como decidir:\n"
            "- Se há recado do Breno pendente, ele É a prioridade. Ponto.\n"
            "- Senão, olhe o funil inteiro (descobre → cadastra → ativa → paga "
            "→ fica) e ataque onde está mais furado AGORA.\n"
            "- Nesta fase (produto no ar, quase nenhum cliente pagando), "
            "conseguir e ativar cliente vale mais que refinar produto. "
            "Só fuja disso se o dado mostrar o contrário.\n"
            "- Se precisar de contexto de fora, pode usar tavily_search uma vez. "
            "Se não precisar, não use — economiza tempo e cota.\n\n"
            "Entregue:\n"
            "1. A PRIORIDADE em uma frase\n"
            "2. POR QUE ela vem antes das outras (com o número que sustenta)\n"
            "3. O QUE FAZER, concreto o bastante pro Executor executar hoje\n"
            "4. COMO SABER SE DEU CERTO (qual número deve mexer, e até quando)\n\n"
            "Uma prioridade. Não duas. Se você listar duas, você falhou na tarefa."
        ),
        expected_output=(
            "A prioridade única do dia, a justificativa com dado, a ação "
            "concreta e o sinal de sucesso."
        ),
        agent=agents["estrategista"],
        context=[tarefa_entender],
    )

    tarefa_fazer = Task(
        description=(
            "Execute a prioridade que o CEO definiu. Entregue trabalho pronto, "
            "não conselho.\n\n"
            "- Se for conteúdo/copy: escreva o texto COMPLETO, pronto pra usar.\n"
            "- Se for abordagem comercial: escreva a mensagem inteira.\n"
            "- Se for mudança no produto: descreva exatamente o que muda e em "
            "qual tela, em português comum. Se for arquivo crítico do site, "
            "NÃO tente alterar — entregue a proposta escrita.\n\n"
            "Depois, sem falta:\n"
            "1. Para CADA recado do Breno que o Analista listou, chame "
            "responder_recado_breno com o id, status ('atendido' se foi "
            "tratado neste ciclo, 'nao_prioridade' com o motivo se não foi) "
            "e atendido_por='ceo'.\n"
            "2. Chame supabase_write_agent_run com loop_name='ceo', "
            "agent_name='executor', output_summary= a prioridade do dia em "
            "uma linha, e output_completo= o que você produziu.\n"
            "3. Chame update_memory com um resumo curto começando por '[CEO]', "
            "incluindo a prioridade de hoje e qual deve ser a de amanhã."
        ),
        expected_output=(
            "O trabalho pronto (texto/proposta completa) + confirmação de que "
            "os recados foram respondidos, o ciclo foi registrado e a memória "
            "atualizada."
        ),
        agent=agents["executor"],
        context=[tarefa_entender, tarefa_decidir],
    )

    tarefa_contar = Task(
        description=(
            "Escreva o e-mail do dia para o Breno. Ele é o dono, não é "
            "programador, e vai ler no celular entre uma ligação e outra.\n\n"
            "Estrutura, em HTML simples (h2, p, ul, li, strong):\n"
            "1. <b>Em uma frase:</b> o que a empresa fez hoje\n"
            "2. <b>Os números:</b> os 3 ou 4 que importam, comparados com o "
            "ciclo anterior. Sem dado, diga 'ainda não temos'\n"
            "3. <b>A prioridade de hoje e por quê</b>\n"
            "4. <b>O que ficou pronto:</b> entregue o material aqui mesmo, "
            "pra ele copiar direto do e-mail\n"
            "5. <b>Preciso de você:</b> o que depende de decisão dele. "
            "Se não depende nada, escreva 'nada hoje'\n"
            "6. <b>Amanhã:</b> a próxima prioridade\n\n"
            "Proibido: 'deploy', 'endpoint', 'query', 'bug', 'API', 'commit'. "
            "Fale por efeito, não por mecanismo.\n"
            "Se o ciclo rendeu pouco, diga que rendeu pouco e por quê — "
            "relatório inflado destrói a confiança dele no time.\n\n"
            "Envie com notify_breno, subject: 'StaFlow — o que fizemos hoje'."
        ),
        expected_output=(
            "Confirmação do envio do e-mail e o texto completo do que foi enviado."
        ),
        agent=agents["relator"],
        context=[tarefa_entender, tarefa_decidir, tarefa_fazer],
    )

    return {"entender": tarefa_entender, "decidir": tarefa_decidir,
            "fazer": tarefa_fazer, "contar": tarefa_contar}


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
            "3. Use listar_agentes para ver o índice de todas as áreas, "
            "depois use read_prompts informando a área escolhida.\n"
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


def build_meta_relatorio_task(relator, tarefa_meta) -> Task:
    """Relatório semanal de sexta — fecha a semana para o CEO."""
    return Task(
        description=(
            "Escreva o FECHAMENTO DA SEMANA para o Breno (CEO, não "
            "programador). Ele precisa entender tudo sem saber nada de código.\n\n"
            "1. Use read_memory para ver tudo que aconteceu nos 4 loops "
            "desta semana (Marketing segunda, Produto terça, Financeiro "
            "quarta, Suporte quinta).\n"
            "2. Use supabase_metrics com loop='todos' para os números "
            "gerais do StaFlow.\n\n"
            "Estruture o email em HTML simples, com estas seções:\n\n"
            "1. A SEMANA EM UMA FRASE\n"
            "2. OS NÚMEROS DO STAFLOW — usuários, assinaturas, comparando "
            "com a semana anterior. Se não houver dado, diga que ainda não temos\n"
            "3. O QUE CADA ÁREA FEZ — um parágrafo curto por área "
            "(Marketing, Produto, Financeiro, Suporte)\n"
            "4. TUDO QUE ESPERA SUA DECISÃO — lista consolidada da semana "
            "inteira. Para cada item: o que é, por que importa, o que "
            "acontece se aprovar ou não. Se não há nada, diga isso\n"
            "5. O TIME ESTÁ MELHORANDO? — o que o Meta-Agente observou e "
            "se ele propôs alguma mudança no jeito dos agentes trabalharem\n"
            "6. PRIORIDADES DA PRÓXIMA SEMANA\n\n"
            "Use HTML básico (h2, p, ul, li, strong). Nada de jargão técnico.\n"
            "Envie com notify_breno, subject: "
            "'StaFlow — fechamento da semana'."
        ),
        expected_output=(
            "Confirmação do envio do email + o texto completo do relatório "
            "semanal que foi enviado."
        ),
        agent=relator,
        context=[tarefa_meta],
    )
