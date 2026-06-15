# Diagnóstico Mobile + Proposta de Abordagem — StaFlow Admin
**Data:** 2026-06-15 | **Dispositivo-alvo:** iPhone 14 (390px × 844px)  
**Status:** Diagnóstico apenas. NÃO implementar sem aprovação do Breno.

---

## Contexto

`colaborador.html` já é mobile-first (`max-width: 420px`, bottom nav, botão 240px) — não tem problema.  
Este documento trata das **páginas admin** (`dashboard.html`, `funcionarios.html`, `ponto.html`, `faltas.html`, `tarefas.html`, `configuracoes.html`, `planos.html`), que usam o shell de `app.css`.

---

## O que já existe em `app.css`

`app.css` tem **2 breakpoints compartilhados**:

### `@media (max-width: 768px)`
- `.app`: `grid-template-columns: 1fr` (sidebar some do grid)
- `.sidebar`: vira drawer fixo (transform: translateX(-100%)), abre com `.open`
- Botão hamburguer (`.menu-toggle`) aparece
- `.main`: padding reduz para 16px × 14px
- `.topbar`: flex-direction column
- `.table-wrap`: overflow-x auto + min-width: 560px nas tables
- `.modal .field-row`: colapsa para 1 coluna

### `@media (max-width: 480px)`
- Padding mínimo (14px × 12px)
- `.card`: padding 16px
- Fontes mínimas

**Conclusão:** A infraestrutura básica de responsividade existe. O hamburguer funciona, tabelas têm scroll horizontal, modais colapsam.

---

## Diagnóstico: o que QUEBRA em 390px (iPhone 14)

### 1. `dashboard.html` — Crítico

**Problema:** Os KPI cards são provavelmente em grid (o código não foi lido completo mas o padrão do resto da app indica). Sem breakpoint específico para ≤390px, cards ficam espremidos ou transbordam.

**Chart.js (gráfico de equipe):** Em 390px, o canvas fica muito pequeno — eixos, labels e legenda sobrepõem. Não há breakpoint de tamanho do canvas.

**Topbar com título + subtítulo:** OK (já colapsa para coluna em 768px).

### 2. `funcionarios.html` — Muito crítico

**Tabela com 7 colunas:** Foto | Nome/Cargo | E-mail | CPF | Data admissão | Turno | Ações  
`min-width: 560px` no `.table-wrap` faz a tabela scrollar horizontalmente.  
Em 390px de viewport, o usuário precisa scrollar 170px+ para ver os botões de ação à direita.  
**UX inaceitável para uso frequente.**

**Formulário de cadastro (modal):** `field-row` já colapsa para 1 col em 768px. OK.

**Barra de filtros:** filtros cargo + busca + botão "+ Novo" em uma linha. Em 390px, quebra para 2+ linhas de forma não controlada.

### 3. `ponto.html` — Médio

**Tabela com 6 colunas:** Funcionário | Entrada | Saída | Total | Status | Ações  
O arquivo já oculta colunas 3, 4 e 5 em `@media (max-width: 600px)`:
```css
.tbl th:nth-child(3), .tbl td:nth-child(3),   /* Saída */
.tbl th:nth-child(4), .tbl td:nth-child(4),   /* Total */
.tbl th:nth-child(5), .tbl td:nth-child(5) { display: none; }
```
Restarão: Funcionário | Entrada | Ações. **Funcional em 390px**, porém sem "Saída" visível, o síndico não vê se o funcionário saiu sem abrir o detalhe.

**Summary strip** (presentes/saiu/ausentes): `display:none` abaixo de 820px — perde informação.

**Topbar com 3 botões** (Emitir Espelho, Relatório Excel, Exportar Dia): em 768px colapsam para `flex: 1`, cada um ocupa ~103px. Em 390px com 3 botões, o texto fica cortado.

### 4. `faltas.html` — Médio

**Tabela com 7 colunas:** Funcionário | Data | Tipo | Justificada | Observação | Atestado | Ações  
`min-width: 560px` → scroll horizontal em 390px. Legível mas trabalhoso.

**Stats grid (3 colunas):** `@media (max-width: 720px)` → 1 coluna. OK.  
`@media (max-width: 980px)` → 2 colunas. OK.

### 5. `tarefas.html` — Baixo

Tabela com colunas menores (Tarefa | Status | Prioridade | Prazo | Ações). Mais simples. Scroll horizontal em 390px mas legível.

### 6. `configuracoes.html` — Baixo

- `grid-two`: colapsa em 880px para coluna única. OK.
- `grid-3`: colapsa em 700px para coluna única. OK.
- `grid-2` do CEP: colapsa em 700px. OK.
- **Formulário completo de condomínio funciona em 390px** — é o mais mobile-friendly das páginas admin.

### 7. `planos.html` — Baixo

Per briefing: "4-col → 2-col → 1-col responsivo." Já implementado no próprio arquivo. Não depende de `app.css`.

---

## Resumo do diagnóstico por severidade

| Página | Severidade em 390px | Principal problema |
|--------|--------------------|--------------------|
| `funcionarios.html` | 🔴 Muito crítico | 7 colunas, scroll 170px+, botões sumidos |
| `dashboard.html` | 🔴 Crítico | KPI grid indefinido, Chart.js em canvas pequeno |
| `ponto.html` | 🟡 Médio | 3 botões cortados, Saída oculta em 600px |
| `faltas.html` | 🟡 Médio | 7 colunas, scroll horizontal |
| `tarefas.html` | 🟢 Baixo | Gerenciável com scroll |
| `configuracoes.html` | 🟢 Baixo | Já bem adaptado |
| `planos.html` | 🟢 Baixo | Já responsivo |

---

## Opção A — Breakpoints progressivos em `app.css` + ajustes por página

**O que é:** Adicionar um 3º breakpoint (`@media (max-width: 390px)` ou `max-width: 420px`) em `app.css` e ajustes cirúrgicos em cada página problemática.

**O que resolve:**
- Ocultar colunas não-essenciais em `funcionarios.html` (ex: esconder CPF, turno, data admissão — manter nome + cargo + ações)
- Empilhar topbar-actions verticalmente
- Dar min-width mais curto à tabela quando colunas reduzem
- Ajustar gráfico dashboard para não colapsar

**O que NÃO resolve:**
- UX de tabela em mobile — scroll horizontal persiste (só com menos colunas)
- Acesso rápido a funcionalidades — não tem bottom nav
- Botões de ação de tabela — ficam apertados ou cortados

**Estimativa:** 4 a 6 horas de desenvolvimento

**Resultado:** App funcional em 390px (sem erros, sem overflow). UX de "desktop encolhido" — usável em emergência, não confortável para uso frequente.

---

## Opção B — CSS mobile-first separado + bottom nav

**O que é:** Criar `app-mobile.css` carregado apenas em `@media (max-width: 600px)`. Redesenhar cada página admin com:
- Bottom navigation (Ponto | Funcionários | Tarefas | Menu) substituindo sidebar
- Tabelas substituídas por cards empilhados verticalmente (`.mobile-card`)
- Ações de linha viram botões touch-friendly (44px min-height)
- Topbar simplificada (apenas h1 + 1 ação principal)
- KPI cards do dashboard em 2×3 grid (max)
- Gráfico dashboard ocultado em mobile (ou simplificado para barra de progresso)

**O que resolve:**
- Experiência nativa mobile para síndicos que gerenciam no celular
- Cada linha de funcionário vira um card com foto + nome + cargo + botões visíveis
- Navegação rápida por aba inferior sem menu lateral
- Touch targets corretos (44px+ per WCAG)

**O que NÃO resolve automaticamente:**
- Formulários complexos (múltiplos campos) — precisam de revisão campo a campo
- Tabela de registros de ponto com muitas colunas — ainda precisará de escolhas editoriais sobre o que mostrar

**Estimativa:** 10 a 14 horas de desenvolvimento

**Resultado:** Produto mobile-first real — síndico pode gerenciar o condomínio pelo celular com conforto.

---

## Comparativo para decisão do Breno

| Critério | Opção A | Opção B |
|----------|---------|---------|
| Tempo de implementação | 4-6h | 10-14h |
| UX em 390px | ⚠️ Funcional | ✅ Confortável |
| Risco de regressão desktop | Baixo | Médio |
| Síndico usa no celular com frequência? | Aceitável | Recomendado |
| Custo de manutenção futuro | Baixo | Médio |
| Bloqueia lançamento? | Não | Não |

---

## Recomendação (a ser aprovada pelo Breno)

**Contexto:** O ICP prioritário são síndicos profissionais e administradoras — ambos provavelmente em desktop. `colaborador.html` já resolve o mobile para os funcionários. Síndicos em mobile são uso secundário (consultar ponto, adicionar falta emergencialmente).

**Sugestão:** Iniciar com **Opção A** para lançamento — resolve os erros críticos (overflow, texto cortado) sem atrasar o go-live. Planejar **Opção B** para Sprint 2 após feedback dos primeiros clientes confirmarem que síndicos querem usar no celular.

> **NÃO IMPLEMENTAR sem aprovação. Esta seção é proposta, não decisão.**

---

## Arquivos que precisam de toque (Opção A)

1. `app.css` — adicionar breakpoint `@media (max-width: 420px)` com regras de tabela e topbar
2. `funcionarios.html` — ocultar colunas CPF + turno + data_admissão em mobile
3. `dashboard.html` — verificar grid de KPI cards e tamanho do Chart.js canvas
4. `ponto.html` — revisar 3 botões no topbar em mobile
5. `faltas.html` — ocultar colunas Observação + Justificada em mobile

**Arquivos que já funcionam em mobile (não tocar na Opção A):**
- `configuracoes.html` — já responsivo
- `planos.html` — já responsivo
- `tarefas.html` — mínimo trabalho, aceitável
