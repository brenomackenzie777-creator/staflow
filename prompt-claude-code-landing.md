# Prompt para Claude Code — Reimplementação da `staflow-landing.html`

> Cole este prompt diretamente no Claude Code para redesenhar a landing page do StaFlow no novo visual enterprise aprovado.

---

## CONTEXTO

Você vai reimplementar completamente o arquivo `staflow-landing.html` com um novo design enterprise B2B. O produto é o **StaFlow** — SaaS brasileiro de gestão de ponto e jornada para condomínios. A nova identidade visual foi aprovada com base num dashboard enterprise estilo Totvs/Senior/Ahgora, com fundo escuro, Inter como fonte, azul corporativo como acento e layout denso e profissional.

**Não mantenha nada do visual atual.** Substitua completamente HTML, CSS e estrutura de seções.

---

## DESIGN SYSTEM — TOKENS OBRIGATÓRIOS

Cole este bloco de CSS variables no `<style>` do arquivo:

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
  --shadow-sm:    0 1px 3px rgba(0,0,0,0.3);
  --shadow-md:    0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg:    0 8px 32px rgba(0,0,0,0.5);
  --shadow-blue:  0 4px 20px rgba(59,130,246,0.25);
  --font:         'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 15px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
```

### Fonte

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
```

---

## ESTRUTURA DE SEÇÕES

O arquivo deve ter exatamente estas seções, nesta ordem:

1. `<nav>` — Navbar sticky
2. `<section id="hero">` — Hero principal
3. `<section id="features">` — Funcionalidades (grid 3 colunas)
4. `<section id="dashboard-preview">` — Preview do dashboard (imagem/mockup)
5. `<section id="como-funciona">` — Como funciona (3 passos)
6. `<section id="para-quem">` — Para quem é (2 perfis: síndico + porteiro)
7. `<section id="planos">` — Planos (3 cards: Starter / Pro / Enterprise)
8. `<section id="cta-final">` — CTA final
9. `<footer>` — Footer

---

## ESPECIFICAÇÕES POR SEÇÃO

---

### 1. NAVBAR

```css
/* Comportamento */
position: sticky; top: 0; z-index: 100;
background: rgba(17,24,39,0.92);
backdrop-filter: blur(12px);
-webkit-backdrop-filter: blur(12px);
border-bottom: 1px solid rgba(55,65,81,0.6);
height: 64px;
padding: 0 clamp(24px, 5vw, 80px);
display: flex; align-items: center; justify-content: space-between;
```

**Conteúdo:**
- **Logo:** `<span style="color:var(--text)">Sta</span><span style="color:var(--blue)">Flow</span>` — Inter 700, 18px, letter-spacing -0.5px
- **Links:** Funcionalidades · Como Funciona · Para Quem · Planos — 14px, peso 500, cor `var(--text-muted)`, hover `var(--text)`
- **Botões à direita:**
  - "Entrar" — botão ghost (border: 1px solid var(--border), bg transparent, cor var(--text-muted))
  - "Começar grátis" — botão primário azul

**CSS botão primário:**
```css
background: var(--blue);
color: var(--text);
font-size: 14px;
font-weight: 600;
padding: 9px 18px;
border-radius: var(--radius-md);
border: none;
cursor: pointer;
box-shadow: var(--shadow-blue);
transition: background 0.15s, transform 0.1s;
text-decoration: none;

/* Hover */
background: var(--blue-dark);
transform: translateY(-1px);
```

---

### 2. HERO

Layout: centralizado, texto + subtítulo + 2 CTAs + badge enterprise acima do título.

```css
/* Container */
padding: 100px clamp(24px, 5vw, 80px) 80px;
max-width: 900px;
margin: 0 auto;
text-align: center;
```

**Estrutura HTML:**
```html
<!-- Tag enterprise -->
<div class="hero-tag">
  <span class="dot"></span> Sistema de Gestão de Ponto — Enterprise
</div>

<!-- Título principal -->
<h1 class="hero-title">
  Gestão de ponto e jornada<br>
  para o seu <span class="highlight">condomínio</span>
</h1>

<!-- Subtítulo -->
<p class="hero-sub">
  Controle de acesso, registro de ponto e gestão de equipes para síndicos
  e administradoras. Simples, preciso, confiável.
</p>

<!-- CTAs -->
<div class="hero-ctas">
  <a href="#planos" class="btn-primary btn-xl">Começar gratuitamente</a>
  <a href="#dashboard-preview" class="btn-ghost btn-xl">Ver demonstração →</a>
</div>

<!-- Stats / social proof -->
<div class="hero-stats">
  <div class="stat"><strong>+500</strong><span>Condomínios</span></div>
  <div class="stat-divider"></div>
  <div class="stat"><strong>+12.000</strong><span>Funcionários</span></div>
  <div class="stat-divider"></div>
  <div class="stat"><strong>99,9%</strong><span>Uptime</span></div>
</div>
```

**CSS específico:**
```css
.hero-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--blue-dim);
  border: 1px solid var(--blue-border);
  border-radius: 99px;
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 500;
  color: var(--blue);
  letter-spacing: 0.3px;
  margin-bottom: 24px;
}

.hero-tag .dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--blue);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.85); }
}

.hero-title {
  font-size: clamp(36px, 5vw, 52px);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -1.5px;
  color: var(--text);
  margin-bottom: 20px;
}

.hero-title .highlight { color: var(--blue); }

.hero-sub {
  font-size: 17px;
  color: var(--text-muted);
  line-height: 1.7;
  max-width: 560px;
  margin: 0 auto 36px;
}

.hero-ctas {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 48px;
}

.btn-xl { padding: 14px 28px; font-size: 15px; }

.btn-ghost {
  background: transparent;
  color: var(--text);
  border: 1px solid var(--border);
  padding: 13px 24px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: border-color 0.15s, background 0.15s;
}
.btn-ghost:hover {
  background: rgba(55,65,81,0.4);
  border-color: var(--text-faint);
}

.hero-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
}

.hero-stats .stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.hero-stats strong { font-size: 22px; font-weight: 700; color: var(--text); }
.hero-stats span   { font-size: 12px; color: var(--text-muted); }
.stat-divider { width: 1px; height: 36px; background: var(--border); }
```

---

### 3. FUNCIONALIDADES

Grid 3 colunas. Fundo levemente diferente para contrastar com o hero.

```css
/* Seção */
background: var(--surface);
border-top: 1px solid var(--border);
border-bottom: 1px solid var(--border);
padding: 80px clamp(24px, 5vw, 80px);
```

**Header da seção (padrão para todas as seções):**
```html
<div class="section-header">
  <p class="section-label">FUNCIONALIDADES</p>
  <h2 class="section-title">Tudo que seu condomínio precisa</h2>
  <p class="section-sub">Controle completo da equipe, do registro ao relatório.</p>
</div>
```

```css
.section-header { text-align: center; margin-bottom: 56px; }

.section-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--blue);
  margin-bottom: 12px;
}

.section-title {
  font-size: clamp(26px, 3.5vw, 36px);
  font-weight: 700;
  letter-spacing: -0.8px;
  color: var(--text);
  margin-bottom: 12px;
}

.section-sub {
  font-size: 16px;
  color: var(--text-muted);
  max-width: 480px;
  margin: 0 auto;
}
```

**Grid de funcionalidades:**
```html
<div class="features-grid">
  <!-- card x6 -->
</div>
```

```css
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  max-width: 1100px;
  margin: 0 auto;
}
```

**Feature card:**
```css
.feature-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.feature-card:hover {
  border-color: rgba(59,130,246,0.35);
  box-shadow: 0 0 20px rgba(59,130,246,0.06);
}

.feature-icon {
  width: 40px; height: 40px;
  border-radius: var(--radius-md);
  background: var(--blue-dim);
  border: 1px solid var(--blue-border);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px;
  font-size: 18px; /* ou SVG */
}

.feature-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}

.feature-desc {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.6;
}
```

**6 funcionalidades para incluir:**
1. **Registro de Ponto** — Funcionários registram entrada e saída pelo app
2. **Controle de Jornada** — Acompanhe horas trabalhadas, extras e faltas em tempo real
3. **App do Funcionário** — PWA mobile com botão de ponto, tarefas e atestados
4. **Gestão de Faltas** — Justificativas, férias e atestados centralizados
5. **Relatórios PDF** — Exportação de espelho de ponto e relatórios mensais
6. **Dashboard em tempo real** — Veja quem está presente agora, gráficos e métricas

---

### 4. DASHBOARD PREVIEW

Seção de impacto visual com screenshot do dashboard.

```css
padding: 80px clamp(24px, 5vw, 80px);
```

**Estrutura:**
- Pequena tag "PREVIEW" + título + subtítulo centralizados
- Container do mockup com glow azul sutil ao redor

```css
.preview-container {
  max-width: 1100px;
  margin: 0 auto;
  position: relative;
}

.preview-container::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(59,130,246,0.3), rgba(139,92,246,0.15), transparent 60%);
  z-index: -1;
  filter: blur(24px);
}

.preview-frame {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

/* Barra de janela fake */
.preview-titlebar {
  background: #171F2E;
  height: 40px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 8px;
  border-bottom: 1px solid var(--border);
}

.preview-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
}
.preview-dot.red    { background: #EF4444; opacity: 0.7; }
.preview-dot.amber  { background: #F59E0B; opacity: 0.7; }
.preview-dot.green  { background: #10B981; opacity: 0.7; }

.preview-url {
  flex: 1;
  background: rgba(55,65,81,0.4);
  border-radius: 4px;
  height: 22px;
  max-width: 320px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: var(--text-faint);
}
```

> **Nota de implementação:** Use uma screenshot do dashboard como `<img>` dentro de `.preview-frame`, ou use um `<iframe>` apontando para `dashboard.html`. Se não houver screenshot, construa um mini-mockup HTML do dashboard com sidebar, KPI cards e tabela.

---

### 5. COMO FUNCIONA

3 passos numerados, layout horizontal.

```css
padding: 80px clamp(24px, 5vw, 80px);
background: var(--surface);
border-top: 1px solid var(--border);
border-bottom: 1px solid var(--border);
```

**Grid:**
```css
.steps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  max-width: 960px;
  margin: 0 auto;
  position: relative;
}

/* Linha conectora entre passos */
.steps-grid::before {
  content: '';
  position: absolute;
  top: 28px; left: 80px; right: 80px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border) 20%, var(--border) 80%, transparent);
}
```

**Step card:**
```css
.step { text-align: center; padding: 0 16px; }

.step-number {
  width: 48px; height: 48px;
  border-radius: 50%;
  background: var(--bg);
  border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: var(--blue);
  margin: 0 auto 20px;
  position: relative;
  z-index: 1;
}

.step-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 10px;
}

.step-desc {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.6;
}
```

**3 passos:**
1. **Cadastre o condomínio** — Configure síndico, unidades e equipe em minutos. Sem instalação.
2. **Distribua o acesso** — Cada funcionário recebe login único para o app mobile de ponto.
3. **Gerencie em tempo real** — Acompanhe presença, horas e relatórios no painel web.

---

### 6. PARA QUEM É

2 colunas: Síndico/Administradora e Funcionário/Porteiro.

```css
padding: 80px clamp(24px, 5vw, 80px);

.profiles-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.profile-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 32px;
}

.profile-card.highlighted {
  border-color: var(--blue-border);
  background: linear-gradient(135deg, rgba(59,130,246,0.04) 0%, var(--surface) 100%);
}

.profile-icon-area {
  width: 52px; height: 52px;
  border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
  margin-bottom: 20px;
}

/* Síndico: fundo azul dim */
.profile-icon-area.blue { background: var(--blue-dim); border: 1px solid var(--blue-border); }
/* Funcionário: fundo verde dim */
.profile-icon-area.green { background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); }

.profile-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 8px; }
.profile-sub   { font-size: 13px; color: var(--text-muted); margin-bottom: 20px; }

.profile-list  { list-style: none; display: flex; flex-direction: column; gap: 10px; }
.profile-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  color: var(--text-muted);
}
.profile-list li::before {
  content: '✓';
  color: var(--blue);
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}
```

**Conteúdo dos cards:**

**Síndico / Administradora:**
- Dashboard completo com presença em tempo real
- Relatórios mensais de ponto em PDF
- Gestão de faltas, férias e atestados
- Múltiplos condomínios num único painel
- Alertas de atraso e ausência

**Funcionário / Porteiro:**
- App mobile leve (funciona como PWA)
- Botão único para registro de ponto
- Histórico de batidas e jornada
- Envio de atestado pelo app
- Recebimento de tarefas do gestor

---

### 7. PLANOS

3 cards de preço: Starter, Pro, Enterprise.

```css
padding: 80px clamp(24px, 5vw, 80px);
background: var(--surface);
border-top: 1px solid var(--border);
border-bottom: 1px solid var(--border);

.plans-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  max-width: 960px;
  margin: 0 auto;
}

.plan-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 28px;
  display: flex;
  flex-direction: column;
}

.plan-card.featured {
  border-color: var(--blue);
  box-shadow: 0 0 0 1px var(--blue), var(--shadow-blue);
  position: relative;
}

/* Badge "Mais popular" */
.plan-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--blue);
  color: var(--text);
  font-size: 11px;
  font-weight: 600;
  padding: 3px 14px;
  border-radius: 99px;
  white-space: nowrap;
}

.plan-name {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.plan-price {
  font-size: 36px;
  font-weight: 800;
  letter-spacing: -1px;
  color: var(--text);
  margin-bottom: 4px;
}
.plan-price span { font-size: 16px; font-weight: 400; color: var(--text-muted); }

.plan-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
}

.plan-features {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  margin-bottom: 24px;
}
.plan-features li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  color: var(--text-muted);
}
.plan-features li::before {
  content: '✓';
  color: var(--green);
  font-weight: 700;
  flex-shrink: 0;
}
```

**Dados dos planos:**

| | Starter | Pro | Enterprise |
|-|---------|-----|------------|
| Preço | R$ 97/mês | R$ 197/mês | Sob consulta |
| Funcionários | Até 15 | Até 60 | Ilimitado |
| Condomínios | 1 | Até 3 | Ilimitado |
| Destaque | — | ✓ (Mais popular) | — |

**Features Starter:** Registro de ponto · App mobile · Dashboard básico · Relatórios PDF · Suporte por e-mail

**Features Pro (tudo do Starter +):** Múltiplos condomínios · Gestão de tarefas · Alertas de ausência · API de integração · Suporte prioritário

**Features Enterprise (tudo do Pro +):** Usuários ilimitados · SLA garantido · Integração com folha · Onboarding dedicado · Conta gerenciada

---

### 8. CTA FINAL

Seção de conversão, fundo com leve brilho azul.

```css
padding: 100px clamp(24px, 5vw, 80px);
text-align: center;
position: relative;
overflow: hidden;

/* Glow de fundo */
.cta-section::before {
  content: '';
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 600px; height: 400px;
  background: radial-gradient(ellipse, rgba(59,130,246,0.08) 0%, transparent 70%);
  pointer-events: none;
}
```

**Conteúdo:**
```html
<p class="section-label">COMECE HOJE</p>
<h2 style="font-size: clamp(28px,4vw,42px); font-weight:800; letter-spacing:-1px; margin-bottom:16px;">
  Seu condomínio organizado em 5 minutos
</h2>
<p style="font-size:17px; color:var(--text-muted); max-width:480px; margin:0 auto 36px;">
  Cadastre-se grátis, sem cartão de crédito. Configure sua equipe e comece a registrar ponto hoje.
</p>
<div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
  <a href="/cadastro" class="btn-primary btn-xl">Criar conta gratuita</a>
  <a href="/contato" class="btn-ghost btn-xl">Falar com vendas</a>
</div>
<p style="margin-top:20px; font-size:12px; color:var(--text-faint);">
  14 dias grátis · Sem cartão de crédito · Cancele a qualquer momento
</p>
```

---

### 9. FOOTER

```css
.footer {
  background: var(--surface);
  border-top: 1px solid var(--border);
  padding: 48px clamp(24px, 5vw, 80px) 32px;
}

.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 40px;
  max-width: 1100px;
  margin: 0 auto 40px;
}

.footer-brand p { font-size: 13px; color: var(--text-muted); margin-top: 12px; max-width: 240px; }

.footer-col h4 {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: var(--text-faint);
  margin-bottom: 16px;
}

.footer-col a {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
  text-decoration: none;
  margin-bottom: 10px;
  transition: color 0.15s;
}
.footer-col a:hover { color: var(--text); }

.footer-bottom {
  border-top: 1px solid var(--border);
  padding-top: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--text-faint);
  max-width: 1100px;
  margin: 0 auto;
}
```

**Colunas do footer:**
- **Col 1:** Logo + "Gestão de ponto para condomínios." + © 2026 StaFlow
- **Col 2: Produto** — Funcionalidades · Dashboard · App Mobile · Planos · API
- **Col 3: Empresa** — Sobre · Blog · Contato · Carreiras · Status
- **Col 4: Suporte** — Documentação · Central de Ajuda · Termos de Uso · Privacidade

---

## REGRAS GERAIS DE IMPLEMENTAÇÃO

1. **Arquivo único** — Tudo num só `staflow-landing.html` (HTML + CSS inline + JS mínimo se necessário)
2. **Zero dependências externas** além do Google Fonts — sem Bootstrap, Tailwind, jQuery
3. **Responsivo** — Mobile-first; abaixo de 768px: nav hambúrguer, grid 1 coluna, hero centralizado
4. **Sem gradientes de cor** no fundo principal — apenas radial-gradient sutil para efeito de glow (azul, baixa opacidade)
5. **Links de navegação** devem rolar suavemente para a seção correspondente (`scroll-behavior: smooth`)
6. **Não use cores fora do design system** — proibido usar teal, rosa, neon
7. **Botão primário = azul `#3B82F6`** — único CTA de cor forte na página
8. **Inter em todos os textos** — sem fallbacks para outras fontes "display"
9. **`background: #111827`** no body — nunca preto puro `#000000`
10. **Transições suaves** — `transition: 0.15s` nos botões, `0.2s` nos cards

---

## ESTRUTURA HTML COMPLETA (skeleton)

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StaFlow — Gestão de Ponto para Condomínios</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    /* === DESIGN SYSTEM VARIABLES === */
    :root { ... }

    /* === RESET === */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--text); font-family: var(--font); ... }

    /* === NAVBAR === */
    /* === HERO === */
    /* === FEATURES === */
    /* === PREVIEW === */
    /* === COMO FUNCIONA === */
    /* === PARA QUEM === */
    /* === PLANOS === */
    /* === CTA FINAL === */
    /* === FOOTER === */
    /* === RESPONSIVE === */
  </style>
</head>
<body>
  <nav class="navbar">...</nav>
  <section id="hero">...</section>
  <section id="features">...</section>
  <section id="dashboard-preview">...</section>
  <section id="como-funciona">...</section>
  <section id="para-quem">...</section>
  <section id="planos">...</section>
  <section id="cta-final" class="cta-section">...</section>
  <footer class="footer">...</footer>
</body>
</html>
```

---

*Prompt gerado por Camila — Design & Identity Visual StaFlow — Jun 2026*  
*Design System completo em: `staflow-design-system.md`*
