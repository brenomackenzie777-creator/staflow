# StaFlow — Memória Compartilhada dos Agentes
<!-- Este arquivo é lido por todos os agentes antes de agir.
     É atualizado automaticamente após cada execução.
     Não editar manualmente — deixe os agentes gerenciarem. -->

## Contexto do Produto
- **Produto:** StaFlow — controle de presença para condomínios
- **URL produção:** https://staflow.app.br
- **Stack:** HTML/CSS/JS estático + Supabase + Stripe LIVE + Vercel
- **Status:** Em produção com usuários reais

## Planos e Preços (DEFINITIVOS — não alterar)
| Plano     | Mensal    | Funcionários |
|-----------|-----------|--------------|
| Starter   | R$ 0      | até 3        |
| Pro       | R$ 99/mês | até 15       |
| Advanced  | R$ 159/mês| até 35       |
| Scale     | R$ 279/mês| até 100      |

## Identidade Visual
- Logo: variante I — dois blocos azuis geométricos em S
- Cor primária: #3B82F6 (azul)
- Fundo principal: #111827
- Superfícies: #1F2937
- Texto: #F9FAFB
- Fonte: Inter

## Loops Especializados (Railway, roda de segunda a sexta 08:00 BRT)
Cada dia da semana roda UM loop de 7 agentes focado numa área do negócio —
não é mais um loop geral tocando tudo de uma vez.

| Dia | Loop | Foco |
|-----|------|------|
| Segunda | Marketing / Crescimento | Aquisição, conversão, campanhas, copy |
| Terça | Produto / Desenvolvimento | Bugs, UX, funcionalidades, qualidade técnica |
| Quarta | Financeiro / Assinaturas | Churn, conversão entre planos, receita |
| Quinta | Suporte / Sucesso do Cliente | Feedbacks, onboarding, atendimento |
| Sexta | Meta-Agente Evolutivo | Avalia a semana inteira nos 4 loops |

Cada loop tem os mesmos 8 papéis (Coletor → Pesquisador → Analista →
Estrategista → Decisor → Executor → Observador → **Relator**), mas com prompts
próprios em `scripts/crew/prompts/<loop>.json`. O Meta-Agente é compartilhado
entre todos os loops (`scripts/crew/prompts/meta.json`) e lê o histórico de
aprovações/rejeições de qualquer loop antes de propor uma mudança de prompt.

**O Relator** é o último agente de cada ciclo e o único que fala com o Breno.
Ele traduz tudo para português leigo (o Breno é CEO, não programador) e envia
por email via Resend. Na sexta-feira há um Relator Semanal que fecha a semana
consolidando os 4 loops. Termos técnicos são proibidos nos relatórios.

Configuração de cada loop (foco e queries de pesquisa) fica em
`scripts/crew/loops.json`. Execuções ficam marcadas no Supabase
(`agent_runs.loop_name`) para não misturar histórico entre áreas.

## Regras de Ouro (todos os agentes devem seguir)
1. Nunca inventar dados ou métricas — sempre ler do Supabase
2. Preços são os da tabela acima — nunca outros valores
3. Output sempre em Markdown estruturado
4. Primeira linha do output = resumo de 1 linha (vai para o log)
5. Se houver dúvida, registrar no output e sinalizar para o Breno
6. **Nenhum agente se auto-modifica em produção.** O Meta-Agente só propõe
   mudanças de prompt via Pull Request — elas só valem depois que o Breno
   revisa e faz merge no GitHub.

## Últimas Execuções
<!-- Preenchido automaticamente pelos agentes -->
(aguardando primeira execução automática)

---
*Última atualização: arquivo inicial — agentes ainda não rodaram*
