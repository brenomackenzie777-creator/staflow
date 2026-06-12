# Prompt para Claude Code — `colaborador.html` (App do Funcionário)

> Cole este prompt no Claude Code para implementar o PWA mobile do funcionário StaFlow no visual enterprise aprovado.

---

## CONTEXTO

Reimplemente `colaborador.html` como PWA mobile (viewport 375–430px). É o app que o funcionário (porteiro, zelador, segurança) usa no celular para registrar ponto, ver tarefas e enviar atestados. O elemento central é o **botão de registro de ponto** — deve ser grande, tátil e claro. O visual é escuro, limpo, sem elementos decorativos desnecessários.

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
  --red:         #EF4444;
  --amber:       #F59E0B;
  --border:      #374151;
  --radius-md:   8px;
  --radius-lg:   12px;
  --radius-xl:   16px;
  --font:        'Inter', -apple-system, sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  height: 100%;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  -webkit-font-smoothing: antialiased;
  overscroll-behavior: none;
}

body {
  max-width: 430px;
  margin: 0 auto;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}
```

Fonte: `Inter` via Google Fonts, pesos 400 500 600 700.

---

## ESTRUTURA HTML

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <meta name="theme-color" content="#111827">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <title>StaFlow — Meu Ponto</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>/* CSS aqui */</style>
</head>
<body>

  <!-- Status bar simulada -->
  <div class="status-bar">
    <span class="status-time" id="statusTime">08:47</span>
    <div class="status-icons">
      <!-- ícones de sinal/bateria SVG pequenos -->
    </div>
  </div>

  <!-- Header do app -->
  <header class="app-header">
    <div class="app-logo">Sta<span>Flow</span></div>
    <button class="avatar-btn" aria-label="Perfil">
      <span id="userInitials">JS</span>
    </button>
  </header>

  <!-- Saudação -->
  <div class="greeting">
    <p class="greeting-name" id="userName">João Silva</p>
    <p class="greeting-role" id="userRole">Porteiro · Turno Manhã</p>
  </div>

  <!-- Conteúdo scrollável -->
  <main class="app-main">

    <!-- Seção de registro de ponto -->
    <section class="punch-section">
      <button class="punch-btn" id="punchBtn" aria-label="Registrar ponto">
        <div class="punch-icon">
          <!-- SVG checkmark -->
        </div>
        <span class="punch-label" id="punchLabel">REGISTRAR<br>PONTO</span>
      </button>

      <!-- Relógio -->
      <div class="clock">
        <p class="clock-time" id="clockTime">08:47</p>
        <p class="clock-date" id="clockDate">Quinta-feira, 11 Jun 2026</p>
      </div>

      <!-- Badges de status -->
      <div class="punch-badges">
        <span class="badge badge-green" id="entradaBadge">Entrada 08:02</span>
        <span class="badge badge-gray" id="jornadaBadge">Jornada 0h45</span>
      </div>
    </section>

    <!-- Registros recentes -->
    <section class="records-section">
      <div class="section-label-row">
        <span class="section-label-sm">ÚLTIMOS REGISTROS</span>
      </div>
      <div class="records-list" id="recordsList">
        <!-- preenchido abaixo -->
      </div>
    </section>

  </main>

  <!-- Bottom navigation -->
  <nav class="bottom-nav">
    <a href="#ponto"    class="nav-item active" data-tab="ponto">
      <!-- SVG relógio -->
      <span>Ponto</span>
    </a>
    <a href="#tarefas"  class="nav-item" data-tab="tarefas">
      <!-- SVG clipboard -->
      <span>Tarefas</span>
    </a>
    <a href="#atestado" class="nav-item" data-tab="atestado">
      <!-- SVG documento -->
      <span>Atestado</span>
    </a>
    <a href="#perfil"   class="nav-item" data-tab="perfil">
      <!-- SVG usuário -->
      <span>Perfil</span>
    </a>
  </nav>

</body>
</html>
```

---

## CSS COMPLETO

### Status bar

```css
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 24px 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  height: 36px;
}
.status-icons { display: flex; gap: 6px; align-items: center; }
.status-icons svg { width: 14px; height: 14px; }
```

### Header

```css
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
}

.app-logo {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.4px;
  color: var(--text);
}
.app-logo span { color: var(--blue); }

.avatar-btn {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--blue);
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: border-color 0.15s;
}
.avatar-btn:hover { border-color: var(--blue-border); }
```

### Saudação

```css
.greeting {
  padding: 2px 20px 16px;
}
.greeting-name {
  font-size: 17px;
  font-weight: 600;
  color: var(--text);
}
.greeting-role {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-top: 2px;
}
```

### Main scrollável

```css
.app-main {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px;
  padding-bottom: 80px; /* espaço para o bottom nav */
}
```

### BOTÃO DE PONTO (elemento principal)

```css
.punch-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0 16px;
}

/* O botão circular */
.punch-btn {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
  transition: transform 0.12s, box-shadow 0.12s;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;

  /* Estado padrão — Registrar Entrada */
  background: var(--blue);
  box-shadow:
    0 0 0 14px rgba(59,130,246,0.08),
    0 0 0 28px rgba(59,130,246,0.04),
    0 16px 40px rgba(59,130,246,0.35);
}

.punch-btn:active {
  transform: scale(0.95);
  box-shadow:
    0 0 0 8px rgba(59,130,246,0.08),
    0 8px 20px rgba(59,130,246,0.25);
}

/* Variante — quando já registrou entrada (saída) */
.punch-btn.state-saida {
  background: var(--surface);
  border: 2px solid var(--border);
  box-shadow:
    0 0 0 14px rgba(55,65,81,0.08),
    0 0 0 28px rgba(55,65,81,0.03),
    0 16px 40px rgba(0,0,0,0.3);
  color: var(--text);
}
.punch-btn.state-saida:active {
  box-shadow: 0 0 0 8px rgba(55,65,81,0.08), 0 8px 20px rgba(0,0,0,0.2);
}

.punch-icon {
  width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
}
.punch-icon svg {
  width: 36px; height: 36px;
}

/* Checkmark SVG — cor escura sobre botão azul */
.punch-btn svg { stroke: rgba(10,15,25,0.8); }
.punch-btn.state-saida svg { stroke: var(--text); }

.punch-label {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-align: center;
  line-height: 1.3;
  color: rgba(10,15,25,0.85);
  pointer-events: none;
}
.punch-btn.state-saida .punch-label { color: var(--text); }
```

### Relógio digital

```css
.clock {
  margin-top: 24px;
  text-align: center;
}
.clock-time {
  font-size: 44px;
  font-weight: 800;
  letter-spacing: -2px;
  color: var(--text);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.clock-date {
  font-size: 12px;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  margin-top: 6px;
}
```

### Badges de status

```css
.punch-badges {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 14px;
  flex-wrap: wrap;
}

.badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 11px;
  border-radius: var(--radius-md);
  font-size: 11px; font-weight: 500;
  letter-spacing: 0.3px;
}
.badge-green  { background:rgba(16,185,129,0.12); color:#10B981; border:1px solid rgba(16,185,129,0.3); }
.badge-blue   { background:rgba(59,130,246,0.12);  color:#3B82F6; border:1px solid rgba(59,130,246,0.3); }
.badge-red    { background:rgba(239,68,68,0.12);   color:#EF4444; border:1px solid rgba(239,68,68,0.3); }
.badge-amber  { background:rgba(245,158,11,0.12);  color:#F59E0B; border:1px solid rgba(245,158,11,0.3); }
.badge-gray   { background:rgba(107,114,128,0.15); color:#9CA3AF; border:1px solid rgba(107,114,128,0.3); }
```

### Seção de registros

```css
.records-section {
  margin-top: 20px;
}

.section-label-row {
  margin-bottom: 10px;
}
.section-label-sm {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--text-faint);
}

.records-list {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.record-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(55,65,81,0.5);
}
.record-row:last-child { border-bottom: none; }

.record-time {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  font-variant-numeric: tabular-nums;
  min-width: 44px;
}
.record-type { font-size: 13px; color: var(--text-muted); flex: 1; margin: 0 12px; }
.record-date { font-size: 11px; color: var(--text-faint); }
```

### Bottom navigation

```css
.bottom-nav {
  position: fixed;
  bottom: 0; left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 430px;
  background: var(--surface);
  border-top: 1px solid var(--border);
  display: flex;
  padding: 8px 0 max(12px, env(safe-area-inset-bottom));
  z-index: 100;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 4px 0;
  text-decoration: none;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.nav-item svg {
  width: 22px; height: 22px;
  stroke: var(--text-faint);
  transition: stroke 0.12s;
}
.nav-item span {
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: var(--text-faint);
  transition: color 0.12s;
}
.nav-item.active svg { stroke: var(--blue); }
.nav-item.active span { color: var(--blue); }
```

---

## DADOS ESTÁTICOS (hardcode inicial)

### Registros recentes no HTML

```html
<div class="records-list">
  <div class="record-row">
    <span class="record-time">08:02</span>
    <span class="record-type">Entrada</span>
    <span class="record-date badge badge-green">Hoje</span>
  </div>
  <div class="record-row">
    <span class="record-time">17:58</span>
    <span class="record-type">Saída</span>
    <span class="record-date">Ontem</span>
  </div>
  <div class="record-row">
    <span class="record-time">08:05</span>
    <span class="record-type">Entrada</span>
    <span class="record-date">Ontem</span>
  </div>
  <div class="record-row">
    <span class="record-time">18:01</span>
    <span class="record-type">Saída</span>
    <span class="record-date">10/06</span>
  </div>
</div>
```

---

## JAVASCRIPT — Relógio em tempo real

```js
function padZero(n) { return String(n).padStart(2, '0'); }

function updateClock() {
  const now = new Date();
  const h = padZero(now.getHours());
  const m = padZero(now.getMinutes());
  const s = padZero(now.getSeconds());

  document.getElementById('clockTime').textContent = `${h}:${m}`;
  document.getElementById('statusTime').textContent = `${h}:${m}`;

  const dias = ['Domingo','Segunda-feira','Terça-feira','Quarta-feira',
                'Quinta-feira','Sexta-feira','Sábado'];
  const meses = ['Jan','Fev','Mar','Abr','Mai','Jun',
                 'Jul','Ago','Set','Out','Nov','Dez'];
  const dateStr = `${dias[now.getDay()]}, ${now.getDate()} ${meses[now.getMonth()]} ${now.getFullYear()}`;
  document.getElementById('clockDate').textContent = dateStr;
}

updateClock();
setInterval(updateClock, 1000);
```

## JAVASCRIPT — Toggle estado do botão de ponto

```js
let pontoState = 'entrada'; // 'entrada' ou 'saida'

document.getElementById('punchBtn').addEventListener('click', function() {
  if (pontoState === 'entrada') {
    // Registrou entrada
    pontoState = 'saida';
    this.classList.add('state-saida');
    document.getElementById('punchLabel').innerHTML = 'REGISTRAR<br>SAÍDA';

    // Atualizar badge
    const now = new Date();
    const h = String(now.getHours()).padStart(2,'0');
    const m = String(now.getMinutes()).padStart(2,'0');
    document.getElementById('entradaBadge').textContent = `Entrada ${h}:${m}`;
    document.getElementById('jornadaBadge').textContent = 'Jornada 0h00';

    // Feedback visual breve (escala)
    this.style.transform = 'scale(0.95)';
    setTimeout(() => this.style.transform = '', 150);

  } else {
    // Registrou saída — resetar
    pontoState = 'entrada';
    this.classList.remove('state-saida');
    document.getElementById('punchLabel').innerHTML = 'REGISTRAR<br>PONTO';
    document.getElementById('entradaBadge').textContent = 'Sem entrada hoje';
    document.getElementById('jornadaBadge').textContent = 'Jornada —';
  }
});
```

---

## SVG ICONS (copie inline)

### Ícone checkmark para o botão
```html
<svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="18" cy="18" r="14" stroke-opacity="0.25" stroke-width="1.5"/>
  <path d="M12 18.5L16.5 23L24 14" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

### Ícone relógio (nav Ponto)
```html
<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8">
  <circle cx="12" cy="12" r="9"/>
  <polyline points="12 6 12 12 16 14"/>
</svg>
```

### Ícone clipboard (nav Tarefas)
```html
<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8">
  <rect x="8" y="2" width="8" height="4" rx="1"/>
  <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
  <line x1="9" y1="12" x2="15" y2="12"/>
  <line x1="9" y1="16" x2="13" y2="16"/>
</svg>
```

### Ícone documento (nav Atestado)
```html
<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8">
  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
  <polyline points="14 2 14 8 20 8"/>
  <line x1="9" y1="13" x2="15" y2="13"/>
  <line x1="9" y1="17" x2="13" y2="17"/>
</svg>
```

### Ícone usuário (nav Perfil)
```html
<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8">
  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
  <circle cx="12" cy="7" r="4"/>
</svg>
```

---

## REGRAS

1. **Viewport móvel única** — max-width 430px, nunca renderizar como desktop
2. **Botão de ponto** — elemento central, 180px de diâmetro, nunca reduzir
3. **Sem tabelas** — conteúdo em cards e listas verticais
4. **Touch-friendly** — elementos clicáveis mínimo 44px de altura
5. **`user-scalable=no`** no viewport meta — comportamento de app nativo
6. **`env(safe-area-inset-bottom)`** no bottom nav — suporte a iPhone com home indicator
7. **Relógio atualiza a cada segundo** via `setInterval`
8. **Cor base #111827** — nunca preto puro

---

*Prompt — App do Funcionário (PWA Mobile) StaFlow · Design System v2.0*
