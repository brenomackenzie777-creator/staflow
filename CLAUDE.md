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

## Agentes e Responsabilidades (loop autoevolutivo — Railway, toda segunda 08:00 BRT)
| # | Agente | Foco |
|---|--------|------|
| 1 | Coletor de Dados | Lê CLAUDE.md + métricas reais do Supabase |
| 2 | Pesquisador de Mercado | Pesquisa concorrentes e tendências (Tavily) |
| 3 | Analista de Dados | Cruza dados internos + pesquisa em insights |
| 4 | Estrategista de Crescimento | Propõe até 3 melhorias concretas |
| 5 | Decisor de Prioridades | Filtra: auto-executa ou pede aprovação do Breno |
| 6 | Executor de Código | Escreve código e abre PR no GitHub |
| 7 | Observador de Aprendizado | Salva aprendizados aqui para o próximo ciclo |
| 8 | Meta-Agente Evolutivo | Analisa aprovações/rejeições e propõe mudanças de prompt via PR |

Os prompts (goal/backstory) dos agentes 1–7 ficam em `scripts/crew/prompts.json`,
não fixos no código — isso permite que o Meta-Agente proponha mudanças reais de
comportamento sem editar Python.

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
