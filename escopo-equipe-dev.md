# StaFlow — Mini Escopo: Equipe de Agentes de Software (Claude Code)
**Status:** APENAS PLANEJAMENTO — não implementar sem aprovação explícita do Breno.
**Data:** 07/08/2026

---

## Por que isso é separado do time de agentes atual

O time de agentes que já roda (loops Marketing/Produto/Financeiro/Suporte + Meta-Agente) usa Groq com um modelo pequeno e gratuito. Isso é suficiente para gerar posts, analisar métricas e escrever relatórios — mas é fraco demais e arriscado demais para escrever código de produção sozinho. Foi exatamente esse ponto fraco que quase derrubou o site (PR com arquivos HTML/CSS/JS vazios, hoje bloqueado à força pela lista de arquivos proibidos em `GitHubPRTool`).

A ideia aqui é diferente: uma equipe separada, especializada só em código, rodando em cima do Claude Code (mais caro, mas muito mais capaz de entender um código real e não quebrar o que já existe).

**Correção importante (decisão do Breno, 07/08):** o planejamento — o que construir, prioridade, escopo — continua sendo trabalho dos agentes atuais (principalmente o loop Produto/Desenvolvimento de terça-feira). O Claude Code entra **só na execução**: pega uma task já definida e escreve o código. Ele não decide o que fazer, só como fazer.

---

## Objetivo

Ter uma forma de pedir correções e melhorias técnicas reais — sem precisar que o Breno (que não é programador) descreva tudo em detalhe técnico toda vez, e sem depender só de mim numa conversa ao vivo.

## Divisão de trabalho

| Etapa | Quem cuida |
|---|---|
| Post de Instagram, relatório, análise de métrica, pesquisa de mercado | Time atual (Groq) — loops de negócio |
| **Planejamento técnico:** identificar bug, priorizar, escrever a task em detalhe | Loop **Produto/Desenvolvimento** (terça-feira) — são "meus agentes" |
| **Execução técnica:** escrever o código de verdade, seguindo a task | Equipe de dev (Claude Code) |
| Decisão de negócio (preço, posicionamento, prioridade estratégica) | Breno + sócios |

---

## Como funcionaria (fluxo proposto)

```
1. Toda terça, o loop Produto/Desenvolvimento roda normalmente
   (Coletor → Pesquisador → Analista → Estrategista → Decisor)
   e identifica o que precisa ser corrigido/construído.

2. Em vez do Executor tentar escrever código ele mesmo (hoje isso é
   bloqueado de propósito pra código sensível — ver GithubPRTool),
   o Executor passa a escrever a TASK em TASK_TEMPLATE.md — que já
   existe no repositório — com a mesma qualidade que o Analista e o
   Estrategista já produzem hoje em texto.

3. A task entra numa fila (pasta /tasks/). Isso é 100% seguro: é só
   texto, não toca em nenhum arquivo de produção.

4. Claude Code (sob demanda, disparado por task nova) lê o arquivo,
   implementa a mudança numa branch nova.

5. Testes mínimos rodam (os já listados no template: Chrome, Safari iOS
   se for página mobile, offline se usa fila do Supabase, sem erro de
   console).

6. Abre um Pull Request — nunca faz merge sozinho.

7. Breno revisa e aprova o merge no GitHub (igual já faz hoje).
```

Isso reaproveita a proteção que já existe: nada vai pra produção sem passar pelos olhos do Breno. E o time de negócio (Groq, mais fraco) só faz o que já faz bem — analisar e escrever texto — nunca código.

---

## O que essa equipe faria bem (e o time atual não deveria tentar)

- Os 2 itens que ficaram pendentes da auditoria técnica: GAP-06 (tolerância de atraso não aplicada visualmente no `ponto.html`) e GAP-08 (email pós-cancelamento não implementado)
- Mudanças em `auth/`, `scripts/`, `sql/` — hoje bloqueadas de propósito pro time de negócio
- Refatorações, correção de bugs relatados por usuários reais
- Escrever migrations SQL novas

## O que essa equipe NÃO faria

- Decisão de preço, posicionamento, prioridade de roadmap — isso é decisão sua/dos sócios
- Merge automático — sempre PR + revisão humana
- Mexer em `CLAUDE.md`, `railway.json`, `package.json` e afins sem pedido explícito (mesma lista de arquivos protegidos que já existe)

---

## Custo e esforço

- Claude Code custa mais por execução que o Groq gratuito — não faz sentido rodar toda semana sem ter task pendente. Proposta: rodar **sob demanda** (quando há uma `TASK_*.md` nova em `/tasks/`), não em cron fixo como o loop de negócio.
- Setup técnico inicial: pasta `/tasks/` pra fila de tasks, um workflow do GitHub Actions que dispara quando uma task nova é commitada, e as credenciais de API já existem (mesmas do resto do projeto).

---

## O que muda no loop Produto/Desenvolvimento (terça-feira)

Hoje o Executor desse loop tem acesso ao `GitHubPRTool` pra tentar escrever código direto — e é travado pela lista de arquivos/pastas proibidas. Com essa divisão, o papel dele muda: em vez de tentar (e ser bloqueado) escrever código, ele escreve a task em `TASK_TEMPLATE.md`. É um trabalho mais alinhado ao que o modelo pequeno já faz bem (estruturar texto), e elimina o risco de PR com arquivo vazio — porque ele nunca mais vai gerar código, só a especificação.

Isso exige um ajuste no prompt do Executor em `scripts/crew/prompts/produto.json` — mudar a instrução de "abra um PR com o código" para "escreva a task em TASK_*.md".

---

## Próximo passo

Isso é só o esboço. Antes de implementar, preciso que você confirme:
1. Quer que eu já monte esse workflow (pasta `/tasks/`, ajuste do prompt do Executor do loop Produto, Action que dispara o Claude Code), ou fica só nesse plano por enquanto?
2. As duas tasks pendentes da auditoria (GAP-06 e GAP-08) são um bom primeiro teste real — o loop Produto (ou eu, escrevendo manualmente) gera a `TASK_*.md` dessas duas, e testamos o Claude Code executando? Ou prefere que eu mesmo resolva essas duas agora, direto, do jeito que fizemos hoje com o email?

---

*escopo-equipe-dev.md — StaFlow · 07/08/2026 · APENAS PLANEJAMENTO*
