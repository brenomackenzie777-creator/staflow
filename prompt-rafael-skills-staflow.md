# Briefing Rafael — Skills Instaladas + Próximas Tarefas StaFlow

**Data:** 26/06/2026  
**Status do projeto:** Stripe LIVE ativo · Logo azul #3B82F6 · 30 skills instaladas no teu Claude Code

---

## Novidades desta semana

| Item | Status |
|------|--------|
| Stripe LIVE mode | ✅ Ativo — price IDs reais configurados no Supabase |
| Logo azul #3B82F6 | ✅ Atualizado em `assets/logo-mark.svg` |
| Instagram (Camila) | ✅ Posts v3 entregues — 9 posts + 5 stories |
| 30 skills no Claude Code | ✅ Instaladas em `~/.claude/commands/` |

---

## As 30 skills disponíveis — o que cada uma faz por ti

### 🔴 CRÍTICAS para StaFlow agora

| Comando | Quando usar |
|---------|-------------|
| `/systematic-debugging` | Quando um bug aparece e não é óbvio onde está. Força metodologia: reproduz → isola → corrige → verifica. Não adivinhas, proves. |
| `/test-driven-development` | Antes de codar qualquer feature nova. Escreve o teste primeiro, depois implementa. Ideal para as features da Fase 2. |
| `/verification-before-completion` | Antes de marcar qualquer tarefa como concluída. Checklist automático: funciona? edge cases? RLS correto? sem regressão? |
| `/wq-web-quality-audit` | Auditoria completa do site. Roda antes de qualquer divulgação pública. |
| `/wq-accessibility` | Verifica se o app passa em WCAG 2.1 AA — obrigatório para clientes corporativos. |
| `/wq-performance` | Core Web Vitals. O `colaborador.html` precisa carregar rápido no celular 4G do porteiro. |
| `/snyk-secure-at-inception` | Segurança desde o início. Roda antes de qualquer nova feature que toca dados sensíveis (CPF, GPS, atestados). |
| `/github-pr-review` | Antes de qualquer merge na main. Não mergeas sem review. |

### 🟡 IMPORTANTES para desenvolvimento

| Comando | Quando usar |
|---------|-------------|
| `/brainstorming` | Antes de decidir como implementar uma feature complexa. Gera 3+ opções, compara trade-offs. |
| `/writing-plans` | Antes de codar. Escreve um plano em `PLAN.md` — o Breno pode ver e aprovar antes de executar. |
| `/subagent-driven-development` | Para features grandes (ex: app mobile Fase 2). Divide em sub-tarefas paralelas, executa com agentes, junta. |
| `/dispatching-parallel-agents` | Quando tens múltiplas tarefas independentes. Faz tudo ao mesmo tempo em vez de sequencial. |
| `/finishing-a-development-branch` | Antes de fechar qualquer branch. Checklist: testes passam, sem console.log, sem TODO, PR criado. |
| `/requesting-code-review` | Gera o PR description completo automaticamente. |
| `/receiving-code-review` | Quando o Breno ou outro dev faz um comment no PR — como responder e aplicar o feedback. |

### 🟢 DESIGN (usar junto com Camila ou para protótipos)

| Comando | Quando usar |
|---------|-------------|
| `/grill-me` | Antes de qualquer nova feature — interroga os requisitos até não restar ambiguidade. |
| `/design-brief` | Analisa o codebase e gera um brief de design. Útil antes de redesenhar qualquer página. |
| `/design-flow` | Processo completo: brief → tasks → build → review. Usa para refatorações de UI. |
| `/design-tokens` | Gera os tokens CSS do Design System v2 em formato padronizado. |
| `/information-architecture` | Mapeia páginas, navegação e hierarquia. Use antes de criar nova página. |
| `/frontend-design` | Constrói componentes seguindo o processo. CSS + acessibilidade + mobile-first. |
| `/design-review` | Review com Lighthouse automático — meta: 90+ performance, 100 acessibilidade. |
| `/brief-to-tasks` | Transforma um brief em TASKS.md com dependências. |

### 🔵 WEB QUALITY — auditoria completa

```bash
# Roda todos os 6 de uma vez antes do lançamento:
/wq-web-quality-audit    # orquestrador — chama os outros
/wq-accessibility        # WCAG 2.1 AA
/wq-performance          # Core Web Vitals (LCP < 2.5s, FID < 100ms, CLS < 0.1)
/wq-seo                  # Meta tags, robots, sitemap
/wq-best-practices       # Segurança de headers, HTTPS, sem mixed content
/wq-core-web-vitals      # Detalhamento dos vitals
```

---

## Tarefas imediatas — usa as skills

### TAREFA 1 — Auditoria completa antes do lançamento

```bash
/wq-web-quality-audit
```

Roda isso na raiz do repo. Entrega um relatório `WQ_AUDIT.md` com score por categoria e lista de correções priorizadas.

**Páginas a auditar:**
- `staflow-landing.html` — pública, primeiro impacto
- `colaborador.html` — PWA do porteiro, mobile-first
- `dashboard.html` — síndico
- `auth/cadastro.html` e `auth/login.html`
- `planos.html` — Stripe checkout

---

### TAREFA 2 — QA brutal do fluxo completo

```bash
/systematic-debugging
```

Usa este skill para mapear bugs. O fluxo a testar:

1. **Cadastro** → condomínio criado → plano escolhido → checkout Stripe LIVE → webhook → subscription ativa
2. **Síndico** cria funcionário → funcionário recebe invite → ativa conta
3. **Funcionário** bate entrada → GPS capturado → registro salvo → dashboard atualiza em realtime
4. **Funcionário** bate saída → par entrada/saída → espelho legal gerado
5. **Síndico** retifica ponto → `audit_status = EDITADO_ADMIN` → trilha auditoria intacta
6. **Offline**: funcionário sem internet → bate ponto → app volta online → drena IndexedDB → registro aparece no dashboard

Documenta cada quebra em `BUGS.md` com: descrição, passo a passo para reproduzir, arquivo/linha provável, prioridade (P1/P2/P3).

---

### TAREFA 3 — Performance no mobile real

```bash
/wq-performance
```

O `colaborador.html` é usado por porteiros em celulares básicos com 4G instável. Precisa:
- First Contentful Paint < 1.5s
- O botão de ponto visível sem scroll
- Funcionar offline (SW + IndexedDB)
- Não travar ao voltar de offline

Testa no Chrome DevTools com throttling "Slow 4G" e CPU 4x slowdown.

---

### TAREFA 4 — Segurança antes de divulgar

```bash
/snyk-secure-at-inception
```

Focos críticos:
- RLS no Supabase — síndico de um condo NÃO pode ver dados de outro (`my_condominio_id()`)
- GPS spoofing — `audit_status` marca corretamente `MOCK_SUSPECT`/`FRAUDE_SUSPECT`
- Bucket `atestados-medicos` — privado, URL com TTL 1h, sem leak de path entre condos
- Edge Functions — HMAC do webhook Stripe válido antes de processar

---

### TAREFA 5 — App mobile (Fase 2)

```bash
/writing-plans    # primeiro — gera PLAN.md para aprovação do Breno
/grill-me         # interroga requisitos antes de codar
/subagent-driven-development   # depois — divide e paraleliza
```

Quando o plano for aprovado, usa `/subagent-driven-development` para executar o app mobile em paralelo: navegação, autenticação, ponto, GPS, offline mode.

---

## Workflow correto para qualquer nova feature

```
1. /grill-me          → interroga requisitos, elimina ambiguidade
2. /writing-plans     → gera PLAN.md (Breno aprova)
3. /test-driven-development  → escreve testes antes de codar
4. [implementa]
5. /snyk-secure-at-inception → verifica segurança
6. /verification-before-completion → checklist antes de marcar done
7. /finishing-a-development-branch → prepara o PR
8. /github-pr-review  → review antes de mergear
```

---

## Contexto técnico do projeto

- **Repo:** github.com/brenomackenzie777-creator/staflow
- **Produção:** https://staflow.app.br
- **Supabase project:** wsxpskrrzqtdoodpoofx
- **Vercel:** Hobby tier
- **Stripe LIVE:** ativo — price IDs em `js/stripe-config.js`
- **Design System:** bg `#111827`, surfaces `#1F2937`, blue `#3B82F6`, text `#F9FAFB`, Inter
- **Plans:** Starter R$0/3func · Pro R$99/15func · Advanced R$159/35func · Scale R$279/100func

---

## Entrega

Para cada tarefa: cria um arquivo de relatório na pasta `_reports/`:
- `WQ_AUDIT.md` — resultado do web quality audit
- `BUGS.md` — bugs encontrados no QA
- `PERFORMANCE.md` — análise de performance mobile
- `SECURITY.md` — resultado da auditoria de segurança
- `PLAN_mobile.md` — plano do app mobile (aguarda aprovação antes de executar)

---

*Briefing gerado pelo Cérebro · StaFlow · 26/06/2026*
