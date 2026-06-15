# Auditoria QA — StaFlow Admin
**Data:** 2026-06-15 | **Auditor:** Rafael (IA CFO/Dir. Comercial)  
**Escopo:** 10 páginas HTML — lidas linha a linha via MCP

---

## Legenda
| Símbolo | Significado |
|---------|-------------|
| ✅ | Funciona corretamente |
| ⚠️ | Warning — não bloqueia lançamento mas deve ser corrigido cedo |
| ❌ | Bug real — comportamento errado observado no código |
| 🔴 | Crítico — bloqueia divulgação ou cria risco legal/financeiro |

---

## 1. `auth/cadastro.html`

| # | Status | Feature | Detalhe |
|---|--------|---------|---------|
| 1 | ✅ | Fluxo 2 etapas (síndico) | Stepper funcional, validação por etapa |
| 2 | ✅ | Fluxo direto (colaborador) | Stepper ocultado corretamente |
| 3 | ✅ | Bloqueio de e-mail descartável | `window.staflowValidators.isEmailDescartavel()` chamado no submit |
| 4 | ✅ | Auto-fill ViaCEP | Dispara no `blur` quando CEP tem 8 dígitos; falha silenciosa |
| 5 | ✅ | Validação CPF | Dígitos verificadores calculados matematicamente |
| 6 | ✅ | Validação CNPJ | Idem |
| 7 | ⚠️ | `localStorage` para claim colaborador | `staflow_pending_colab_claim` é silenciosamente ignorado em modo privado/incognito. Colaborador que abriu o link de convite em aba privada não é vinculado. **Sem mensagem de aviso.** |
| 8 | ⚠️ | Toggle síndico/colaborador | Trocar de modo no meio do preenchimento reseta o form sem aviso — pode frustrar usuário que digitou dados |

**Bloqueador de lançamento?** Não. Itens 7 e 8 são edge cases.

---

## 2. `auth/login.html`

| # | Status | Feature | Detalhe |
|---|--------|---------|---------|
| 1 | ✅ | "Esqueci minha senha" | Redireciona para `/auth/recuperar-senha.html` |
| 2 | ✅ | Botão reabilitado pós-redirect | Não fica travado em loading |
| 3 | ✅ | Route guard | Direciona para dashboard, colaborador ou planos conforme perfil |
| 4 | ⚠️ | `toast()` definida duas vezes | Linha ~72 e ~129. Última vence. Sem impacto funcional, mas revela ctrl+c/ctrl+v em alguma iteração passada. |

**Bloqueador de lançamento?** Não.

---

## 3. `dashboard.html`

| # | Status | Feature | Detalhe |
|---|--------|---------|---------|
| 1 | ✅ | 6 KPI cards com dados reais | Consultas paralelas via `Promise.allSettled` |
| 2 | ✅ | Realtime WebSocket | Subscreve `postgres_changes` em `registros_ponto`, `faltas`, `tarefas` |
| 3 | ✅ | Skeleton loader | Exibido enquanto promises pendentes |
| 4 | ✅ | Empty state (sem funcionários) | Detectado e exibido corretamente |
| 5 | ⚠️ | Chart.js via CDN | `https://cdn.jsdelivr.net/npm/chart.js` — se o CDN cair, todos os gráficos somem. Sem `try/catch` ou fallback. |
| 6 | ⚠️ | Realtime por aba | Cada aba aberta do dashboard cria 1 conexão WebSocket persistente. Limite free Supabase: 200 conexões simultâneas. Com 100+ síndicos logados ao mesmo tempo, o limite é atingido. Ver análise de capacidade. |
| 7 | ⚠️ | Hover em membro da equipe | Cada hover dispara 1 query ao Supabase (horas individuais do funcionário). Sem debounce. Mover o mouse rápido sobre 15 nomes = 15 queries simultâneas. |
| 8 | ⚠️ | Coluna `salario_base` | Cards de conformidade (13º, férias, FGTS, passivo trabalhista) dependem da migration 011. Se não aplicada, cálculos usam fallback CCT-RJ (R$ 1.412) que pode não refletir salário real. Comentário no código admite isso. |

**Bloqueador de lançamento?** Não. Item 6 vira problema em escala (>100 síndicos simultâneos).

---

## 4. `funcionarios.html`

| # | Status | Feature | Detalhe |
|---|--------|---------|---------|
| 1 | ✅ | Dupla proteção de limite de plano | `openNew()` verifica client-side + `submit()` re-consulta DB + trigger `enforce_plan_limit_funcionarios` |
| 2 | ✅ | Upload de foto | Bucket `fotos-funcionarios`, 5 MB, signed URLs |
| 3 | ✅ | Validação CPF | Matemática completa |
| 4 | ✅ | Bloqueio de e-mail descartável | |
| 5 | ✅ | Alerta CCT-RJ | Aparece automaticamente ao selecionar cargo `faxineira` (NR-15) |
| 6 | ✅ | Empty state | |
| 7 | ❌ | Limite Pro incorreto | `PLAN_LIMITS = { ..., pro: 15, ... }` no JavaScript — mas `planos.html` anuncia **"Até 20 funcionários"** no plano Pro. O valor que vale na prática é 15 (reforçado também pelo trigger do DB). Cliente Pro que tentar o 16º verá erro inesperado tendo contratado "20". **Risco de chargeback/reclamação.** |
| 8 | ⚠️ | Botão "Excluir" — race condition | `btn.disabled = true` ocorre dentro do handler async. Um double-click muito rápido pode enviar 2 requisições de DELETE antes da primeira resposta retornar. Baixa probabilidade mas possível. |

**Bloqueador de lançamento?** Item 7 **SIM** — o número anunciado não bate com o código.  
**Correção item 7:** Escolher um valor e sincronizar. Recomendo fixar em **20** (atualizar trigger DB, `PLAN_LIMITS` no JS e `enforce_plan_limit_funcionarios`) pois é o número anunciado ao mercado.

---

## 5. `tarefas.html`

| # | Status | Feature | Detalhe |
|---|--------|---------|---------|
| 1 | ✅ | Ciclo de status por clique | `pendente → em_andamento → concluída → pendente` |
| 2 | ✅ | Exportação CSV | Via `window.staflowApp.exportCSV()` |
| 3 | ✅ | Filtros | Status, prioridade, busca textual |
| 4 | ✅ | Campo status oculto em criação | Correto (novo = `pendente` por default) |
| 5 | ⚠️ | Sem debounce em `cycleStatus` | Cliques rápidos no badge de status disparam múltiplas atualizações no DB simultâneas, podendo criar race condition onde o status volta para um estado intermediário. Solução: `btn.disabled = true` durante o `await`, re-habilita depois. |

**Bloqueador de lançamento?** Não. Workaround: clicar devagar.

---

## 6. `planos.html`

| # | Status | Feature | Detalhe |
|---|--------|---------|---------|
| 1 | 🔴 | **CNPJ inválido no rodapé** | Footer exibe `"CNPJ AGUARDANDO EMISSÃO"` — literal, em produção, visível a qualquer visitante. CNPJ real: `67.255.600/0001-71`. **Risco legal: site operando sem identificação fiscal da empresa.** |
| 2 | ❌ | Pro: "Até 20 funcionários" | Texto na card do plano Pro diz 20, mas o código em `funcionarios.html` limita a 15. Ver item 7 de funcionarios.html acima. |
| 3 | ❌ | Scale: preço mensal errado | Card exibe **R$ 279/mês** — preço oficial do briefing é **R$ 249/mês**. Diferença de R$30. |
| 4 | ⚠️ | Cupom em modo anual calcula errado | `aplicarDesconto()` usa preços mensais como base mesmo quando o toggle está em "anual". Ex: cupom 10% no Pro anual deveria dar desconto sobre R$ 950, mas calcula sobre R$ 99. |
| 5 | ⚠️ | Sem destaque do plano atual | Usuário logado no Pro não vê qual plano está ativo. Nenhuma card fica highlighted ou disabled. UX confuso para upgrades. |
| 6 | ⚠️ | Dependência de `stripe-config.js` | `window.STAFLOW_STRIPE_PRICES` deve estar definido antes. Se o arquivo não carregar (falha de rede), todos os botões pagos mostram erro silencioso "integração não configurada". |

**Bloqueador de lançamento?** Itens 1, 2 e 3 **SIM**.

---

## 7. `ponto.html`

| # | Status | Feature | Detalhe |
|---|--------|---------|---------|
| 1 | ✅ | Espelho de ponto legal | HTML imprimível A4, SHA-256, campos MTE 671 |
| 2 | ✅ | Retificação com auditoria | Campo `motivo_edicao` obrigatório (mín. 5 chars), marca `EDITADO_ADMIN` |
| 3 | ✅ | Pills de fraude GPS | `FRAUDE_SUSPECT`, `MOCK_SUSPECT`, `LOW_ACCURACY` visíveis na tabela e no espelho |
| 4 | ✅ | Summary strip (presentes/saiu/ausentes) | Ocultada abaixo de 820px (per-page CSS) |
| 5 | ✅ | Empty states | Sem funcionários e sem resultado de filtro |
| 6 | ✅ | Exportar Excel + Emitir Espelho | Ambos os botões presentes |
| 7 | ✅ | Disclaimer MTE 671 | Presente no rodapé |
| 8 | ⚠️ | Edge case de timezone na `dayRange()` | `start = dateStr + 'T00:00:00.000Z'` trata a string local como UTC midnight. Síndico em Brasília (UTC-3) consultando "hoje" entre 21h00 e 23h59 BRT vê dados do dia errado (hora UTC já virou). **Correção:** usar `T03:00:00.000Z` como hora de início do dia brasilieiro, ou converter com `new Date(dateStr + 'T00:00:00-03:00')`. |
| 9 | ⚠️ | Botões Entrada/Saída: sem guard extra | `btn.disabled = true` é definido após enter no handler. `loading-btn` + `pointer-events: none` são setados sincronicamente, então double-click é bem protegido. Risco baixíssimo. |

**Bloqueador de lançamento?** Item 8 é um bug real mas ocorre apenas durante a janela 21h-00h BRT. Não bloqueia divulgação, mas deve ser corrigido antes do 1º cliente de produção.

---

## 8. `faltas.html`

| # | Status | Feature | Detalhe |
|---|--------|---------|---------|
| 1 | ✅ | Upload de atestado | LGPD Art. 11 anotado no label, 10 MB, JPG/PNG/PDF |
| 2 | ✅ | Signed URL para download | Expira em 1h |
| 3 | ✅ | Stats (total/não-justificadas/atestados) | Filtro por mês funciona independente dos outros filtros |
| 4 | ✅ | Filtros | Mês, tipo, funcionário, busca textual |
| 5 | ✅ | Export CSV | Respeita filtros ativos |
| 6 | ✅ | Delete remove atestado do storage | Chama `deleteAtestadoStorage()` antes do DELETE no DB |
| 7 | ⚠️ | Botão "Excluir" confirm: sem guard double-click | Mesmo padrão de `funcionarios.html` — `btn.disabled` set após `await` start. Risco baixo mas real. |

**Bloqueador de lançamento?** Não.

---

## 9. `colaborador.html`

| # | Status | Feature | Detalhe |
|---|--------|---------|---------|
| 1 | ✅ | Botão punch 4 estados | Entrada → Almoço → Volta → Saída, com animação e GPS |
| 2 | ✅ | Antifraude GPS | `FRAUDE_SUSPECT` (≥2 sinais), `MOCK_SUSPECT` (1 sinal), `LOW_ACCURACY` (>150m) |
| 3 | ✅ | Fila offline IndexedDB | Batida enfileirada se `!navigator.onLine`, sincroniza ao reconectar |
| 4 | ✅ | Deduplicação na sync | Error code `23505` (unique_violation) tratado como sucesso — batida offline que já chegou não duplica |
| 5 | ✅ | Hora noturna CLT 73 | Cálculo correto para período 22h-05h com fator 60/52,5 |
| 6 | ✅ | Task toggle com rollback otimista | Atualiza UI antes do `await`, faz rollback se DB retorna erro |
| 7 | ✅ | Justificativa LGPD + upload | Bucket privado, 10 MB |
| 8 | ✅ | Block screen + botão retry | Implementado na sessão anterior |
| 9 | ✅ | PWA completo | Manifest + apple-touch-icon + meta viewport |
| 10 | ⚠️ | IndexedDB em modo incognito | `open()` lança exceção — fallback cai no INSERT direto que falha com erro de rede. Usuário vê `❌ Não foi possível salvar offline (storage bloqueado)`. Não tem workaround no app. |
| 11 | ⚠️ | GPS timeout 8s | Durante os 8s o botão fica travado em "loading" sem feedback visual claro. Em guaritas com GPS fraco, acontece com frequência. Sugestão: mostrar contador regressivo ou oferecer "Registrar sem GPS" após 3s. |
| 12 | ⚠️ | Limite fixo de 4 batidas/dia | `btn.disabled = (qtd >= 4)` — funcionário com jornada especial (hora extra autorizada, 2 turnos) não consegue registrar 5ª ou 6ª batida. Sem mensagem explicativa ao ser bloqueado. |

**Bloqueador de lançamento?** Não. Items 11 e 12 afetam UX de casos de uso reais mas não quebram o produto.

---

## 10. `configuracoes.html`

| # | Status | Feature | Detalhe |
|---|--------|---------|---------|
| 1 | ✅ | Cancelamento `cancel_at_period_end` | Handler correto após fix desta sessão — usa `data.message` da API, não muda plano local |
| 2 | ✅ | ViaCEP no CEP | Auto-fill logradouro/bairro/cidade/estado |
| 3 | ✅ | Upload de CCT | 20 MB PDF, signed URL p/ visualização, remove versão anterior |
| 4 | ✅ | Tolerância de atraso | Default 10 min (CLT), range 0-60 |
| 5 | ✅ | Salvar perfil + reset de senha | |
| 6 | ⚠️ | Texto do modal de cancelamento desatualizado | Modal diz **"Você perderá acesso imediato ao plano pago. O condomínio voltará ao plano Starter (3 funcionários)."** — mas com `cancel_at_period_end=true`, o acesso continua até o fim do período. O texto contradiz o comportamento real. **Correção:** Alterar para "Seu acesso ao plano pago continuará até o fim do período atual. Após isso, o condomínio retorna ao Starter." |
| 7 | ⚠️ | Estado "Cancelamento agendado" no card assinatura | O `atualizarCardAssinatura()` já mostra "⏳ Cancelamento agendado" — mas o botão "Cancelar plano" continua visível mesmo após agendamento. Usuário pode tentar cancelar duas vezes. |

**Bloqueador de lançamento?** Item 6 não bloqueia tecnicamente mas é comunicação falsa ao usuário sobre o comportamento do produto. **Corrigir antes de divulgar.**

---

## Resumo executivo — Classificação por criticidade

### 🔴 Bloqueia divulgação (corrigir AGORA)
1. **`planos.html` — CNPJ "AGUARDANDO EMISSÃO"** no rodapé público. → Colocar `67.255.600/0001-71`
2. **`planos.html` — Pro anuncia "20 funcionários"** mas limite em código é 15. → Sincronizar para 20 (atualizar trigger + JS)
3. **`planos.html` — Scale R$ 279/mês** — preço errado (deve ser R$ 249). → Corrigir HTML

### ❌ Bug real (corrigir antes do 1º cliente pago)
4. **`configuracoes.html` — Modal de cancelamento com texto errado** — anuncia perda imediata de acesso quando na verdade mantém acesso. Risco de reclamação.
5. **`ponto.html` — Timezone bug** na `dayRange()` — dia errado na janela 21h-00h BRT.

### ⚠️ Warnings (backlog imediato pós-lançamento)
6. Cupom em modo anual usa base mensal → desconto errado
7. Sem destaque do plano atual em `planos.html`
8. Double-click em botões de exclusão (funcionarios.html, faltas.html)
9. Sem debounce em cycleStatus (tarefas.html)
10. Sem debounce em hover de equipe (dashboard.html)
11. Chart.js sem fallback de CDN
12. Colaborador: GPS timeout longo sem feedback
13. Colaborador: limite fixo de 4 batidas sem explicação
14. `configuracoes.html`: botão "Cancelar plano" persiste após cancelamento agendado

---

## Fixes rápidos dos 🔴 (estimativa)

| Fix | Arquivo | Tempo |
|-----|---------|-------|
| CNPJ no footer | `planos.html` | 2 min |
| Preço Scale R$249 | `planos.html` | 2 min |
| Pro "20 funcionários" → atualizar texto | `planos.html` | 2 min |
| Pro limite → atualizar `PLAN_LIMITS` em `funcionarios.html` | `funcionarios.html` | 5 min |
| Pro limite → atualizar trigger DB | SQL migration | 10 min |
| Texto modal cancelamento | `configuracoes.html` | 5 min |
| Timezone `dayRange()` | `ponto.html` | 15 min |

**Total estimado fixes críticos: ~40 minutos de desenvolvimento.**
