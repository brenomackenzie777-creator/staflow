# Prompt para Claude Code — `dashboard.html` (e páginas internas)

> Cole este prompt no Claude Code para implementar o dashboard principal e todas as páginas internas do StaFlow no visual enterprise aprovado.

---

## CONTEXTO

Reimplemente `dashboard.html` e as páginas internas (funcionarios.html, ponto.html, faltas.html, tarefas.html, configuracoes.html) com o novo visual enterprise StaFlow. O layout base é **sidebar fixa 220px + área de conteúdo**. Todas as páginas compartilham o mesmo shell (sidebar + topbar) — só o conteúdo central muda.

---

## DESIGN SYSTEM — VARIÁVEIS CSS (obrigatório em todas as páginas)

```css
:root {
  --bg:           #111827;
  --surface:      #1F2937;
  --surface-2:    #374151;
  --surface-hover:#243040;
  --text:         #F9FAFB;
  --text-muted:   #9CA3AF;
  --text-faint:   #6B7280;
  --blue:         #3B82F6;
  --blue-dark:    #1D4ED8;
  --blue-dim:     rgba(59,130,246,0.12);
  --blue-border:  rgba(59,130,246,0.35);
  --green:        #10B981;
  --red:          #EF4444;
  --amber:        #F59E0B;
  --purple:       #8B5CF6;
  --border:       #374151;
  --border-subtle:rgba(55,65,81,0.5);
  --radius-sm:    4px;
  --radius-md:    6px;
  --radius-lg:    8px;
  --radius-xl:    12px;
  --shadow-md:    0 4px 12px rgba(0,0,0,0.4);
  --shadow-blue:  0 4px 20px rgba(59,130,246,0.25);
  --font:         'Inter', -apple-system, sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
  display: flex;
  min-height: 100vh;
}
```

Fonte: `Inter` via Google Fonts, pesos 400 500 600 700.

---

## ESTRUTURA DE LAYOUT (shell compartilhado)

```html
<body>
  <aside class="sidebar">...</aside>
  <div class="main-wrap">
    <header class="topbar">...</header>
    <main class="content">
      <!-- conteúdo específico de cada página -->
    </main>
  </div>
</body>
```

---

## 1. SIDEBAR

```css
.sidebar {
  width: 220px;
  min-height: 100vh;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0; top: 0;
  z-index: 50;
}

/* Logo */
.sidebar-logo {
  padding: 18px 20px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: var(--text);
  border-bottom: 1px solid var(--border);
  text-decoration: none;
  display: block;
}
.sidebar-logo span { color: var(--blue); }

/* Seção de nav */
.nav-section { padding: 16px 12px 8px; }
.nav-section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--text-faint);
  padding: 0 8px;
  margin-bottom: 4px;
}

/* Item de nav */
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 400;
  color: var(--text-muted);
  text-decoration: none;
  transition: background 0.12s, color 0.12s;
  margin-bottom: 1px;
}
.nav-item svg { width: 16px; height: 16px; stroke: currentColor; flex-shrink: 0; }
.nav-item:hover  { background: rgba(55,65,81,0.5); color: var(--text); }
.nav-item.active {
  background: var(--blue-dim);
  color: var(--blue);
  font-weight: 600;
  border: 1px solid var(--blue-border);
}

/* Divisor vertical */
.sidebar-divider { height: 1px; background: var(--border); margin: 8px 12px; }

/* Perfil no rodapé */
.sidebar-profile {
  margin-top: auto;
  border-top: 1px solid var(--border);
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(14,20,34,0.6);
}
.profile-avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: var(--blue);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
  color: var(--text);
  flex-shrink: 0;
}
.profile-name  { font-size: 13px; font-weight: 600; color: var(--text); }
.profile-role  { font-size: 11px; color: var(--text-muted); }
```

**Itens de navegação e ícones (usar SVG Heroicons outline 16px):**

| Item | Ícone sugerido | href |
|------|---------------|------|
| Dashboard | chart-bar | dashboard.html |
| Funcionários | users | funcionarios.html |
| Controle de Ponto | clock | ponto.html |
| Faltas / Férias | calendar | faltas.html |
| Tarefas | clipboard-list | tarefas.html |
| Relatórios | document-report | relatorios.html |
| *(divisor)* | | |
| Configurações | cog | configuracoes.html |

---

## 2. TOPBAR

```css
.main-wrap {
  margin-left: 220px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.topbar {
  height: 64px;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 40;
}

/* Breadcrumb / título da página */
.topbar-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: var(--text);
}
.topbar-breadcrumb {
  font-size: 11px;
  color: var(--text-faint);
  margin-top: 2px;
}

/* Ações à direita */
.topbar-actions { display: flex; align-items: center; gap: 10px; }

/* Badge de data */
.date-badge {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 6px 12px;
  font-size: 12px;
  color: var(--text-muted);
}

/* Botão primário (topbar) */
.btn-primary {
  background: var(--blue);
  color: var(--text);
  border: none;
  border-radius: var(--radius-md);
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex; align-items: center; gap: 6px;
  text-decoration: none;
  transition: background 0.15s;
}
.btn-primary:hover { background: var(--blue-dark); }

/* Botão ghost (topbar) */
.btn-ghost {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.btn-ghost:hover { background: var(--surface); color: var(--text); }
```

---

## 3. ÁREA DE CONTEÚDO

```css
.content {
  flex: 1;
  padding: 28px;
}
```

---

## 4. COMPONENTES REUTILIZÁVEIS

### KPI Card

```html
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-icon" style="--icon-color:#3B82F6">
      <!-- SVG icon -->
    </div>
    <div class="kpi-body">
      <p class="kpi-label">Total de Funcionários</p>
      <p class="kpi-value">42</p>
      <p class="kpi-trend trend-up">▲ 3 este mês</p>
    </div>
  </div>
  <!-- repetir x4 -->
</div>
```

```css
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.kpi-icon {
  width: 38px; height: 38px;
  border-radius: var(--radius-md);
  background: rgba(var(--icon-color-rgb, 59,130,246), 0.12);
  border: 1px solid rgba(var(--icon-color-rgb, 59,130,246), 0.3);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  color: var(--icon-color, var(--blue));
}
.kpi-icon svg { width: 18px; height: 18px; }

.kpi-label { font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }
.kpi-value { font-size: 26px; font-weight: 700; letter-spacing: -0.5px; color: var(--text); line-height: 1; }
.kpi-trend { font-size: 11px; margin-top: 6px; font-weight: 500; }
.trend-up   { color: var(--green); }
.trend-down { color: var(--red); }
.trend-flat { color: var(--text-faint); }
```

### Tabela

```css
.table-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  background: rgba(23,31,45,0.8);
}
.table-header h3 { font-size: 14px; font-weight: 600; color: var(--text); }

table { width: 100%; border-collapse: collapse; }

thead tr {
  background: rgba(18,26,40,0.8);
  border-bottom: 1px solid var(--border);
}
thead th {
  text-align: left;
  padding: 10px 20px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: var(--text-faint);
}

tbody tr {
  border-bottom: 1px solid var(--border-subtle);
  transition: background 0.1s;
}
tbody tr:hover   { background: var(--surface-hover); }
tbody tr:last-child { border-bottom: none; }

tbody td {
  padding: 12px 20px;
  font-size: 13px;
  color: var(--text-muted);
}
tbody td.td-name { color: var(--text); font-weight: 500; }

/* Avatar em linha */
.row-avatar {
  display: flex; align-items: center; gap: 10px;
}
.avatar-circle {
  width: 30px; height: 30px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700;
  flex-shrink: 0;
}
```

### Badge de status

```css
.badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 9px;
  border-radius: var(--radius-sm);
  font-size: 11px; font-weight: 500;
  white-space: nowrap;
}
.badge-green  { background:rgba(16,185,129,0.12); color:#10B981; border:1px solid rgba(16,185,129,0.3); }
.badge-blue   { background:rgba(59,130,246,0.12);  color:#3B82F6; border:1px solid rgba(59,130,246,0.3); }
.badge-red    { background:rgba(239,68,68,0.12);   color:#EF4444; border:1px solid rgba(239,68,68,0.3); }
.badge-amber  { background:rgba(245,158,11,0.12);  color:#F59E0B; border:1px solid rgba(245,158,11,0.3); }
.badge-gray   { background:rgba(107,114,128,0.15); color:#9CA3AF; border:1px solid rgba(107,114,128,0.3); }
```

### Card de seção genérico

```css
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: 20px;
}
.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
}
.panel-title { font-size: 14px; font-weight: 600; color: var(--text); }
.panel-body  { padding: 20px; }
```

---

## 5. PÁGINA: DASHBOARD (dashboard.html)

### KPI Cards — dados reais
| Label | Valor | Trend | Cor ícone |
|-------|-------|-------|-----------|
| Total de Funcionários | 42 | — | `#3B82F6` |
| Presentes Hoje | 38 | ▲ 90,5% | `#10B981` |
| Horas Trabalhadas | 186h | ▲ 12% | `#F59E0B` |
| Faltas no Mês | 4 | ▼ 2 | `#EF4444` |

### Gráfico de barras — Horas por semana

Implemente com `<canvas>` via **Chart.js (CDN)** ou com SVG puro. Dados da semana:

```js
// Se usar Chart.js
const data = {
  labels: ['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'],
  datasets: [{
    data: [7.5, 8.0, 8.5, 9.0, 8.0, 2.0, 0],
    backgroundColor: (ctx) =>
      ctx.dataIndex === 3 ? '#3B82F6' : 'rgba(59,130,246,0.4)',
    borderRadius: 4,
    borderSkipped: false,
  }]
};
const options = {
  responsive: true,
  plugins: { legend: { display: false } },
  scales: {
    x: { grid: { color: 'rgba(55,65,81,0.4)' }, ticks: { color: '#6B7280' } },
    y: { grid: { color: 'rgba(55,65,81,0.4)' }, ticks: { color: '#6B7280' }, max: 10 }
  }
};
```

Título do chart panel: **"Horas Trabalhadas — Semana Atual"**  
Subtítulo: **"Jun 2026 · Total: 186h acumuladas"**

### Donut — Status funcionários

```js
// Chart.js doughnut
labels: ['Presentes', 'Em Férias', 'Ausentes'],
data:   [38, 2, 2],
backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
borderWidth: 0,
cutout: '68%'
```

Layout dos dois charts: **dois painéis lado a lado** — bar chart 60% largura, donut 40% largura.

### Tabela de funcionários
Colunas: **Funcionário / Cargo / Entrada / Horas Hoje / Status / Ações**

Dados das primeiras 7 linhas:

| Nome | Cargo | Entrada | Horas | Status |
|------|-------|---------|-------|--------|
| João Silva | Porteiro | 08:02 | 0h45 | Presente |
| Maria Santos | Zeladora | 07:58 | 0h49 | Presente |
| Carlos Lima | Seg. Noturno | 08:10 | 0h37 | Presente |
| Ana Ferreira | Recepcionista | 07:55 | 0h52 | Presente |
| Paulo Costa | Jardineiro | 08:15 | 0h32 | Presente |
| Roberto Souza | Faxineiro | — | — | Ausente |
| Fernanda Alves | Zeladora | — | — | Em Férias |

Coluna "Ações": ícone de olho + ícone de lápis (botões ghost 28px).

---

## 6. PÁGINA: FUNCIONÁRIOS (funcionarios.html)

### Topbar desta página
- Título: "Funcionários"
- Botão primário: "+ Novo Funcionário"
- Botão ghost: "↓ Exportar"

### Filtros/busca acima da tabela

```html
<div class="table-filters">
  <input type="search" placeholder="Buscar funcionário..." class="search-input">
  <select class="filter-select">
    <option>Todos os cargos</option>
    <option>Porteiro</option>
    <option>Zelador</option>
    <option>Segurança</option>
  </select>
  <select class="filter-select">
    <option>Todos os status</option>
    <option>Ativo</option>
    <option>Inativo</option>
  </select>
</div>
```

```css
.table-filters {
  display: flex; gap: 10px; margin-bottom: 16px; align-items: center;
}
.search-input {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 8px 14px;
  font-size: 13px; color: var(--text); flex: 1; max-width: 320px;
  outline: none;
}
.search-input:focus { border-color: var(--blue-border); box-shadow: 0 0 0 3px var(--blue-dim); }
.filter-select {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 8px 12px;
  font-size: 13px; color: var(--text-muted); cursor: pointer; outline: none;
}
```

### Tabela completa
Colunas: **Funcionário / CPF / Cargo / Turno / Admissão / Status / Ações**

15 linhas de funcionários fictícios com dados realistas (admissão entre 2021–2024, turnos Manhã/Tarde/Noite).

---

## 7. PÁGINA: CONTROLE DE PONTO (ponto.html)

### Topbar
- Título: "Controle de Ponto"
- Seletor de mês: dropdown `<select>` com meses (Jan–Jun 2026)
- Botão ghost: "↓ Espelho de Ponto PDF"

### Filtro de funcionário
Input de busca + select de cargo acima da tabela.

### Tabela de batidas do mês
Colunas: **Data / Dia / Entrada / Saída Almoço / Retorno / Saída / Total / Ocorrência**

20 linhas representando dias úteis de Jun 2026. Finais de semana com badge `Folga`. Ocorrências: `Normal`, `Hora Extra`, `Falta`, `Atestado`.

Cor das ocorrências:
- Normal → `badge-gray`
- Hora Extra → `badge-blue`
- Falta → `badge-red`
- Atestado → `badge-amber`

### Resumo mensal (abaixo da tabela)
Cards pequenos em linha: **Dias Trabalhados / Total de Horas / Horas Extras / Faltas / Atrasos**

---

## 8. PÁGINA: FALTAS / FÉRIAS (faltas.html)

### Topbar
- Título: "Faltas / Férias"
- Botão: "+ Registrar Ocorrência"

### Tabs de navegação

```css
.tabs { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 1px solid var(--border); }
.tab {
  padding: 10px 16px; font-size: 13px; font-weight: 500;
  color: var(--text-muted); cursor: pointer; border-bottom: 2px solid transparent;
  transition: color 0.15s;
}
.tab.active { color: var(--blue); border-bottom-color: var(--blue); }
```

Tabs: **Todas as Ocorrências · Férias · Atestados · Faltas Injustificadas**

### Tabela
Colunas: **Funcionário / Tipo / Período / Dias / Motivo / Status / Ações**

Status das ocorrências:
- Aprovado → `badge-green`
- Pendente → `badge-amber`
- Rejeitado → `badge-red`

---

## 9. PÁGINA: TAREFAS (tarefas.html)

### Layout: Kanban (3 colunas)

```css
.kanban { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }

.kanban-col {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
}
.kanban-col-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 14px;
}
.kanban-col-title { font-size: 13px; font-weight: 600; color: var(--text); }
.col-count {
  background: var(--surface-2); color: var(--text-faint);
  font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 99px;
}

.task-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 14px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: border-color 0.15s;
}
.task-card:hover { border-color: var(--blue-border); }
.task-title { font-size: 13px; font-weight: 500; color: var(--text); margin-bottom: 8px; }
.task-meta  { display: flex; justify-content: space-between; align-items: center; }
.task-assignee { font-size: 11px; color: var(--text-muted); }
.task-due { font-size: 11px; color: var(--text-faint); }
```

Colunas: **A Fazer (4 cards) · Em Andamento (3 cards) · Concluído (5 cards)**

Exemplo de tasks: "Limpeza do hall" · "Verificar extintores" · "Relatório mensal" · "Trocar lâmpadas" · "Ronda noturna"

---

## 10. PÁGINA: CONFIGURAÇÕES (configuracoes.html)

### Layout: menu lateral + formulário

```css
.settings-layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 20px;
}
.settings-nav {
  display: flex; flex-direction: column; gap: 2px;
}
.settings-nav-item {
  padding: 9px 12px; border-radius: var(--radius-md);
  font-size: 13px; color: var(--text-muted);
  cursor: pointer; transition: background 0.12s, color 0.12s;
}
.settings-nav-item:hover  { background: var(--surface-hover); color: var(--text); }
.settings-nav-item.active { background: var(--blue-dim); color: var(--blue); font-weight: 600; }
```

Seções: Condomínio · Equipe · Plano e Faturamento · Notificações · Segurança

### Formulário de Condomínio (seção padrão ativa)
Campos: Nome do Condomínio · CNPJ · Endereço · Responsável · E-mail · Telefone

```css
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.field label {
  display: block; font-size: 10px; font-weight: 600;
  letter-spacing: 1.2px; text-transform: uppercase;
  color: var(--text-faint); margin-bottom: 6px;
}
.field input {
  width: 100%; background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 10px 14px;
  font-size: 14px; color: var(--text); font-family: var(--font); outline: none;
}
.field input:focus { border-color: var(--blue-border); box-shadow: 0 0 0 3px var(--blue-dim); }
.field input::placeholder { color: var(--text-faint); }
```

Botão salvar: `btn-primary` + botão "Cancelar" ghost à esquerda.

---

## REGRAS GERAIS

1. **Um arquivo por página** — `dashboard.html`, `funcionarios.html`, `ponto.html`, `faltas.html`, `tarefas.html`, `configuracoes.html`
2. **Sidebar e topbar idênticos** em todas as páginas — só muda `nav-item.active` e o conteúdo de `.content`
3. **Chart.js via CDN** para gráficos: `https://cdn.jsdelivr.net/npm/chart.js`
4. **Sem frameworks CSS externos** — só Inter + CSS puro
5. **Todas as tabelas responsivas** — `overflow-x: auto` em telas < 1024px
6. **Página ativa na sidebar** — adicionar `class="active"` no `.nav-item` correspondente à página atual

---

*Prompt — Dashboard & Páginas Internas StaFlow · Design System v2.0*
