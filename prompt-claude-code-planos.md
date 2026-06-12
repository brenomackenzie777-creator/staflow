# Prompt para Claude Code — `planos.html`

> Cole este prompt no Claude Code para implementar a página de preços do StaFlow com os 4 planos reais: Starter · Pro · Advanced · Scale.

---

## CONTEXTO

Reimplemente `planos.html` com os 4 planos reais do StaFlow. A página é standalone (mesma navbar da landing page, sem sidebar). Os planos devem ter tabela comparativa completa abaixo dos cards. O destaque visual vai para o plano **Pro** (mais vendido).

---

## DESIGN SYSTEM — VARIÁVEIS CSS

```css
:root {
  --bg:          #111827;
  --surface:     #1F2937;
  --surface-2:   #374151;
  --text:        #F9FAFB;
  --text-muted:  #9CA3AF;
  --text-faint:  #6B7280;
  --blue:        #3B82F6;
  --blue-dark:   #1D4ED8;
  --blue-dim:    rgba(59,130,246,0.12);
  --blue-border: rgba(59,130,246,0.35);
  --green:       #10B981;
  --amber:       #F59E0B;
  --border:      #374151;
  --radius-md:   6px;
  --radius-lg:   8px;
  --radius-xl:   12px;
  --shadow-blue: 0 4px 20px rgba(59,130,246,0.25);
  --font:        'Inter', -apple-system, sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 15px;
  -webkit-font-smoothing: antialiased;
}
```

Fonte: `Inter` via Google Fonts, pesos 400 500 600 700 800.

---

## ESTRUTURA HTML

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>...</head>
<body>

  <!-- Navbar (idêntica à landing) -->
  <nav class="navbar">...</nav>

  <!-- Hero da página de planos -->
  <section class="plans-hero">...</section>

  <!-- Toggle mensal/anual -->
  <div class="billing-toggle">...</div>

  <!-- 4 cards de plano -->
  <section class="plans-grid-section">
    <div class="plans-grid">
      <!-- Starter / Pro / Advanced / Scale -->
    </div>
  </section>

  <!-- Tabela comparativa -->
  <section class="compare-section">...</section>

  <!-- FAQ -->
  <section class="faq-section">...</section>

  <!-- CTA final -->
  <section class="cta-section">...</section>

  <footer>...</footer>

</body>
</html>
```

---

## 1. NAVBAR

Idêntica à landing page. Logo `StaFlow` (Sta branco, Flow azul), links Funcionalidades · Dashboard · Planos (active), botões "Entrar" e "Começar grátis".

```css
.navbar {
  position: sticky; top: 0; z-index: 100;
  background: rgba(17,24,39,0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(55,65,81,0.6);
  padding: 0 clamp(24px,5vw,80px);
  height: 64px;
  display: flex; align-items: center; justify-content: space-between;
}
/* Mesmos estilos da landing — reutilize o CSS */
```

---

## 2. HERO DA PÁGINA

```html
<section class="plans-hero">
  <p class="section-label">PLANOS E PREÇOS</p>
  <h1 class="plans-hero-title">Escolha o plano ideal<br>para seu condomínio</h1>
  <p class="plans-hero-sub">
    Comece grátis por 14 dias. Sem cartão de crédito. Cancele quando quiser.
  </p>
</section>
```

```css
.plans-hero {
  text-align: center;
  padding: 72px clamp(24px,5vw,80px) 40px;
}
.section-label {
  font-size: 11px; font-weight: 600; letter-spacing: 2px;
  text-transform: uppercase; color: var(--blue); margin-bottom: 14px;
}
.plans-hero-title {
  font-size: clamp(32px,4.5vw,48px);
  font-weight: 800; letter-spacing: -1.2px;
  color: var(--text); line-height: 1.1; margin-bottom: 14px;
}
.plans-hero-sub {
  font-size: 16px; color: var(--text-muted); max-width: 440px; margin: 0 auto;
}
```

---

## 3. TOGGLE MENSAL / ANUAL

```html
<div class="billing-toggle">
  <button class="toggle-btn active" data-billing="monthly">Mensal</button>
  <button class="toggle-btn" data-billing="annual">
    Anual
    <span class="discount-tag">-20%</span>
  </button>
</div>
```

```css
.billing-toggle {
  display: flex; align-items: center; justify-content: center; gap: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 4px;
  width: fit-content;
  margin: 0 auto 48px;
}
.toggle-btn {
  background: transparent; border: none; cursor: pointer;
  padding: 8px 20px; border-radius: 9px;
  font-family: var(--font); font-size: 14px; font-weight: 500;
  color: var(--text-muted);
  display: flex; align-items: center; gap: 8px;
  transition: background 0.15s, color 0.15s;
}
.toggle-btn.active { background: var(--bg); color: var(--text); }

.discount-tag {
  background: rgba(16,185,129,0.15);
  color: var(--green);
  border: 1px solid rgba(16,185,129,0.3);
  font-size: 10px; font-weight: 700;
  padding: 2px 7px; border-radius: 99px;
  letter-spacing: 0.3px;
}
```

```js
// Toggle billing
const toggleBtns = document.querySelectorAll('.toggle-btn');
toggleBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    toggleBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const isAnnual = btn.dataset.billing === 'annual';
    // Atualizar preços
    document.querySelectorAll('.plan-price-monthly').forEach(el => {
      el.style.display = isAnnual ? 'none' : 'block';
    });
    document.querySelectorAll('.plan-price-annual').forEach(el => {
      el.style.display = isAnnual ? 'block' : 'none';
    });
  });
});
```

---

## 4. CARDS DE PLANO

```css
.plans-grid-section {
  padding: 0 clamp(24px,5vw,80px) 60px;
}
.plans-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  max-width: 1160px;
  margin: 0 auto;
}

.plan-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 28px 24px;
  display: flex; flex-direction: column;
  position: relative;
  transition: border-color 0.2s;
}
.plan-card:hover { border-color: rgba(59,130,246,0.3); }

/* Destaque: Pro */
.plan-card.featured {
  border-color: var(--blue);
  box-shadow: 0 0 0 1px var(--blue), var(--shadow-blue), 0 0 40px rgba(59,130,246,0.08);
}
.plan-badge {
  position: absolute; top: -13px; left: 50%; transform: translateX(-50%);
  background: var(--blue); color: var(--text);
  font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
  padding: 4px 16px; border-radius: 99px; white-space: nowrap;
}

.plan-name {
  font-size: 12px; font-weight: 700;
  letter-spacing: 1.2px; text-transform: uppercase;
  color: var(--text-muted); margin-bottom: 12px;
}
.plan-card.featured .plan-name { color: var(--blue); }

/* Preço */
.plan-price-wrap { margin-bottom: 8px; }
.plan-price {
  font-size: 38px; font-weight: 800;
  letter-spacing: -1.5px; color: var(--text); line-height: 1;
}
.plan-price sup { font-size: 18px; font-weight: 600; vertical-align: super; }
.plan-price sub {
  font-size: 14px; font-weight: 400; color: var(--text-muted);
  vertical-align: baseline; letter-spacing: 0;
}
.plan-price-annual { display: none; } /* JS controla visibilidade */

.plan-desc {
  font-size: 13px; color: var(--text-muted); line-height: 1.5;
  margin-bottom: 20px; padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
  min-height: 52px;
}

/* Lista de features */
.plan-features {
  list-style: none; flex: 1;
  display: flex; flex-direction: column; gap: 9px;
  margin-bottom: 24px;
}
.plan-features li {
  display: flex; align-items: flex-start; gap: 9px;
  font-size: 13px; color: var(--text-muted);
}
.plan-features li::before {
  content: '';
  display: inline-block;
  width: 14px; height: 14px; flex-shrink: 0; margin-top: 1px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M3 8l4 4 6-6' stroke='%2310B981' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-size: contain; background-repeat: no-repeat;
}
.plan-features li.disabled {
  opacity: 0.4;
}
.plan-features li.disabled::before {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M5 11l6-6M11 11L5 5' stroke='%236B7280' stroke-width='1.8' stroke-linecap='round'/%3E%3C/svg%3E");
}

/* Botão CTA do card */
.plan-cta {
  display: block; text-align: center;
  padding: 11px; border-radius: var(--radius-md);
  font-size: 14px; font-weight: 600;
  text-decoration: none; cursor: pointer;
  transition: background 0.15s, transform 0.1s; border: none;
  font-family: var(--font);
}
.plan-cta-primary {
  background: var(--blue); color: var(--text);
  box-shadow: var(--shadow-blue);
}
.plan-cta-primary:hover { background: var(--blue-dark); transform: translateY(-1px); }
.plan-cta-ghost {
  background: transparent; color: var(--text);
  border: 1px solid var(--border);
}
.plan-cta-ghost:hover { background: var(--surface-2); }
```

---

## DADOS DOS 4 PLANOS

### STARTER
- **Nome:** Starter
- **Preço mensal:** R$ 97/mês · Anual: R$ 77/mês (cobrado R$ 924/ano)
- **Descrição:** Ideal para condomínios pequenos que estão começando com controle digital de ponto.
- **Funcionários:** Até 15
- **Condomínios:** 1
- **CTA:** "Começar grátis" (ghost)
- **Features:**
  - Registro de ponto via app
  - Dashboard básico
  - Relatórios mensais em PDF
  - App mobile para funcionários
  - Suporte por e-mail
  - ~~Múltiplos condomínios~~ (disabled)
  - ~~API de integração~~ (disabled)
  - ~~Onboarding dedicado~~ (disabled)

### PRO ⭐ (Mais Popular)
- **Nome:** Pro
- **Preço mensal:** R$ 197/mês · Anual: R$ 157/mês (cobrado R$ 1.884/ano)
- **Descrição:** Para condomínios em crescimento que precisam de controle completo e múltiplas unidades.
- **Funcionários:** Até 60
- **Condomínios:** Até 3
- **CTA:** "Começar grátis" (azul primário)
- **Badge:** "Mais Popular"
- **Features:**
  - Tudo do Starter
  - Múltiplos condomínios (até 3)
  - Gestão de tarefas
  - Alertas de atraso e ausência
  - Gestão de férias e atestados
  - API de integração
  - Suporte prioritário

### ADVANCED
- **Nome:** Advanced
- **Preço mensal:** R$ 397/mês · Anual: R$ 317/mês (cobrado R$ 3.804/ano)
- **Descrição:** Para administradoras com múltiplos condomínios e equipes grandes que exigem relatórios avançados.
- **Funcionários:** Até 150
- **Condomínios:** Até 10
- **CTA:** "Começar grátis" (ghost)
- **Features:**
  - Tudo do Pro
  - Até 10 condomínios
  - Relatórios personalizados
  - Exportação para folha de pagamento
  - Permissões avançadas por usuário
  - Webhooks e integrações
  - SLA 99,9% garantido
  - Gerente de conta dedicado

### SCALE
- **Nome:** Scale
- **Preço:** Sob consulta
- **Descrição:** Para grandes administradoras e redes de condomínios com necessidades específicas de contrato.
- **Funcionários:** Ilimitado
- **Condomínios:** Ilimitado
- **CTA:** "Falar com vendas" (ghost)
- **Features:**
  - Tudo do Advanced
  - Funcionários e condomínios ilimitados
  - Onboarding e migração dedicados
  - SLA e contrato personalizados
  - Integração com sistemas legados
  - Treinamento presencial
  - Suporte 24/7 com gerente dedicado
  - NDA e compliance customizado

---

## 5. TABELA COMPARATIVA

```html
<section class="compare-section">
  <div class="compare-inner">
    <div class="section-header" style="text-align:center;margin-bottom:40px;">
      <p class="section-label">COMPARATIVO</p>
      <h2 class="compare-title">Veja o que está incluso em cada plano</h2>
    </div>
    <div class="compare-table-wrap">
      <table class="compare-table">...</table>
    </div>
  </div>
</section>
```

```css
.compare-section {
  background: var(--surface);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  padding: 72px clamp(24px,5vw,80px);
}
.compare-inner { max-width: 1000px; margin: 0 auto; }
.compare-title {
  font-size: clamp(22px,3vw,30px); font-weight: 700;
  letter-spacing: -0.5px; color: var(--text);
}
.compare-table-wrap { overflow-x: auto; }

.compare-table {
  width: 100%; border-collapse: collapse;
  min-width: 640px;
}

/* Header row */
.compare-table thead th {
  padding: 14px 20px;
  font-size: 13px; font-weight: 700;
  text-align: center; color: var(--text);
  background: var(--bg);
  border-bottom: 2px solid var(--border);
}
.compare-table thead th:first-child { text-align: left; width: 38%; }
.compare-table thead th.col-featured { color: var(--blue); }

/* Section header rows */
.compare-table tr.section-row td {
  background: rgba(18,26,40,0.7);
  font-size: 10px; font-weight: 700;
  letter-spacing: 1.2px; text-transform: uppercase;
  color: var(--text-faint);
  padding: 10px 20px;
  border-top: 1px solid var(--border);
}

/* Data rows */
.compare-table tbody tr td {
  padding: 13px 20px;
  font-size: 13px; color: var(--text-muted);
  border-bottom: 1px solid rgba(55,65,81,0.4);
  text-align: center;
}
.compare-table tbody tr td:first-child { text-align: left; color: var(--text); }
.compare-table tbody tr:hover td { background: rgba(55,65,81,0.15); }

/* Check / X SVGs inline */
.check { color: var(--green); font-size: 15px; }
.cross  { color: var(--text-faint); font-size: 15px; opacity: 0.5; }
.val    { font-weight: 600; color: var(--text); }
```

### Conteúdo da tabela

```html
<table class="compare-table">
  <thead>
    <tr>
      <th>Funcionalidade</th>
      <th>Starter</th>
      <th class="col-featured">Pro</th>
      <th>Advanced</th>
      <th>Scale</th>
    </tr>
  </thead>
  <tbody>
    <tr class="section-row"><td colspan="5">Limites</td></tr>
    <tr>
      <td>Funcionários</td>
      <td class="val">15</td>
      <td class="val">60</td>
      <td class="val">150</td>
      <td class="val">Ilimitado</td>
    </tr>
    <tr>
      <td>Condomínios</td>
      <td class="val">1</td>
      <td class="val">3</td>
      <td class="val">10</td>
      <td class="val">Ilimitado</td>
    </tr>
    <tr>
      <td>Usuários gestores</td>
      <td class="val">2</td>
      <td class="val">5</td>
      <td class="val">15</td>
      <td class="val">Ilimitado</td>
    </tr>

    <tr class="section-row"><td colspan="5">Ponto e Jornada</td></tr>
    <tr>
      <td>Registro de ponto via app</td>
      <td>✓</td><td>✓</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
      <td>Dashboard em tempo real</td>
      <td>Básico</td><td class="val">Completo</td><td class="val">Completo</td><td class="val">Completo</td>
    </tr>
    <tr>
      <td>Relatórios PDF mensais</td>
      <td>✓</td><td>✓</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
      <td>Exportação p/ folha de pag.</td>
      <td>—</td><td>—</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
      <td>Relatórios personalizados</td>
      <td>—</td><td>—</td><td>✓</td><td>✓</td>
    </tr>

    <tr class="section-row"><td colspan="5">Gestão de Equipe</td></tr>
    <tr>
      <td>Gestão de faltas e férias</td>
      <td>—</td><td>✓</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
      <td>Gestão de tarefas</td>
      <td>—</td><td>✓</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
      <td>Alertas de ausência</td>
      <td>—</td><td>✓</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
      <td>Permissões avançadas</td>
      <td>—</td><td>—</td><td>✓</td><td>✓</td>
    </tr>

    <tr class="section-row"><td colspan="5">Integrações e API</td></tr>
    <tr>
      <td>API REST</td>
      <td>—</td><td>✓</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
      <td>Webhooks</td>
      <td>—</td><td>—</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
      <td>Integrações legadas</td>
      <td>—</td><td>—</td><td>—</td><td>✓</td>
    </tr>

    <tr class="section-row"><td colspan="5">Suporte</td></tr>
    <tr>
      <td>Suporte por e-mail</td>
      <td>✓</td><td>✓</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
      <td>Suporte prioritário</td>
      <td>—</td><td>✓</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
      <td>Gerente de conta</td>
      <td>—</td><td>—</td><td>✓</td><td>✓</td>
    </tr>
    <tr>
      <td>Suporte 24/7</td>
      <td>—</td><td>—</td><td>—</td><td>✓</td>
    </tr>
    <tr>
      <td>SLA garantido</td>
      <td>—</td><td>—</td><td class="val">99,9%</td><td class="val">Custom</td>
    </tr>
  </tbody>
</table>
```

Substitua `✓` por span com classe `.check` e `—` por span com classe `.cross` para aplicar as cores.

---

## 6. FAQ

```html
<section class="faq-section">
  <div class="faq-inner">
    <p class="section-label" style="text-align:center">PERGUNTAS FREQUENTES</p>
    <h2 class="faq-title">Dúvidas comuns</h2>
    <div class="faq-list">
      <!-- items -->
    </div>
  </div>
</section>
```

```css
.faq-section { padding: 72px clamp(24px,5vw,80px); }
.faq-inner { max-width: 720px; margin: 0 auto; }
.faq-title {
  font-size: 28px; font-weight: 700; letter-spacing: -0.5px;
  text-align: center; margin-bottom: 40px; color: var(--text);
}

.faq-item {
  border-bottom: 1px solid var(--border);
  padding: 18px 0;
  cursor: pointer;
}
.faq-question {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 15px; font-weight: 500; color: var(--text);
}
.faq-question span { font-size: 18px; color: var(--text-muted); transition: transform 0.2s; }
.faq-item.open .faq-question span { transform: rotate(45deg); }
.faq-answer {
  font-size: 14px; color: var(--text-muted); line-height: 1.7;
  margin-top: 12px; display: none;
}
.faq-item.open .faq-answer { display: block; }
```

**5 perguntas:**
1. **Posso testar antes de pagar?** — Sim. Todos os planos têm 14 dias gratuitos, sem cartão de crédito.
2. **Posso trocar de plano depois?** — Sim. Você pode fazer upgrade ou downgrade a qualquer momento pelo painel.
3. **Como os funcionários registram o ponto?** — Pelo app PWA StaFlow no celular. Basta acessar o link e salvar na tela inicial.
4. **Preciso instalar algum software?** — Não. O StaFlow é 100% web — funciona em qualquer navegador e não precisa de instalação.
5. **Quais formas de pagamento são aceitas?** — Cartão de crédito, boleto bancário e Pix. Faturamento mensal ou anual.

```js
// FAQ accordion
document.querySelectorAll('.faq-item').forEach(item => {
  item.querySelector('.faq-question').addEventListener('click', () => {
    item.classList.toggle('open');
  });
});
```

---

## 7. CTA FINAL

```html
<section class="cta-section">
  <div class="cta-inner">
    <p class="section-label">COMECE AGORA</p>
    <h2 class="cta-title">Experimente grátis por 14 dias</h2>
    <p class="cta-sub">
      Escolha qualquer plano e teste sem compromisso. Sem cartão de crédito.
    </p>
    <div class="cta-actions">
      <a href="auth/cadastro.html" class="btn-primary-xl">Criar conta gratuita</a>
      <a href="#" class="btn-ghost-xl">Falar com vendas</a>
    </div>
    <p class="cta-note">14 dias grátis · Cancele a qualquer momento · LGPD compliant</p>
  </div>
</section>
```

```css
.cta-section {
  background: var(--surface);
  border-top: 1px solid var(--border);
  padding: 80px clamp(24px,5vw,80px);
  text-align: center;
  position: relative; overflow: hidden;
}
.cta-section::before {
  content: '';
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  width: 600px; height: 400px;
  background: radial-gradient(ellipse, rgba(59,130,246,0.07) 0%, transparent 70%);
  pointer-events: none;
}
.cta-inner { position: relative; z-index: 1; }
.cta-title {
  font-size: clamp(28px,4vw,40px); font-weight: 800;
  letter-spacing: -1px; color: var(--text); margin-bottom: 14px;
}
.cta-sub { font-size: 16px; color: var(--text-muted); max-width: 440px; margin: 0 auto 32px; }
.cta-actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 20px; }
.btn-primary-xl {
  background: var(--blue); color: var(--text); border: none;
  padding: 14px 28px; border-radius: var(--radius-md);
  font-size: 15px; font-weight: 600; cursor: pointer;
  text-decoration: none; box-shadow: var(--shadow-blue);
  transition: background 0.15s, transform 0.1s;
}
.btn-primary-xl:hover { background: var(--blue-dark); transform: translateY(-1px); }
.btn-ghost-xl {
  background: transparent; color: var(--text);
  border: 1px solid var(--border);
  padding: 13px 24px; border-radius: var(--radius-md);
  font-size: 15px; font-weight: 500; text-decoration: none;
  transition: background 0.15s;
}
.btn-ghost-xl:hover { background: rgba(55,65,81,0.4); }
.cta-note { font-size: 12px; color: var(--text-faint); }
```

---

## REGRAS

1. **4 planos exatos**: Starter · Pro · Advanced · Scale — não alterar nomes nem preços
2. **Pro é o featured** — destaque azul, badge "Mais Popular", botão primário
3. **Toggle mensal/anual** obrigatório com JS funcionando
4. **Preços anuais = preço mensal × 0,8** (desconto de 20%)
5. **Tabela comparativa** com todas as linhas especificadas
6. **FAQ com accordion** JavaScript funcional
7. **Sem sidebar** — página standalone com navbar da landing
8. **Grid 4 colunas** em desktop; 2 colunas em tablet (768px); 1 coluna em mobile
9. **Cores do design system** — nunca inventar novas cores
10. **Botões "Criar conta"** linkam para `auth/cadastro.html`

---

*Prompt — Página de Planos StaFlow · Starter / Pro / Advanced / Scale · Design System v2.0*
