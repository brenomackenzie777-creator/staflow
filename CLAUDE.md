# StaFlow — Memória Compartilhada dos Agentes
<!-- Este arquivo é lido por todos os agentes antes de agir.
     É atualizado automaticamente após cada execução.
     Não editar manualmente — deixe os agentes gerenciarem. -->

## Contexto do Produto
- **Produto:** StaFlow — controle de presença para condomínios
- **URL produção:** https://staflow.app.br
- **Stack:** HTML/CSS/JS estático + Supabase + Stripe LIVE + Vercel
- **Status:** Em produção com usuários reais
- **Mercado e concorrência:** ver `mercado-concorrencia.md` (pesquisa breve de
  07/08/2026 — 327 mil condomínios ativos no Brasil, dois tipos de concorrente:
  ERPs condominiais completos como Superlógica/TownSq/MyCond, e SaaS de ponto
  genérico como Ahgora/Tangerino/Pontotel. StaFlow é nicho: ponto feito
  especificamente pra condomínio, preço mais simples e direto). Os agentes de
  marketing e financeiro têm a ferramenta `read_market_context` pra ler isso.

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

## Loops Especializados (Railway, roda TODO DIA às 08:00 BRT)
**Atualizado em 08/08/2026, a pedido do Breno:** em vez de UM loop por dia
útil, agora roda quantos loops de negócio couberem no dia — todo santo dia,
inclusive fim de semana — até usar **70% da cota diária do Groq** (100 mil
tokens/dia no free tier; os outros 30% ficam de reserva pra retries e pro
Meta-Agente de sexta — passou por 50% → 90% → 70% no mesmo dia, ver nota
de bug abaixo).

**Bug encontrado e corrigido em 08/08/2026 (log real analisado pelo Claude):**
a causa real era MAIOR do que o agendamento duplicado do GitHub Actions
(que também foi desligado — ver abaixo). O Breno tinha **DOIS projetos
Railway diferentes conectados ao mesmo repositório GitHub** (um chamado
"adequate-dream", outro "terrific-celebration"), os dois com cron nas
11:00 UTC e os dois rodando o loop inteiro a cada `git push` — ou seja,
todo commit do dia disparava o time de agentes DUAS VEZES em paralelo,
os dois gastando da mesma chave/cota do Groq sem se enxergar. Foi assim
que a cota de 100.000 tokens/dia sumia mesmo com o orçamento interno
ainda achando que tinha gasto 0%. Resolvido pelo Breno: projeto
"adequate-dream" **excluído**, "terrific-celebration" **renomeado para
"staflow"** — esse é o único projeto Railway que resta rodando o time.
Também foi desligado o agendamento automático do GitHub Actions (ver
`.github/workflows/agentes.yml`); **Railway (projeto "staflow") é agora
o único agendador**. O workflow do GitHub continua disponível pra rodar
manualmente (Actions → Run workflow) se o Railway cair.

A ordem das 4 áreas gira dia a dia (dia do ano % 4) pra nenhuma ficar
sempre por último quando o orçamento aperta.

| Loop | Foco |
|------|------|
| Marketing / Crescimento | Aquisição, conversão, campanhas, copy |
| Produto / Desenvolvimento | Bugs, UX, funcionalidades, qualidade técnica |
| Financeiro / Assinaturas | Churn, conversão entre planos, receita |
| Suporte / Sucesso do Cliente | Feedbacks, onboarding, atendimento |

Toda sexta-feira, se ainda sobrar orçamento depois da rotação do dia, roda
também o **Meta-Agente Evolutivo**, que avalia a semana inteira nos 4 loops.

Cada loop tem os mesmos 8 papéis (Coletor → Pesquisador → Analista →
Estrategista → Decisor → Executor → Observador → **Relator**), mas com prompts
próprios em `scripts/crew/prompts/<loop>.json`. O Meta-Agente é compartilhado
entre todos os loops (`scripts/crew/prompts/meta.json`) e lê o histórico de
aprovações/rejeições de qualquer loop antes de propor uma mudança de prompt.

Lógica de orçamento e rotação: `scripts/crew/main.py`. Ajustável por variável
de ambiente no Railway: `FRACAO_ORCAMENTO_DIARIO` (padrão 0.9) e
`COTA_DIARIA_TOKENS` (padrão 100000).

**O Relator** é o último agente de cada ciclo e o único que fala com o Breno.
Ele traduz tudo para português leigo (o Breno é CEO, não programador) e envia
por email via Resend. Na sexta-feira há um Relator Semanal que fecha a semana
consolidando os 4 loops. Termos técnicos são proibidos nos relatórios.

Configuração de cada loop (foco e queries de pesquisa) fica em
`scripts/crew/loops.json`. Execuções ficam marcadas no Supabase
(`agent_runs.loop_name`) para não misturar histórico entre áreas.

## Canal único com o Breno ("Time de IA")
**Criado em 08/08/2026, a pedido do Breno:** ele quer o time como uma
empresa — trabalha sozinho, mas ele pode comentar/pedir a qualquer
momento por UM canal só, em vez de precisar saber qual dos 4 loops (ou
qual dos 3 agentes antigos Camila/Marcos/Rafael) procurar.

Mecanismo (não é chat ao vivo — os loops só rodam 1x/dia):
1. Página `/agentes.html` ("Time de IA" no menu) — o Breno escreve um
   recado (texto livre + área opcional) que grava em
   `public.time_recados` (status inicial `pendente`).
2. O **Coletor** de cada loop lê os recados pendentes/em andamento no
   início do ciclo (`ler_recados_breno`) — um recado relevante à área
   dele vira PRIORIDADE MÁXIMA do ciclo, acima de qualquer prioridade
   que o time escolheria sozinho.
3. O **Decisor** responde cada recado que o Coletor sinalizou
   (`responder_recado_breno`): marca `atendido` (com o que foi feito),
   `em_andamento` ou `nao_prioridade` (sempre com o motivo). Nunca fica
   sem resposta.
4. O Breno vê a resposta na mesma página `/agentes.html`, no histórico.

Se o recado não tiver área definida, qualquer um dos 4 loops pode
pegá-lo — o primeiro a rodar decide se é dele ou não.

Para pedidos que precisam de resposta NA HORA (não no próximo ciclo de
até 24h), o canal continua sendo esta conversa com o Claude/Cowork.

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
