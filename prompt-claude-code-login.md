# Prompt para Claude Code — `login.html` e `cadastro.html`

> Cole este prompt no Claude Code para implementar as telas de autenticação do StaFlow no visual enterprise aprovado.

---

## CONTEXTO

Reimplemente `auth/login.html` e `auth/cadastro.html`. São páginas standalone (sem sidebar), com card centralizado sobre o fundo escuro. Visual sóbrio, enterprise, sem exagero gráfico.

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
  --red:         #EF4444;
  --border:      #374151;
  --radius-md:   6px;
  --radius-lg:   8px;
  --shadow-lg:   0 8px 32px rgba(0,0,0,0.5);
  --font:        'Inter', -apple-system, sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 14px;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  position: relative;
  -webkit-font-smoothing: antialiased;
}

/* Glow radial sutil no canto superior direito */
body::before {
  content: '';
  position: fixed;
  top: -200px; right: -200px;
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 65%);
  pointer-events: none;
}
```

Fonte: `Inter` via Google Fonts, pesos 400 500 600 700.

---

## ESTRUTURA HTML BASE (ambas as páginas)

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title><!-- Login ou Criar conta --> · StaFlow</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>/* CSS aqui */</style>
</head>
<body>
  <div class="auth-wrapper">
    <div class="auth-card">

      <!-- Logo -->
      <div class="auth-brand">
        <a href="../index.html" class="brand-logo">
          Sta<span>Flow</span>
        </a>
        <p class="brand-tagline">Gestão de ponto para condomínios</p>
      </div>

      <div class="auth-divider"></div>

      <!-- Conteúdo específico (login ou cadastro) -->

    </div>
    <p class="auth-footer">© 2026 StaFlow · Todos os direitos reservados</p>
  </div>
</body>
</html>
```

---

## CSS DO CARD E COMPONENTES

```css
.auth-wrapper {
  width: 100%;
  max-width: 440px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  position: relative;
  z-index: 1;
}

.auth-card {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 36px 40px 32px;
  box-shadow: var(--shadow-lg);
}

/* Logo */
.auth-brand { text-align: center; margin-bottom: 24px; }

.brand-logo {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: var(--text);
  text-decoration: none;
}
.brand-logo span { color: var(--blue); }

.brand-tagline {
  font-size: 12px;
  color: var(--text-faint);
  letter-spacing: 0.3px;
  margin-top: 6px;
}

/* Divisor */
.auth-divider {
  height: 1px;
  background: var(--border);
  margin-bottom: 28px;
}

/* Título do formulário */
.auth-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.4px;
  color: var(--text);
  margin-bottom: 6px;
}
.auth-sub {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 24px;
  line-height: 1.5;
}

/* Campos */
.field { margin-bottom: 16px; }

.field label {
  display: block;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.3px;
  text-transform: uppercase;
  color: var(--text-faint);
  margin-bottom: 6px;
}

.field input {
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 11px 14px;
  font-family: var(--font);
  font-size: 14px;
  color: var(--text);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.field input::placeholder { color: var(--text-faint); }
.field input:focus {
  border-color: var(--blue-border);
  box-shadow: 0 0 0 3px var(--blue-dim);
}

/* Campo com botão interno (senha) */
.input-wrap { position: relative; }
.input-wrap input { padding-right: 52px; }
.toggle-pass {
  position: absolute; right: 12px; top: 50%;
  transform: translateY(-50%);
  background: none; border: none;
  font-size: 10px; font-weight: 600; letter-spacing: 0.8px;
  color: var(--text-faint); cursor: pointer; padding: 4px;
  transition: color 0.15s;
}
.toggle-pass:hover { color: var(--blue); }

/* Mensagem de erro de campo */
.field-error {
  font-size: 11px;
  color: var(--red);
  margin-top: 5px;
  display: none;
}
.field.has-error input { border-color: var(--red); }
.field.has-error .field-error { display: block; }

/* Botão principal */
.btn-submit {
  width: 100%;
  background: var(--blue);
  color: var(--text);
  border: none;
  border-radius: var(--radius-md);
  padding: 12px;
  font-family: var(--font);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
  transition: background 0.15s, transform 0.1s;
  box-shadow: 0 4px 14px rgba(59,130,246,0.25);
}
.btn-submit:hover { background: var(--blue-dark); transform: translateY(-1px); }
.btn-submit:active { transform: translateY(0); }

/* Links auxiliares */
.auth-aux {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 18px;
}
.auth-link {
  font-size: 13px;
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.15s;
}
.auth-link:hover { color: var(--blue); }

/* Divisor "ou" */
.auth-or {
  display: flex; align-items: center; gap: 12px;
  margin: 20px 0;
  font-size: 12px; color: var(--text-faint);
}
.auth-or::before, .auth-or::after {
  content: ''; flex: 1; height: 1px; background: var(--border);
}

/* Footer */
.auth-footer {
  font-size: 11px;
  color: var(--text-faint);
  letter-spacing: 0.5px;
}
```

---

## PÁGINA 1: LOGIN (`auth/login.html`)

### Conteúdo do card

```html
<h1 class="auth-title">Entrar</h1>
<p class="auth-sub">Acesse o painel do seu condomínio.</p>

<form id="loginForm" novalidate>

  <div class="field">
    <label for="email">E-mail</label>
    <input id="email" type="email" name="email"
           placeholder="voce@condominio.com.br" autocomplete="email">
  </div>

  <div class="field">
    <label for="senha">Senha</label>
    <div class="input-wrap">
      <input id="senha" type="password" name="senha"
             placeholder="••••••••" autocomplete="current-password">
      <button class="toggle-pass" type="button" aria-label="Mostrar senha">VER</button>
    </div>
  </div>

  <button class="btn-submit" type="submit">Entrar na conta</button>

  <div class="auth-aux">
    <a href="recuperar-senha.html" class="auth-link">Esqueci minha senha</a>
    <a href="cadastro.html" class="auth-link">Criar conta →</a>
  </div>

</form>
```

### JavaScript de toggle de senha

```js
document.querySelector('.toggle-pass').addEventListener('click', function() {
  const input = document.getElementById('senha');
  const isPass = input.type === 'password';
  input.type = isPass ? 'text' : 'password';
  this.textContent = isPass ? 'OCULTAR' : 'VER';
});
```

---

## PÁGINA 2: CADASTRO (`auth/cadastro.html`)

### Conteúdo do card

```html
<h1 class="auth-title">Criar conta</h1>
<p class="auth-sub">14 dias grátis. Sem cartão de crédito.</p>

<form id="cadastroForm" novalidate>

  <div class="form-row" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
    <div class="field">
      <label for="nome">Nome</label>
      <input id="nome" type="text" placeholder="Seu nome" autocomplete="given-name">
    </div>
    <div class="field">
      <label for="sobrenome">Sobrenome</label>
      <input id="sobrenome" type="text" placeholder="Sobrenome" autocomplete="family-name">
    </div>
  </div>

  <div class="field">
    <label for="email">E-mail profissional</label>
    <input id="email" type="email" placeholder="voce@condominio.com.br" autocomplete="email">
  </div>

  <div class="field">
    <label for="condominio">Nome do condomínio</label>
    <input id="condominio" type="text" placeholder="Ex: Edifício Central Park">
  </div>

  <div class="field">
    <label for="senha">Senha</label>
    <div class="input-wrap">
      <input id="senha" type="password" placeholder="Mínimo 8 caracteres"
             autocomplete="new-password">
      <button class="toggle-pass" type="button" aria-label="Mostrar senha">VER</button>
    </div>
    <!-- Barra de força de senha -->
    <div class="pwd-strength" id="pwdStrength">
      <div class="pwd-bar"></div>
      <div class="pwd-bar"></div>
      <div class="pwd-bar"></div>
      <div class="pwd-bar"></div>
    </div>
  </div>

  <!-- Checkbox termos -->
  <label class="checkbox-label">
    <input type="checkbox" id="termos">
    <span>Li e aceito os <a href="#" class="auth-link">Termos de Uso</a> e
    <a href="#" class="auth-link">Política de Privacidade</a></span>
  </label>

  <button class="btn-submit" type="submit" style="margin-top:16px;">
    Criar conta grátis
  </button>

  <p style="text-align:center;margin-top:16px;font-size:13px;color:var(--text-muted)">
    Já tem uma conta? <a href="login.html" class="auth-link">Entrar →</a>
  </p>

</form>
```

### CSS adicional cadastro

```css
/* Barra de força de senha */
.pwd-strength {
  display: flex; gap: 4px; margin-top: 8px;
}
.pwd-bar {
  flex: 1; height: 3px; border-radius: 2px;
  background: var(--surface-2);
  transition: background 0.2s;
}
/* JS adiciona classes: .weak .fair .strong .very-strong */
.pwd-strength.weak      .pwd-bar:nth-child(1) { background: var(--red); }
.pwd-strength.fair      .pwd-bar:nth-child(-n+2) { background: var(--amber); }
.pwd-strength.strong    .pwd-bar:nth-child(-n+3) { background: var(--blue); }
.pwd-strength.very-strong .pwd-bar { background: var(--green); }

/* Checkbox */
.checkbox-label {
  display: flex; align-items: flex-start; gap: 10px;
  font-size: 13px; color: var(--text-muted); cursor: pointer;
  margin-top: 4px; line-height: 1.5;
}
.checkbox-label input[type="checkbox"] {
  width: 16px; height: 16px; flex-shrink: 0; margin-top: 1px;
  accent-color: var(--blue); cursor: pointer;
}
```

### JavaScript força de senha

```js
document.getElementById('senha').addEventListener('input', function() {
  const val = this.value;
  const bar = document.getElementById('pwdStrength');
  bar.className = 'pwd-strength';
  if (!val) return;
  if (val.length < 6) bar.classList.add('weak');
  else if (val.length < 8) bar.classList.add('fair');
  else if (val.length < 12 || !/[^a-zA-Z0-9]/.test(val)) bar.classList.add('strong');
  else bar.classList.add('very-strong');
});
```

---

## REGRAS

1. **Sem sidebar, sem topbar** — páginas completamente standalone
2. **Fundo `#111827`** com glow radial sutil (azul baixa opacidade) — sem gradiente de cor forte
3. **Logo linka para `../index.html`** (landing page)
4. **Campos com placeholder acinzentado** — `var(--text-faint)`
5. **Nenhum campo com `required` HTML** — validação deve ser feita por JS se implementada
6. **`autocomplete`** nos inputs para melhor UX
7. **Responsivo** — card fullwidth em mobile, `padding: 28px 24px`

---

*Prompt — Login & Cadastro StaFlow · Design System v2.0*
